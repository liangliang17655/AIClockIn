"""Interactive client preparation only: never invokes a reward control."""
import json
import os
from pathlib import Path
import subprocess
import tempfile
import time
import uuid

from .doubaowork import desktop_status
from .store import OperationLock


def powershell(script, timeout=60):
    # A file avoids Windows' command-line limit and preserves Chinese in PS 5.
    from .runtime import prepare
    prepare()
    with tempfile.NamedTemporaryFile(suffix='.ps1', mode='w', encoding='utf-8-sig',
                                     delete=False) as stream:
        stream.write(script)
        path = Path(stream.name)
    try:
        exe = Path(os.environ['SystemRoot']) / 'System32/WindowsPowerShell/v1.0/powershell.exe'
        result = subprocess.run([str(exe), '-NoProfile', '-NonInteractive', '-File', str(path)],
                                capture_output=True, timeout=timeout, creationflags=0x08000000)
        if result.returncode:
            raise RuntimeError('powershell_failed')
        return json.loads(result.stdout.decode('utf-8-sig'))
    finally:
        path.unlink(missing_ok=True)


class ClientBackend:
    desktop_status = staticmethod(desktop_status)

    def running(self):
        return powershell("$session=(Get-Process -Id $PID).SessionId; [bool]@(Get-Process DoubaoWork -ErrorAction SilentlyContinue | Where-Object SessionId -eq $session).Count | ConvertTo-Json")

    def locate(self):
        result = powershell(r'''
$ErrorActionPreference='Stop'
$paths=@()
foreach($root in @('HKCU:\Software\Microsoft\Windows\CurrentVersion\Uninstall\*','HKLM:\Software\Microsoft\Windows\CurrentVersion\Uninstall\*','HKLM:\Software\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall\*')){
 foreach($item in @(Get-ItemProperty $root -ErrorAction SilentlyContinue)){
  if($item.DisplayName -like '*豆包工作*' -or $item.DisplayName -eq 'DoubaoWork'){
   if($item.InstallLocation){$paths+=Join-Path $item.InstallLocation 'DoubaoWork.exe'}
  }
 }
}
$paths+='D:\LenovoSoftstore\Install\doubaogongzuo\DoubaoWork\DoubaoWork.exe'
$valid=@($paths | Select-Object -Unique | Where-Object {
 if(Test-Path -LiteralPath $_ -PathType Leaf){
  $sig=Get-AuthenticodeSignature -LiteralPath $_
  $sig.Status -eq 'Valid' -and $sig.SignerCertificate.Subject -like '*北京春田知韵科技有限公司*'
 }
})
@{path=if($valid.Count -eq 1){$valid[0]}else{$null}}|ConvertTo-Json -Compress
''')
        return Path(result['path']) if result.get('path') else None

    def launch(self, exe):
        subprocess.Popen([str(exe)], cwd=exe.parent, stdin=subprocess.DEVNULL,
                         stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    def inspect(self, timeout):
        script = Path(__file__).with_name('doubao_session.ps1').read_text(encoding='utf-8')
        return powershell(script, timeout)

    def inspect_identity(self):
        """Opt-in visible settings inspection; not a verified account binding."""
        script = Path(__file__).with_name('doubao_session.ps1').read_text(encoding='utf-8')
        definitions = script.split('$steps=@();$fingerprint=', 1)[0]
        return powershell(definitions + "\nRestore-ClientWindows; $end=[DateTime]::UtcNow.AddSeconds(15); "
                          "do {$settings=@(@(Nodes)|Where-Object {$_.Current.ControlType -eq [System.Windows.Automation.ControlType]::Button -and $_.Current.Name -eq '设置' -and -not $_.Current.IsOffscreen}); "
                          "if($settings.Count -eq 1){break};Start-Sleep -Milliseconds 500}while([DateTime]::UtcNow -lt $end);"
                          "$value=Read-VisibleIdentity; "
                          "@{account_fingerprint=$value;identity_verified=$false;"
                          "settings_closed=$script:identitySettingsClosed;close_hresult=$script:identityCloseHresult;"
                          "source='official_settings_visible_number'}|ConvertTo-Json -Compress", 30)

    def inspect_ledger(self, keep_open=False):
        script = Path(__file__).with_name('doubao_session.ps1').read_text(encoding='utf-8')
        definitions = script.split('$steps=@();$fingerprint=', 1)[0]
        flag = '$true' if keep_open else '$false'
        return powershell(definitions + '\n$result=Read-RewardLedger ' + flag + '; $result|ConvertTo-Json -Depth 5 -Compress', 45)

    def close_ledger(self):
        script = Path(__file__).with_name('doubao_session.ps1').read_text(encoding='utf-8')
        definitions = script.split('$steps=@();$fingerprint=', 1)[0]
        return powershell(definitions + "\n$w=@(@(Nodes)|Where-Object {$_.Current.ControlType -eq [System.Windows.Automation.ControlType]::Window -and $_.Current.Name -eq '奖励发放明细' -and -not $_.Current.IsOffscreen});"
                          "$closed=($w.Count -eq 0);if($w.Count -eq 1){$closed=Close-KnownDialog $w[0]};@{closed=$closed}|ConvertTo-Json -Compress", 20)

    def refresh_activity(self):
        script = Path(__file__).with_name('doubao_session.ps1').read_text(encoding='utf-8')
        definitions = script.split('$steps=@();$fingerprint=', 1)[0]
        return powershell(definitions + r'''
$nodes=@(Nodes)
$docs=@($nodes|Where-Object {$_.Current.ControlType -eq [System.Windows.Automation.ControlType]::Document -and $_.Current.Name -eq '免费用豆包工作' -and -not $_.Current.IsOffscreen})
$buttons=@($nodes|Where-Object {$_.Current.ControlType -eq [System.Windows.Automation.ControlType]::Button -and $_.Current.Name -eq '刷新' -and $_.Current.IsEnabled -and -not $_.Current.IsOffscreen})
$requested=$false
if($docs.Count -eq 1 -and $buttons.Count -eq 1){
 $p=$null;if($buttons[0].TryGetCurrentPattern([System.Windows.Automation.InvokePattern]::Pattern,[ref]$p)){$p.Invoke();$requested=$true;Start-Sleep -Seconds 2}
}
@{refresh_requested=$requested;business_freshness_verified=$false}|ConvertTo-Json -Compress
''', 20)


def prepare_session(store, backend=None, expected_fingerprint=None):
    backend = backend or ClientBackend()
    result = dict(ready=False, launch_started=False, claim_attempted=False,
                  checkin_state='unknown', identity_binding='unverified', reason='unknown')
    with OperationLock(store.root):
        try:
            if not backend.desktop_status()[0]:
                result['reason'] = 'desktop_unavailable'
            else:
                if not backend.running():
                    exe = backend.locate()
                    if not exe:
                        result['reason'] = 'trusted_client_not_found'
                    else:
                        result['reason'] = 'launch_failed'
                        backend.launch(exe)
                        result['launch_started'] = True
                if backend.running() or result['launch_started']:
                    result['reason'] = 'inspection_failed'
                    data = backend.inspect(timeout=90)
                    result['activity_ready'] = bool(data.get('activity_ready'))
                    for key in ('error_type', 'hresult'):
                        if key in data:
                            result[key] = data[key]
                    fingerprint = data.get('account_fingerprint')
                    result['steps'] = data.get('steps', [])
                    result['claim_button_count'] = data.get('claim_button_count', 0)
                    if data.get('login_required'):
                        result['reason'] = 'login_required'
                    elif fingerprint and expected_fingerprint and fingerprint != expected_fingerprint:
                        result['reason'] = 'account_mismatch'
                    elif not data.get('activity_ready'):
                        result['reason'] = data.get('reason', 'activity_unavailable')
                    elif not fingerprint:
                        result['reason'] = 'identity_unknown'
                    else:
                        result.update(ready=True, reason='prepared_not_signed')
                    # A visible Doubao number is a candidate identifier, not a verified UID.
                    result['account_fingerprint'] = fingerprint
        except subprocess.TimeoutExpired:
            result['reason'] = 'inspection_timeout'
        except Exception as exc:
            result['error_type'] = type(exc).__name__
        store.record(uuid.uuid4().hex, 'doubaowork', '当前会话（身份待确认）',
                     '预检完成（未领取）' if result['ready'] else '预检失败', None, None,
                     json.dumps(result, ensure_ascii=False))
    return result


def check_bound_session(store, backend=None):
    """Fail-closed identity/official-page workflow. No reward submission exists here."""
    from .doubao_binding import load, read_candidate
    from .doubao_receipt import classify
    from datetime import datetime, timezone, timedelta
    backend = backend or ClientBackend()
    result = dict(ready=False, query_completed=False, claim_attempted=False,
                  checkin_state='unknown', identity_binding='unconfirmed',
                  identity_verified=False, reason='binding_unreadable')
    account_id = uuid.uuid4().hex

    class StopCheck(Exception):
        pass

    with OperationLock(store.root):
        try:
            bound = load(store)
            if not bound:
                raise StopCheck('binding_required')
            if not backend.desktop_status()[0]:
                raise StopCheck('desktop_unavailable')
            if not backend.running():
                result['reason'] = 'client_location_failed'
                exe = backend.locate()
                if not exe:
                    raise StopCheck('trusted_client_not_found')
                result['reason'] = 'launch_failed'
                backend.launch(exe)
                result['launch_started'] = True
                deadline = time.monotonic() + 30
                while not backend.running():
                    if time.monotonic() >= deadline:
                        raise StopCheck('client_start_timeout')
                    time.sleep(.5)
            result['reason'] = 'identity_unavailable'
            if read_candidate(backend) != bound['fingerprint']:
                raise StopCheck('account_mismatch')
            result['identity_binding'] = 'before_match_only'
            result['reason'] = 'activity_unavailable'
            page = backend.inspect(timeout=90)
            if not page.get('activity_ready'):
                result['navigation_reason'] = page.get('reason', 'unknown')
                result['navigation_error_type'] = page.get('error_type')
                result['navigation_hresult'] = page.get('hresult')
                raise StopCheck('activity_unavailable')
            result['reason'] = 'reward_ledger_unavailable'
            ledger = backend.inspect_ledger()
            result['reason'] = 'identity_recheck_unavailable'
            if read_candidate(backend) != bound['fingerprint']:
                raise StopCheck('account_mismatch_after_query')
            result['identity_binding'] = 'matched_user_binding'
            # Settings inspection changes the active UI; prove the return, not just Invoke.
            result['reason'] = 'activity_return_failed'
            page = backend.inspect(timeout=90)
            if not page.get('activity_ready'):
                result['navigation_reason'] = page.get('reason', 'unknown')
                raise StopCheck('activity_return_failed')
            if not backend.desktop_status()[0]:
                raise StopCheck('desktop_unavailable')
            account_id = bound['id']
            result.update(query_completed=True, reason='daily_state_unknown',
                          claim_button_count=page.get('claim_button_count', 0),
                          navigation_steps=page.get('steps', []),
                          state_evidence=page.get('state_evidence', {}))
            receipt = classify(ledger, datetime.now(timezone(timedelta(hours=8))).date().isoformat())
            result['ledger_header_verified'] = bool(ledger.get('header_verified'))
            result['ledger_reason'] = ledger.get('reason', 'unknown')
            result['official_receipt'] = receipt
            if receipt['state'] == 'already_signed':
                labels = result['state_evidence'].get('labels', [])
                if result['claim_button_count'] or any(s in labels for s in ('立即签到','今日未签到','未签到')):
                    result['reason'] = 'state_evidence_conflict'
                else:
                    result.update(checkin_state='already_signed', reason='already_signed_skip')
        except StopCheck as exc:
            result['reason'] = str(exc)
        except Exception as exc:
            result['error_type'] = type(exc).__name__
        state = ('今日已签到（查询，未领取）' if result['checkin_state'] == 'already_signed'
                 else '状态未知（未领取）' if result['query_completed'] else '核对失败（未领取）')
        store.record(account_id, 'doubaowork',
                     '用户确认绑定账号' if result['query_completed'] else '未完成身份核对的独立记录',
                     state,
                     None, None, json.dumps(result, ensure_ascii=False))
    return result
