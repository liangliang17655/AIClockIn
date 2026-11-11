"""Opt-in native click verification on the frozen UI; existing foreign links stay untouched."""
import ctypes as c
from ctypes import wintypes as w
import json
from pathlib import Path
import sys
import tempfile
import time

sys.path.insert(0,str(Path(__file__).resolve().parent.parent))
from aiclockin.runtime import prepare
from aiclockin.store import Store,write_json
from aiclockin.update_apply import start
from aiclockin.version import current
from tests.verify_install_windows import process_api,matches_pid,close_app
from tests.verify_update_windows import wait_until

CALLBACK=c.WINFUNCTYPE(w.BOOL,w.HWND,w.LPARAM)
user=c.WinDLL('user32')
user.EnumWindows.argtypes=[CALLBACK,w.LPARAM]
user.EnumChildWindows.argtypes=[w.HWND,CALLBACK,w.LPARAM]
user.GetWindowThreadProcessId.argtypes=[w.HWND,c.POINTER(w.DWORD)]
user.GetWindowTextW.argtypes=[w.HWND,w.LPWSTR,c.c_int]
user.GetClassNameW.argtypes=[w.HWND,w.LPWSTR,c.c_int]
user.GetWindowRect.argtypes=[w.HWND,c.POINTER(w.RECT)]
user.PostMessageW.argtypes=[w.HWND,w.UINT,w.WPARAM,w.LPARAM]
user.IsWindowVisible.argtypes=[w.HWND]
user.SetForegroundWindow.argtypes=[w.HWND]
user.SetCursorPos.argtypes=[c.c_int,c.c_int]
user.mouse_event.argtypes=[w.DWORD,w.DWORD,w.DWORD,w.DWORD,c.c_size_t]


def windows(exe,parent=None):
    api=process_api();result=[]
    @CALLBACK
    def visit(hwnd,_):
        pid=w.DWORD();user.GetWindowThreadProcessId(hwnd,c.byref(pid))
        if user.IsWindowVisible(hwnd) and matches_pid(api,pid.value,exe):
            title=c.create_unicode_buffer(256);cls=c.create_unicode_buffer(64);rect=w.RECT()
            user.GetWindowTextW(hwnd,title,256);user.GetClassNameW(hwnd,cls,64);user.GetWindowRect(hwnd,c.byref(rect))
            result.append({'hwnd':hwnd,'title':title.value,'class':cls.value,
                           'rect':(rect.left,rect.top,rect.right,rect.bottom)})
        return True
    if parent is None:user.EnumWindows(visit,0)
    else:user.EnumChildWindows(parent,visit,0)
    return result


def click(item):
    left,top,right,bottom=item['rect']
    point=((bottom-top)//2<<16)|((right-left)//2)
    user.PostMessageW(item['hwnd'],0x201,1,point)
    user.PostMessageW(item['hwnd'],0x202,0,point)


def screen_click(x,y):
    user.SetCursorPos(x,y)
    user.mouse_event(2,0,0,0,0);user.mouse_event(4,0,0,0,0)


def verify(exe,data,expected):
    process=start([str(exe),'--data',str(data)],exe.parent)
    try:
        root=wait_until(lambda:next((x for x in windows(exe) if x['title']=='AIClockIn · 每日签到'),None))
        user.SetForegroundWindow(root['hwnd']);time.sleep(.15)
        # Tk draws these controls in a shared native window; use the verified default layout.
        screen_click(root['rect'][2]-92,root['rect'][1]+82)
        panel=wait_until(lambda:next((x for x in windows(exe) if 246<=x['rect'][2]-x['rect'][0]<=250),None))
        screen_click(panel['rect'][0]+124,panel['rect'][1]+135)
        dialog=wait_until(lambda:next((x for x in windows(exe) if x['title']==expected),None))
        user.PostMessageW(dialog['hwnd'],0x111,1,0)  # Only acknowledge the test's own result dialog.
        return {'real_frozen_menu_click':True,'real_shortcut_command':True,'result_dialog':expected}
    finally:
        close_app(exe)
        process.wait(timeout=15)


def main():
    import argparse
    parser=argparse.ArgumentParser();parser.add_argument('--existing',action='store_true');args=parser.parse_args()
    prepare();base=Path(__file__).resolve().parent.parent
    if args.existing:
        report=verify(base/'AIClockIn.exe',base/'data','桌面快捷方式已创建')
    else:
        exe=base/f'dist/release/v{current()}/AIClockIn-v{current()}-windows-x64.exe'
        with tempfile.TemporaryDirectory(prefix='settings-frozen-') as folder:
            data=Path(folder);Store(data).save_accounts([])
            write_json(data/'update-settings.json',{'auto_check':False})
            # Current user's existing root-install desktop link must not be replaced by this test EXE.
            report=verify(exe,data,'创建快捷方式失败')
    output=Path('D:/个人开发软件/AI工作区/outputs/AIClockIn-validation/settings')
    write_json(output/('frozen-success.json' if args.existing else 'frozen-conflict.json'),report)
    print(json.dumps(report,ensure_ascii=False))


if __name__=='__main__':main()
