"""Opt-in frozen install/link/upgrade checks entirely in D-drive isolated directories."""
import json
import os
import ctypes
from ctypes import wintypes as w
from pathlib import Path
import shutil
import sys
import tempfile
import xml.etree.ElementTree as ET

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from aiclockin.runtime import prepare
from aiclockin.installer import install, shell, InstallError
from aiclockin.update_apply import start
from aiclockin.schedule import WindowsTask, TaskManager, powershell
from aiclockin.store import Store, write_json
from aiclockin.update import file_hash
from aiclockin.version import current
from tests.verify_update_windows import wait_until, close_windows


def close_app(target):
    def closed():
        titles(target, close=True)
        return not matching_processes(target)
    wait_until(closed, timeout=30)


def process_api():
    api=ctypes.WinDLL('kernel32',use_last_error=True)
    api.OpenProcess.argtypes=[w.DWORD,w.BOOL,w.DWORD];api.OpenProcess.restype=w.HANDLE
    api.CloseHandle.argtypes=[w.HANDLE]
    api.QueryFullProcessImageNameW.argtypes=[w.HANDLE,w.DWORD,w.LPWSTR,ctypes.POINTER(w.DWORD)]
    return api


def matches_pid(api,pid,target):
    handle=api.OpenProcess(0x1000,False,pid)
    if not handle:return False
    try:
        name=ctypes.create_unicode_buffer(32768);size=w.DWORD(len(name))
        return bool(api.QueryFullProcessImageNameW(handle,0,name,ctypes.byref(size)) and Path(name.value).resolve()==target.resolve())
    finally:api.CloseHandle(handle)


def matching_processes(target):
    class Entry(ctypes.Structure):
        _fields_=[('size',w.DWORD),('usage',w.DWORD),('pid',w.DWORD),('heap',ctypes.c_size_t),
                  ('module',w.DWORD),('threads',w.DWORD),('parent',w.DWORD),('priority',w.LONG),
                  ('flags',w.DWORD),('name',w.WCHAR*260)]
    api=process_api()
    api.CreateToolhelp32Snapshot.argtypes=[w.DWORD,w.DWORD];api.CreateToolhelp32Snapshot.restype=w.HANDLE
    api.Process32FirstW.argtypes=[w.HANDLE,ctypes.POINTER(Entry)]
    api.Process32NextW.argtypes=[w.HANDLE,ctypes.POINTER(Entry)]
    snapshot=api.CreateToolhelp32Snapshot(2,0)
    if snapshot==w.HANDLE(-1).value:raise OSError('Process snapshot failed')
    result=[]
    try:
        entry=Entry();entry.size=ctypes.sizeof(entry)
        valid=api.Process32FirstW(snapshot,ctypes.byref(entry))
        while valid:
            if entry.name.casefold()==target.name.casefold() and matches_pid(api,entry.pid,target):result.append(entry.pid)
            valid=api.Process32NextW(snapshot,ctypes.byref(entry))
    finally:api.CloseHandle(snapshot)
    return result


def titles(target,close=False):
    api=process_api();user=ctypes.WinDLL('user32')
    user.GetWindowThreadProcessId.argtypes=[w.HWND,ctypes.POINTER(w.DWORD)]
    user.GetWindowTextW.argtypes=[w.HWND,w.LPWSTR,ctypes.c_int]
    user.PostMessageW.argtypes=[w.HWND,w.UINT,w.WPARAM,w.LPARAM]
    result=[]
    callback=ctypes.WINFUNCTYPE(w.BOOL,w.HWND,w.LPARAM)
    @callback
    def visit(hwnd,_):
        pid=w.DWORD();user.GetWindowThreadProcessId(hwnd,ctypes.byref(pid))
        if matches_pid(api,pid.value,target):
            text=ctypes.create_unicode_buffer(512);user.GetWindowTextW(hwnd,text,len(text))
            if text.value:
                result.append(text.value)
                if close:user.PostMessageW(hwnd,0x10,0,0)
        return True
    user.EnumWindows(visit,0)
    return result


def read_link(path):
    return shell("$s=(New-Object -ComObject WScript.Shell).CreateShortcut($v.path);"
                 "@{target=$s.TargetPath;arguments=$s.Arguments;working=$s.WorkingDirectory}|ConvertTo-Json -Compress", {'path': str(path)})


def main():
    prepare()
    base = Path(__file__).resolve().parent.parent
    version = current()
    exe = base / f'dist/release/v{version}/AIClockIn-v{version}-windows-x64.exe'
    report = {'version': version, 'source_sha256': file_hash(exe)}
    with tempfile.TemporaryDirectory(prefix='install-test-') as folder:
        folder = Path(folder)
        download = folder/'download'; download.mkdir()
        downloaded = download/'AIClockIn.exe'; shutil.copyfile(exe, downloaded)
        bootstrap = start([str(downloaded)], download)
        wait_until(lambda: 'AIClockIn · 安装与桌面入口' in titles(downloaded))
        close_app(downloaded)
        assert bootstrap.wait(timeout=10) == 1, 'Cancelled installer should not claim success'
        assert not (download/'data').exists(), 'Bootstrap created data in download location'
        report['first_launch_installer_before_data'] = True
        desk = folder / 'mock desktop'; desk.mkdir()
        target = folder / 'installed'; data = folder / 'custom data'
        installed = install(exe, target, data, version, desktop=desk)
        assert installed == target / 'AIClockIn.exe'
        assert file_hash(installed) == file_hash(exe)
        assert not (exe.parent / 'data').exists(), 'Installer polluted downloaded file location'
        link = desk / 'AIClockIn 自动签到.lnk'
        properties = read_link(link)
        assert Path(properties['target']) == installed
        assert str(data) in properties['arguments'] and '--data' in properties['arguments']
        assert Path(properties['working']) == target
        write_json(data / 'update-settings.json', {'auto_check': False})
        store = Store(data)
        rows = [{'id':'a','platform':'workbuddy','name':'synthetic','enabled':False,
                 'credentials':{'uid':'synthetic','access_token':'synthetic'}}]
        store.save_accounts(rows)
        store.record('a','workbuddy','synthetic','失败',None,None,'offline install fixture')
        before = {p.name:file_hash(p) for p in data.iterdir() if p.name != 'operation.lock'}
        install(installed, target, data, version, desktop=desk)
        assert before == {p.name:file_hash(p) for p in data.iterdir() if p.name != 'operation.lock'}
        assert store.accounts() == rows
        # Launch through the actual .lnk, not by directly invoking the target EXE.
        os.startfile(str(link))
        wait_until(lambda: 'AIClockIn · 每日签到' in titles(installed))
        close_app(installed)
        # Existing foreign link must not be overwritten.
        other = folder / 'other'; other.mkdir()
        try:
            install(exe, other, other/'data', version, desktop=desk)
            raise AssertionError('Foreign link overwritten')
        except InstallError as exc:
            assert '快捷方式' in str(exc)
            assert read_link(link)['target'] == str(installed)
        # A real legacy executable in a fixed location is upgraded in place, retaining task/data.
        old = folder / 'legacy'; old.mkdir()
        shutil.copyfile(base/'AIClockIn.exe', old/'AIClockIn.exe')
        old_data = old/'data'; Store(old_data).save_accounts([])
        old_desk = folder/'legacy desktop'; old_desk.mkdir()
        import uuid
        backend=WindowsTask('AIClockIn-InstallTest-'+uuid.uuid4().hex[:12])
        manager=TaskManager(old_data,old/'AIClockIn.exe',backend)
        try:
            manager.enable()
            xml=ET.tostring(ET.fromstring(backend.get()))
            old_before={p.name:file_hash(p) for p in old_data.iterdir() if p.name != 'operation.lock'}
            install(exe,old,old_data,version,desktop=old_desk)
            assert file_hash(old/'AIClockIn.exe') == file_hash(exe)
            assert old_before == {p.name:file_hash(p) for p in old_data.iterdir() if p.name != 'operation.lock'}
            assert xml == ET.tostring(ET.fromstring(backend.get()))
            powershell(f"Start-ScheduledTask -TaskName '{backend.name}'")
            def ran():
                value=json.loads(powershell(f"$t=Get-ScheduledTask -TaskName '{backend.name}';$i=Get-ScheduledTaskInfo -TaskName '{backend.name}';@{{state=[string]$t.State;result=$i.LastTaskResult;ran=($i.LastRunTime.Year -gt 2020)}}|ConvertTo-Json -Compress"))
                return value if value['ran'] and value['state'] != 'Running' else None
            result=wait_until(ran)
            assert result['result'] == 1, result
            report['task_after_upgrade']=True
        finally:
            if backend.get() is not None: backend.remove()
            report['task_cleaned']=backend.get() is None
        report.update({'fresh_install':True,'real_lnk_launch':True,'custom_data_args':True,
                       'repeat_install_data_preserved':True,'foreign_link_preserved':True,'legacy_upgrade':True})
    write_json(Path('D:/个人开发软件/AI工作区/outputs/AIClockIn-validation/install/windows-install.json'),report)
    print(json.dumps(report,ensure_ascii=False))


if __name__ == '__main__':
    main()
