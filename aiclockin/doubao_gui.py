"""Small read-only quota window; all Tk access remains on the main thread."""
import queue
import threading
import tkinter as tk
from tkinter import ttk

from . import doubaowork


FIELDS = (('binding', '账号绑定'), ('checkin', '今日签到'), ('cumulative', '活动累计获得'),
          ('total', '活动赠送总额'), ('used', '活动赠送已用'), ('remaining', '活动赠送剩余'),
          ('expiry', '到期时间'), ('observed_at', '本次读取时间'))


def describe(detail):
    return '\n'.join(f'{label}：{detail.get(key) if detail.get(key) is not None else "未知"}'
                     for key, label in FIELDS) + '\n' + detail.get('issue', '')


class QuotaWindow:
    def __init__(self, app):
        self.app = app
        self.window = tk.Toplevel(app.root)
        self.window.title('豆包工作 · 当前会话只读额度')
        self.window.geometry('620x550')
        self.window.minsize(570, 520)
        self.events = queue.Queue()
        self.busy = False
        self.closed = False
        frame = ttk.Frame(self.window, padding=22)
        frame.pack(fill='both', expand=True)
        frame.columnconfigure(1, weight=1)
        ttk.Label(frame, text='豆包工作', style='Section.TLabel').grid(row=0, column=0, columnspan=2, sticky='w')
        ttk.Label(frame, text='账号身份待确认 · 仅关联当前客户端页面，不绑定个人账号',
                  style='Muted.TLabel', wraplength=550).grid(row=1, column=0, columnspan=2, sticky='w', pady=(5, 16))
        self.values = {}
        for row, (key, label) in enumerate(FIELDS, 2):
            ttk.Label(frame, text=label).grid(row=row, column=0, sticky='w', pady=5, padx=(0, 25))
            self.values[key] = tk.StringVar(value='未知')
            ttk.Label(frame, textvariable=self.values[key], wraplength=360).grid(row=row, column=1, sticky='w', pady=5)
        self.values['binding'].set('账号身份待确认')
        self.values['checkin'].set('状态未知')
        self.message = tk.StringVar(value='请保持官方活动页或“订阅与额度管理”页打开，再点击关联并刷新。')
        ttk.Label(frame, textvariable=self.message, wraplength=550, style='Muted.TLabel').grid(
            row=10, column=0, columnspan=2, sticky='w', pady=(14, 8))
        ttk.Label(frame, text='查询记录按次独立保存，可在主窗口查看。仅支持已验证的交互式读取；\n不加入自动签到，不代表后台、锁屏或客户端关闭后可查询。',
                  wraplength=550, style='Muted.TLabel').grid(row=11, column=0, columnspan=2, sticky='w', pady=(0, 14))
        self.button = ttk.Button(frame, text='关联当前客户端并刷新额度', command=self.refresh, style='Primary.TButton')
        self.button.grid(row=12, column=0, columnspan=2, sticky='ew')
        self.window.protocol('WM_DELETE_WINDOW', self.close)
        self.job = self.window.after(150, self.poll)

    def refresh(self):
        if self.busy or self.app.running or self.app.updating:
            self.message.set('其他操作正在进行，请稍后刷新。')
            return
        self.busy = True
        self.button.configure(state='disabled')
        for key, value in self.values.items():
            value.set('账号身份待确认' if key == 'binding' else '状态未知' if key == 'checkin' else '未知')
        self.message.set('正在只读查询，最多等待约 20 秒；不会执行领取。')

        def read():
            result = doubaowork.query()
            saved = True
            try:
                doubaowork.record(self.app.store, result)
            except Exception:
                saved = False  # Never surface database/credential exception contents.
            self.events.put((result, saved))

        threading.Thread(target=read, daemon=True).start()

    def poll(self):
        if self.closed:
            return
        try:
            result, saved = self.events.get_nowait()
            self.busy = False
            self.button.configure(state='normal', text='刷新额度（当前客户端）')
            for key, value in self.values.items():
                item = getattr(result, key)
                value.set('未知' if item is None else str(item))
            self.message.set(f'{result.state}；' + ('按次记录已保存。' if saved else '记录保存失败，请重试。') + result.issue)
            self.app.refresh()
        except queue.Empty:
            pass
        self.job = self.window.after(150, self.poll)

    def close(self):
        if self.busy:
            self.message.set('正在查询，请等待完成后关闭，避免丢失本次结果。')
            return
        self.closed = True
        self.window.after_cancel(self.job)
        self.window.destroy()
