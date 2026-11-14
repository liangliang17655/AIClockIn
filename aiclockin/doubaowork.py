"""Interactive Windows UIA quota observations, never a check-in/identity provider."""
import base64
import ctypes
from ctypes import wintypes
from dataclasses import asdict, dataclass
from datetime import datetime
import json
import os
import re
from pathlib import Path
import subprocess
import uuid


# No UI actions or private API calls. Only exact official-page document titles.
SCRIPT = r'''
$ErrorActionPreference='Stop'
[Console]::OutputEncoding=New-Object System.Text.UTF8Encoding($false)
$stage='assembly'
try {
Add-Type -AssemblyName UIAutomationClient
Add-Type -AssemblyName UIAutomationTypes
$stage='processes'
$targets=@(Get-Process -Name DoubaoWork -ErrorAction SilentlyContinue)
$targetIds=@($targets.Id)
$quota=@();$campaign=@();$truncated=$false
$walker=[System.Windows.Automation.TreeWalker]::RawViewWalker
if($targets.Count -gt 0){
 $stage='windows'
 $root=[System.Windows.Automation.AutomationElement]::RootElement
 $windows=$root.FindAll([System.Windows.Automation.TreeScope]::Children,[System.Windows.Automation.Condition]::TrueCondition)
 foreach($window in $windows){
  if($targetIds -notcontains $window.Current.ProcessId){continue}
  $queue=New-Object System.Collections.Queue
  $queue.Enqueue($window);$count=0
  while($queue.Count -gt 0 -and $count -lt 2000){
   $stage='traversal'
   $element=$queue.Dequeue();$count++;$current=$element.Current
   if($current.ControlType -eq [System.Windows.Automation.ControlType]::Document -and
      $current.Name -in @('订阅与额度管理 - 豆包','免费用豆包工作')){
    $pattern=$element.GetCurrentPattern([System.Windows.Automation.TextPattern]::Pattern)
    $stage='text'
    $text=$pattern.DocumentRange.GetText(20000)
    if($current.Name -eq '订阅与额度管理 - 豆包'){
     $m=[regex]::Match($text,'活动赠送额度\s+已用\s+(\d+)\s*/\s*(\d+)')
     if($m.Success){
      $expiry=[regex]::Match($text,'\d+月\d+日\s+\d{2}:\d{2}\s*到期').Value
      $quota+=@{used=[int64]$m.Groups[1].Value;total=[int64]$m.Groups[2].Value;expiry=$expiry}
     }
    }else{
     $m=[regex]::Match($text,'累计获得额度：\s*(\d+)\s*点')
     if($m.Success){$campaign+=@{cumulative=[int64]$m.Groups[1].Value}}
    }
    $text=$null
   }
   $child=$walker.GetFirstChild($element)
   while($null -ne $child){$queue.Enqueue($child);$child=$walker.GetNextSibling($child)}
  }
  if($queue.Count -gt 0){$truncated=$true}
 }
}
@{running=($targets.Count -gt 0);truncated=$truncated;quota=$quota;campaign=$campaign}|ConvertTo-Json -Depth 5 -Compress
} catch {
 @{error=@{stage=$stage;type=$_.Exception.GetType().FullName;hresult=$_.Exception.HResult}}|ConvertTo-Json -Depth 3 -Compress
}
'''


@dataclass
class Observation:
    observed_at: str
    cumulative: int | None = None
    used: int | None = None
    total: int | None = None
    remaining: int | None = None
    expiry: str | None = None
    identity: str | None = None
    earned: int | None = None
    binding: str = '账号身份待确认'
    checkin: str = '状态未知'
    source: str = 'Windows UIA Raw View / 当前客户端页面'
    issue: str = ''

    @property
    def has_data(self):
        return self.cumulative is not None or self.remaining is not None

    @property
    def state(self):
        return '额度查询成功' if self.has_data else '额度查询失败'


def _empty(issue):
    return Observation(datetime.now().astimezone().isoformat(timespec='seconds'), issue=issue)


def parse(data):
    result = _empty('')
    try:
        if isinstance(data, dict) and isinstance(data.get('error'), dict):
            error = data['error']
            stage = error.get('stage')
            stage = stage if stage in ('assembly', 'processes', 'windows', 'traversal', 'text') else 'unknown'
            kind = error.get('type', '')
            kind = kind if isinstance(kind, str) and re.fullmatch(r'[A-Za-z][A-Za-z0-9_.]{0,180}', kind) else 'UnknownError'
            code = error.get('hresult')
            code = code if type(code) is int else None
            return _empty(f'Windows UIA 异常：阶段 {stage}，类型 {kind}，HRESULT {code}；未判定登录失效。')
        if not isinstance(data, dict) or not isinstance(data.get('running'), bool):
            raise ValueError()
        if not data['running']:
            return _empty('豆包工作客户端未运行；请手动打开客户端和相关页面。')
        if data.get('truncated') is not False:
            return _empty('页面节点超出读取范围，未采用不完整数据。')
        quotas = set()
        for row in data.get('quota', []):
            used, total = row['used'], row['total']
            if type(used) is not int or type(total) is not int or not 0 <= used <= total <= 10**12:
                raise ValueError()
            expiry = row.get('expiry') or None
            # The probe emits only this bounded label, never arbitrary page content.
            if expiry is not None:
                if not re.fullmatch(r'\d+月\d+日\s+\d{2}:\d{2}\s*到期', expiry):
                    raise ValueError()
            quotas.add((used, total, expiry))
        cumulative = set()
        for row in data.get('campaign', []):
            value = row['cumulative']
            if type(value) is not int or not 0 <= value <= 10**12:
                raise ValueError()
            cumulative.add(value)
        if len(quotas) > 1 or len(cumulative) > 1:
            return _empty('多个页面数据冲突，无法确认当前会话，已拒绝关联。')
        if quotas:
            result.used, result.total, result.expiry = quotas.pop()
            result.remaining = result.total - result.used
        if cumulative:
            result.cumulative = cumulative.pop()
        if result.remaining is not None and result.cumulative is not None:
            # No stable identity links the two document sources. Prefer quota and
            # require a separate observation for cumulative; never join on a PID.
            result.cumulative = None
            result.issue = '账号身份未确认，不合并活动页与额度页；本次仅采用额度页。'
        missing = []
        if result.cumulative is None:
            missing.append('累计额度未知：请保持“免费用豆包工作”活动页打开')
        if result.remaining is None:
            missing.append('剩余额度未知：请保持“设置－订阅与额度管理”页打开')
        result.issue = '；'.join(filter(None, [result.issue, *missing]))
        return result
    except (KeyError, TypeError, ValueError, OverflowError):
        return _empty('页面结构或字段不符合已验证格式，额度保持未知。')


def desktop_status():
    """Read the input desktop only; never unlock, switch desktops or request elevation."""
    user = ctypes.WinDLL('user32', use_last_error=True)
    user.OpenInputDesktop.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
    user.OpenInputDesktop.restype = wintypes.HANDLE
    user.CloseDesktop.argtypes = [wintypes.HANDLE]
    user.GetUserObjectInformationW.argtypes = [wintypes.HANDLE, ctypes.c_int, ctypes.c_void_p,
                                              wintypes.DWORD, ctypes.POINTER(wintypes.DWORD)]
    handle = user.OpenInputDesktop(0, False, 1)  # DESKTOP_READOBJECTS
    if not handle:
        return False, ctypes.get_last_error()
    try:
        name = ctypes.create_unicode_buffer(256)
        needed = wintypes.DWORD()
        if not user.GetUserObjectInformationW(handle, 2, name, ctypes.sizeof(name), ctypes.byref(needed)):
            return False, ctypes.get_last_error()
        return name.value.casefold() == 'default', 0
    finally:
        user.CloseDesktop(handle)


def query(timeout=20):
    available, code = desktop_status()
    if not available:
        return _empty(f'当前输入桌面不可访问（锁屏、会话或权限限制；Win32 {code}），额度未知，不判定登录失效。')
    encoded = base64.b64encode(SCRIPT.encode('utf-16-le')).decode('ascii')
    executable = Path(os.environ.get('SystemRoot', 'C:/Windows')) / 'System32/WindowsPowerShell/v1.0/powershell.exe'
    try:
        process = subprocess.run([str(executable), '-NoLogo', '-NoProfile', '-NonInteractive',
                                  '-EncodedCommand', encoded], capture_output=True,
                                 timeout=timeout, creationflags=subprocess.CREATE_NO_WINDOW)
        if process.returncode:
            return _empty(f'Windows UIA 子进程退出码 {process.returncode}；额度未知，不判定登录失效。')
        available, code = desktop_status()
        if not available:
            return _empty(f'读取期间输入桌面变为不可访问（Win32 {code}），未采用缓存页面数据。')
        return parse(json.loads(process.stdout.decode('utf-8-sig')))
    except subprocess.TimeoutExpired:
        return _empty('界面读取超时，未采用旧数据；请等待页面加载后重试。')
    except OSError as exc:
        return _empty(f'无法启动 Windows UIA：{type(exc).__name__}，Win32 {getattr(exc, "winerror", None)}。')
    except (UnicodeError, ValueError):
        return _empty('无法获取有效 UIA 结果；Windows PowerShell 或页面读取不可用。')


def record(store, result):
    # Each observation is deliberately unbound; never merge on nickname/process.
    details = asdict(result)
    details['quota_scope'] = '活动赠送额度，不代表全部产品额度'
    store.record('doubao-observation-' + uuid.uuid4().hex, 'doubaowork',
                 '未绑定会话（账号身份待确认）', result.state, None, result.remaining,
                 json.dumps(details, ensure_ascii=False))
