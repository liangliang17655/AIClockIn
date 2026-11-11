"""Tk owns all widgets; threads only send update events through the existing queue."""
import json
import os
from pathlib import Path
import sys
import threading
import tkinter as tk
from tkinter import ttk, messagebox
import uuid

from .update import ROOT, check, download, expected_hash, UpdateError
from .update_apply import create_transaction, launch_helper
from .store import write_json
from .version import current


class UpdateUI:
    def __init__(self, app, header, enabled=True):
        self.app, self.root = app, app.root
        self.checking = self.downloading = self.installing = False
        self.dialog = None
        self.startup_job = None
        self.cancel = threading.Event()
        self.settings = app.store.root / 'update-settings.json'
        try:
            auto = json.loads(self.settings.read_text('utf-8')).get('auto_check') is not False
        except (OSError, ValueError, AttributeError):
            auto = True
        self.auto = tk.BooleanVar(value=auto)
        self.button = ttk.Menubutton(header, text='设置', width=7)
        self.menu = tk.Menu(self.button, tearoff=False)
        self.menu.add_command(label='检查更新', command=lambda: self.check(True))
        self.menu.add_checkbutton(label='自动检查更新', variable=self.auto, command=self.save_settings)
        self.menu.add_command(label='关于软件', command=self.about)
        self.button.configure(menu=self.menu)
        self.button.pack(side='right', padx=(12, 0))
        if enabled and auto:
            self.startup_job = self.root.after(1200, lambda: self.check(False))

    def send(self, kind, value):
        self.app.events.put(('update:' + kind, value))

    def save_settings(self):
        try:
            write_json(self.settings, {'auto_check': self.auto.get()})
        except OSError:
            messagebox.showerror('保存失败', '更新偏好未能保存，请检查目录权限。', parent=self.root)

    def about(self):
        messagebox.showinfo('关于 AIClockIn', f'AIClockIn v{current()}\nWorkBuddy / Trae CN 本地多账号签到\n'
                            '发布仓库：liangliang17655/AIClockIn\n账号凭据由当前 Windows 用户加密保存。', parent=self.root)

    def check(self, manual):
        if self.checking or self.downloading or self.installing:
            if manual:
                self.app.notice.set('更新操作正在进行，请稍候。')
            return
        self.checking = True
        if manual:
            self.app.notice.set('正在连接 GitHub 检查更新…')
        def run():
            try:
                self.send('checked', (manual, check(current()), None))
            except Exception as exc:
                self.send('checked', (manual, None, str(exc) if isinstance(exc, UpdateError) else '检查更新失败，请稍后重试'))
        threading.Thread(target=run, daemon=True).start()

    def handle(self, kind, value):
        if kind == 'checked':
            self.checking = False
            manual, item, error = value
            if error:
                if manual:
                    self.app.notice.set(error)
                    if messagebox.askretrycancel('检查更新失败', error, parent=self.root):
                        self.check(True)
            elif item:
                self.show_release(item)
            elif manual:
                self.app.notice.set('当前已经是最新正式版本。')
                messagebox.showinfo('检查更新', f'当前 v{current()} 已经是最新正式版本。', parent=self.root)
        elif kind == 'progress':
            done, total = value
            if self.dialog and self.dialog.winfo_exists():
                self.progress.configure(value=100 * done / total)
                self.status.set(f'正在下载 {done / 1048576:.1f} / {total / 1048576:.1f} MB')
        elif kind == 'downloaded':
            self.downloading = False
            item, path, error = value
            if error:
                self.status.set(error)
                self.install_button.configure(text='重新下载', state='normal', command=lambda: self.begin_download(item))
                self.later.configure(text='稍后更新', state='normal', command=self.close_dialog)
            else:
                self.status.set('下载完成，SHA256 校验通过。安装时将关闭窗口，成功后自动重启。')
                self.install_button.configure(text='安装并重启', state='normal', command=lambda: self.install(item, path))
                self.later.configure(text='稍后更新', state='normal', command=self.close_dialog)
        elif kind == 'helper':
            error = value
            if error:
                self.installing = False
                self.app.updating = False
                for button in self.app.buttons:
                    button.configure(state='normal')
                self.status.set(error)
                self.install_button.configure(state='normal')
                self.later.configure(state='normal')
            else:
                self.root.destroy()
                return True

    def close_dialog(self):
        if self.installing:
            return
        if self.downloading:
            self.cancel.set()
            self.status.set('正在取消下载…')
            return
        if self.dialog:
            self.dialog.destroy()
            self.dialog = None

    def show_release(self, item):
        if self.dialog and self.dialog.winfo_exists():
            self.dialog.lift()
            return
        win = self.dialog = tk.Toplevel(self.root)
        win.title('AIClockIn · 发现新版本')
        win.geometry('580x480'); win.minsize(480, 380); win.transient(self.root)
        win.protocol('WM_DELETE_WINDOW', self.close_dialog)
        box = ttk.Frame(win, padding=20); box.pack(fill='both', expand=True)
        box.columnconfigure(0, weight=1); box.rowconfigure(3, weight=1)
        ttk.Label(box, text='发现新版本', style='Section.TLabel').grid(row=0, column=0, sticky='w')
        ttk.Label(box, text=f'当前 v{current()}    →    最新 {item.tag}').grid(row=1, column=0, sticky='w', pady=(6, 12))
        ttk.Label(box, text='本次更新内容').grid(row=2, column=0, sticky='w')
        frame = ttk.Frame(box); frame.grid(row=3, column=0, sticky='nsew', pady=8)
        self.notes = tk.Text(frame, wrap='word', font=('Microsoft YaHei UI', 10), relief='flat', padx=10, pady=8)
        self.notes.insert('1.0', item.notes); self.notes.configure(state='disabled')
        scroll = ttk.Scrollbar(frame, command=self.notes.yview)
        self.notes.configure(yscrollcommand=scroll.set)
        scroll.pack(side='right', fill='y'); self.notes.pack(fill='both', expand=True)
        self.progress = ttk.Progressbar(box, maximum=100)
        self.progress.grid(row=4, column=0, sticky='ew', pady=(4, 8))
        self.status = tk.StringVar(value='仅更新程序，账号、签到记录和自动任务保持原位置。')
        ttk.Label(box, textvariable=self.status, wraplength=420, style='Muted.TLabel').grid(row=5, column=0, sticky='ew')
        actions = ttk.Frame(box); actions.grid(row=6, column=0, sticky='ew', pady=(14, 0))
        self.install_button = ttk.Button(actions, text='立即更新', style='Primary.TButton', command=lambda: self.begin_download(item))
        self.install_button.pack(side='right')
        self.later = ttk.Button(actions, text='稍后更新', command=self.close_dialog)
        self.later.pack(side='right', padx=8)

    def begin_download(self, item):
        if self.downloading or self.installing:
            return
        if not getattr(sys, 'frozen', False):
            self.status.set('源码预览可检查版本；自动安装请使用打包后的 AIClockIn.exe。')
            return
        self.downloading = True; self.cancel.clear()
        self.install_button.configure(state='disabled')
        self.later.configure(text='取消下载', command=self.cancel.set)
        self.status.set('正在获取 SHA256 并下载…')
        def run():
            try:
                path = download(item, ROOT / uuid.uuid4().hex,
                                lambda n, total: self.send('progress', (n, total)), self.cancel)
                self.send('downloaded', (item, path, None))
            except Exception as exc:
                self.send('downloaded', (item, None, str(exc) if isinstance(exc, UpdateError) else '下载失败，当前版本未修改'))
        threading.Thread(target=run, daemon=True).start()

    def install(self, item, path):
        if self.app.running:
            self.status.set('请等待当前签到或账号操作结束后，再点击安装。')
            return
        if self.installing:
            return
        if Path(sys.executable).name != 'AIClockIn.exe':
            self.status.set('请先将软件命名为 AIClockIn.exe 并放在固定目录，再进行自动更新。')
            return
        if not messagebox.askokcancel('准备安装', '即将关闭窗口并更新。请关闭其他 AIClockIn 窗口。\n'
                                     '账号和记录保留，安装成功后自动启动。', parent=self.dialog):
            return
        self.installing = self.app.updating = True
        self.install_button.configure(state='disabled'); self.later.configure(state='disabled')
        for button in self.app.buttons:
            button.configure(state='disabled')
        self.status.set('正在准备独立更新程序…')
        def run():
            try:
                manifest = create_transaction(Path(sys.executable), path, self.app.store.root, item.tag, expected_hash(item))
                launch_helper(manifest, os.getpid())
                self.send('helper', None)
            except Exception:
                self.send('helper', '无法准备更新辅助程序，当前版本未修改。请稍后重试。')
        threading.Thread(target=run, daemon=True).start()
