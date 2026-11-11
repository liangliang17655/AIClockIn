"""Synthetic update dialog and existing layout preview, without network requests."""
from pathlib import Path
import sys
import tempfile
import tkinter as tk

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from aiclockin.gui import App
from aiclockin.runtime import prepare
from aiclockin.store import Store
from aiclockin.update import Release
from tests.preview import capture


def main():
    prepare()
    output = Path('D:/个人开发软件/AI工作区/outputs/AIClockIn-validation/update')
    output.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='update-preview-') as folder:
        root = tk.Tk()
        try:
            app = App(root, Store(Path(folder)), check_updates=False)
            for geometry, name in [('1080x780', 'main'), ('920x660', 'compact')]:
                root.geometry(geometry); root.update()
                capture(root.winfo_id(), output / (name + '.bmp'))
            app.updates.show_release(Release('v0.2.1', '【预览示例，并非线上版本】\n\n- 修复示例问题。\n- 优化运行稳定性。\n\n更新仅替换程序文件，账号和记录保留。', '', '', 1, None, None))
            root.update()
            capture(app.updates.dialog.winfo_id(), output / 'dialog.bmp')
        finally:
            root.destroy()


if __name__ == '__main__':
    main()
