"""Capture actual native welcome page, exit before any installation."""
import ctypes as c
from ctypes import wintypes as w
from pathlib import Path
import sys
import time

sys.path.insert(0,str(Path(__file__).resolve().parent.parent))
from aiclockin.runtime import prepare
from aiclockin.health_process import HealthProcess
from aiclockin.update_apply import child_env
from tests.preview import capture
from tests.verify_update_windows import wait_until

CALLBACK=c.WINFUNCTYPE(w.BOOL,w.HWND,w.LPARAM)
u=c.WinDLL('user32');k=c.WinDLL('kernel32')
u.SetProcessDPIAware()
u.EnumWindows.argtypes=[CALLBACK,w.LPARAM];u.EnumChildWindows.argtypes=[w.HWND,CALLBACK,w.LPARAM]
u.GetWindowThreadProcessId.argtypes=[w.HWND,c.POINTER(w.DWORD)]
u.GetClassNameW.argtypes=[w.HWND,w.LPWSTR,c.c_int];u.GetWindowTextW.argtypes=[w.HWND,w.LPWSTR,c.c_int]
u.IsWindowVisible.argtypes=[w.HWND];u.IsWindowEnabled.argtypes=[w.HWND]
u.SendMessageW.argtypes=[w.HWND,w.UINT,w.WPARAM,w.LPARAM]
u.SetForegroundWindow.argtypes=[w.HWND]
u.GetDlgCtrlID.argtypes=[w.HWND]
u.GetWindowRect.argtypes=[w.HWND,c.POINTER(w.RECT)]
u.SetCursorPos.argtypes=[c.c_int,c.c_int]
u.mouse_event.argtypes=[w.DWORD,w.DWORD,w.DWORD,w.DWORD,c.c_size_t]
u.SetWindowPos.argtypes=[w.HWND,w.HWND,c.c_int,c.c_int,c.c_int,c.c_int,w.UINT]
u.WindowFromPoint.argtypes=[w.POINT];u.WindowFromPoint.restype=w.HWND
u.GetAncestor.argtypes=[w.HWND,w.UINT];u.GetAncestor.restype=w.HWND
u.GetParent.argtypes=[w.HWND];u.GetParent.restype=w.HWND


def click(hwnd):
    # Deliver the native BN_CLICKED notification to the immediate VCL parent.
    # This remains deterministic when the input desktop is locked during background QA.
    u.SendMessageW(u.GetParent(hwnd),0x111,u.GetDlgCtrlID(hwnd),hwnd);time.sleep(.25)


def descendants(pid):
    class Entry(c.Structure):
        _fields_=[('size',w.DWORD),('usage',w.DWORD),('pid',w.DWORD),('heap',c.c_size_t),('module',w.DWORD),
                  ('threads',w.DWORD),('parent',w.DWORD),('priority',w.LONG),('flags',w.DWORD),('name',w.WCHAR*260)]
    k.CreateToolhelp32Snapshot.argtypes=[w.DWORD,w.DWORD];k.CreateToolhelp32Snapshot.restype=w.HANDLE
    k.Process32FirstW.argtypes=[w.HANDLE,c.POINTER(Entry)];k.Process32NextW.argtypes=[w.HANDLE,c.POINTER(Entry)]
    k.CloseHandle.argtypes=[w.HANDLE]
    snapshot=k.CreateToolhelp32Snapshot(2,0);parents={}
    try:
        entry=Entry();entry.size=c.sizeof(entry);valid=k.Process32FirstW(snapshot,c.byref(entry))
        while valid:
            parents[entry.pid]=entry.parent;valid=k.Process32NextW(snapshot,c.byref(entry))
    finally:k.CloseHandle(snapshot)
    found={pid}
    for _ in range(5):found.update(child for child,parent in parents.items() if parent in found)
    return found


def windows(pids,parent=None):
    result=[]
    @CALLBACK
    def visit(hwnd,_):
        pid=w.DWORD();u.GetWindowThreadProcessId(hwnd,c.byref(pid))
        if pid.value in pids and u.IsWindowVisible(hwnd):
            text=c.create_unicode_buffer(512);cls=c.create_unicode_buffer(128)
            u.GetWindowTextW(hwnd,text,512);u.GetClassNameW(hwnd,cls,128)
            result.append((hwnd,cls.value,text.value))
        return True
    if parent is None:u.EnumWindows(visit,0)
    else:u.EnumChildWindows(parent,visit,0)
    return result


def main():
    prepare();base=Path(__file__).resolve().parent.parent
    output=Path('D:/个人开发软件/AI工作区/outputs/AIClockIn-validation/inno')
    exe=base/'dist/release/v0.4.0/AIClockInSetup.exe'
    command=[str(exe),'/LANG=chinesesimplified','/DIR='+str(output/'preview-install'),'/DATA='+str(output/'preview-install/data')]
    with HealthProcess(command,output,child_env()) as process:
        def wizard():
            return next((row for row in windows(descendants(process.info.pid)) if row[1]=='TWizardForm'),None)
        form=wait_until(wizard)
        u.SetWindowPos(form[0],w.HWND(-1),0,0,0,0,0x43)
        u.SetForegroundWindow(form[0]);time.sleep(1)
        capture(form[0],output/'setup-welcome.bmp')
    assert not (output/'preview-install/AIClockIn.exe').exists()
    print('Native welcome page captured; exited before installation.')


if __name__=='__main__':main()
