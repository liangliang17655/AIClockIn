"""Offline installation checks, using synthetic data and persistent diagnostics only."""
import json
import os
from pathlib import Path
import platform
import struct
import sys
import tempfile
import traceback


def perform(stage):
    stage('imports')
    import tkinter as tk
    from .store import Store
    from .gui import App
    stage('dpapi')
    with tempfile.TemporaryDirectory(prefix='selftest-') as folder:
        store = Store(Path(folder))
        rows = [{'id': 'selftest', 'platform': 'workbuddy', 'name': '离线示例', 'enabled': True,
                 'credentials': {'uid': 'synthetic-user', 'access_token': 'synthetic-secret'}}]
        store.save_accounts(rows)
        assert store.accounts() == rows
        assert b'synthetic-secret' not in store.account_file.read_bytes()
        stage('sqlite')
        store.record('selftest', 'workbuddy', '离线示例', '失败', None, None, '离线自检，没有请求平台')
        assert Store(Path(folder)).history()[0]['state'] == '失败'
        stage('tk')
        root = tk.Tk()
        root.withdraw()
        try:
            app = App(root, store, check_updates=False, probe_auto=False)
            root.update()
            assert set(app.accounts.get_children()) == {'selftest', 'doubaowork-current-session'}
            assert len(app.history.get_children()) == 1
        finally:
            root.destroy()
    return {'dpapi': True, 'history': True, 'gui': True}


def run(report):
    from . import runtime
    report = Path(report or runtime.TEMP / 'diagnostics' / 'health.json').resolve()
    if report.drive.upper() != 'D:':
        raise ValueError('自检报告只能写入 D 盘')
    value = {'ok': False, 'stage': 'prepare', 'python': platform.python_version(),
             'windows': platform.platform(), 'bits': struct.calcsize('P') * 8,
             'home': str(runtime.home()), 'extracted': str(getattr(sys, '_MEIPASS', 'source')),
             'work': str(report.parent / 'work')}
    original = {key: os.environ.get(key) for key in ('TEMP', 'TMP', 'TMPDIR')}
    previous_temp = tempfile.tempdir
    def stage(name):
        value['stage'] = name
        # A crash/forced timeout still leaves the last reached stage on disk.
        save()
    def save():
        report.parent.mkdir(parents=True, exist_ok=True)
        pending = report.with_suffix('.pending')
        pending.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding='utf-8')
        os.replace(pending, report)
    try:
        save()
        runtime.prepare(report.parent / 'work')
        from .version import current
        value['version'] = current()
        value.update(perform(stage))
        value.update(ok=True, stage='complete')
    except Exception as exc:
        # Only synthetic self-check state exists here; never load real accounts.
        value.update(error_type=type(exc).__name__, message=str(exc), traceback=traceback.format_exc())
    finally:
        for key, previous in original.items():
            if previous is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = previous
        tempfile.tempdir = previous_temp
    save()
    return 0 if value['ok'] else 1
