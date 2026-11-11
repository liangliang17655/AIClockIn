"""Standalone application and no-window workers."""
import argparse
from pathlib import Path
import sys
from aiclockin.runtime import prepare, home


def selftest(report):
    import tempfile
    import tkinter as tk
    from aiclockin.store import Store, write_json
    from aiclockin.gui import App
    with tempfile.TemporaryDirectory(prefix='selftest-') as folder:
        store = Store(Path(folder))
        rows = [{'id': 'selftest', 'platform': 'workbuddy', 'name': '离线示例', 'enabled': True,
                 'credentials': {'uid': 'synthetic-user', 'access_token': 'synthetic-secret'}}]
        store.save_accounts(rows)
        assert store.accounts() == rows
        assert b'synthetic-secret' not in store.account_file.read_bytes()
        store.record('selftest', 'workbuddy', '离线示例', '失败', None, None, '离线自检，没有请求平台')
        assert Store(Path(folder)).history()[0]['state'] == '失败'
        root = tk.Tk()
        root.withdraw()
        try:
            app = App(root, store, check_updates=False)
            root.update()
            assert len(app.accounts.get_children()) == 1 and len(app.history.get_children()) == 1
        finally:
            root.destroy()
    from aiclockin.version import current
    value = {'ok': True, 'dpapi': True, 'history': True, 'gui': True, 'version': current(),
             'extracted': str(getattr(sys, '_MEIPASS', 'source')), 'home': str(home())}
    if report:
        write_json(report, value)
    return 0


def main():
    parser = argparse.ArgumentParser(description='AIClockIn 本地核心签到')
    modes = parser.add_mutually_exclusive_group()
    for option in ('silent', 'status', 'add-workbuddy', 'add-trae', 'auto-on', 'auto-off', 'self-test'):
        modes.add_argument('--' + option, action='store_true')
    parser.add_argument('--data', type=Path)
    parser.add_argument('--account')
    parser.add_argument('--report', type=Path)
    modes.add_argument('--apply-update', type=Path)
    parser.add_argument('--wait-pid', type=int, default=0)
    parser.add_argument('--wait-parent', type=int, default=0)
    args = parser.parse_args()
    prepare()
    if args.report and args.report.resolve().drive.upper() != 'D:':
        raise ValueError('报告只能写入 D 盘')
    if args.self_test:
        return selftest(args.report)
    if args.apply_update:
        from aiclockin.update_apply import run_helper
        return run_helper(args.apply_update, args.wait_pid, args.wait_parent)
    if getattr(sys, 'frozen', False):
        from aiclockin.update_apply import UpdateGate, pending, launch_helper
        with UpdateGate(Path(sys.executable)):
            interrupted = pending(Path(sys.executable))
        if interrupted:
            if any((args.silent, args.status, args.add_workbuddy, args.add_trae, args.auto_on, args.auto_off)):
                return 2  # Do not use real accounts while an interrupted update needs recovery.
            import os
            launch_helper(interrupted, os.getpid())
            return 0
    from aiclockin.store import Store, Busy, write_json
    from aiclockin.service import Service
    store = Store(args.data or home() / 'data')
    worker = any((args.silent, args.status, args.add_workbuddy, args.add_trae, args.auto_on, args.auto_off))
    try:
        service = Service(store)
        if args.silent or args.status:
            ok, text = service.run(args.status, args.account)
        elif args.add_workbuddy:
            text, ok = service.import_workbuddy(), True
        elif args.add_trae:
            text, ok = service.login_trae(), True
        elif args.auto_on or args.auto_off:
            if not getattr(sys, 'frozen', False):
                raise ValueError('请使用打包后的 EXE 设置自动签到')
            from aiclockin.schedule import TaskManager
            manager = TaskManager(store.root, Path(sys.executable))
            manager.enable() if args.auto_on else manager.disable()
            text, ok = ('后台自动签到已开启，关闭窗口后也会执行。' if args.auto_on else '后台自动签到已停用。'), True
        else:
            import tkinter as tk
            from aiclockin.gui import App
            root = tk.Tk()
            App(root, store)
            root.mainloop()
            return 0
        if args.report:
            write_json(args.report, {'ok': ok, 'message': text})
        return 0 if ok else 1
    except Exception as exc:
        # These paths emit controlled exceptions; scrub in case a provider message contains credentials.
        from aiclockin.service import scrub
        try:
            rows = store.accounts()
        except Exception:
            rows = []
        text = scrub(exc, rows)
        if args.report:
            write_json(args.report, {'ok': False, 'message': text})
        if not worker:
            import ctypes
            ctypes.windll.user32.MessageBoxW(None, text, 'AIClockIn', 0x10)
        return 2 if isinstance(exc, Busy) else 1


if __name__ == '__main__':
    try:
        raise SystemExit(main())
    except SystemExit:
        raise
    except Exception:
        if not any(arg.startswith('--') for arg in sys.argv[1:]):
            import ctypes
            ctypes.windll.user32.MessageBoxW(None, '启动失败，请确认 D 盘及程序目录可写。', 'AIClockIn', 0x10)
        raise SystemExit(1)
