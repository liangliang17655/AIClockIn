"""Standalone application and no-window workers."""
import argparse
from pathlib import Path
import sys
from aiclockin.runtime import prepare, home


def selftest(report):
    from aiclockin.selfcheck import run
    return run(report)


def main():
    parser = argparse.ArgumentParser(description='AIClockIn 本地核心签到')
    modes = parser.add_mutually_exclusive_group()
    for option in ('silent', 'status', 'add-workbuddy', 'add-trae', 'auto-on', 'auto-off', 'self-test', 'install', 'uninstall-task'):
        modes.add_argument('--' + option, action='store_true')
    parser.add_argument('--data', type=Path)
    parser.add_argument('--account')
    parser.add_argument('--report', type=Path)
    modes.add_argument('--apply-update', type=Path)
    modes.add_argument('--apply-setup', type=Path)
    parser.add_argument('--wait-pid', type=int, default=0)
    parser.add_argument('--wait-parent', type=int, default=0)
    args = parser.parse_args()
    if args.self_test:
        return selftest(args.report)
    prepare()
    if args.report and args.report.resolve().drive.upper() != 'D:':
        raise ValueError('报告只能写入 D 盘')
    from aiclockin.package import data_root, register_running
    if args.uninstall_task:
        from aiclockin.setup_support import remove_own_task
        return remove_own_task(Path(sys.executable),args.data or data_root(home()))
    if args.apply_setup:
        from aiclockin.setup_update import run_helper
        return run_helper(args.apply_setup,args.wait_pid)
    if args.apply_update:
        from aiclockin.update_apply import run_helper
        return run_helper(args.apply_update, args.wait_pid, args.wait_parent)
    if getattr(sys, 'frozen', False):
        from aiclockin.update_apply import UpdateGate, pending, launch_helper
        with UpdateGate(Path(sys.executable)):
            interrupted = pending(Path(sys.executable))
            from aiclockin import setup_update
            setup_interrupted=setup_update.pending(Path(sys.executable))
            if not interrupted and not setup_interrupted:
                register_running(Path(sys.executable))
        if setup_interrupted:
            if setup_update.active(setup_interrupted):return 2
            if any((args.silent,args.status,args.add_workbuddy,args.add_trae,args.auto_on,args.auto_off)):return 2
            import os
            setup_update.launch_helper(setup_interrupted,os.getpid())
            return 0
        if interrupted:
            if any((args.silent, args.status, args.add_workbuddy, args.add_trae, args.auto_on, args.auto_off)):
                return 2  # Do not use real accounts while an interrupted update needs recovery.
            import os
            launch_helper(interrupted, os.getpid())
            return 0
    if args.install:
        raise ValueError('请运行 AIClockInSetup.exe 安装包')
    from aiclockin.store import Store, Busy, write_json
    from aiclockin.service import Service
    store = Store(args.data or data_root(home()))
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
