"""Opt-in real EXE upgrade in a disposable D-drive installation. No real credentials."""
import ctypes
from ctypes import wintypes as w
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import time
import uuid
import xml.etree.ElementTree as ET

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from aiclockin.runtime import prepare
from aiclockin.store import Store, write_json
from aiclockin.update import ROOT, file_hash
from aiclockin.update_apply import create_transaction, start, replace_transaction, ApplyError
from aiclockin.schedule import WindowsTask, TaskManager, powershell


def wait_until(predicate, timeout=45):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        value = predicate()
        if value:
            return value
        time.sleep(.15)
    raise AssertionError('Timed out waiting for isolated update')


def close_windows(exe):
    # Only send WM_CLOSE to windows owned by processes with this exact test executable path.
    kernel = ctypes.WinDLL('kernel32', use_last_error=True)
    user = ctypes.WinDLL('user32', use_last_error=True)
    kernel.OpenProcess.argtypes = [w.DWORD, w.BOOL, w.DWORD]; kernel.OpenProcess.restype = w.HANDLE
    kernel.QueryFullProcessImageNameW.argtypes = [w.HANDLE, w.DWORD, w.LPWSTR, ctypes.POINTER(w.DWORD)]
    kernel.CloseHandle.argtypes = [w.HANDLE]
    user.GetWindowThreadProcessId.argtypes = [w.HWND, ctypes.POINTER(w.DWORD)]
    user.PostMessageW.argtypes = [w.HWND, w.UINT, w.WPARAM, w.LPARAM]
    count = []
    callback_type = ctypes.WINFUNCTYPE(w.BOOL, w.HWND, w.LPARAM)
    @callback_type
    def visit(hwnd, _):
        pid = w.DWORD(); user.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
        handle = kernel.OpenProcess(0x1000, False, pid.value)
        if handle:
            try:
                name = ctypes.create_unicode_buffer(32768); size = w.DWORD(len(name))
                if kernel.QueryFullProcessImageNameW(handle, 0, name, ctypes.byref(size)) and Path(name.value).resolve() == exe.resolve():
                    user.PostMessageW(hwnd, 0x10, 0, 0); count.append(hwnd)
            finally:
                kernel.CloseHandle(handle)
        return True
    user.EnumWindows(visit, 0)
    return bool(count)


def main():
    prepare()
    base = Path(__file__).resolve().parent.parent
    new = base / 'dist/release/v0.2.0/AIClockIn-v0.2.0-windows-x64.exe'
    old = base / 'AIClockIn.exe'  # Current local baseline; recorded first run used v0.1.0. Bootstrap is manual.
    output = Path('D:/个人开发软件/AI工作区/outputs/AIClockIn-validation/update')
    output.mkdir(parents=True, exist_ok=True)
    record = {'source': str(new), 'new_hash': file_hash(new), 'old_hash': file_hash(old)}
    task_name = 'AIClockIn-UpdateTest-' + uuid.uuid4().hex[:12]
    backend = WindowsTask(task_name)
    with tempfile.TemporaryDirectory(prefix='update-install-') as folder:
        folder = Path(folder)
        target = folder / 'AIClockIn.exe'; shutil.copyfile(old, target)
        data = folder / 'custom data'
        store = Store(data)
        rows = [{'id': 'a', 'platform': 'workbuddy', 'name': 'synthetic A', 'enabled': False,
                 'credentials': {'uid': 'synthetic-a', 'access_token': 'synthetic-a'}},
                {'id': 'b', 'platform': 'trae', 'name': 'synthetic B', 'enabled': False,
                 'credentials': {'userId': 'synthetic-b', 'accessToken': 'synthetic-b'}}]
        store.save_accounts(rows)
        store.record('a', 'workbuddy', 'synthetic A', '失败', None, None, 'offline synthetic history')
        write_json(data / 'update-settings.json', {'auto_check': False})
        manager = TaskManager(data, target, backend)
        process = helper = None
        try:
            manager.enable()
            before_xml = ET.tostring(ET.fromstring(backend.get()))
            before = {p.name: file_hash(p) for p in data.iterdir()}
            manifest = create_transaction(target, new, data, '0.2.0', file_hash(new))
            helper_exe = manifest.parent / 'helper.exe'; shutil.copyfile(new, helper_exe)
            process = start([str(target), '--data', str(data)], folder)
            # Wait for Tk to exist before preparing the helper, then close the old GUI cleanly.
            time.sleep(1)
            helper = start([str(helper_exe), '--apply-update', str(manifest), '--wait-pid', str(process.pid)], manifest.parent)
            wait_until(lambda: (manifest.parent / 'helper-ready.json').exists())
            (manifest.parent / 'authorized').write_text('1', encoding='ascii')
            wait_until(lambda: close_windows(target))
            assert process.wait(timeout=20) == 0
            assert helper.wait(timeout=100) == 0
            result = json.loads((manifest.parent / 'result.json').read_text('utf-8'))
            assert result['ok'] and result['state'] == 'committed', result
            assert file_hash(target) == file_hash(new)
            health = json.loads((manifest.parent / 'health.json').read_text('utf-8'))
            assert health['ok'] and health['version'] == '0.2.0'
            assert health['extracted'].startswith('D:')
            assert Store(data).accounts() == rows
            assert before == {p.name: file_hash(p) for p in data.iterdir()}, 'Data changed during upgrade'
            assert before_xml == ET.tostring(ET.fromstring(backend.get())), 'Task definition changed'
            # New GUI was automatically started. Close only this disposable installation.
            wait_until(lambda: close_windows(target))
            time.sleep(.5)
            record.update({'real_helper_replace': True, 'relaunch': True, 'data_hashes_preserved': True,
                           'dpapi_preserved': True, 'task_xml_preserved': True, 'health': health,
                           'transaction': str(manifest)})
            powershell(f"Start-ScheduledTask -TaskName '{task_name}' -TaskPath '\\'")
            def ran():
                info = json.loads(powershell(f"$t=Get-ScheduledTask -TaskName '{task_name}';$i=Get-ScheduledTaskInfo -TaskName '{task_name}';@{{State=[string]$t.State;Result=$i.LastTaskResult;Ran=($i.LastRunTime.Year -gt 2020)}}|ConvertTo-Json -Compress"))
                return info if info['Ran'] and info['State'] != 'Running' else None
            info = wait_until(ran)
            assert info['Result'] == 1, info  # No enabled accounts; truthful failure, no network calls.
            record['task_executes_new_exe'] = True
            record['task_exit_no_enabled_accounts'] = info['Result']
            assert before_xml == ET.tostring(ET.fromstring(backend.get()))
            assert not (folder / 'data').exists(), 'Task lost custom --data'
            # Real candidate with deliberately wrong expected version must fail health and restore.
            rollback = create_transaction(target, new, data, '99.0.0', file_hash(new))
            try:
                replace_transaction(rollback)
                raise AssertionError('Expected health version mismatch')
            except ApplyError:
                assert file_hash(target) == file_hash(new)
                assert json.loads(rollback.read_text('utf-8'))['state'] == 'restored'
            record['real_health_failure_restored'] = True
        finally:
            close_windows(target)
            if process and process.poll() is None:
                process.wait(timeout=15)
            if backend.get() is not None:
                backend.remove()
            record['task_cleanup'] = backend.get() is None
            write_json(output / 'windows-update.json', record)
    print(json.dumps(record, ensure_ascii=False))


if __name__ == '__main__':
    main()
