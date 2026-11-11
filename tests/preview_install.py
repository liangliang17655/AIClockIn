"""Synthetic installer preview, never writes an installation or desktop link."""
from pathlib import Path
import sys
import tkinter as tk
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from aiclockin.installer import InstallerUI, DEFAULT
from aiclockin.runtime import prepare
from tests.preview import capture


def main():
    prepare()
    output=Path('D:/个人开发软件/AI工作区/outputs/AIClockIn-validation/install')
    output.mkdir(parents=True,exist_ok=True)
    for existing,name in ((False,'new'),(True,'existing')):
        root=tk.Tk()
        try:
            with patch('aiclockin.installer.location',return_value=(DEFAULT,DEFAULT/'data',existing)):
                app=InstallerUI(root,DEFAULT/'AIClockIn.exe',DEFAULT/'data' if existing else None)
            root.geometry('560x340');root.update()
            capture(root.winfo_id(),output/(name+'.bmp'))
            root.after_cancel(app.job)
        finally:root.destroy()


if __name__=='__main__':main()
