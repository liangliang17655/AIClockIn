"""Install the existing onefile program and a current-user desktop link; never move data."""
import base64
import ctypes
from ctypes import wintypes as w
import json
import os
from pathlib import Path
import queue
import subprocess
import sys
import threading
import tkinter as tk
from tkinter import filedialog, ttk
import uuid
import xml.etree.ElementTree as ET

from .store import OperationLock
from .update import ROOT, file_hash, validate_pe
from .update_apply import UpdateGate, atomic_replace, create_transaction, durable_copy, health_check, replace_transaction, start, child_env
from .version import current

DEFAULT = Path('D:/AIClockIn')
AUTO_TASK = object()


class InstallError(RuntimeError):
    pass


def needs_install(source, *, frozen, gui, data=None):
    local = Path(source).parent / 'data'
    return bool(frozen and gui and data is None and not any((local / name).is_file() for name in ('accounts.json', 'history.db')))


def split_arguments(arguments):
    api = ctypes.WinDLL('shell32', use_last_error=True)
    api.CommandLineToArgvW.argtypes = [w.LPCWSTR, ctypes.POINTER(ctypes.c_int)]
    api.CommandLineToArgvW.restype = ctypes.POINTER(w.LPWSTR)
    count = ctypes.c_int()
    values = api.CommandLineToArgvW('AIClockIn.exe ' + arguments, ctypes.byref(count))
    if not values:
        raise InstallError('无法读取已有自动签到的数据路径')
    free = ctypes.WinDLL('kernel32').LocalFree
    free.argtypes = [ctypes.c_void_p]
    try:
        return [values[index] for index in range(1, count.value)]
    finally:
        free(values)


def location(source, data=None, task=AUTO_TASK):
    source = Path(source).resolve()
    if data is not None:
        return source.parent, Path(data).resolve(), True
    local = source.parent / 'data'
    if source.drive.upper() == 'D:' and any((local / name).exists() for name in ('accounts.json', 'history.db')):
        return source.parent, local, True
    if task is AUTO_TASK:
        from .schedule import WindowsTask
        try:
            task = WindowsTask()
        except Exception:
            raise InstallError('无法确认原自动任务，请在原软件“设置 → 创建桌面快捷方式”操作，避免选错数据目录') from None
    if task is not None:
        from .schedule import NS
        try:
            xml = task.get()
            if xml:
                root = ET.fromstring(xml)
                exe = Path(root.findtext('t:Actions/t:Exec/t:Command', namespaces=NS) or '').resolve()
                owner = root.findtext('t:Principals/t:Principal/t:UserId', namespaces=NS)
                args = split_arguments(root.findtext('t:Actions/t:Exec/t:Arguments', namespaces=NS) or '')
                if exe.name != 'AIClockIn.exe' or exe.drive.upper() != 'D:' or not exe.is_file() or owner != task.user:
                    raise InstallError('已有自动任务无法安全识别，请从原软件创建桌面快捷方式')
                index = args.index('--data')
                saved = Path(args[index + 1]).resolve()
                if saved.drive.upper() != 'D:':
                    raise InstallError('已有自动任务的数据目录不在 D 盘')
                return exe.parent, saved, True
        except InstallError:
            raise
        except Exception:
            raise InstallError('读取已有自动任务失败，未迁移或覆盖任何账号，请从原软件创建快捷方式') from None
    existing = any((DEFAULT / 'data' / name).is_file() for name in ('accounts.json', 'history.db'))
    return DEFAULT, DEFAULT / 'data', existing


def destination(folder):
    folder = Path(folder).resolve()
    if folder.drive.upper() != 'D:' or folder == Path('D:/'):
        raise InstallError('请选择 D 盘中的文件夹，程序和账号数据不会安装到 C 盘')
    return folder / 'AIClockIn.exe'


def shell(script, value):
    payload = base64.b64encode(json.dumps(value, ensure_ascii=False).encode('utf-8')).decode('ascii')
    script = ("$ErrorActionPreference='Stop';[Console]::OutputEncoding=[Text.UTF8Encoding]::new($false);"
              "$v=[Text.Encoding]::UTF8.GetString([Convert]::FromBase64String('" + payload + "'))|ConvertFrom-Json;" + script)
    encoded = base64.b64encode(script.encode('utf-16le')).decode('ascii')
    result = subprocess.run(['powershell.exe', '-NoProfile', '-NonInteractive', '-EncodedCommand', encoded],
                            capture_output=True, timeout=30, creationflags=subprocess.CREATE_NO_WINDOW)
    if result.returncode:
        raise InstallError('无法创建或验证桌面快捷方式，请检查桌面写入权限及同名文件')
    return json.loads(result.stdout.decode('utf-8-sig'))


def create_shortcut(target, data, desktop=None):
    target, data = Path(target).resolve(), Path(data).resolve()
    arguments = subprocess.list2cmdline(['--data', str(data)])
    value = {'target': str(target), 'data': str(data), 'arguments': arguments,
             'folder': str(target.parent), 'desktop': str(Path(desktop).resolve()) if desktop else None}
    script = r"""
$sh=New-Object -ComObject WScript.Shell;
$desk=if($v.desktop){$v.desktop}else{$sh.SpecialFolders.Item('Desktop')};
if(-not (Test-Path -LiteralPath $desk -PathType Container)){throw 'Desktop unavailable'};
$link=Join-Path $desk 'AIClockIn 自动签到.lnk';
if(Test-Path -LiteralPath $link){
    $old=$sh.CreateShortcut($link);
    if($old.TargetPath -ne $v.target -or $old.Arguments -ne $v.arguments){throw 'Different existing shortcut'};
    @{path=$link;target=$old.TargetPath;arguments=$old.Arguments;working=$old.WorkingDirectory}|ConvertTo-Json -Compress;return
};
$temp=Join-Path $desk ('.AIClockIn-'+[Guid]::NewGuid().ToString('N')+'.lnk');
try{
    $s=$sh.CreateShortcut($temp);$s.TargetPath=$v.target;$s.Arguments=$v.arguments;
    $s.WorkingDirectory=$v.folder;$s.IconLocation=$v.target+',0';$s.Description='AIClockIn 自动签到';$s.Save();
    $check=$sh.CreateShortcut($temp);
    if($check.TargetPath -ne $v.target -or $check.Arguments -ne $v.arguments -or $check.WorkingDirectory -ne $v.folder){throw 'Link verification failed'};
    [IO.File]::Move($temp,$link);
    @{path=$link;target=$check.TargetPath;arguments=$check.Arguments;working=$check.WorkingDirectory}|ConvertTo-Json -Compress
}finally{if(Test-Path -LiteralPath $temp){Remove-Item -LiteralPath $temp -Force}}
"""
    return shell(script, value)['path']


def install(source, folder, data, expected, desktop=None):
    source, data = Path(source).resolve(), Path(data).resolve()
    target = destination(folder)
    if data.drive.upper() != 'D:' or target.is_relative_to(data):
        raise InstallError('数据目录必须在 D 盘，并与程序文件分开')
    if not source.is_file():
        raise InstallError('安装来源程序不存在')
    ROOT.mkdir(parents=True, exist_ok=True)
    transaction = ROOT / ('install-' + uuid.uuid4().hex)
    transaction.mkdir()
    stage = target.with_name('.AIClockIn-install-' + uuid.uuid4().hex + '.exe')
    try:
        validate_pe(source)
        target.parent.mkdir(parents=True, exist_ok=True)
        with UpdateGate(target, timeout=2), OperationLock(data):
            digest = file_hash(source)
            if target.exists() and file_hash(target) != digest:
                manifest = create_transaction(target, source, data, expected, digest)
                replace_transaction(manifest)
            elif not target.exists():
                durable_copy(source, stage)
                if file_hash(stage) != digest:
                    raise InstallError('安装文件校验失败')
                health_check(stage, transaction / 'transaction.json', expected)
                atomic_replace(target, stage)
            try:
                create_shortcut(target, data, desktop=desktop)
            except Exception:
                raise InstallError(f'程序文件已就位，但桌面快捷方式未创建；请检查同名快捷方式和桌面权限后重试。程序位置：{target}') from None
        return target
    except InstallError:
        raise
    except Exception:
        raise InstallError('安装未完成，请关闭其他 AIClockIn 窗口及后台操作后重试；原账号、记录和任务未迁移') from None
    finally:
        stage.unlink(missing_ok=True)


class InstallerUI:
    def __init__(self, root, source, data=None):
        self.root, self.source = root, Path(source).resolve()
        self.from_app = data is not None
        self.events, self.busy, self.installed = queue.Queue(), False, None
        self.target_folder, self.data, self.existing = location(source, data)
        root.title('AIClockIn · 安装与桌面入口')
        root.geometry('600x350'); root.minsize(560, 340)
        root.configure(bg='#F7F9FC')
        icon = Path(__file__).resolve().parent.parent / 'assets/app.ico'
        if icon.is_file():
            root.iconbitmap(str(icon))
        style = ttk.Style(root); style.theme_use('clam')
        style.configure('.', font=('Microsoft YaHei UI', 10), background='#F7F9FC', foreground='#1C2840')
        style.configure('TFrame', background='#F7F9FC')
        style.configure('Install.TButton', padding=(12, 7), background='#2863E8', foreground='white')
        style.map('Install.TButton', background=[('active', '#1E52CB'), ('disabled', '#B6C8EC')])
        root.protocol('WM_DELETE_WINDOW', self.close)
        box = ttk.Frame(root, padding=24); box.pack(fill='both', expand=True)
        box.columnconfigure(0, weight=1); box.rowconfigure(4, weight=1)
        ttk.Label(box, text='创建桌面快捷方式' if self.existing else '安装 AIClockIn', font=('Microsoft YaHei UI', 17, 'bold')).grid(row=0, column=0, columnspan=2, sticky='w', pady=(0, 12))
        ttk.Label(box, text='程序保存在 D 盘，桌面上创建快捷方式。以后双击桌面图标即可打开。',
                  wraplength=510).grid(row=1, column=0, columnspan=2, sticky='w', pady=(0, 16))
        self.path = tk.StringVar(value=str(self.target_folder))
        self.entry = ttk.Entry(box, textvariable=self.path, state='readonly' if self.existing else 'normal')
        self.entry.grid(row=2, column=0, sticky='ew')
        self.browse = ttk.Button(box, text='选择目录', command=self.choose, state='disabled' if self.existing else 'normal')
        self.browse.grid(row=2, column=1, padx=(8, 0))
        explanation = ('检测到现有程序，保留原目录、账号和自动任务，只补桌面入口。' if self.existing
                       else '默认安装到 D:\\AIClockIn。开启自动签到后，不用每天打开窗口。')
        ttk.Label(box, text=explanation, wraplength=510).grid(row=3, column=0, columnspan=2, sticky='w', pady=(12, 0))
        self.status = tk.StringVar(value='不会自动开启或修改 Windows 签到任务。')
        ttk.Label(box, textvariable=self.status, wraplength=510).grid(row=4, column=0, columnspan=2, sticky='nw', pady=16)
        self.action = ttk.Button(box, text='创建桌面快捷方式' if self.existing else '安装并创建桌面快捷方式', style='Install.TButton', command=self.begin)
        self.action.grid(row=5, column=0, columnspan=2, sticky='e')
        self.job = root.after(100, self.poll)

    def choose(self):
        folder = filedialog.askdirectory(parent=self.root, initialdir='D:/', title='选择 D 盘安装目录')
        if folder:
            self.path.set(folder)

    def begin(self):
        if self.busy:
            return
        if not self.path.get().strip():
            self.status.set('请选择 D 盘安装目录。'); return
        try:
            target = destination(self.path.get())
        except InstallError as exc:
            self.status.set(str(exc)); return
        data = self.data if self.existing else target.parent / 'data'
        self.busy = True; self.action.configure(state='disabled'); self.entry.configure(state='readonly'); self.browse.configure(state='disabled')
        self.status.set('正在检查程序并创建桌面快捷方式，请稍候…')
        def run():
            try:
                result = install(self.source, target.parent, data, current())
                self.events.put((result, data, None))
            except Exception as exc:
                self.events.put((None, data, str(exc) if isinstance(exc, InstallError) else '安装失败，请稍后重试'))
        threading.Thread(target=run, daemon=True).start()

    def poll(self):
        try:
            target, data, error = self.events.get_nowait()
            self.busy = False; self.action.configure(state='normal')
            if error:
                self.status.set(error)
                if not self.existing:
                    self.entry.configure(state='normal'); self.browse.configure(state='normal')
            else:
                self.installed = target
                self.status.set(f'已完成！桌面上已有“AIClockIn 自动签到”。程序位置：{target.parent}')
                if self.from_app:
                    self.action.configure(text='完成', command=self.close)
                else:
                    self.action.configure(text='完成并打开软件', command=lambda: self.open_app(target, data))
        except queue.Empty:
            pass
        self.job = self.root.after(100, self.poll)

    def open_app(self, target, data):
        try:
            start([str(target), '--data', str(data)], target.parent)
        except OSError:
            self.status.set('快捷方式已创建，启动失败，请稍后从桌面打开。'); return
        self.close()

    def close(self):
        if not self.busy:
            self.root.after_cancel(self.job)
            self.root.destroy()


def run(source, data=None):
    root = tk.Tk()
    try:
        app = InstallerUI(root, source, data)
        root.mainloop()
    except Exception as exc:
        from tkinter import messagebox
        messagebox.showerror('安装未开始', str(exc) if isinstance(exc, InstallError) else '无法打开安装窗口，请检查 D 盘。', parent=root)
        root.destroy()
        return 1
    return 0 if app.installed else 1
