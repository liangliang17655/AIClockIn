"""Current-user DPAPI accounts, transactional history, and an OS-owned operation lock."""
import base64
from contextlib import contextmanager
import ctypes
from ctypes import wintypes as w
from datetime import datetime
import json
import msvcrt
import os
from pathlib import Path
import sqlite3
import uuid


class Blob(ctypes.Structure):
    _fields_ = [('size', w.DWORD), ('data', ctypes.POINTER(ctypes.c_ubyte))]


def crypt(data, decrypt=False):
    api = ctypes.WinDLL('crypt32', use_last_error=True)
    kernel = ctypes.WinDLL('kernel32')
    buffer = (ctypes.c_ubyte * len(data)).from_buffer_copy(data)
    source, target = Blob(len(data), buffer), Blob()
    fn = api.CryptUnprotectData if decrypt else api.CryptProtectData
    fn.argtypes = [ctypes.POINTER(Blob), ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p,
                   ctypes.c_void_p, w.DWORD, ctypes.POINTER(Blob)]
    fn.restype = w.BOOL
    if not fn(ctypes.byref(source), None, None, None, None, 1, ctypes.byref(target)):
        raise ValueError('账号无法解密，请使用原 Windows 用户；不会覆盖原文件')
    kernel.LocalFree.argtypes = [ctypes.c_void_p]
    try:
        return ctypes.string_at(target.data, target.size)
    finally:
        kernel.LocalFree(target.data)


def write_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + '.' + uuid.uuid4().hex + '.tmp')
    try:
        with temporary.open('x', encoding='utf-8') as stream:
            json.dump(value, stream, ensure_ascii=False, indent=2)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


class Busy(RuntimeError):
    pass


class OperationLock:
    def __init__(self, root):
        self.path = Path(root) / 'operation.lock'

    def __enter__(self):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.file = self.path.open('a+b')
        if self.file.tell() == 0:
            self.file.write(b'0')
            self.file.flush()
        self.file.seek(0)
        try:
            msvcrt.locking(self.file.fileno(), msvcrt.LK_NBLCK, 1)
        except OSError:
            self.file.close()
            raise Busy('已有签到或账号操作进行中，请稍后重试') from None
        return self

    def __exit__(self, *args):
        self.file.seek(0)
        msvcrt.locking(self.file.fileno(), msvcrt.LK_UNLCK, 1)
        self.file.close()


class Store:
    def __init__(self, root):
        self.root = Path(root).resolve()
        if self.root.drive.upper() != 'D:':
            raise ValueError('AIClockIn 数据仅保存在 D 盘')
        self.root.mkdir(parents=True, exist_ok=True)
        self.account_file = self.root / 'accounts.json'
        self.database = self.root / 'history.db'
        with self.connect() as db:
            db.execute('''CREATE TABLE IF NOT EXISTS history (
                id INTEGER PRIMARY KEY, time TEXT, account_id TEXT, platform TEXT,
                name TEXT, state TEXT, earned REAL, balance REAL, detail TEXT)''')

    @contextmanager
    def connect(self):
        db = sqlite3.connect(self.database, timeout=15)
        try:
            with db:
                yield db
        finally:
            db.close()

    def accounts(self):
        if not self.account_file.exists():
            return []
        try:
            envelope = json.loads(self.account_file.read_text('utf-8'))
            if envelope.get('format') != 'AIClockIn-1':
                raise ValueError()
            rows = [json.loads(crypt(base64.b64decode(blob, validate=True), True)) for blob in envelope['accounts']]
            if any(not isinstance(row, dict) or not row.get('id') or row.get('platform') not in ('workbuddy', 'trae') for row in rows):
                raise ValueError()
            if len({row['id'] for row in rows}) != len(rows):
                raise ValueError()
            return rows
        except Exception as exc:
            raise ValueError('账号文件损坏或无法解密，已停止操作，不会重置数据') from exc

    def save_accounts(self, accounts):
        self.accounts()  # A damaged existing file is never silently replaced.
        if len({row['id'] for row in accounts}) != len(accounts):
            raise ValueError('账号标识重复，已拒绝保存')
        blobs = [base64.b64encode(crypt(json.dumps(row, ensure_ascii=False).encode('utf-8'))).decode('ascii') for row in accounts]
        write_json(self.account_file, {'format': 'AIClockIn-1', 'accounts': blobs})

    def record(self, account_id, platform, name, state, earned, balance, detail):
        with self.connect() as db:
            db.execute('INSERT INTO history(time,account_id,platform,name,state,earned,balance,detail) VALUES(?,?,?,?,?,?,?,?)',
                (datetime.now().astimezone().isoformat(timespec='seconds'), account_id, platform, name, state, earned, balance, detail))

    def history(self, account_id=None):
        with self.connect() as db:
            db.row_factory = sqlite3.Row
            if account_id:
                result = db.execute('SELECT * FROM history WHERE account_id=? ORDER BY id DESC LIMIT 200', (account_id,))
            else:
                result = db.execute('SELECT * FROM history ORDER BY id DESC LIMIT 200')
            return [dict(row) for row in result]
