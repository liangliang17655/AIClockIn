"""Folder distribution metadata and current-install process marker."""
import configparser
import ctypes
from ctypes import wintypes as w
import hashlib
import json
from pathlib import Path
import shutil

from .update import file_hash
from .store import write_json

_marker = None


def unicode_md5(text):
    return hashlib.md5(text.encode('utf-16-le')).hexdigest()


def running_name(exe):
    return 'Local\\AIClockIn-run-' + unicode_md5(str(Path(exe).resolve()).lower())


def register_running(exe):
    global _marker
    api=ctypes.WinDLL('kernel32',use_last_error=True)
    api.CreateMutexW.argtypes=[ctypes.c_void_p,w.BOOL,w.LPCWSTR];api.CreateMutexW.restype=w.HANDLE
    _marker=api.CreateMutexW(None,False,running_name(exe))
    if not _marker:raise RuntimeError('无法登记程序运行状态')


def data_root(folder):
    folder=Path(folder).resolve();config=folder/'install-info.ini'
    if not config.exists():return folder/'data'
    content=config.read_bytes()
    encoding='utf-16' if content[:2] in (b'\xff\xfe',b'\xfe\xff') else 'utf-8-sig'
    try:text=content.decode(encoding)
    except UnicodeError:text=content.decode('mbcs')
    parser=configparser.ConfigParser(interpolation=None)
    parser.read_string(text)
    value=Path(parser.get('Data','Directory')).resolve()
    if value.drive.upper()!='D:':raise ValueError('安装数据目录必须在 D 盘')
    return value


def write_manifest(folder,version,runtime=None):
    folder=Path(folder)
    if runtime is None:
        candidates=[p.name for p in folder.iterdir() if p.is_dir() and p.name.startswith('_runtime-v')]
        if len(candidates)!=1:raise ValueError('请明确指定本次运行目录')
        runtime=candidates[0]
    if Path(runtime).name!=runtime or not runtime.startswith('_runtime-v'):raise ValueError('运行目录名称无效')
    files={p.relative_to(folder).as_posix():file_hash(p) for p in folder.rglob('*')
           if p.is_file() and ((p.name=='AIClockIn.exe' and p.parent==folder) or p.relative_to(folder).parts[0]==runtime)}
    write_json(folder/'bundle-manifest.json',{'format':'onedir','version':version,'runtime':runtime,'files':files})


def copy_bundle(folder,dest):
    folder,dest=Path(folder).resolve(),Path(dest).resolve()
    manifest=json.loads((folder/'bundle-manifest.json').read_text('utf-8'))
    files=manifest.get('files',{})
    if not isinstance(files,dict) or not 1<=len(files)<=10000:raise ValueError('运行目录清单无效')
    for name,digest in files.items():
        path=Path(name)
        if path.is_absolute() or '..' in path.parts or not (path.name=='AIClockIn.exe' and len(path.parts)==1 or path.parts[0].startswith('_runtime-v')):
            raise ValueError('运行目录清单包含不允许的路径')
        source=(folder/path).resolve()
        if not source.is_relative_to(folder) or file_hash(source)!=digest:raise ValueError('运行目录文件校验失败')
        target=dest/path;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(source,target)
    shutil.copyfile(folder/'bundle-manifest.json',dest/'bundle-manifest.json')
    return manifest
