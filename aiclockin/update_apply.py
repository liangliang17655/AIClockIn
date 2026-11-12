"""Local helper transaction. Never touches account files, databases or task definitions."""
import ctypes
from ctypes import wintypes as w
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time
import uuid

from .store import OperationLock, Busy, write_json
from .update import ROOT, file_hash, version
from .health_process import HealthProcess


class ApplyError(RuntimeError):
    pass


def kernel():
    api = ctypes.WinDLL('kernel32', use_last_error=True)
    api.CreateMutexW.argtypes = [ctypes.c_void_p, w.BOOL, w.LPCWSTR]
    api.CreateMutexW.restype = w.HANDLE
    api.WaitForSingleObject.argtypes = [w.HANDLE, w.DWORD]
    api.WaitForSingleObject.restype = w.DWORD
    api.CloseHandle.argtypes = [w.HANDLE]
    api.ReleaseMutex.argtypes = [w.HANDLE]
    api.OpenProcess.argtypes = [w.DWORD, w.BOOL, w.DWORD]
    api.OpenProcess.restype = w.HANDLE
    return api


class UpdateGate:
    def __init__(self, target, timeout=90):
        from .package import unicode_md5
        self.name = 'Local\\AIClockIn-update-' + unicode_md5(str(Path(target).resolve()).lower())
        self.timeout = timeout

    def __enter__(self):
        self.api = kernel()
        self.handle = self.api.CreateMutexW(None, False, self.name)
        if not self.handle:
            raise ApplyError('无法创建更新互斥锁')
        status = self.api.WaitForSingleObject(self.handle, int(self.timeout * 1000))
        if status not in (0, 0x80):
            self.api.CloseHandle(self.handle)
            raise ApplyError('程序正在更新，请稍后重新打开')
        return self

    def __exit__(self, *args):
        self.api.ReleaseMutex(self.handle)
        self.api.CloseHandle(self.handle)


def child_env():
    return {**os.environ, 'PYINSTALLER_RESET_ENVIRONMENT': '1', 'PYTHONDONTWRITEBYTECODE': '1'}


def start(command, cwd):
    return subprocess.Popen(command, cwd=cwd, env=child_env(), stdin=subprocess.DEVNULL,
                            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                            creationflags=subprocess.CREATE_NO_WINDOW | subprocess.CREATE_NEW_PROCESS_GROUP)


def save_manifest(path, value):
    write_json(path, value)


def load_manifest(path):
    path = Path(path).resolve()
    if path.name != 'transaction.json' or not path.is_relative_to(ROOT.resolve()) or path.stat().st_size > 16384:
        raise ApplyError('更新事务路径无效')
    value = json.loads(path.read_text('utf-8'))
    target, candidate, data = map(lambda k: Path(value[k]).resolve(), ('target', 'candidate', 'data'))
    if (target.drive.upper() != 'D:' or target.name != 'AIClockIn.exe' or data.drive.upper() != 'D:'
            or target.is_relative_to(data) or not candidate.is_relative_to(path.parent)
            or candidate == path or candidate.name in ('helper.exe', 'previous.exe')
            or value['state'] not in ('ready', 'replacing', 'committed', 'restored', 'failed', 'restore-failed')):
        raise ApplyError('更新事务内容无效')
    import re
    if any(not re.fullmatch('[0-9a-f]{64}', value[k]) for k in ('new_hash', 'old_hash')):
        raise ApplyError('更新事务哈希无效')
    version(value['version'])
    return value


def create_transaction(target, candidate, data, new_version, digest):
    ROOT.mkdir(parents=True, exist_ok=True)
    folder = ROOT / uuid.uuid4().hex
    folder.mkdir()
    # Candidate may already be in a separate download transaction. Copy to this private transaction.
    source = Path(candidate).resolve()
    copied = folder / 'candidate.exe'
    shutil.copyfile(source, copied)
    target = Path(target).resolve()
    value = {'target': str(target), 'candidate': str(copied), 'data': str(Path(data).resolve()),
             'version': new_version.lstrip('v'), 'new_hash': digest, 'old_hash': file_hash(target), 'state': 'ready'}
    manifest = folder / 'transaction.json'
    save_manifest(manifest, value)
    load_manifest(manifest)
    if file_hash(copied) != digest:
        raise ApplyError('辅助安装前校验失败')
    return manifest


def health_check(target, manifest, expected, timeout=90):
    report = manifest.parent / 'health.json'
    report.unlink(missing_ok=True)
    try:
        with HealthProcess([str(target), '--self-test', '--report', str(report)], target.parent, child_env()) as process:
            code = process.wait(timeout=timeout)
    except subprocess.TimeoutExpired:
        raise ApplyError('新版本离线健康检查超时') from None
    try:
        value = json.loads(report.read_text('utf-8'))
        valid = code == 0 and value.get('ok') is True and value.get('version') == expected
    except (OSError, ValueError):
        valid = False
    if not valid:
        raise ApplyError('新版本健康检查失败，准备恢复旧版')
    return True


def atomic_replace(target, staged):
    # Same-directory staging: os.replace is MoveFileExW(REPLACE_EXISTING) on Windows.
    # An open executable causes failure rather than truncating it in place.
    api = kernel()
    api.MoveFileExW.argtypes = [w.LPCWSTR, w.LPCWSTR, w.DWORD]
    if not api.MoveFileExW(str(staged), str(target), 0x1 | 0x8):  # REPLACE_EXISTING | WRITE_THROUGH
        raise ctypes.WinError(ctypes.get_last_error())


def durable_copy(source, target):
    with Path(source).open('rb') as reader, Path(target).open('wb') as writer:
        shutil.copyfileobj(reader, writer, 256*1024)
        writer.flush()
        os.fsync(writer.fileno())


def restore(manifest, value):
    target = Path(value['target'])
    backup = manifest.parent / 'previous.exe'
    if not backup.is_file() or file_hash(backup) != value['old_hash']:
        raise ApplyError('旧版备份校验失败；已保留事务文件，请手动恢复')
    stage = target.with_name('.AIClockIn-restore-' + manifest.parent.name + '.tmp')
    try:
        durable_copy(backup, stage)
        atomic_replace(target, stage)
        if file_hash(target) != value['old_hash']:
            raise ApplyError('旧版本恢复校验失败')
        value['state'] = 'restored'
        save_manifest(manifest, value)
    finally:
        stage.unlink(missing_ok=True)


def recover(manifest):
    manifest = Path(manifest)
    value = load_manifest(manifest)
    if value['state'] in ('replacing', 'restore-failed'):
        restore(manifest, value)


def replace_transaction(manifest):
    manifest = Path(manifest)
    value = load_manifest(manifest)
    if value['state'] in ('replacing', 'restore-failed'):
        recover(manifest)
        return
    if value['state'] != 'ready':
        raise ApplyError('此更新事务已经结束')
    target, candidate = Path(value['target']), Path(value['candidate'])
    if file_hash(candidate) != value['new_hash'] or file_hash(target) != value['old_hash']:
        raise ApplyError('程序内容已变化，已停止更新')
    stage = target.with_name('.AIClockIn-update-' + manifest.parent.name + '.tmp')
    replaced = False
    try:
        durable_copy(candidate, stage)
        if file_hash(stage) != value['new_hash']:
            raise ApplyError('暂存文件校验失败')
        durable_copy(target, manifest.parent / 'previous.exe')
        if file_hash(manifest.parent / 'previous.exe') != value['old_hash']:
            raise ApplyError('原程序备份校验失败')
        value['state'] = 'replacing'
        save_manifest(manifest, value)
        atomic_replace(target, stage)
        replaced = True
        health_check(target, manifest, value['version'])
        value['state'] = 'committed'
        save_manifest(manifest, value)
    except Exception as exc:
        try:
            if replaced:
                restore(manifest, value)
            else:
                value['state'] = 'failed'
                save_manifest(manifest, value)
        except Exception:
            value['state'] = 'restore-failed'
            save_manifest(manifest, value)
            raise ApplyError(f'更新失败且自动恢复未完成；备份保留在 {manifest.parent}') from None
        raise ApplyError('更新未完成，原版本已保留或恢复：' + str(exc)) from None
    finally:
        stage.unlink(missing_ok=True)


def pending(target):
    if not ROOT.exists():
        return None
    for manifest in ROOT.glob('*/transaction.json'):
        try:
            value = load_manifest(manifest)
            if Path(value['target']) == Path(target).resolve() and value['state'] in ('replacing', 'restore-failed'):
                return manifest
        except (OSError, ValueError, KeyError, ApplyError):
            continue
    return None


def wait_handle(api, handle, timeout=90):
    if api.WaitForSingleObject(handle, int(timeout*1000)) != 0:
        raise ApplyError('等待旧窗口退出超时，当前版本未修改')


def run_helper(manifest, pid, parent_pid=0):
    manifest = Path(manifest).resolve()
    value = load_manifest(manifest)
    api = kernel()
    handle = api.OpenProcess(0x100000, False, pid) if pid else None
    parent = api.OpenProcess(0x100000, False, parent_pid) if parent_pid else None
    ready = manifest.parent / 'helper-ready.json'
    error = None
    try:
        if (pid and not handle) or (parent_pid and not parent):
            raise ApplyError('无法确认旧程序进程，已停止更新')
        with UpdateGate(value['target']):
            write_json(ready, {'ok': True})
            if handle:
                wait_handle(api, handle)
            if parent:
                wait_handle(api, parent)
            if (manifest.parent / 'abort').exists() or not (manifest.parent / 'authorized').exists():
                raise ApplyError('更新准备已取消，当前版本未修改')
            # PyInstaller's outer bootloader briefly retains the image after Python exits.
            # Retry the transaction only on pre-replacement file access failures.
            deadline = time.monotonic() + 90
            while True:
                try:
                    with OperationLock(value['data']):
                        replace_transaction(manifest)
                    break
                except Busy:
                    if time.monotonic() >= deadline:
                        raise ApplyError('后台签到或授权仍在进行，未替换程序')
                    time.sleep(0.25)
                except ApplyError:
                    raise
    except Exception as exc:
        error = str(exc)
        write_json(manifest.parent / 'result.json', {'ok': False, 'message': error})
    finally:
        if handle:
            api.CloseHandle(handle)
        if parent:
            api.CloseHandle(parent)
    if error:
        ctypes.windll.user32.MessageBoxW(None, error, 'AIClockIn 更新未完成', 0x10)
    # Do not launch a potentially damaged image when rollback itself failed.
    state = load_manifest(manifest)['state']
    if state != 'restore-failed':
        try:
            start([value['target'], '--data', value['data']], Path(value['target']).parent)
        except OSError:
            ctypes.windll.user32.MessageBoxW(None, '程序已保留，请手动双击 AIClockIn.exe 启动。', 'AIClockIn', 0x10)
    write_json(manifest.parent / 'result.json', {'ok': not error, 'message': error or '更新完成', 'state': state})
    return 1 if error else 0


def launch_helper(manifest, pid):
    manifest = Path(manifest).resolve()
    helper = manifest.parent / 'helper.exe'
    shutil.copyfile(sys.executable, helper)
    process = start([str(helper), '--apply-update', str(manifest), '--wait-pid', str(pid),
                     '--wait-parent', str(os.getppid())], manifest.parent)
    ready = manifest.parent / 'helper-ready.json'
    deadline = time.monotonic() + 30
    while time.monotonic() < deadline:
        if ready.exists():
            (manifest.parent / 'authorized').write_text('1', encoding='ascii')
            return process
        if process.poll() is not None:
            break
        time.sleep(0.1)
    (manifest.parent / 'abort').write_text('1', encoding='ascii')
    raise ApplyError('更新辅助程序未能准备就绪，当前窗口保持打开')
