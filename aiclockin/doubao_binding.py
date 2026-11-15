"""User-confirmed visible-number binding; never claims an immutable platform UID."""
import base64
from datetime import datetime
import json
import re
import uuid

from .store import OperationLock, crypt, write_json


def valid_fingerprint(value):
    return isinstance(value, str) and re.fullmatch(r'[0-9a-f]{64}', value) is not None


def load(store):
    path = store.root / 'doubao-binding.json'
    if not path.exists():
        return None
    try:
        envelope = json.loads(path.read_text('utf-8'))
        if envelope['version'] != 1:
            raise ValueError()
        value = json.loads(crypt(base64.b64decode(envelope['protected'], validate=True), decrypt=True))
        if (not valid_fingerprint(value['fingerprint']) or
            not re.fullmatch(r'[0-9a-f]{32}', value['id']) or
            value['mode'] != 'user_confirmed_visible_number' or value['identity_verified'] is not False):
            raise ValueError()
        datetime.fromisoformat(value['confirmed_at'])
        return value
    except Exception:
        raise ValueError('豆包绑定无法读取；保留原文件，请使用原 Windows 用户检查。') from None


def read_candidate(backend):
    if not backend.desktop_status()[0]:
        raise ValueError('桌面锁屏或无交互桌面，未读取账号。')
    if not backend.running():
        raise ValueError('豆包工作未运行，请先在官方客户端登录。')
    value = backend.inspect_identity().get('account_fingerprint')
    if not valid_fingerprint(value):
        raise ValueError('当前可见豆包号无法确认；未使用昵称或缓存替代。')
    return value


def confirm(store, candidate, backend, *, confirmed=False):
    if confirmed is not True or not valid_fingerprint(candidate):
        raise ValueError('必须先由用户确认当前账号。')
    with OperationLock(store.root):
        old = load(store)
        if old and old['fingerprint'] != candidate:
            raise ValueError('已绑定其他账号；停止操作，原绑定和记录保留。')
        if read_candidate(backend) != candidate:
            raise ValueError('确认期间账号发生变化；绑定未保存。')
        if old:
            return old
        value = {'id': uuid.uuid4().hex, 'fingerprint': candidate,
                 'mode': 'user_confirmed_visible_number', 'identity_verified': False,
                 'confirmed_at': datetime.now().astimezone().isoformat(timespec='seconds')}
        payload = crypt(json.dumps(value, ensure_ascii=False).encode('utf-8'))
        write_json(store.root / 'doubao-binding.json',
                   {'version': 1, 'protected': base64.b64encode(payload).decode('ascii')})
        return value
