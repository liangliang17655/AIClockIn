$ErrorActionPreference='Stop'
[Console]::OutputEncoding=New-Object System.Text.UTF8Encoding($false)
trap {
 @{activity_ready=$false;reason='uia_exception';error_type=$_.Exception.GetType().FullName;hresult=$_.Exception.HResult}|ConvertTo-Json -Compress
 exit 0
}
Add-Type -AssemblyName UIAutomationClient
Add-Type -AssemblyName UIAutomationTypes
$walker=[System.Windows.Automation.TreeWalker]::RawViewWalker
function Nodes {
 $session=(Get-Process -Id $PID).SessionId
 $ids=@((Get-Process DoubaoWork -ErrorAction SilentlyContinue | Where-Object SessionId -eq $session).Id)
 $roots=[System.Windows.Automation.AutomationElement]::RootElement.FindAll([System.Windows.Automation.TreeScope]::Children,[System.Windows.Automation.Condition]::TrueCondition)
 $queue=New-Object System.Collections.Queue
 foreach($root in $roots){if($ids -contains $root.Current.ProcessId){$queue.Enqueue($root)}}
 $count=0
 while($queue.Count -gt 0 -and $count -lt 8000){
  $e=$queue.Dequeue();$count++
  try {
   Write-Output $e
   $child=$walker.GetFirstChild($e)
   while($null -ne $child){$queue.Enqueue($child);$child=$walker.GetNextSibling($child)}
  }catch{}
 }
}
function Close-KnownDialog($dialog) {
 if($null -eq $dialog -or ($dialog.Current.LocalizedControlType -ne '对话框' -and $dialog.Current.Name -ne '奖励发放明细')){return $false}
 $dialogId=($dialog.GetRuntimeId() -join ',');$dialogPid=$dialog.Current.ProcessId
 $closeButtons=@($dialog.FindAll([System.Windows.Automation.TreeScope]::Descendants,[System.Windows.Automation.Condition]::TrueCondition)|Where-Object {
  $_.Current.ControlType -eq [System.Windows.Automation.ControlType]::Button -and $_.Current.IsEnabled -and -not $_.Current.IsOffscreen -and
  ($_.Current.Name -in @('关闭','Close') -or $_.Current.ClassName -match '(^|\s)closeIcon-[A-Za-z0-9_-]+(\s|$)')
 })
 if($closeButtons.Count -eq 1){
  $invoke=$null
  if($closeButtons[0].TryGetCurrentPattern([System.Windows.Automation.InvokePattern]::Pattern,[ref]$invoke)){$invoke.Invoke();Start-Sleep -Milliseconds 200}
  $remaining=@(@(Nodes)|Where-Object {($_.GetRuntimeId() -join ',') -eq $dialogId -and -not $_.Current.IsOffscreen})
  if($remaining.Count -eq 0){return $true}
 }
 $wp=$null
 if($dialog.TryGetCurrentPattern([System.Windows.Automation.WindowPattern]::Pattern,[ref]$wp)){
  try{$wp.Close()}catch{
   $script:identityCloseHresult=if($null -ne $_.Exception.InnerException){$_.Exception.InnerException.HResult}else{$_.Exception.HResult}
  }
 }
 $remaining=@(@(Nodes)|Where-Object {($_.GetRuntimeId() -join ',') -eq $dialogId -and -not $_.Current.IsOffscreen})
 if($remaining.Count -eq 1){
  # Normal dialog Escape only after positive focus; never invoke the main window's Close.
  $dialog.SetFocus();$focus=[System.Windows.Automation.AutomationElement]::FocusedElement
  if($null -ne $focus -and $focus.Current.ProcessId -eq $dialogPid){
   Add-Type -AssemblyName System.Windows.Forms
   [System.Windows.Forms.SendKeys]::SendWait('{ESC}')
   Start-Sleep -Milliseconds 350
  }
 }
 $remaining=@(@(Nodes)|Where-Object {($_.GetRuntimeId() -join ',') -eq $dialogId -and -not $_.Current.IsOffscreen})
 return ($remaining.Count -eq 0)
}
function Restore-ClientWindows {
 foreach($e in @(Nodes)){
  if($e.Current.ControlType -ne [System.Windows.Automation.ControlType]::Window -or $e.Current.NativeWindowHandle -eq 0){continue}
  $wp=$null
  if($e.TryGetCurrentPattern([System.Windows.Automation.WindowPattern]::Pattern,[ref]$wp) -and $wp.Current.WindowVisualState -eq [System.Windows.Automation.WindowVisualState]::Minimized){$wp.SetWindowVisualState([System.Windows.Automation.WindowVisualState]::Normal)}
 }
}
function Read-VisibleIdentity {
 # Restrict identity extraction to the official settings dialog, not chat text.
 $nodes=@(Nodes)
 $settings=@($nodes|Where-Object {$_.Current.ControlType -eq [System.Windows.Automation.ControlType]::Button -and $_.Current.Name -eq '设置' -and $_.Current.IsEnabled -and -not $_.Current.IsOffscreen})
 if($settings.Count -ne 1){return $null}
 $invoke=$null
 if(-not $settings[0].TryGetCurrentPattern([System.Windows.Automation.InvokePattern]::Pattern,[ref]$invoke)){return $null}
 $invoke.Invoke()
 $end=[DateTime]::UtcNow.AddSeconds(8)
 $values=@();$dialog=$null
 do {
  $values=@()
  foreach($e in @(Nodes)){
   $c=$e.Current
   if($c.ControlType -ne [System.Windows.Automation.ControlType]::Button -or $c.IsOffscreen){continue}
   $m=[regex]::Match($c.Name,'豆包号[：:]\s*([A-Za-z0-9_-]+)')
   if(-not $m.Success){continue}
   $parent=$walker.GetParent($e)
   for($i=0;$i -lt 5 -and $null -ne $parent;$i++){
    if($parent.Current.ControlType -eq [System.Windows.Automation.ControlType]::Window -and $parent.Current.LocalizedControlType -eq '对话框'){
     $dialog=$parent;$values+=$m.Groups[1].Value;break
    }
    $parent=$walker.GetParent($parent)
   }
  }
  if($values.Count -gt 0){break}
  Start-Sleep -Milliseconds 350
 }while([DateTime]::UtcNow -lt $end)
 $hash=$null;$values=@($values|Select-Object -Unique)
 if($values.Count -eq 1){
  $sha=[Security.Cryptography.SHA256]::Create()
  $hash=([BitConverter]::ToString($sha.ComputeHash([Text.Encoding]::UTF8.GetBytes($values[0])))).Replace('-','').ToLowerInvariant()
  $sha.Dispose()
 }
 $script:identitySettingsClosed=Close-KnownDialog $dialog
 if(-not $script:identitySettingsClosed){return $null}
 return $hash
}
function Read-RewardLedger([bool]$keepOpen=$false) {
 $result=@{header_verified=$false;dialog_closed=$false;rows=@();source='official_reward_ledger';reason='activity_missing'}
 $windows=@(@(Nodes)|Where-Object {$_.Current.ControlType -eq [System.Windows.Automation.ControlType]::Window -and $_.Current.Name -eq '奖励发放明细' -and -not $_.Current.IsOffscreen})
 if($windows.Count -eq 0){
  $docs=@(@(Nodes)|Where-Object {$_.Current.ControlType -eq [System.Windows.Automation.ControlType]::Document -and $_.Current.Name -eq '免费用豆包工作' -and -not $_.Current.IsOffscreen})
  if($docs.Count -ne 1){return $result}
  $result.reason='prize_button_missing'
  $buttons=@($docs[0].FindAll([System.Windows.Automation.TreeScope]::Descendants,[System.Windows.Automation.Condition]::TrueCondition)|Where-Object {$_.Current.ControlType -eq [System.Windows.Automation.ControlType]::Button -and $_.Current.Name -eq '我的奖品' -and $_.Current.IsEnabled})
  if($buttons.Count -ne 1){return $result}
  $scroll=$null
  if($buttons[0].TryGetCurrentPattern([System.Windows.Automation.ScrollItemPattern]::Pattern,[ref]$scroll)){$scroll.ScrollIntoView()}
  $end=[DateTime]::UtcNow.AddSeconds(2)
  do {Start-Sleep -Milliseconds 150}while($buttons[0].Current.IsOffscreen -and [DateTime]::UtcNow -lt $end)
  $invoke=$null
  $result.reason='prize_button_not_actionable'
  if($buttons[0].Current.IsOffscreen -or -not $buttons[0].TryGetCurrentPattern([System.Windows.Automation.InvokePattern]::Pattern,[ref]$invoke)){return $result}
  $invoke.Invoke()
  $result.reason='ledger_unavailable'
  $end=[DateTime]::UtcNow.AddSeconds(8)
  do {
   Start-Sleep -Milliseconds 350
   $windows=@(@(Nodes)|Where-Object {$_.Current.ControlType -eq [System.Windows.Automation.ControlType]::Window -and $_.Current.Name -eq '奖励发放明细' -and -not $_.Current.IsOffscreen})
  }while($windows.Count -eq 0 -and [DateTime]::UtcNow -lt $end)
 }
 if($windows.Count -ne 1){return $result}
 try {
  $result.reason='table_missing';$end=[DateTime]::UtcNow.AddSeconds(5);$rows=@()
  do {
   $tables=@($windows[0].FindAll([System.Windows.Automation.TreeScope]::Descendants,[System.Windows.Automation.Condition]::TrueCondition)|Where-Object {$_.Current.ControlType -eq [System.Windows.Automation.ControlType]::Table})
   if($tables.Count -eq 1){$rows=@($tables[0].FindAll([System.Windows.Automation.TreeScope]::Children,[System.Windows.Automation.Condition]::TrueCondition))}
   if($rows.Count -gt 1){break};Start-Sleep -Milliseconds 200
  }while([DateTime]::UtcNow -lt $end)
  if($tables.Count -ne 1){return $result}
  $result.reason='rows_unavailable'
  if($rows.Count -eq 0 -or $rows.Count -gt 200){return $result}
  $header=@($rows[0].FindAll([System.Windows.Automation.TreeScope]::Children,[System.Windows.Automation.Condition]::TrueCondition)|ForEach-Object {$_.Current.Name})
  $result.reason='header_mismatch'
  if(($header -join '|') -ne '时间|日常任务|获得奖励'){return $result}
  $result.header_verified=$true
  $result.reason='read'
  foreach($row in @($rows|Select-Object -Skip 1)){
   $cells=@($row.FindAll([System.Windows.Automation.TreeScope]::Children,[System.Windows.Automation.Condition]::TrueCondition))
   if($cells.Count -ne 3 -or $cells[1].Current.Name -ne '每日签到'){continue}
   $stamp=$cells[0].Current.Name;$reward=[regex]::Match($cells[2].Current.Name,'^\+(\d+)\s*额度$')
   if($stamp -match '^\d{4}-\d{2}-\d{2} \d{2}:\d{2}$' -and $reward.Success){
    $result.rows+=@{time=$stamp;task='每日签到';earned=[int64]$reward.Groups[1].Value}
   }
  }
 }finally{if(-not $keepOpen){$result.dialog_closed=Close-KnownDialog $windows[0]}}
 return $result
}
$steps=@();$fingerprint=$null;$opened=$false;$reason='activity_unavailable'
$deadline=[DateTime]::UtcNow.AddSeconds(65)
while([DateTime]::UtcNow -lt $deadline){
 $nodes=@(Nodes)
 # Restore the existing client, never create a second process here.
 foreach($e in $nodes){
  $wp=$null
  if($e.TryGetCurrentPattern([System.Windows.Automation.WindowPattern]::Pattern,[ref]$wp)){
   if($wp.Current.WindowVisualState -eq [System.Windows.Automation.WindowVisualState]::Minimized){$wp.SetWindowVisualState([System.Windows.Automation.WindowVisualState]::Normal);$steps+='restore'}
  }
 }
 # Reuse the already verified SelectionItem route when the official tab exists.
 if(-not $opened){
  $activeDocs=@($nodes|Where-Object {$_.Current.ControlType -eq [System.Windows.Automation.ControlType]::Document -and $_.Current.Name -eq '免费用豆包工作' -and -not $_.Current.IsOffscreen})
  if($activeDocs.Count -eq 1){$opened=$true;$steps+='visible_activity_document'}
 }
 if(-not $opened){
  $tabs=@($nodes|Where-Object {$_.Current.ControlType -eq [System.Windows.Automation.ControlType]::TabItem -and $_.Current.Name -eq '免费用豆包工作' -and -not $_.Current.IsOffscreen -and $_.Current.IsEnabled})
  $selectedTabs=@($tabs|Where-Object {$sp=$null;$_.TryGetCurrentPattern([System.Windows.Automation.SelectionItemPattern]::Pattern,[ref]$sp) -and $sp.Current.IsSelected})
  if($selectedTabs.Count -eq 1){$tabs=$selectedTabs}
  if($tabs.Count -gt 1){@{activity_ready=$false;reason='activity_tab_ambiguous';steps=$steps}|ConvertTo-Json -Compress;exit 0}
  if($tabs.Count -eq 1){
   $selection=$null
   if($tabs[0].TryGetCurrentPattern([System.Windows.Automation.SelectionItemPattern]::Pattern,[ref]$selection)){$selection.Select();$opened=$true;$steps+='existing_activity_tab';$nodes=@(Nodes)}
  }
 }
 if(-not $opened){
  $menus=@()
  foreach($e in $nodes){
   $c=$e.Current;$p=$null
   if($c.ControlType -eq [System.Windows.Automation.ControlType]::Button -and $c.AutomationId -like 'radix*' -and $c.IsEnabled -and -not $c.IsOffscreen -and $e.TryGetCurrentPattern([System.Windows.Automation.ExpandCollapsePattern]::Pattern,[ref]$p)){
    # Account trigger has two images around its label group. Task dropdowns do not.
    $types=@();$child=$walker.GetFirstChild($e)
    while($null -ne $child){$types+=$child.Current.ControlType.ProgrammaticName;$child=$walker.GetNextSibling($child)}
    if(($types -join ',') -eq 'ControlType.Image,ControlType.Group,ControlType.Image'){$menus+=,$e}
   }
  }
  if($menus.Count -eq 1){
   $p=$menus[0].GetCurrentPattern([System.Windows.Automation.ExpandCollapsePattern]::Pattern)
   if($p.Current.ExpandCollapseState -eq [System.Windows.Automation.ExpandCollapseState]::Collapsed){$p.Expand()}
   if($steps -notcontains 'account_menu'){$steps+='account_menu'}
   Start-Sleep -Milliseconds 400
   $nodes=@(Nodes);$ids=@()
   foreach($e in $nodes){
    if($e.Current.ControlType -eq [System.Windows.Automation.ControlType]::Button){
     $m=[regex]::Match($e.Current.Name,'豆包号[：:]\s*([A-Za-z0-9_-]+)')
     if($m.Success){$ids+=$m.Groups[1].Value}
    }
   }
   $ids=@($ids|Select-Object -Unique)
   if($ids.Count -eq 1){
    $sha=[Security.Cryptography.SHA256]::Create()
    $menuFingerprint=([BitConverter]::ToString($sha.ComputeHash([Text.Encoding]::UTF8.GetBytes($ids[0])))).Replace('-','').ToLowerInvariant()
    $sha.Dispose()
    if($null -ne $fingerprint -and $menuFingerprint -ne $fingerprint){
     @{activity_ready=$false;reason='account_identity_conflict';steps=$steps}|ConvertTo-Json -Compress;exit 0
    }
    $fingerprint=$menuFingerprint
   }
   $items=@($nodes|Where-Object {$_.Current.ControlType -eq [System.Windows.Automation.ControlType]::MenuItem -and $_.Current.Name -eq '免费用豆包工作' -and $_.Current.IsEnabled -and -not $_.Current.IsOffscreen})
   if($items.Count -eq 1){
    $invoke=$null
    if($items[0].TryGetCurrentPattern([System.Windows.Automation.InvokePattern]::Pattern,[ref]$invoke)){$invoke.Invoke();$opened=$true;$steps+='activity_menu'}
   }else{$reason='activity_menu_missing'}
  }
 }
 $docs=@($nodes|Where-Object {$_.Current.ControlType -eq [System.Windows.Automation.ControlType]::Document -and $_.Current.Name -eq '免费用豆包工作' -and -not $_.Current.IsOffscreen})
 if($opened -and $docs.Count -eq 1){
  $all=@($docs[0].FindAll([System.Windows.Automation.TreeScope]::Descendants,[System.Windows.Automation.Condition]::TrueCondition))
  $buttons=@($all|Where-Object {$_.Current.ControlType -eq [System.Windows.Automation.ControlType]::Button -and $_.Current.Name -eq '立即签到' -and $_.Current.IsEnabled -and -not $_.Current.IsOffscreen})
  $labels=@($all|Where-Object {$_.Current.Name -in @('每日签到','立即签到','今日已签到','今日未签到','已签到','未签到','签到成功')}|ForEach-Object {$_.Current.Name}|Select-Object -Unique)
  $dates=@();$tp=$null
  if($docs[0].TryGetCurrentPattern([System.Windows.Automation.TextPattern]::Pattern,[ref]$tp)){
   $text=$tp.DocumentRange.GetText(20000)
   $dates=@([regex]::Matches($text,'20\d{2}[-年/]\d{1,2}[-月/]\d{1,2}|\d{1,2}月\d{1,2}日')|ForEach-Object Value|Select-Object -Unique)
  }
  @{running=$true;activity_ready=$true;account_fingerprint=$fingerprint;claim_button_count=$buttons.Count;steps=$steps;state_evidence=@{labels=$labels;date_tokens=$dates;date_semantics_verified=$false}}|ConvertTo-Json -Depth 4 -Compress
  exit 0
 }
 Start-Sleep -Milliseconds 800
}
@{activity_ready=$false;account_fingerprint=$fingerprint;reason=$reason;steps=$steps}|ConvertTo-Json -Compress
