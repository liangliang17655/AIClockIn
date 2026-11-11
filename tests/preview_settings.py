from pathlib import Path
import sys
import tempfile
import tkinter as tk

sys.path.insert(0,str(Path(__file__).resolve().parent.parent))
from aiclockin.gui import App
from aiclockin.runtime import prepare
from aiclockin.store import Store
from tests.preview import capture


def main():
    prepare()
    output=Path('D:/个人开发软件/AI工作区/outputs/AIClockIn-validation/settings')
    output.mkdir(parents=True,exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='settings-preview-') as folder:
        root=tk.Tk()
        try:
            app=App(root,Store(Path(folder)),check_updates=False)
            for size,name in (('1080x780','default'),('920x660','compact')):
                root.geometry(size);root.update()
                app.updates.menu.show();root.update()
                capture(root.winfo_id(),output/(name+'.bmp'))
                capture(app.updates.menu.window.winfo_id(),output/(name+'-menu.bmp'))
                app.updates.menu.close()
        finally:root.destroy()


if __name__=='__main__':main()
