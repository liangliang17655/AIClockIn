"""Verified Setup updates using a complete, independent folder-distribution helper."""
import ctypes
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import time
import uuid
import winreg

from .package import copy_bundle,running_name
from .store import OperationLock,Busy,write_json
from .update import ROOT,file_hash,version
from .update_apply import UpdateGate,child_env,kernel,start,durable_copy,atomic_replace,health_check,wait_handle
from .health_process import HealthProcess

REGISTRY_KEY=r'Software\Microsoft\Windows\CurrentVersion\Uninstall\AIClockIn-49F2C4C8-EE14-4FC3-83D1-E2826227F14D_is1'


class SetupError(RuntimeError):pass


def capture_registry(target):
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER,REGISTRY_KEY,0,winreg.KEY_READ|winreg.KEY_WOW64_64KEY) as key:
            location=winreg.QueryValueEx(key,'InstallLocation')[0]
            if Path(location).resolve()!=Path(target).parent.resolve():raise SetupError('已有安装登记属于其他目录，请手动运行 Setup')
            values=[]
            for index in range(winreg.QueryInfoKey(key)[1]):
                name,value,kind=winreg.EnumValue(key,index)
                if not isinstance(value,(str,int,list)):raise SetupError('安装登记格式不支持自动备份')
                values.append([name,value,kind])
            return values
    except FileNotFoundError:return None


def restore_registry(value):
    previous=value['registry']
    if previous is None:
        try:
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER,REGISTRY_KEY,0,winreg.KEY_READ|winreg.KEY_WOW64_64KEY) as key:
                location=winreg.QueryValueEx(key,'InstallLocation')[0]
                if Path(location).resolve()!=Path(value['target']).parent:raise SetupError('安装登记路径变化，未删除未知登记')
            winreg.DeleteKeyEx(winreg.HKEY_CURRENT_USER,REGISTRY_KEY,winreg.KEY_WOW64_64KEY)
        except FileNotFoundError:pass
    else:
        with winreg.CreateKeyEx(winreg.HKEY_CURRENT_USER,REGISTRY_KEY,0,winreg.KEY_ALL_ACCESS|winreg.KEY_WOW64_64KEY) as key:
            for index in reversed(range(winreg.QueryInfoKey(key)[1])):winreg.DeleteValue(key,winreg.EnumValue(key,index)[0])
            for name,data,kind in previous:winreg.SetValueEx(key,name,0,kind,data)


def load(manifest):
    manifest=Path(manifest).resolve()
    if manifest.name!='setup.json' or not manifest.is_relative_to(ROOT.resolve()) or manifest.stat().st_size>256000:raise SetupError('Setup 事务路径无效')
    value=json.loads(manifest.read_text('utf-8'))
    target,data,candidate=(Path(value[k]).resolve() for k in ('target','data','candidate'))
    if target.name!='AIClockIn.exe' or target.drive.upper()!='D:' or data.drive.upper()!='D:' or target.is_relative_to(data):raise SetupError('Setup 目标或数据目录无效')
    if candidate!=manifest.parent/'candidate.exe' or value['state'] not in ('ready','installing','committed','restored','restore-failed'):raise SetupError('Setup 事务格式无效')
    if not re.fullmatch('[0-9a-f]{64}',value['new_hash']):raise SetupError('Setup 校验值无效')
    version(value['version'])
    for name,digest in value['backup'].items():
        if Path(name).name!=name or not (name in ('AIClockIn.exe','bundle-manifest.json','install-info.ini') or re.fullmatch(r'unins[0-9]+\.(exe|dat|msg)',name)):
            raise SetupError('Setup 备份文件名无效')
        if not re.fullmatch('[0-9a-f]{64}',digest):raise SetupError('Setup 备份校验值无效')
    return value


def prepare(target,candidate,data,tag,digest):
    target,candidate,data=Path(target).resolve(),Path(candidate).resolve(),Path(data).resolve()
    if file_hash(candidate)!=digest:raise SetupError('Setup 安装包校验失败')
    folder=ROOT/uuid.uuid4().hex;folder.mkdir(parents=True)
    copy_bundle(target.parent,folder/'helper')
    durable_copy(candidate,folder/'candidate.exe')
    backup=folder/'backup';backup.mkdir()
    names=['AIClockIn.exe','bundle-manifest.json','install-info.ini']+[p.name for p in target.parent.glob('unins*') if p.is_file()]
    hashes={}
    for name in names:
        path=target.parent/name
        if path.is_file():durable_copy(path,backup/name);hashes[name]=file_hash(path)
    value={'target':str(target),'data':str(data),'candidate':str(folder/'candidate.exe'),'version':tag.lstrip('v'),
           'new_hash':digest,'backup':hashes,'registry':capture_registry(target),'state':'ready'}
    manifest=folder/'setup.json';write_json(manifest,value);load(manifest)
    return manifest


def setup_command(value,manifest):
    return [value['candidate'],'/VERYSILENT','/SUPPRESSMSGBOXES','/NORESTART','/NOCLOSEAPPLICATIONS',
            '/DIR='+str(Path(value['target']).parent),'/DATA='+value['data'],'/LOG='+str(Path(manifest).parent/'install.log')]


def run_setup(value,manifest):
    with HealthProcess(setup_command(value,manifest),Path(value['target']).parent,child_env()) as process:
        return process.wait(180)


def restore(manifest,value):
    with UpdateGate(value['target']):
        _restore(manifest,value)


def _restore(manifest,value):
    for name,digest in value['backup'].items():
        if file_hash(manifest.parent/'backup'/name)!=digest:raise SetupError('旧程序备份损坏，停止自动恢复')
    # Old versioned runtime remains in place. Restore metadata first, launcher last.
    for name in sorted(value['backup'],key=lambda name:name=='AIClockIn.exe'):
        target=Path(value['target']).parent/name
        if target.is_file() and file_hash(target)==value['backup'][name]:continue
        stage=target.with_name('.restore-'+uuid.uuid4().hex+'.tmp')
        try:
            durable_copy(manifest.parent/'backup'/name,stage)
            for attempt in range(30):
                try:atomic_replace(target,stage);break
                except PermissionError:
                    if attempt==29:raise
                    time.sleep(.1)
        finally:stage.unlink(missing_ok=True)
    restore_registry(value)
    value['state']='restored';write_json(manifest,value)


def execute(manifest):
    manifest=Path(manifest);value=load(manifest)
    if value['state'] in ('installing','restore-failed'):
        restore(manifest,value);return
    if value['state']!='ready':raise SetupError('Setup 事务已经结束')
    if file_hash(value['candidate'])!=value['new_hash']:raise SetupError('Setup 安装包内容已变化')
    value['state']='installing';write_json(manifest,value)
    try:
        code=run_setup(value,manifest)
        if code!=0:raise SetupError(f'Setup 安装未完成（退出码 {code}）')
        health_check(Path(value['target']),manifest,value['version'])
        value['state']='committed';write_json(manifest,value)
    except Exception:
        try:restore(manifest,value)
        except Exception:
            value['state']='restore-failed';write_json(manifest,value)
            raise SetupError(f'安装失败且自动恢复未完成，备份保留在 {manifest.parent}') from None
        raise SetupError('Setup 更新未完成，原程序已恢复，账号和记录保留') from None


def pending(target):
    if not ROOT.exists():return None
    for manifest in ROOT.glob('*/setup.json'):
        try:
            value=load(manifest)
            if Path(value['target'])==Path(target).resolve() and value['state'] in ('installing','restore-failed'):return manifest
        except (ValueError,OSError,KeyError,SetupError):continue
    return None


def run_helper(manifest,pid):
    manifest=Path(manifest).resolve();value=load(manifest);api=kernel();handle=api.OpenProcess(0x100000,False,pid) if pid else None
    error=None
    try:
        if pid and not handle:raise SetupError('无法确认旧进程，未启动 Setup')
        with UpdateGate(manifest):
            write_json(manifest.parent/'helper-ready.json',{'ok':True})
            if handle:wait_handle(api,handle)
            if not (manifest.parent/'authorized').exists() or (manifest.parent/'abort').exists():raise SetupError('Setup 更新已取消')
            api.OpenMutexW.argtypes=[ctypes.c_ulong,ctypes.c_int,ctypes.c_wchar_p];api.OpenMutexW.restype=ctypes.c_void_p
            deadline=time.monotonic()+90
            while True:
                marker=api.OpenMutexW(0x100000,False,running_name(value['target']))
                if marker:api.CloseHandle(marker)
                try:
                    if marker:raise Busy('其他窗口或后台任务未退出')
                    with OperationLock(value['data']):execute(manifest)
                    break
                except Busy:
                    if time.monotonic()>=deadline:raise SetupError('请先关闭其他窗口或等待后台操作结束')
                    time.sleep(.25)
    except Exception as exc:error=str(exc)
    finally:
        if handle:api.CloseHandle(handle)
    state=load(manifest)['state']
    write_json(manifest.parent/'result.json',{'ok':error is None,'message':error or '更新完成','state':state})
    if error:ctypes.windll.user32.MessageBoxW(None,error,'AIClockIn 更新未完成',0x10)
    if state!='restore-failed':start([value['target'],'--data',value['data']],Path(value['target']).parent)
    return 1 if error else 0


def launch_helper(manifest,pid):
    manifest=Path(manifest).resolve();exe=manifest.parent/'helper/AIClockIn.exe'
    process=start([str(exe),'--apply-setup',str(manifest),'--wait-pid',str(pid)],exe.parent)
    deadline=time.monotonic()+30
    while time.monotonic()<deadline:
        if (manifest.parent/'helper-ready.json').exists():
            (manifest.parent/'authorized').write_text('1',encoding='ascii');return process
        if process.poll() is not None:break
        time.sleep(.1)
    (manifest.parent/'abort').write_text('1',encoding='ascii')
    raise SetupError('完整更新辅助程序未就绪，原窗口保持打开')


def active(manifest):
    api=kernel();api.OpenMutexW.argtypes=[ctypes.c_ulong,ctypes.c_int,ctypes.c_wchar_p];api.OpenMutexW.restype=ctypes.c_void_p
    handle=api.OpenMutexW(0x100000,False,UpdateGate(manifest).name)
    if handle:api.CloseHandle(handle)
    return bool(handle)
