import os
from pathlib import Path
import subprocess
import sys
import tempfile

def default_temp():
    if getattr(sys, 'frozen', False):
        return Path(sys.executable).resolve().parent / '.runtime'
    return Path('D:/个人开发软件/AI工作区/temp/AIClockIn/runtime')


TEMP = default_temp()


def prepare(directory=None):
    if not Path('D:/').is_dir():
        raise RuntimeError('D 盘不可用，已停止运行')
    temporary = Path(directory) if directory is not None else TEMP
    if temporary.resolve().drive.upper() != 'D:':
        raise ValueError('临时目录必须在 D 盘')
    temporary.mkdir(parents=True, exist_ok=True)
    for key in ('TEMP', 'TMP', 'TMPDIR'):
        os.environ[key] = str(temporary)
    tempfile.tempdir = str(temporary)


def home():
    return Path(sys.executable).resolve().parent if getattr(sys, 'frozen', False) else Path(__file__).resolve().parent.parent


def launch(root, *arguments):
    entry = [sys.executable] if getattr(sys, 'frozen', False) else [sys.executable, '-B', str(home() / 'main.py')]
    return subprocess.Popen([*entry, *arguments, '--data', str(root)], cwd=home(),
        stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        env={**os.environ, 'PYINSTALLER_RESET_ENVIRONMENT': '1', 'PYTHONDONTWRITEBYTECODE': '1'},
        creationflags=subprocess.CREATE_NO_WINDOW | subprocess.CREATE_NEW_PROCESS_GROUP)
