"""Read-only UIA spike. Optional navigation selects existing tabs/menu entries only.

No claim invocation, private HTTP, cookie access or changes to production data/tasks.
"""
import argparse
import base64
from datetime import datetime
import json
from pathlib import Path
import subprocess
import sys
import time

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from aiclockin.doubaowork import desktop_status


SCRIPT = r'''
$ErrorActionPreference='Stop'
[Console]::OutputEncoding=New-Object System.Text.UTF8Encoding($false)
Add-Type -AssemblyName UIAutomationClient
Add-Type -AssemblyName UIAutomationTypes
$ids=@(Get-Process -Name DoubaoWork -ErrorAction SilentlyContinue|ForEach-Object {$_.Id})
$walk=[System.Windows.Automation.TreeWalker]::RawViewWalker
function Test-Campaign($node){
 for($depth=0;$node -and $depth -lt 30;$depth++){
  if($node.Current.ControlType -eq [System.Windows.Automation.ControlType]::Document){return ($node.Current.Name -in @('免费用豆包工作','免费用豆包'))}
  $node=$walk.GetParent($node)
 }
 return $false
}
$windows=@();$documents=@();$contexts=@();$errors=@();$navigation=@();$sections=@();$truncated=$false
$roots=[System.Windows.Automation.AutomationElement]::RootElement.FindAll([System.Windows.Automation.TreeScope]::Children,[System.Windows.Automation.Condition]::TrueCondition)
foreach($root in $roots){
 if($ids -notcontains $root.Current.ProcessId){continue}
 if(__RESTORE__){$wp=$null;if($root.TryGetCurrentPattern([System.Windows.Automation.WindowPattern]::Pattern,[ref]$wp)){$wp.SetWindowVisualState([System.Windows.Automation.WindowVisualState]::Normal)}}
 $queue=New-Object System.Collections.Queue;$queue.Enqueue($root);$count=0
 while($queue.Count -gt 0 -and $count -lt 3000){
  $element=$queue.Dequeue();$count++
  try{
   $c=$element.Current
   $knownNav=$c.Name -in @('免费用豆包工作','免费用豆包','免费领额度')
   if($knownNav -and $c.ControlType -in @([System.Windows.Automation.ControlType]::MenuItem,[System.Windows.Automation.ControlType]::TabItem) -and -not (Test-Campaign $element)){
    $action='observed'
    if(__NAVIGATE__ -and -not $c.IsOffscreen){
     if($c.ControlType -eq [System.Windows.Automation.ControlType]::TabItem){($element.GetCurrentPattern([System.Windows.Automation.SelectionItemPattern]::Pattern)).Select();$action='selected_existing_tab'}
     elseif($c.ControlType -eq [System.Windows.Automation.ControlType]::MenuItem){($element.GetCurrentPattern([System.Windows.Automation.InvokePattern]::Pattern)).Invoke();$action='opened_activity_menu'}
    }
    $navigation+=@{label=$c.Name;action=$action;offscreen=$c.IsOffscreen}
   }
   if($c.ControlType -eq [System.Windows.Automation.ControlType]::Document){
    $name=if($c.Name -in @('免费用豆包工作','免费用豆包','订阅与额度管理 - 豆包','豆包工作')){$c.Name}else{'other_document'}
    $pattern=$null;$length=$null;$labels=@()
    if($name -in @('免费用豆包工作','免费用豆包') -and $element.TryGetCurrentPattern([System.Windows.Automation.TextPattern]::Pattern,[ref]$pattern)){
     try{
      $text=$pattern.DocumentRange.GetText(20000);$length=$text.Length
      $labels=@([regex]::Matches($text,'今日已签到|今日未签到|已签到|未签到|立即签到|签到成功|每日签到')|ForEach-Object {$_.Value}|Select-Object -Unique)
      $text=$null
     }catch{
      $ex=$_.Exception;for($depth=0;$depth -lt 4 -and $ex.InnerException;$depth++){$ex=$ex.InnerException}
      if($errors.Count -lt 10){$errors+=@{type=$ex.GetType().FullName;hresult=$ex.HResult;stage='document_text'}}
     }
    }
    $documents+=@{name=$name;chars=$length;labels=$labels}
   }
   if($c.ControlType -eq [System.Windows.Automation.ControlType]::Group -and $c.Name -like '从容开工*' -and (Test-Campaign $element)){
    $banner=New-Object System.Collections.Queue;$banner.Enqueue($element);$bn=0;$types=@{};$invokes=0;$focusable=0;$dateLabels=@();$stateLabels=@()
    while($banner.Count -and $bn -lt 100){
     $node=$banner.Dequeue();$bn++;$v=$node.Current;$key=$v.ControlType.ProgrammaticName;$types[$key]=1+$types[$key]
     if($v.IsKeyboardFocusable){$focusable++}
     if(@($node.GetSupportedPatterns()|Where-Object {$_.ProgrammaticName -eq 'InvokePatternIdentifiers.Pattern'}).Count){$invokes++}
     $dateLabels+=@([regex]::Matches($v.Name,'\d{4}[-/]\d{1,2}[-/]\d{1,2}|\d{1,2}月\d{1,2}日|今日|今天')|ForEach-Object {$_.Value})
     $stateLabels+=@([regex]::Matches($v.Name,'今日已签到|今日未签到|已签到|未签到|立即签到|签到成功|已领取|未领取')|ForEach-Object {$_.Value})
     $bc=$walk.GetFirstChild($node);while($bc){$banner.Enqueue($bc);$bc=$walk.GetNextSibling($bc)}
    }
    $sections+=@{name='daily_banner';nodes=$bn;types=$types;invoke_nodes=$invokes;keyboard_focusable=$focusable;date_labels=$dateLabels;state_labels=$stateLabels;truncated=($banner.Count -gt 0)}
   }
   if($c.Name -match '^(每日签到|立即签到|今日已签到|今日未签到|已签到|未签到|签到成功)$' -and (Test-Campaign $element)){
    if(__REVEAL__ -and $c.Name -eq '每日签到'){$sp=$null;if($element.TryGetCurrentPattern([System.Windows.Automation.ScrollItemPattern]::Pattern,[ref]$sp)){$sp.ScrollIntoView()}}
    # Inspect only this control and its immediate card; no Invoke/Select on it.
    $nodes=@($element);$parent=$walk.GetParent($element)
    if($parent){$parent=$walk.GetParent($parent)}
    if($parent){$card=New-Object System.Collections.Queue;$card.Enqueue($parent);$siblings=0;while($card.Count -and $siblings -lt 80){$node=$card.Dequeue();$nodes+=@($node);$siblings++;$child=$walk.GetFirstChild($node);while($child){$card.Enqueue($child);$child=$walk.GetNextSibling($child)}}}
    $observations=@()
    foreach($node in $nodes){
     $v=$node.Current;$label=$v.Name
     # Restrict persisted text to business labels, dates and reward amounts.
     if($label -notmatch '^(每日签到|立即签到|今日已签到|今日未签到|已签到|未签到|签到成功|今日|今天|\+?\d+\s*额度|\d{1,2}月\d{1,2}日|\d{4}[-/]\d{1,2}[-/]\d{1,2})$'){$label=if($label){'[other_text]'}else{''}}
     $observations+=@{label=$label;type=$v.ControlType.ProgrammaticName;enabled=$v.IsEnabled;offscreen=$v.IsOffscreen;patterns=@($node.GetSupportedPatterns()|ForEach-Object {$_.ProgrammaticName})}
    }
    $contexts+=@{anchor=$c.Name;scope='two_ancestor_group_not_exclusive_signin_card';controls=$observations}
   }
   $child=$walk.GetFirstChild($element);while($child){$queue.Enqueue($child);$child=$walk.GetNextSibling($child)}
  }catch{
   $ex=$_.Exception;for($depth=0;$depth -lt 4 -and $ex.InnerException;$depth++){$ex=$ex.InnerException}
   if($errors.Count -lt 10){$errors+=@{type=$ex.GetType().FullName;hresult=$ex.HResult}}
  }
 }
 if($queue.Count -gt 0){$truncated=$true}
 $windows+=@{handle=$root.Current.NativeWindowHandle;nodes=$count;offscreen=$root.Current.IsOffscreen}
}
@{running=($ids.Count -gt 0);windows=$windows;documents=$documents;signin_contexts=$contexts;navigation=$navigation;sections=$sections;errors=$errors;truncated=$truncated}|ConvertTo-Json -Depth 8 -Compress
'''


def capture(navigate=False, restore=False, reveal=False):
    available, code = desktop_status()
    if not available:
        return {'phase': 'desktop_unavailable', 'win32': code}
    script = SCRIPT.replace('__NAVIGATE__', '$true' if navigate else '$false')
    script = script.replace('__RESTORE__', '$true' if restore else '$false')
    script = script.replace('__REVEAL__', '$true' if reveal else '$false')
    try:
        result = subprocess.run(['powershell.exe', '-NoProfile', '-NonInteractive', '-EncodedCommand',
                                 base64.b64encode(script.encode('utf-16-le')).decode('ascii')],
                                capture_output=True, timeout=20, creationflags=subprocess.CREATE_NO_WINDOW)
        if result.returncode:
            return {'phase': 'probe_error', 'exit_code': result.returncode}
        available, code = desktop_status()
        if not available:
            return {'phase': 'desktop_changed', 'win32': code}
        return {'phase': 'captured', **json.loads(result.stdout.decode('utf-8-sig'))}
    except subprocess.TimeoutExpired:
        return {'phase': 'timeout'}
    except (OSError, ValueError, UnicodeError) as exc:
        return {'phase': 'probe_error', 'type': type(exc).__name__}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--samples', type=int, choices=range(1, 6), default=3)
    parser.add_argument('--navigate', action='store_true')
    parser.add_argument('--restore', action='store_true', help='Restore the existing window, never start/restart the client')
    parser.add_argument('--reveal', action='store_true', help='Scroll the daily card into view without invoking it')
    args = parser.parse_args()
    output = args.out.resolve()
    if output.drive.upper() != 'D:':
        parser.error('Output must stay on D drive')
    rows = []
    for index in range(args.samples):
        rows.append({'time': datetime.now().astimezone().isoformat(), **capture(args.navigate and index == 0, args.restore and index == 0, args.reveal and index == 0)})
        if index + 1 < args.samples:
            time.sleep(2)  # Bounded resnapshot; never reuses stale AutomationElements.
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps({'samples': rows, 'verdict': 'unknown',
                                  'claim_clicked': False, 'note': 'Labels are not verified account/day/receipt evidence.'},
                                 ensure_ascii=False, indent=2), 'utf-8')
    print(json.dumps({'output': str(output), 'phases': [r['phase'] for r in rows],
                      'contexts': [len(r.get('signin_contexts', [])) for r in rows], 'claim_clicked': False}, ensure_ascii=False))


if __name__ == '__main__':
    main()
