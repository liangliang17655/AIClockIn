"""Small read-only quota window; all Tk access remains on the main thread."""
import queue
import threading
import tkinter as tk
from tkinter import ttk, messagebox

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
        self.window.title('豆包工作 · 账号与签到')
        self.window.geometry('620x610')
        self.window.minsize(570, 580)
        self.events = queue.Queue()
        self.busy = False
        self.closed = False
        frame = ttk.Frame(self.window, padding=22)
        frame.pack(fill='both', expand=True)
        frame.columnconfigure(1, weight=1)
        ttk.Label(frame, text='豆包工作', style='Section.TLabel').grid(row=0, column=0, columnspan=2, sticky='w')
        ttk.Label(frame, text='支持用户确认的单账号绑定；可见豆包号匹配不等于平台 UID 已验证。',
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
        ttk.Label(frame, text='仅身份核对通过的查询关联绑定账号，否则按次独立保存。\n需要未锁屏的交互桌面；状态未知就停止，当前不执行领取。',
                  wraplength=550, style='Muted.TLabel').grid(row=11, column=0, columnspan=2, sticky='w', pady=(0, 14))
        self.button = ttk.Button(frame, text='关联当前客户端并刷新额度', command=self.refresh, style='Primary.TButton')
        self.button.grid(row=12, column=0, columnspan=2, sticky='ew')
        self.bind_button = ttk.Button(frame, text='绑定当前账号…', command=self.bind_account)
        self.bind_button.grid(row=13, column=0, sticky='ew', pady=(8, 0), padx=(0, 8))
        self.check_button = ttk.Button(frame, text='核对账号并检查签到状态', command=self.check_account)
        self.check_button.grid(row=13, column=1, sticky='ew', pady=(8, 0))
        self.show_binding()
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
            self.events.put(('quota', (result, saved)))

        threading.Thread(target=read, daemon=True).start()

    def show_binding(self):
        from .doubao_binding import load
        try:
            bound = load(self.app.store)
            self.values['binding'].set('已绑定（用户确认；本次额度未核对）' if bound else '账号身份待确认')
        except ValueError:
            self.values['binding'].set('绑定无法读取；未替换原文件')

    def background(self, kind, function):
        if self.busy or self.app.running or self.app.updating:
            self.message.set('其他操作正在进行，请稍后重试。')
            return
        self.busy = True
        for key, value in self.values.items():
            if key != 'binding':
                value.set('状态未知' if key == 'checkin' else '未知')
        for button in (self.button, self.bind_button, self.check_button):
            button.configure(state='disabled')
        self.message.set('正在核对官方客户端，未知时停止；不会领取。')
        def run():
            try:
                self.events.put((kind, function()))
            except Exception:
                self.events.put(('error', '操作未完成；原绑定和记录保留。请检查客户端和交互桌面。'))
        threading.Thread(target=run, daemon=True).start()

    def bind_account(self):
        from .doubao_binding import read_candidate
        from .doubao_session import ClientBackend
        from .store import OperationLock
        def read():
            with OperationLock(self.app.store.root):
                return read_candidate(ClientBackend())
        self.background('binding_candidate', read)

    def check_account(self):
        from .doubao_session import check_bound_session
        self.background('binding_check', lambda: check_bound_session(self.app.store))

    def poll(self):
        if self.closed:
            return
        try:
            kind, payload = self.events.get_nowait()
            self.busy = False
            for button in (self.button, self.bind_button, self.check_button):
                button.configure(state='normal')
            if kind == 'quota':
                result, saved = payload
                self.button.configure(text='刷新额度（当前客户端）')
                for key, value in self.values.items():
                    item = getattr(result, key)
                    value.set('未知' if item is None else str(item))
                self.message.set(f'{result.state}；' + ('按次记录已保存。' if saved else '记录保存失败，请重试。') + result.issue)
            elif kind == 'binding_candidate':
                if messagebox.askyesno('确认绑定当前账号',
                    '请确认官方客户端当前登录的是你要绑定的账号。\n'
                    f'可见豆包号指纹：{payload[:12]}…\n\n'
                    '这属于用户确认绑定，不代表平台 UID 已验证。\n保存前将重新读取；账号变化就停止。', parent=self.window):
                    from .doubao_binding import confirm
                    from .doubao_session import ClientBackend
                    self.background('binding_saved', lambda: confirm(self.app.store, payload, ClientBackend(), confirmed=True))
                else:
                    self.message.set('已取消；未保存绑定。')
            elif kind == 'binding_saved':
                self.message.set('用户确认绑定已加密保存；尚未启用自动领取。')
            elif kind == 'binding_check':
                signed = payload['checkin_state'] == 'already_signed'
                self.values['checkin'].set('今日已签到（官方奖励明细）' if signed else '状态未知')
                receipt = payload.get('official_receipt', {})
                self.message.set((f"官方明细：{receipt.get('official_time')}，奖励 {receipt.get('official_reward')} 额度；已跳过领取。"
                                  if signed else '核对已停止，未领取。原因：' + payload['reason']))
            else:
                self.message.set(payload)
            self.show_binding()
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
