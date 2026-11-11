"""Independent platform workflows based on verified public request behavior.

No old project imports, no notifications, no device rotation or identity changes.
"""
import math
import time
from .http import RequestFailure
from .models import Outcome

WB_BASE = 'https://www.codebuddy.cn'
WB_STATUS = '/v2/billing/meter/checkin-activity-status'
WB_CLAIM = '/v2/billing/meter/daily-checkin'
TR_BASE = 'https://api.trae.cn'
TR_STATUS = TR_BASE + '/trae/api/v2/ug/checkin_credits/status'
TR_CLAIM = TR_BASE + '/trae/api/v2/ug/checkin_credits/claim'
TR_BALANCE = TR_BASE + '/trae/api/v2/pay/ide_user_ent_usage'
TR_EXCHANGE = 'https://api.trae.com.cn/cloudide/api/v3/trae/oauth/ExchangeToken'
TR_CLIENT = 'en1oxy7wnw8j9n'
TR_VERSION = '0.1.43'


def number(value):
    if isinstance(value, bool):
        return None
    try:
        result = float(value)
        return result if math.isfinite(result) else None
    except (TypeError, ValueError):
        return None


def scope(payload):
    return payload['data'] if isinstance(payload.get('data'), dict) else payload


def accepted(payload):
    return isinstance(payload, dict) and payload.get('code') in (None, 0, 200, '0', '200') and payload.get('success') is not False


def message(payload):
    return str(payload.get('message') or payload.get('msg') or scope(payload).get('message') or '接口拒绝请求')


def checked(payload):
    if str(payload.get('code')) == '9095':
        return False
    if str(payload.get('code')) == '10001':
        return True
    if not accepted(payload):
        return False
    for obj in (scope(payload), payload):
        for key in ('today_checked_in', 'checked_in', 'checkedIn', 'claimed', 'did_checked_in', 'is_checked_in'):
            if key in obj:
                return obj[key] is True or str(obj[key]).lower() in ('true', '1')
    text = message(payload).lower()
    return '设备' not in text and any(word in text for word in ('已签到', '已经签到', 'already checked', 'already claimed'))


def failure(payload):
    return Outcome('失败', detail=f"接口 code={payload.get('code')}：{message(payload)}")


def known_status(payload):
    if checked(payload):
        return True
    for obj in (scope(payload), payload):
        for key in ('today_checked_in', 'checked_in', 'checkedIn', 'claimed', 'did_checked_in', 'is_checked_in'):
            if key in obj and (isinstance(obj[key], bool) or str(obj[key]).lower() in ('0', '1', 'true', 'false')):
                return True
    return '未签到' in message(payload)


class WorkBuddy:
    def __init__(self, http):
        self.http = http

    def run(self, account, status_only=False):
        c = account['credentials']
        headers = {'Authorization': 'Bearer ' + c['access_token'], 'Accept': 'application/json'}
        for key, name in [('uid', 'X-User-Id'), ('domain', 'X-Domain'), ('enterprise_id', 'X-Enterprise-Id')]:
            if c.get(key):
                headers[name] = str(c[key])
        if c.get('enterprise_id'):
            headers['X-Tenant-Id'] = str(c['enterprise_id'])
        call = lambda route: self.http.post(WB_BASE + route, headers, {})
        status = call(WB_STATUS)
        was_checked = checked(status)
        if not was_checked and not accepted(status):
            return failure(status)
        if not known_status(status):
            return Outcome('失败', detail='无法识别签到状态，已停止领取，请稍后重试')
        if status_only and not was_checked:
            return Outcome('未签到', detail='今日尚未领取；本次只查询，不领取')
        if not was_checked:
            claimed = call(WB_CLAIM)
            if not accepted(claimed) and not checked(claimed):
                return failure(claimed)
            was_checked = checked(claimed)
            status = call(WB_STATUS)
            if not checked(status):
                return Outcome('失败', detail='领取后回查未确认签到，请稍后查询状态')
        earned = None if was_checked or status_only else number(scope(status).get('daily_credit'))
        balance = None
        try:
            summary = call('/billing/meter/get-user-resource-summary')
            packages = scope(summary).get('Packages', []) if accepted(summary) else []
            values = [number(p.get('CycleRemainCapacity')) for p in packages if isinstance(p, dict)]
            if values and all(value is not None for value in values):
                balance = sum(values)
        except RequestFailure:
            pass
        return Outcome('已签到' if was_checked else '成功', earned, balance,
                       '今日已领取，不重复签到' if was_checked else ('签到已确认' + ('；余额未获取' if balance is None else '')))


class Trae:
    def __init__(self, http):
        self.http = http

    def refresh(self, credentials):
        payload = self.http.post(TR_EXCHANGE, {}, {'ClientID': TR_CLIENT, 'ClientSecret': '-',
            'RefreshToken': credentials['refreshToken'], 'UserID': credentials.get('userId', '')})
        obj = payload.get('Result') if isinstance(payload.get('Result'), dict) else scope(payload)
        token = obj.get('Token') or obj.get('AccessToken') or obj.get('access_token')
        if not token:
            raise RequestFailure('Trae 登录已失效，请重新添加该账号')
        credentials['accessToken'] = token
        credentials['refreshToken'] = obj.get('RefreshToken') or obj.get('refreshToken') or obj.get('refresh_token') or credentials['refreshToken']
        expires = number(obj.get('TokenExpireAt') or obj.get('expiresAt'))
        if expires:
            credentials['expiresAt'] = expires / 1000 if expires > 1e12 else expires

    def run(self, account, status_only=False):
        c = account['credentials']
        if not c.get('claimDeviceId'):
            return Outcome('失败', detail='缺少本机官方客户端设备信息，请重新登录添加')
        if number(c.get('expiresAt')) is not None and c['expiresAt'] < time.time() + 86400:
            self.refresh(c)
        def headers():
            return {'Authorization': 'Cloud-IDE-JWT ' + c['accessToken'], 'x-device-id': c['claimDeviceId'],
                    'X-Device-Id': c['claimDeviceId'], 'X-User-Region': 'CN', 'x-device-brand': 'PC',
                    'x-device-type': 'PC', 'x-os-version': 'Windows', 'x-app-version': TR_VERSION,
                    'User-Agent': 'Trae/' + TR_VERSION}
        call = lambda url: self.http.post(url, headers(), {})
        def balance():
            try:
                payload = call(TR_BALANCE)
                obj = scope(payload)
                usage = obj.get('usage_summary') or {}
                total, used = number(usage.get('total_amount')), number(usage.get('consumed_amount'))
                if accepted(payload) and total is not None and used is not None:
                    return total - used
            except RequestFailure:
                pass
            return None
        status = call(TR_STATUS)
        if str(status.get('code')) == '1001':
            try:
                self.refresh(c)
            except RequestFailure as exc:
                return Outcome('失败', detail=str(exc))
            status = call(TR_STATUS)
        if str(status.get('code')) == '9095':
            return Outcome('设备受限', detail='9095：该设备今日领取受限，本账号不记为签到成功')
        if checked(status):
            return Outcome('已签到', balance=balance(), detail='今日已领取，不重复签到')
        if not accepted(status):
            return failure(status)
        if not known_status(status):
            return Outcome('失败', detail='无法识别签到状态，已停止领取，请稍后重试')
        if status_only:
            return Outcome('未签到', detail='今日尚未领取；本次只查询，不领取')
        before = balance()
        claim = call(TR_CLAIM)
        if str(claim.get('code')) == '1001':
            self.refresh(c)
            claim = call(TR_CLAIM)
        if str(claim.get('code')) == '9095':
            return Outcome('设备受限', detail='9095：该设备今日已领取，请按平台规则使用；不会更改设备或重复请求')
        if not accepted(claim):
            return failure(claim)
        status = call(TR_STATUS)
        if not checked(status):
            time.sleep(1)
            status = call(TR_STATUS)
        if not checked(status):
            return Outcome('失败', detail='领取后回查未确认到账，请稍后查询状态')
        after = balance()
        earned = after - before if before is not None and after is not None and after > before else None
        # Do not turn a platform estimate into a measured gain.
        return Outcome('成功', earned, after, '签到已确认' + ('；本次获得未能实测' if earned is None else '') + ('；余额未获取' if after is None else ''))
