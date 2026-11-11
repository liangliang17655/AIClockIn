"""Normal desktop-account discovery and browser authorization; no device changes."""
import json
import os
from pathlib import Path
import re
import time
import urllib.parse
import uuid
import webbrowser
from http.server import BaseHTTPRequestHandler, HTTPServer

from .http import RequestFailure
from .providers import TR_CLIENT, TR_VERSION, Trae


def workbuddy_accounts():
    from . import workbuddy_auth as adapter
    found = {}
    for snapshot in adapter.wb_auth_snapshots(quiet=True):
        if not snapshot.load() or snapshot.expired:
            continue
        record = snapshot.record
        key = record.get('uid') or adapter._jwt_subject(record['access_token']) or record['access_token']
        if key not in found or (snapshot.expires_at or 0) > found[key][1]:
            found[key] = (record, snapshot.expires_at or 0)
    return [row for row, _ in found.values()]


def desktop_trae_device():
    """Read identifiers already assigned by the actual installed desktop client."""
    root = Path(os.environ.get('APPDATA', str(Path.home() / 'AppData/Roaming')))
    for name in ('TRAE SOLO CN', 'Trae CN', 'Trae', 'TRAE'):
        directory = root / name
        machine = directory / 'machineid'
        for relative in ('ahanet/tt_net_config.config', 'tt_net_config.config'):
            config = directory / relative
            if config.is_file() and machine.is_file():
                text = config.read_text('utf-8', errors='replace')
                matches = re.findall(r'device_id&#\*([^@$]*)@\$', text)
                machine_id = machine.read_text('utf-8').strip()
                if matches and machine_id:
                    return matches[0], machine_id
    raise ValueError('请先安装并登录 Trae CN 官方桌面客户端，再添加账号')


def login_trae(http):
    device, machine = desktop_trae_device()
    captured = {}
    def object_param(raw):
        try:
            value = json.loads(raw or '{}')
            return value if isinstance(value, dict) else {}
        except ValueError:
            return {}
    class Callback(BaseHTTPRequestHandler):
        def do_GET(self):
            parsed = urllib.parse.urlparse(self.path)
            params = urllib.parse.parse_qs(parsed.query)
            values = {key: val[0] for key, val in params.items() if val}
            valid = parsed.path in ('/authorize', '/callback') and (values.get('refreshToken') or values.get('refresh_token') or object_param(values.get('userJwt')).get('Token'))
            self.send_response(200 if valid else 400)
            self.send_header('Content-Type', 'text/html; charset=utf-8')
            self.end_headers()
            self.wfile.write(('授权已接收，请返回 AIClockIn 查看结果。' if valid else '无效授权回调。').encode('utf-8'))
            if valid:
                captured.update(values)

        def log_message(self, *args):
            pass
    server = None
    for port in range(18080, 18100):
        try:
            server = HTTPServer(('127.0.0.1', port), Callback)
            break
        except OSError:
            continue
    if server is None:
        raise ValueError('本地授权回调端口被占用，请稍后重试')
    params = {'login_version': '1', 'auth_from': 'solo', 'login_channel': 'native_ide',
        'plugin_version': '2.3.62834', 'auth_type': 'local', 'client_id': TR_CLIENT, 'redirect': '0',
        'login_trace_id': uuid.uuid4().hex[:16], 'auth_callback_url': f'http://127.0.0.1:{server.server_port}/authorize',
        'machine_id': machine, 'device_id': device, 'x_device_id': device, 'x_machine_id': machine,
        'x_device_brand': 'PC', 'x_device_type': 'PC', 'x_os_version': 'Windows', 'x_app_version': TR_VERSION, 'x_app_type': 'stable'}
    try:
        if not webbrowser.open('https://www.trae.cn/authorization?' + urllib.parse.urlencode(params)):
            raise ValueError('无法打开默认浏览器，请检查浏览器设置')
        deadline = time.monotonic() + 300
        server.timeout = .5
        while not captured and time.monotonic() < deadline:
            server.handle_request()
    finally:
        server.server_close()
    if not captured:
        raise ValueError('登录等待超时，请重新添加账号')
    info, jwt = object_param(captured.get('userInfo')), object_param(captured.get('userJwt'))
    c = {'userId': str(info.get('UserID') or ''), 'refreshToken': captured.get('refreshToken') or captured.get('refresh_token') or jwt.get('RefreshToken'),
         'accessToken': jwt.get('Token') or '', 'claimDeviceId': device, 'machineId': machine}
    if not c['refreshToken']:
        raise RequestFailure('授权未提供可续期凭据，请重新登录')
    Trae(http).refresh(c)
    if not c['userId'] or not info.get('ScreenName'):
        response = http.post('https://api.trae.com.cn/cloudide/api/v3/trae/GetUserInfo',
            {'x-cloudide-token': c['accessToken'], 'User-Agent': 'Trae/' + TR_VERSION}, {'ReqSource': 'IDE', 'IDEVersion': TR_VERSION})
        user = response.get('Result') or response
        c['userId'] = str(user.get('UserID') or c['userId'])
        info['ScreenName'] = user.get('ScreenName') or info.get('ScreenName')
    if not c['userId']:
        raise ValueError('无法确认登录账号，请重新授权')
    return c, str(info.get('ScreenName') or 'Trae CN 账号')
