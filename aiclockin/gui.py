"""AIClockIn's new UI: accounts, one action, clear automation state, and history."""
import json
from pathlib import Path
import queue
import sys
import threading
import tkinter as tk
from tkinter import messagebox, simpledialog, ttk
import uuid

from .runtime import TEMP, launch
from .service import Service, scrub

DOUBAO_SESSION = 'doubaowork-current-session'


def platform_name(platform):
    return {'workbuddy': 'WorkBuddy', 'trae': 'Trae CN', 'doubaowork': '豆包工作'}.get(platform, platform)


def amount(value):
    return '—' if value is None else f'{value:,.2f}'.rstrip('0').rstrip('.')


class App:
    def __init__(self, root, store, check_updates=True, probe_auto=True):
        self.probe_auto = probe_auto
        self.root, self.store = root, store
        self.events = queue.Queue()
        self.running = False
        self.updating = False
        self.auto_enabled = False
        self.buttons = []
        self.account_rows, self.record_rows = {}, {}
        root.title('AIClockIn · 每日签到')
        root.geometry('1080x780')
        root.minsize(920, 660)
        root.configure(bg='#F7F9FC')
        icon_path = Path(__file__).resolve().parent.parent / 'assets/app.ico'
        if icon_path.exists():
            root.iconbitmap(str(icon_path))
        style = ttk.Style(root)
        style.theme_use('clam')
        style.configure('.', font=('Microsoft YaHei UI', 10), background='#F7F9FC', foreground='#1C2840')
        style.configure('TFrame', background='#F7F9FC')
        style.configure('TLabel', background='#F7F9FC')
        style.configure('Title.TLabel', font=('Microsoft YaHei UI', 23, 'bold'), foreground='#152542')
        style.configure('Muted.TLabel', foreground='#758399', font=('Microsoft YaHei UI', 9))
        style.configure('Section.TLabel', font=('Microsoft YaHei UI', 11, 'bold'))
        style.configure('TButton', background='#FFFFFF', foreground='#344560', padding=(12, 7),
                        bordercolor='#DFE5EF', lightcolor='#FFFFFF', darkcolor='#FFFFFF', borderwidth=1)
        style.map('TButton', background=[('active', '#ECF2FD'), ('pressed', '#DFE9FC')], foreground=[('disabled', '#A1ADBF')])
        style.configure('Primary.TButton', background='#2863E8', foreground='#FFFFFF', bordercolor='#2863E8')
        style.map('Primary.TButton', background=[('disabled', '#B6C8EC'), ('active', '#1E52CB'), ('pressed', '#1843AD')],
                  foreground=[('!disabled', '#FFFFFF'), ('disabled', '#F5F8FF')])
        style.configure('Treeview', rowheight=30, background='#FFFFFF', fieldbackground='#FFFFFF',
                        foreground='#3C4C63', bordercolor='#E1E7F0', lightcolor='#E1E7F0', darkcolor='#E1E7F0')
        style.configure('Treeview.Heading', background='#EDF2FA', foreground='#708198', padding=(10, 8),
                        font=('Microsoft YaHei UI', 9, 'bold'), relief='flat')
        style.map('Treeview', background=[('selected', '#E8F0FF')], foreground=[('selected', '#1D4DA2')])
        style.map('Treeview.Heading', background=[('active', '#E7EDF8')])
        style.configure('Vertical.TScrollbar', background='#D3DDEB', troughcolor='#F7F9FC', borderwidth=0)
        style.layout('Vertical.TScrollbar', [('Vertical.Scrollbar.trough', {'sticky': 'ns', 'children':
                     [('Vertical.Scrollbar.thumb', {'expand': '1', 'sticky': 'nswe'})]})])
        base = ttk.Frame(root, padding=(24, 18))
        base.pack(fill='both', expand=True)
        base.columnconfigure(0, weight=1)
        base.rowconfigure(3, weight=1, minsize=105)
        base.rowconfigure(6, weight=2, minsize=105)
        header = ttk.Frame(base)
        header.grid(row=0, column=0, sticky='ew', pady=(0, 14))
        icon = tk.Canvas(header, width=48, height=48, bg='#F7F9FC', highlightthickness=0)
        icon.create_oval(3, 3, 43, 43, fill='#2863E8', outline='')
        icon.create_line(23, 12, 23, 24, 32, 24, fill='white', width=3, capstyle='round')
        icon.pack(side='left', padx=(0, 12))
        title = ttk.Frame(header)
        title.pack(side='left')
        ttk.Label(title, text='AIClockIn', style='Title.TLabel').pack(anchor='w')
        ttk.Label(title, text='只做签到，简单一点。', style='Muted.TLabel').pack(anchor='w')
        from .update_gui import UpdateUI
        self.updates = UpdateUI(self, header, enabled=check_updates)
        ttk.Label(header, text='本机加密保存', style='Muted.TLabel').pack(side='right', padx=(12, 0))

        auto = ttk.Frame(base, padding=(12, 9))
        auto.grid(row=1, column=0, sticky='ew', pady=(0, 12))
        auto.columnconfigure(0, weight=1)
        self.auto_title = tk.StringVar(value='正在检查自动签到…')
        self.auto_detail = tk.StringVar(value='读取任务状态，不会领取积分。')
        self.auto_label = ttk.Label(auto, textvariable=self.auto_title, style='Section.TLabel')
        self.auto_label.grid(row=0, column=0, sticky='w')
        ttk.Label(auto, textvariable=self.auto_detail, style='Muted.TLabel').grid(row=1, column=0, sticky='w', pady=(3, 0))
        self.auto_button = self.button(auto, '开启自动签到', self.toggle_auto)
        self.auto_button.grid(row=0, column=1, rowspan=2, padx=(10, 0))

        account_header = ttk.Frame(base)
        account_header.grid(row=2, column=0, sticky='ew', pady=(0, 8))
        self.count = ttk.Label(account_header, text='我的账号', style='Section.TLabel')
        self.count.pack(side='left')
        self.button(account_header, '全部签到', lambda: self.worker('--silent'), primary=True).pack(side='right')
        self.button(account_header, '添加 Trae CN', lambda: self.worker('--add-trae')).pack(side='right', padx=7)
        self.button(account_header, '添加 WorkBuddy', lambda: self.worker('--add-workbuddy')).pack(side='right')
        self.button(account_header, '豆包工作（只读）', self.open_doubao).pack(side='right', padx=7)
        self.accounts = self.table(base, 3, ('platform', 'name', 'enabled', 'last'),
                                   ('平台', '账号', '状态', '最近结果'), (130, 330, 110, 250))
        self.accounts.bind('<<TreeviewSelect>>', lambda event: self.refresh_history())
        actions = ttk.Frame(base)
        actions.grid(row=4, column=0, sticky='ew', pady=(8, 12))
        for text, action in [('查询状态', self.query), ('重命名', self.rename), ('启用 / 停用', self.toggle), ('删除', self.delete)]:
            self.button(actions, text, action).pack(side='left', padx=(0, 7))
        self.button(actions, '刷新', self.refresh_all).pack(side='right')
        history_header = ttk.Frame(base)
        history_header.grid(row=5, column=0, sticky='ew', pady=(0, 8))
        self.history_label = ttk.Label(history_header, text='签到记录', style='Section.TLabel')
        self.history_label.pack(side='left')
        ttk.Button(history_header, text='查看全部', command=self.clear_selection).pack(side='right')
        self.history = self.table(base, 6, ('time', 'platform', 'name', 'state', 'earned', 'balance'),
            ('时间', '平台', '账号', '结果', '本次获得', '余额'), (170, 100, 210, 100, 100, 100))
        self.history.bind('<<TreeviewSelect>>', self.show_detail)
        detail_frame = ttk.Frame(base)
        detail_frame.grid(row=7, column=0, sticky='ew', pady=(8, 0))
        self.detail = tk.Text(detail_frame, height=2, wrap='word', relief='flat', borderwidth=0, padx=10, pady=6,
                              bg='#EDF2F8', fg='#718096', font=('Microsoft YaHei UI', 9))
        self.detail.pack(side='left', fill='x', expand=True)
        scroll = ttk.Scrollbar(detail_frame, orient='vertical', command=self.detail.yview)
        self.detail.configure(yscrollcommand=scroll.set)
        scroll.pack(side='right', fill='y')
        self.set_detail('选择记录查看详情。“—”表示未知，不代表 0 积分。')
        self.notice = tk.StringVar(value='先添加账号；开启自动签到后，不用打开这个窗口。')
        ttk.Label(base, textvariable=self.notice, style='Muted.TLabel', wraplength=980).grid(row=8, column=0, sticky='ew', pady=(8, 0))
        self.refresh()
        self.read_auto()
        self.poll_job = root.after(200, self.poll)
        root.bind('<Destroy>', self.stop, add='+')

    def stop(self, event):
        if event.widget == self.root:
            if self.poll_job:
                self.root.after_cancel(self.poll_job)
            if self.updates.startup_job:
                self.root.after_cancel(self.updates.startup_job)
            self.updates.cancel.set()

    def button(self, parent, text, action, primary=False):
        button = ttk.Button(parent, text=text, command=action, style='Primary.TButton' if primary else 'TButton')
        self.buttons.append(button)
        return button

    def table(self, parent, row, fields, labels, widths):
        frame = ttk.Frame(parent)
        frame.grid(row=row, column=0, sticky='nsew')
        tree = ttk.Treeview(frame, columns=fields, show='headings', selectmode='browse', height=3)
        for field, label, width in zip(fields, labels, widths):
            tree.heading(field, text=label)
            tree.column(field, width=width, minwidth=70)
        scroll = ttk.Scrollbar(frame, orient='vertical', command=tree.yview)
        tree.configure(yscrollcommand=scroll.set)
        tree.pack(side='left', fill='both', expand=True)
        scroll.pack(side='right', fill='y')
        tree.tag_configure('error', foreground='#B84336')
        tree.tag_configure('success', foreground='#188069')
        return tree

    def refresh(self):
        try:
            accounts = self.store.accounts()
            selected = self.accounts.selection()
            self.accounts.delete(*self.accounts.get_children())
            self.account_rows = {a['id']: a for a in accounts}
            latest = {}
            for row in self.store.history():
                latest.setdefault(row['account_id'], row)
            for a in accounts:
                state = latest.get(a['id'], {}).get('state', '尚无记录')
                self.accounts.insert('', 'end', iid=a['id'], values=('WorkBuddy' if a['platform'] == 'workbuddy' else 'Trae CN',
                    scrub(a['name'], [a]), '已启用' if a.get('enabled', True) else '已停用', state),
                    tags=('error',) if state in ('失败', '设备受限') else ())
            self.account_rows[DOUBAO_SESSION] = {'platform': 'doubaowork'}
            self.accounts.insert('', 'end', iid=DOUBAO_SESSION, values=(
                '豆包工作', '当前客户端 · 账号身份待确认', '仅手动只读', '选择后查询额度'))
            if selected and selected[0] in self.account_rows:
                self.accounts.selection_set(selected[0])
            self.count.configure(text=f'账号 / 会话   {len(accounts) + 1}')
            self.refresh_history()
        except Exception as exc:
            self.notice.set(str(exc))

    def refresh_history(self):
        selected = self.accounts.selection()
        doubao_selected = bool(selected and selected[0] == DOUBAO_SESSION)
        self.history_label.configure(text='所选账号记录' if selected else '签到记录 · 最近 200 条')
        if doubao_selected:
            self.history_label.configure(text='豆包工作 · 按次查询记录（不代表同一账号）')
        self.history.delete(*self.history.get_children())
        self.record_rows = {}
        for row in self.store.history(selected[0] if selected and not doubao_selected else None):
            if doubao_selected and row['platform'] != 'doubaowork':
                continue
            key = str(row['id'])
            self.record_rows[key] = row
            state = row['state']
            self.history.insert('', 'end', iid=key, values=(row['time'].replace('T', ' ')[:19],
                platform_name(row['platform']), row['name'], state, amount(row['earned']), amount(row['balance'])),
                tags=('error',) if state in ('失败', '设备受限', '额度查询失败') else ('success',))

    def set_detail(self, text):
        self.detail.configure(state='normal')
        self.detail.delete('1.0', 'end')
        self.detail.insert('1.0', text)
        self.detail.configure(state='disabled')

    def show_detail(self, event=None):
        selection = self.history.selection()
        if selection and selection[0] in self.record_rows:
            row = self.record_rows[selection[0]]
            if row['platform'] == 'doubaowork':
                from .doubao_gui import describe
                try:
                    self.set_detail(describe(json.loads(row['detail'])))
                except (ValueError, TypeError, AttributeError):
                    self.set_detail('豆包工作查询详情无法读取。')
            else:
                self.set_detail(row['detail'])

    def clear_selection(self):
        self.accounts.selection_remove(*self.accounts.selection())
        self.refresh_history()

    def refresh_all(self):
        self.refresh()
        self.read_auto()

    def read_auto(self):
        if not self.probe_auto:
            return  # Offline installation check must not inspect real Windows tasks.
        if not getattr(sys, 'frozen', False):
            self.auto_title.set('自动签到在 EXE 中设置')
            self.auto_detail.set('开发预览不会读取或修改系统任务。')
            return
        def read():
            try:
                from .schedule import TaskManager
                status = TaskManager(self.store.root, Path(sys.executable)).status()
            except Exception:
                status = {'enabled': False, 'label': '自动状态暂时无法读取', 'detail': '请稍后刷新；不会因此执行签到。'}
            self.events.put(('auto', status))
        threading.Thread(target=read, daemon=True).start()

    def toggle_auto(self):
        if not getattr(sys, 'frozen', False):
            self.notice.set('请使用 AIClockIn.exe 开启自动签到。')
            return
        self.worker('--auto-off' if self.auto_enabled else '--auto-on')

    def worker(self, *arguments):
        if self.running or self.updating:
            return
        TEMP.mkdir(parents=True, exist_ok=True)
        report = TEMP / ('result-' + uuid.uuid4().hex + '.json')
        try:
            process = launch(self.store.root, *arguments, '--report', str(report))
        except OSError:
            self.notice.set('无法启动后台进程，请检查程序文件是否完整。')
            return
        self.running = True
        for button in self.buttons:
            button.configure(state='disabled')
        self.notice.set('正在处理…关闭窗口不会中断；添加 Trae 时请在浏览器完成登录。')
        def wait():
            code = process.wait()
            text = '操作完成' if code == 0 else '操作未完成，请查看记录或重试'
            try:
                if report.exists():
                    text = json.loads(report.read_text('utf-8'))['message']
            except (OSError, ValueError, KeyError):
                text = '操作结果暂时无法读取，请刷新记录查看。'
            finally:
                try:
                    report.unlink(missing_ok=True)
                except OSError:
                    pass
            self.events.put(('done', text))
        threading.Thread(target=wait, daemon=True).start()

    def poll(self):
        if self.poll_job:
            self.root.after_cancel(self.poll_job)
            self.poll_job = None
        try:
            while True:
                kind, value = self.events.get_nowait()
                if kind == 'auto':
                    self.auto_enabled = value['enabled']
                    self.auto_title.set(value['label'])
                    self.auto_detail.set(value['detail'])
                    self.auto_label.configure(foreground='#188069' if value['enabled'] else '#718096')
                    self.auto_button.configure(text='停用自动签到' if value['enabled'] else '开启自动签到')
                elif kind.startswith('update:'):
                    if self.updates.handle(kind[7:], value):
                        return
                elif kind == 'done':
                    self.running = False
                    for button in self.buttons:
                        button.configure(state='normal')
                    self.notice.set(value)
                    self.refresh_all()
        except queue.Empty:
            pass
        if self.root.winfo_exists():
            self.poll_job = self.root.after(200, self.poll)

    def selection(self):
        selected = self.accounts.selection()
        if not selected:
            self.notice.set('请先选择一个账号。')
            return None
        if selected[0] == DOUBAO_SESSION:
            self.notice.set('豆包工作仅关联当前只读会话，不支持账号重命名、启停或删除。')
            return None
        return selected[0]

    def query(self):
        if self.accounts.selection() == (DOUBAO_SESSION,):
            self.open_doubao()
            return
        selected = self.selection()
        if selected:
            self.worker('--status', '--account', selected)

    def open_doubao(self):
        if self.running or self.updating:
            self.notice.set('当前操作正在进行，请稍后打开豆包工作查询。')
            return
        dialog = getattr(self, 'doubao_window', None)
        if dialog and not dialog.closed:
            dialog.window.lift()
            return
        from .doubao_gui import QuotaWindow
        self.doubao_window = QuotaWindow(self)

    def edit(self, **changes):
        if self.updating:
            return
        selected = self.selection()
        if selected:
            try:
                Service(self.store).edit(selected, **changes)
                self.refresh()
                self.notice.set('账号已更新，历史记录保留。')
            except Exception as exc:
                self.notice.set(str(exc))

    def rename(self):
        selected = self.selection()
        if selected:
            name = simpledialog.askstring('账号名称', '输入一个便于辨认的名字：', parent=self.root,
                initialvalue=self.accounts.item(selected, 'values')[1])
            if name and name.strip():
                self.edit(name=name)

    def toggle(self):
        selected = self.selection()
        if selected:
            self.edit(enabled=not self.account_rows[selected].get('enabled', True))

    def delete(self):
        if self.selection() and messagebox.askyesno('移除账号', '仅删除本项目的账号凭据，签到历史保留。', parent=self.root):
            self.edit(delete=True)
