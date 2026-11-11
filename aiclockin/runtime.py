import os
from pathlib import Path
import subprocess
import sys
import tempfile

TEMP = Path('D:/个人开发软件/AI工作区/temp/AIClockIn/runtime')


def prepare():
    if not Path('D:/').is_dir():
        raise RuntimeError('D 盘不可用，已停止运行')
    TEMP.mkdir(parents=True, exist_ok=True)
    for key in ('TEMP', 'TMP', 'TMPDIR'):
        os.environ[key] = str(TEMP)
    tempfile.tempdir = str(TEMP)


def home():
    return Path(sys.executable).resolve().parent if getattr(sys, 'frozen', False) else Path(__file__).resolve().parent.parent


def launch(root, *arguments):
    entry = [sys.executable] if getattr(sys, 'frozen', False) else [sys.executable, '-B', str(home() / 'main.py')]
    return subprocess.Popen([*entry, *arguments, '--data', str(root)], cwd=home(),
        stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        env={**os.environ, 'PYINSTALLER_RESET_ENVIRONMENT': '1', 'PYTHONDONTWRITEBYTECODE': '1'},
        creationflags=subprocess.CREATE_NO_WINDOW | subprocess.CREATE_NEW_PROCESS_GROUP)
