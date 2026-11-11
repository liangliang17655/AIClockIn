"""One sequential run, stable account IDs, and truthful persistent results."""
import re
import uuid
from .http import HTTP
from .models import Outcome
from .providers import WorkBuddy, Trae
from .store import OperationLock


def scrub(text, accounts=()):
    text = str(text)
    values = [str(v) for row in accounts for v in row.get('credentials', {}).values() if isinstance(v, (str, int)) and str(v)]
    for value in sorted(set(values), key=len, reverse=True):
        text = text.replace(value, '***')
    text = re.sub(r'(?i)(?:Bearer|Cloud-IDE-JWT)\s+[^\s,;"\x27}]+', '***', text)
    text = re.sub(r'(?i)((?:access_?token|refresh_?token|token|secret|userJwt)\s*["\x27]?\s*[:=]\s*["\x27]?)[^\s,;"\x27}]+', r'\1***', text)
    return text.replace('\r', ' ').replace('\n', ' ')[:1200]


class Service:
    def __init__(self, store, http=None):
        self.store = store
        self.http = http or HTTP()

    @staticmethod
    def owner(platform, credentials):
        return str(credentials.get('uid') or credentials.get('userId') or credentials.get('access_token') or '')

    def merge(self, accounts, platform, credentials, name):
        identity = self.owner(platform, credentials)
        match = next((a for a in accounts if a['platform'] == platform and self.owner(platform, a['credentials']) == identity), None)
        if match:
            match['credentials'] = credentials
        else:
            accounts.append({'id': str(uuid.uuid4()), 'platform': platform, 'name': name,
                             'enabled': True, 'credentials': credentials})

    def import_workbuddy(self):
        from .auth import workbuddy_accounts
        with OperationLock(self.store.root):
            found = workbuddy_accounts()
            if not found:
                raise ValueError('没有发现有效 WorkBuddy 登录。请先在官方桌面端登录，再点击添加。')
            accounts = self.store.accounts()
            for item in found:
                name = item.pop('name', '') or 'WorkBuddy 账号'
                item.pop('enabled', None)
                self.merge(accounts, 'workbuddy', item, name)
            self.store.save_accounts(accounts)
            return f'已添加或更新 {len(found)} 个 WorkBuddy 账号'

    def login_trae(self):
        from .auth import login_trae
        with OperationLock(self.store.root):
            credentials, name = login_trae(self.http)
            accounts = self.store.accounts()
            self.merge(accounts, 'trae', credentials, name)
            self.store.save_accounts(accounts)
            return 'Trae CN 账号已添加'

    def edit(self, account_id, name=None, enabled=None, delete=False):
        with OperationLock(self.store.root):
            accounts = self.store.accounts()
            row = next((a for a in accounts if a['id'] == account_id), None)
            if row is None:
                raise ValueError('账号已不存在，请刷新')
            if delete:
                accounts.remove(row)
            else:
                if name is not None:
                    row['name'] = name.strip()[:60]
                if enabled is not None:
                    row['enabled'] = bool(enabled)
            self.store.save_accounts(accounts)

    def run(self, status_only=False, account_id=None, sync=True):
        with OperationLock(self.store.root):
            accounts = self.store.accounts()
            selected = [a for a in accounts if a.get('enabled', True) and (not account_id or a['id'] == account_id)]
            if not selected:
                return False, '请先添加并启用至少一个账号'
            if sync and any(a['platform'] == 'workbuddy' for a in selected):
                try:
                    from .auth import workbuddy_accounts
                    found = workbuddy_accounts()
                    for row in selected:
                        if row['platform'] != 'workbuddy':
                            continue
                        candidate = next((c for c in found if self.owner('workbuddy', c) == self.owner('workbuddy', row['credentials'])), None)
                        if candidate:
                            from .workbuddy_auth import _jwt_expires_at
                            if (_jwt_expires_at(candidate['access_token']) or 0) >= (_jwt_expires_at(row['credentials']['access_token']) or 0):
                                row['credentials'] = {k: v for k, v in candidate.items() if k not in ('name', 'enabled')}
                except Exception:
                    pass  # Existing encrypted credentials remain available.
            successes = 0
            for account in selected:
                provider = WorkBuddy(self.http) if account['platform'] == 'workbuddy' else Trae(self.http)
                try:
                    result = provider.run(account, status_only)
                except Exception as exc:
                    result = Outcome('失败', detail=scrub(exc, accounts))
                self.store.save_accounts(accounts)  # Persist refreshed credentials before the next account.
                name, detail = scrub(account['name'], accounts), scrub(result.detail, accounts)
                if status_only:
                    detail = '状态查询；' + detail
                self.store.record(account['id'], account['platform'], name, result.state,
                                  result.earned, result.balance, detail)
                successes += result.ok
            return successes == len(selected), f'已处理 {len(selected)} 个账号：{successes} 个正常，{len(selected) - successes} 个未完成'
