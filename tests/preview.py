"""Preview only synthetic data, capturing this app's own window with Win32."""
import ctypes
from ctypes import wintypes as w
from pathlib import Path
import struct
import sys
import tempfile
import tkinter as tk

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from aiclockin.gui import App
from aiclockin.runtime import prepare
from aiclockin.store import Store


def capture(hwnd, path):
    u, g = ctypes.windll.user32, ctypes.windll.gdi32
    u.GetAncestor.argtypes, u.GetAncestor.restype = [w.HWND, w.UINT], w.HWND
    hwnd = u.GetAncestor(hwnd, 2)
    u.GetWindowRect.argtypes = [w.HWND, ctypes.POINTER(w.RECT)]
    rect = w.RECT()
    u.GetWindowRect(hwnd, ctypes.byref(rect))
    width, height = rect.right - rect.left, rect.bottom - rect.top
    u.GetWindowDC.argtypes, u.GetWindowDC.restype = [w.HWND], w.HDC
    u.PrintWindow.argtypes = [w.HWND, w.HDC, w.UINT]
    u.ReleaseDC.argtypes = [w.HWND, w.HDC]
    g.CreateCompatibleDC.argtypes, g.CreateCompatibleDC.restype = [w.HDC], w.HDC
    g.CreateCompatibleBitmap.argtypes, g.CreateCompatibleBitmap.restype = [w.HDC, ctypes.c_int, ctypes.c_int], w.HBITMAP
    g.SelectObject.argtypes, g.SelectObject.restype = [w.HDC, w.HANDLE], w.HANDLE
    g.GetDIBits.argtypes = [w.HDC, w.HBITMAP, w.UINT, w.UINT, ctypes.c_void_p, ctypes.c_void_p, w.UINT]
    g.DeleteObject.argtypes = [w.HANDLE]
    g.DeleteDC.argtypes = [w.HDC]
    source = u.GetWindowDC(hwnd)
    target = g.CreateCompatibleDC(source)
    bitmap = g.CreateCompatibleBitmap(source, width, height)
    previous = g.SelectObject(target, bitmap)
    try:
        assert u.PrintWindow(hwnd, target, 2)
        g.SelectObject(target, previous)
        pixels = ctypes.create_string_buffer(width * height * 4)
        header = struct.pack('<IiiHHIIiiII', 40, width, height, 1, 32, 0, len(pixels), 0, 0, 0, 0)
        info = ctypes.create_string_buffer(header)
        assert g.GetDIBits(target, bitmap, 0, height, pixels, info, 0)
        path.write_bytes(struct.pack('<2sIHHI', b'BM', 54 + len(pixels), 0, 0, 54) + header + pixels.raw)
    finally:
        g.SelectObject(target, previous)
        g.DeleteObject(bitmap)
        g.DeleteDC(target)
        u.ReleaseDC(hwnd, source)


def main():
    prepare()
    output = Path('D:/个人开发软件/AI工作区/outputs/AIClockIn-validation')
    output.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='preview-') as folder:
        store = Store(Path(folder))
        rows = [{'id': 'a', 'platform': 'workbuddy', 'name': '我的 WorkBuddy', 'enabled': True, 'credentials': {'uid': 'synthetic-a', 'access_token': 'synthetic-a'}},
                {'id': 'b', 'platform': 'trae', 'name': '我的 Trae CN', 'enabled': True, 'credentials': {'userId': 'synthetic-b', 'accessToken': 'synthetic-b'}}]
        store.save_accounts(rows)
        store.record('a', 'workbuddy', '我的 WorkBuddy', '成功', 100, 1078.17, '示例数据：签到已确认')
        store.record('b', 'trae', '我的 Trae CN', '设备受限', None, None, '示例数据：9095 设备限制，不代表该账号已领取')
        root = tk.Tk()
        try:
            app = App(root, store)
            app.auto_title.set('自动签到未开启')
            app.auto_detail.set('开启后，每天自动执行。关闭窗口也能签到。')
            for size, name in [('1080x780', 'default'), ('920x660', 'compact')]:
                root.geometry(size)
                root.update()
                root.after(250, lambda n=name: (capture(root.winfo_id(), output / (n + '.bmp')), root.quit()))
                root.mainloop()
        finally:
            root.destroy()
    print(output)


if __name__ == '__main__':
    main()
