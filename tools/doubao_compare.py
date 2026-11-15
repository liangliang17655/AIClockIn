"""Capture real campaign trees before/after a USER claim; never invokes a claim."""
import argparse
import base64
from datetime import datetime, timedelta, timezone
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from tools.probe_doubao_signin import SCRIPT
from aiclockin.doubaowork import desktop_status
from aiclockin.runtime import prepare

DETAIL = r'''
    $tree=@();$pageText=$null;$treeTruncated=$false;$shot=@{saved=$false;reason='not_requested'}
    if($name -in @('免费用豆包工作','免费用豆包')){
     if(__SCREENSHOT__){
      $find=New-Object System.Collections.Queue;$find.Enqueue($element);$fn=0
      while($find.Count -and $fn -lt 2000){
       $b=$find.Dequeue();$fn++
       if($b.Current.ControlType -eq [System.Windows.Automation.ControlType]::Group -and $b.Current.Name -like '从容开工*'){
        try{
         ($b.GetCurrentPattern([System.Windows.Automation.ScrollItemPattern]::Pattern)).ScrollIntoView()
         $rect=$b.Current.BoundingRectangle
         $shot=Save-Banner $root.Current.NativeWindowHandle $rect $element.Current.BoundingRectangle
        }catch{$shot=@{saved=$false;reason='banner_capture_failed';hresult=$_.Exception.HResult;type=$_.Exception.GetType().FullName;message=$_.Exception.Message}}
        break
       }
       $child=$walk.GetFirstChild($b);while($child){$find.Enqueue($child);$child=$walk.GetNextSibling($child)}
      }
     }
     $tp=$null;if($element.TryGetCurrentPattern([System.Windows.Automation.TextPattern]::Pattern,[ref]$tp)){$pageText=Protect ($tp.DocumentRange.GetText(20000))}
     $tq=New-Object System.Collections.Queue;$tq.Enqueue(@{element=$element;path='0'})
     while($tq.Count -and $tree.Count -lt 2000){
      $item=$tq.Dequeue();$node=$item.element;$v=$node.Current;$r=$v.BoundingRectangle
      $tree+=@{path=$item.path;name=(Protect $v.Name);automation_id=(Protect $v.AutomationId);type=$v.ControlType.ProgrammaticName;
       enabled=$v.IsEnabled;offscreen=$v.IsOffscreen;focusable=$v.IsKeyboardFocusable;help=(Protect $v.HelpText);status=(Protect $v.ItemStatus);
       patterns=@($node.GetSupportedPatterns()|ForEach-Object {$_.ProgrammaticName});bounds=@($r.X,$r.Y,$r.Width,$r.Height)}
      $child=$walk.GetFirstChild($node);$ci=0;while($child){$tq.Enqueue(@{element=$child;path=($item.path+'/'+$ci)});$ci++;$child=$walk.GetNextSibling($child)}
     }
     $treeTruncated=($tq.Count -gt 0)
    }
    $documents+=@{name=$name;chars=$length;labels=$labels;text=$pageText;tree=$tree;tree_truncated=$treeTruncated;screenshot=$shot}
'''

PREFIX = r'''
function Protect([string]$text){
 $text=[regex]::Replace($text,'https?://\S+','[URL]')
 $text=[regex]::Replace($text,'(?<!\d)1[3-9]\d{9}(?!\d)','[PHONE]')
 $text=[regex]::Replace($text,'(?i)(邀请码|inviteCode|token|cookie)\s*[:=：]\s*[^\s]+','$1=[REDACTED]')
 $text=[regex]::Replace($text,'\beyJ[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\b','[JWT]')
 return $text
}
if(__SCREENSHOT__){
 Add-Type -AssemblyName System.Drawing
 Add-Type @'
using System;using System.Runtime.InteropServices;
public class PairCapture {
 [StructLayout(LayoutKind.Sequential)] public struct RECT {public int L,T,R,B;}
 [StructLayout(LayoutKind.Sequential)] public struct POINT {public int X,Y; public POINT(int x,int y){X=x;Y=y;}}
 [DllImport("user32.dll")] public static extern bool SetProcessDPIAware();
 [DllImport("user32.dll")] public static extern bool GetWindowRect(IntPtr h,out RECT r);
 [DllImport("user32.dll")] public static extern IntPtr GetForegroundWindow();
 [DllImport("user32.dll")] public static extern IntPtr GetAncestor(IntPtr h,uint flags);
 [DllImport("user32.dll")] public static extern IntPtr WindowFromPoint(POINT p);
}
'@
 [PairCapture]::SetProcessDPIAware()|Out-Null
}
function Save-Banner($handle,$rect,$documentRect){
 $wr=New-Object PairCapture+RECT
 if(-not [PairCapture]::GetWindowRect([IntPtr]$handle,[ref]$wr)){throw 'No target bounds'}
 $left=[Math]::Max($wr.L,[Math]::Max($rect.X,$documentRect.X))
 $top=[Math]::Max($wr.T,[Math]::Max($rect.Y,$documentRect.Y))
 $right=[Math]::Min($wr.R,[Math]::Min($rect.Right,$documentRect.Right))
 $bottom=[Math]::Min($wr.B,[Math]::Min($rect.Bottom,$documentRect.Bottom))
 $x=[int]($left-$wr.L);$y=[int]($top-$wr.T);$width=[int]($right-$left);$height=[int]($bottom-$top)
 if($width -le 0 -or $height -le 0){return @{saved=$false;reason='banner_outside_window'}}
 # GPU PrintWindow can look nonblank yet omit text; use only actual unobscured pixels.
 if([PairCapture]::GetAncestor([PairCapture]::GetForegroundWindow(),2) -ne [IntPtr]$handle){return @{saved=$false;reason='client_not_foreground'}}
 foreach($point in @(@(([int]$left+4),([int]$top+4)),@(([int]$right-4),([int]$top+4)),@(([int]$left+4),([int]$bottom-4)),@(([int]$right-4),([int]$bottom-4)))){
  $pt=[PairCapture+POINT]::new([int]$point[0],[int]$point[1])
  if([PairCapture]::GetAncestor([PairCapture]::WindowFromPoint($pt),2) -ne [IntPtr]$handle){return @{saved=$false;reason='banner_occluded'}}
 }
 $crop=New-Object Drawing.Bitmap($width,$height)
 $graphics=[Drawing.Graphics]::FromImage($crop)
 try{
  $graphics.CopyFromScreen([int]$left,[int]$top,0,0,(New-Object Drawing.Size($width,$height)))
  $colors=New-Object 'System.Collections.Generic.HashSet[int]'
  for($ix=1;$ix -lt 20;$ix++){for($iy=1;$iy -lt 20;$iy++){[void]$colors.Add($crop.GetPixel([int](($width-1)*$ix/20),[int](($height-1)*$iy/20)).ToArgb())}}
  if($colors.Count -lt 3){return @{saved=$false;reason='flat_image_not_accepted'}}
  $crop.Save($shotPath,[Drawing.Imaging.ImageFormat]::Png)
 }finally{$graphics.Dispose();$crop.Dispose()}
 return @{saved=$true;scope='visible_UIA_region_intersect_campaign_document';method='foreground_campaign_crop';path=$shotPath;visual_verified=$false}
}
'''


def capture(output, label, screenshot=False, focus_signin=False, passive=False):
    prepare()  # Includes D-drive TEMP for optional Add-Type compilation.
    output = output.resolve()
    if output.drive.upper() != 'D:':
        raise ValueError('Output must be on D drive')
    if output.exists():
        raise ValueError('Refusing to overwrite an existing observation')
    if screenshot and output.with_suffix('.png').exists():
        raise ValueError('Refusing to overwrite an existing screenshot')
    output.parent.mkdir(parents=True, exist_ok=True)
    now = datetime.now(timezone(timedelta(hours=8)))
    data = {'captured_at': now.isoformat(), 'beijing_day': now.date().isoformat(), 'label': label,
            'identity_verified': False, 'sign_state': 'unknown', 'claim_clicked': False, 'capture_ok': False}
    available, code = desktop_status()
    if not available:
        data.update(error='desktop_unavailable', win32=code)
    else:
        flag = '$true' if screenshot else '$false'
        shot_path = base64.b64encode(str(output.with_suffix('.png')).encode('utf-8')).decode('ascii')
        script = "$ErrorActionPreference='Stop';[Console]::OutputEncoding=[Text.UTF8Encoding]::new($false);"
        script += "$shotPath=[Text.Encoding]::UTF8.GetString([Convert]::FromBase64String('" + shot_path + "'));"
        detail = DETAIL
        if focus_signin:
            detail = detail.replace("$b.Current.ControlType -eq [System.Windows.Automation.ControlType]::Group -and $b.Current.Name -like '从容开工*'",
                                    "$b.Current.ControlType -eq [System.Windows.Automation.ControlType]::Button -and $b.Current.Name -eq '立即签到'")
        script += PREFIX + SCRIPT.replace('$documents+=@{name=$name;chars=$length;labels=$labels}', detail)
        action_flag = '$false' if passive else '$true'
        script = script.replace('__SCREENSHOT__', flag).replace('__RESTORE__', action_flag).replace('__NAVIGATE__', action_flag).replace('__REVEAL__', '$false')
        script_path = None
        try:
            executable = Path(os.environ.get('SystemRoot', 'C:/Windows')) / 'System32/WindowsPowerShell/v1.0/powershell.exe'
            with tempfile.NamedTemporaryFile('w', encoding='utf-8-sig', suffix='.ps1', delete=False) as temporary:
                temporary.write(script)
                script_path = Path(temporary.name)
            result = subprocess.run([str(executable), '-NoProfile', '-NonInteractive', '-File', str(script_path)],
                                    capture_output=True, timeout=35, creationflags=subprocess.CREATE_NO_WINDOW)
            if result.returncode:
                data.update(error='probe_exit', exit_code=result.returncode)
            elif not desktop_status()[0]:
                data.update(error='desktop_changed')
            else:
                raw = json.loads(result.stdout.decode('utf-8-sig'))
                docs = [d for d in raw.get('documents', []) if d.get('name') in ('免费用豆包工作', '免费用豆包')]
                data.update(documents=docs, errors=raw.get('errors'), navigation=raw.get('navigation'))
                data['capture_ok'] = (len(docs) == 1 and bool(docs[0].get('tree'))
                                      and docs[0].get('text') is not None
                                      and not docs[0].get('tree_truncated') and not raw.get('errors'))
        except subprocess.TimeoutExpired:
            data.update(error='capture_timeout')
        except (OSError, ValueError, UnicodeError) as exc:
            data.update(error=type(exc).__name__, win32=getattr(exc, 'winerror', None))
        finally:
            if script_path:
                script_path.unlink(missing_ok=True)
    data['screenshot_requested'] = screenshot
    data['evidence_complete'] = bool(data['capture_ok'] and (
        not screenshot or all(d.get('screenshot', {}).get('saved') for d in data.get('documents', []))))
    with output.open('x', encoding='utf-8') as stream:
        json.dump(data, stream, ensure_ascii=False, indent=2)
    return data


def compare(before, after):
    usable = (before.get('capture_ok') and after.get('capture_ok')
              and before.get('evidence_complete', True) and after.get('evidence_complete', True))
    same_day = bool(before.get('beijing_day')) and before.get('beijing_day') == after.get('beijing_day')
    try:
        a_time = datetime.fromisoformat(before['captured_at'])
        b_time = datetime.fromisoformat(after['captured_at'])
        ordered = a_time.tzinfo is not None and b_time.tzinfo is not None and a_time <= b_time
    except (KeyError, TypeError, ValueError):
        ordered = False
    report = {'usable_pair': bool(usable and same_day and ordered), 'same_capture_day': same_day,
              'chronological_order': ordered,
              'identity_verified': False, 'sign_state': 'unknown', 'receipt_verified': False,
              'changes': [], 'note': 'Capture labels and computer date do not prove business state or identity.'}
    if not report['usable_pair']:
        report['error'] = 'Missing valid same-day captures'
        return report
    left, right = before['documents'][0], after['documents'][0]
    report['text_before'] = left.get('text'); report['text_after'] = right.get('text')
    for field in ('name', 'enabled', 'offscreen', 'bounds', 'patterns', 'status', 'help', 'type', 'focusable', 'automation_id'):
        a = {n['path']: n.get(field) for n in left['tree']}
        b = {n['path']: n.get(field) for n in right['tree']}
        for path in sorted(a.keys() | b.keys()):
            if a.get(path) != b.get(path):
                report['changes'].append({'path': path, 'field': field, 'before': a.get(path), 'after': b.get(path)})
    # Candidate requires both a semantic Button and invocation support. Never Group/Text.
    for label, doc in (('before', left), ('after', right)):
        report[label + '_button_candidates'] = [n for n in doc['tree'] if n.get('type') == 'ControlType.Button'
            and 'InvokePatternIdentifiers.Pattern' in n.get('patterns', []) and n.get('name') in ('立即签到', '签到')]
    import re
    values = []
    for doc in (left, right):
        match = re.search(r'累计获得额度：\s*(\d+)\s*点', doc.get('text') or '')
        values.append(int(match[1]) if match else None)
    report['cumulative_before'], report['cumulative_after'] = values
    report['cumulative_delta'] = values[1] - values[0] if None not in values else None
    report['earned'] = None  # A cumulative difference is not a receipt.
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    modes = parser.add_subparsers(dest='mode', required=True)
    cap = modes.add_parser('capture'); cap.add_argument('--out', type=Path, required=True)
    cap.add_argument('--label', required=True); cap.add_argument('--screenshot', action='store_true')
    cap.add_argument('--focus-signin', action='store_true', help='Scroll the uniquely named sign-in control for a button-only screenshot; never Invoke')
    cap.add_argument('--passive', action='store_true', help='Do not restore/select/scroll while user interacts')
    diff = modes.add_parser('compare'); diff.add_argument('before', type=Path); diff.add_argument('after', type=Path)
    diff.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    if args.mode == 'capture':
        if args.passive and args.screenshot:
            parser.error('Passive observations cannot scroll for screenshots')
        data = capture(args.out, args.label, args.screenshot, args.focus_signin, args.passive)
        if sys.stdout is not None:
            print(json.dumps({'capture_ok': data['capture_ok'], 'evidence_complete': data['evidence_complete'], 'label': args.label, 'out': str(args.out)}, ensure_ascii=False))
        return 0 if data['evidence_complete'] else 1
    if args.out.resolve().drive.upper() != 'D:' or args.out.exists():
        parser.error('Use a new D-drive output file')
    result = compare(json.loads(args.before.read_text('utf-8')), json.loads(args.after.read_text('utf-8')))
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, ensure_ascii=False, indent=2), 'utf-8')
    if sys.stdout is not None:
        print(json.dumps({'usable_pair': result['usable_pair'], 'changes': len(result['changes']), 'sign_state': 'unknown'}))
    return 0 if result['usable_pair'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
