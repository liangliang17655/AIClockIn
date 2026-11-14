#ifndef AppVersion
  #error AppVersion is required
#endif
#ifndef BundleDir
  #error BundleDir is required
#endif
#ifndef ReleaseDir
  #error ReleaseDir is required
#endif
#ifndef RuntimeDir
  #define RuntimeDir "_runtime-v" + AppVersion
#endif
#ifndef AppId
  #define AppId "AIClockIn-49F2C4C8-EE14-4FC3-83D1-E2826227F14D"
#endif
#ifndef HealthTimeoutMs
  #define HealthTimeoutMs 90000
#endif
#ifndef ShortcutName
  #define ShortcutName "AIClockIn 自动签到"
#endif

[Setup]
AppId={#AppId}
AppName=AIClockIn
AppVersion={#AppVersion}
AppPublisher=AIClockIn
AppPublisherURL=https://github.com/liangliang17655/AIClockIn
DefaultDirName={code:DefaultDirectory}
DefaultGroupName=AIClockIn
DisableProgramGroupPage=no
DisableDirPage=no
AllowNoIcons=yes
PrivilegesRequired=lowest
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
SetupArchitecture=x64
WizardStyle=modern
OutputDir={#ReleaseDir}
OutputBaseFilename=AIClockIn-v{#AppVersion}-Setup-windows-x64
SetupIconFile=..\assets\app.ico
UninstallDisplayIcon={app}\AIClockIn.exe
Uninstallable=yes
SetupLogging=yes
CloseApplications=no
RestartApplications=no
DisableWelcomePage=no
Compression=lzma2
SolidCompression=yes
LicenseFile=..\LICENSE

[Languages]
Name: "chinesesimplified"; MessagesFile: "compiler:Languages\ChineseSimplified.isl"
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "创建桌面快捷方式"; GroupDescription: "快捷方式："

[Files]
; Keep old versioned dependencies intact; the new executable is installed last.
Source: "{#BundleDir}\{#RuntimeDir}\*"; DestDir: "{app}\{#RuntimeDir}"; Flags: ignoreversion onlyifdoesntexist recursesubdirs createallsubdirs
Source: "{#BundleDir}\bundle-manifest.json"; DestDir: "{app}"; Flags: ignoreversion
Source: "{#BundleDir}\AIClockIn.exe"; DestDir: "{app}"; Flags: ignoreversion

[INI]
Filename: "{app}\install-info.ini"; Section: "Data"; Key: "Directory"; String: "{code:DataDirectory}"

[Icons]
Name: "{autodesktop}\{#ShortcutName}"; Filename: "{app}\AIClockIn.exe"; Parameters: "{code:ShortcutArguments}"; WorkingDir: "{app}"; Tasks: desktopicon
Name: "{group}\AIClockIn"; Filename: "{app}\AIClockIn.exe"; Parameters: "{code:ShortcutArguments}"; WorkingDir: "{app}"
Name: "{group}\卸载 AIClockIn"; Filename: "{uninstallexe}"

[Run]
Filename: "{app}\AIClockIn.exe"; Parameters: "{code:ShortcutArguments}"; Description: "启动 AIClockIn"; Flags: nowait postinstall skipifsilent; Check: CanLaunch

[Code]
type
  { Explicit Win64 STARTUPINFOW / PROCESS_INFORMATION layout; SetupArchitecture=x64. }
  THealthStartup = record
    cb, Pad: Cardinal;
    Reserved, Desktop, Title: Int64;
    X, Y, XSize, YSize, XChars, YChars, Fill, Flags: Cardinal;
    ShowWindow, ReservedSize: Word;
    Pad2: Cardinal;
    Reserved2, StdIn, StdOut, StdErr: Int64;
  end;
  THealthProcess = record
    ProcessHandle, ThreadHandle: Int64;
    ProcessId, ThreadId: Cardinal;
  end;
var
  ExistingDir, ExistingData: String;
  OldExe, OldManifest, OldInfo: String;
  HadExe, HadManifest, HadInfo, StartedFiles, InstallOK, HadRegistration: Boolean;
  InstallFailure, PreviousVersion: String;
  DiagnosticDir, DiagnosticLog, HealthReport: String;
  GateHandle: Int64;

function HealthCreateProcess(Application, CommandLine: String; ProcessAttributes, ThreadAttributes: Int64;
  InheritHandles: Boolean; Flags: Cardinal; Environment: Int64; Directory: String;
  var Startup: THealthStartup; var Process: THealthProcess): Boolean;
  external 'CreateProcessW@kernel32.dll stdcall';
function HealthExitCode(Process: Int64; var Code: Cardinal): Boolean;
  external 'GetExitCodeProcess@kernel32.dll stdcall';
function HealthTerminate(Process: Int64; Code: Cardinal): Boolean;
  external 'TerminateProcess@kernel32.dll stdcall';
procedure HealthZeroStartup(var Startup: THealthStartup; Count: Int64);
  external 'RtlZeroMemory@kernel32.dll stdcall';

function KernelDeleteFile(Target: String): Boolean;
  external 'DeleteFileW@kernel32.dll stdcall';
function KernelCopyFile(Source, Target: String; FailIfExists: Boolean): Boolean;
  external 'CopyFileW@kernel32.dll stdcall';
function KernelLastError: Cardinal;
  external 'GetLastError@kernel32.dll stdcall';

function CreateMutex(Attributes: Integer; InitialOwner: Boolean; Name: String): Int64;
  external 'CreateMutexW@kernel32.dll stdcall';
function WaitForSingleObject(Handle: Int64; Milliseconds: Cardinal): Cardinal;
  external 'WaitForSingleObject@kernel32.dll stdcall';
function ReleaseMutex(Handle: Int64): Boolean;
  external 'ReleaseMutex@kernel32.dll stdcall';
function CloseHandle(Handle: Int64): Boolean;
  external 'CloseHandle@kernel32.dll stdcall';

procedure ReleaseGate;
begin
  if GateHandle<>0 then begin ReleaseMutex(GateHandle);CloseHandle(GateHandle);GateHandle:=0;end;
end;

function AcquireGate: Boolean;
var Status: Cardinal;
begin
  ReleaseGate;
  GateHandle:=CreateMutex(0,False,'Local\AIClockIn-update-'+GetMD5OfUnicodeString(Lowercase(ExpandConstant('{app}\AIClockIn.exe'))));
  if GateHandle=0 then begin Result:=False;exit;end;
  Status:=WaitForSingleObject(GateHandle,0);
  Result:=(Status=0) or (Status=128);
  if not Result then begin CloseHandle(GateHandle);GateHandle:=0;end;
end;

function DataDirectory(Param: String): String;
begin
  if ExistingData <> '' then Result := ExistingData
  else Result := GetIniString('Data','Directory',AddBackslash(WizardDirValue)+'data',AddBackslash(WizardDirValue)+'install-info.ini');
  Result:=RemoveBackslashUnlessRoot(ExpandFileName(Result));
end;

function ShortcutArguments(Param: String): String;
var DataDir: String;
begin
  DataDir:=DataDirectory('');
  if (Pos(' ',DataDir)>0) or (Pos(#9,DataDir)>0) then DataDir:='"'+DataDir+'"';
  Result:='--data '+DataDir;
end;

function DefaultDirectory(Param: String): String;
begin
  if ExistingDir <> '' then Result := ExistingDir else Result := 'D:\AIClockIn';
end;

function AppMutexName(Param: String): String;
begin
  Result := 'Local\AIClockIn-run-' + GetMD5OfUnicodeString(Lowercase(ExpandConstant('{app}\AIClockIn.exe')));
end;

function InitializeSetup: Boolean;
var Service, Task, Actions, Action, Network, Locator, Wmi, Account: Variant; Args: String; P: Integer;
begin
  Result := True;
  if not DirExists('D:\') then begin
    SuppressibleMsgBox('D 盘不可用，安装已停止。', mbError, MB_OK, IDOK); Result := False; exit;
  end;
  ExistingDir := '';
  ExistingData := ExpandConstant('{param:DATA|}');
  if (ExistingData <> '') and (CompareText(Copy(ExpandFileName(ExistingData),1,3),'D:\') <> 0) then begin Result := False; exit; end;
  if ExistingData<>'' then exit;
  { Remember only this Windows user's data location across uninstall/reinstall. }
  if RegQueryStringValue(HKCU64,'Software\{#AppId}','DataDirectory',ExistingData) then begin
    if (CompareText(Copy(ExpandFileName(ExistingData),1,3),'D:\')=0) and
       (FileExists(AddBackslash(ExistingData)+'accounts.json') or FileExists(AddBackslash(ExistingData)+'history.db')) then exit;
    ExistingData:='';
  end;
  try
    Service := CreateOleObject('Schedule.Service'); Service.Connect;
    Task := Service.GetFolder('\').GetTask('AIClockIn-Auto');
    Network := CreateOleObject('WScript.Network');
    Locator := CreateOleObject('WbemScripting.SWbemLocator');
    Wmi := Locator.ConnectServer('', 'root\cimv2');
    Account := Wmi.Get('Win32_UserAccount.Domain="'+Network.UserDomain+'",Name="'+Network.UserName+'"');
    if CompareText(Task.Definition.Principal.UserId,Account.SID)<>0 then RaiseException('Task belongs to a different user');
    Actions := Task.Definition.Actions;
    if Actions.Count = 1 then begin
      Action := Actions.Item(1);
      if FileExists(Action.Path) and (CompareText(ExtractFileName(Action.Path),'AIClockIn.exe')=0) and
         (CompareText(Copy(ExpandFileName(Action.Path),1,3),'D:\')=0) then begin
        ExistingDir := ExtractFileDir(Action.Path);
        Args := Action.Arguments; P := Pos('--data ',Args);
        if (ExistingData='') and (P>0) then begin
          ExistingData := Trim(Copy(Args,P+7,Length(Args)));
          if Copy(ExistingData,1,1)='"' then ExistingData := Copy(ExistingData,2,Length(ExistingData)-2);
        end;
      end;
    end;
  except
    Log('No readable AIClockIn task; preserving any data in the chosen directory.');
  end;
  if (ExistingDir='') and FileExists(ExpandConstant('{src}\AIClockIn.exe')) and
     FileExists(ExpandConstant('{src}\data\accounts.json')) and
     (CompareText(Copy(ExpandConstant('{src}'),1,3),'D:\')=0) then ExistingDir := ExpandConstant('{src}');
end;

procedure InitializeWizard;
begin
  if ExistingDir<>'' then begin
    WizardForm.DirEdit.Text := ExistingDir;
    WizardForm.DirEdit.ReadOnly := True;
    WizardForm.DirBrowseButton.Enabled := False;
  end;
end;

function NextButtonClick(CurPageID: Integer): Boolean;
begin
  Result := True;
  if CurPageID=wpSelectDir then begin
    Result := (CompareText(Copy(ExpandFileName(WizardDirValue),1,3),'D:\')=0) and (Length(WizardDirValue)>3);
    if not Result then SuppressibleMsgBox('请选择 D 盘内的文件夹。账号和记录不会迁移。',mbError,MB_OK,IDOK);
  end;
end;

function PrepareToInstall(var NeedsRestart: Boolean): String;
var DataDir, RegisteredDir: String; Stream: TFileStream;
begin
  Result := '';
  if not AcquireGate then begin Result:='另一个安装或更新正在进行，请稍后重试。';exit;end;
  if CheckForMutexes(AppMutexName('')) then begin Result := '请先关闭所有 AIClockIn 窗口并等待后台任务结束，再安装。';ReleaseGate;exit;end;
  if (CompareText(Copy(ExpandFileName(WizardDirValue),1,3),'D:\')<>0) or (Length(WizardDirValue)<=3) then begin Result := '安装目录必须在 D 盘文件夹内。';ReleaseGate;exit;end;
  DataDir := DataDirectory('');
  if CompareText(Copy(ExpandFileName(DataDir),1,3),'D:\')<>0 then begin Result := '数据目录必须在 D 盘。';ReleaseGate;exit;end;
  if Pos(Lowercase(AddBackslash(ExpandFileName(DataDir))),Lowercase(AddBackslash(ExpandFileName(WizardDirValue))))=1 then begin
    Result:='数据目录必须与程序文件分开，不能是程序目录或它的上级目录。';ReleaseGate;exit;
  end;
  HadRegistration:=RegQueryStringValue(HKCU64,'Software\Microsoft\Windows\CurrentVersion\Uninstall\{#AppId}_is1','DisplayVersion',PreviousVersion);
  if RegQueryStringValue(HKCU64,'Software\Microsoft\Windows\CurrentVersion\Uninstall\{#AppId}_is1','InstallLocation',RegisteredDir) and
    (CompareText(RemoveBackslashUnlessRoot(RegisteredDir),RemoveBackslashUnlessRoot(WizardDirValue))<>0) then begin
      Result:='请使用原安装目录升级，账号和记录不会自动迁移。';ReleaseGate;exit;
  end;
  OldExe := ExpandConstant('{tmp}\previous.exe');OldManifest := ExpandConstant('{tmp}\previous-manifest.json');OldInfo := ExpandConstant('{tmp}\previous-info.ini');
  HadExe := FileExists(ExpandConstant('{app}\AIClockIn.exe'));
  HadManifest := FileExists(ExpandConstant('{app}\bundle-manifest.json'));
  HadInfo := FileExists(ExpandConstant('{app}\install-info.ini'));
  if HadExe then begin
    try Stream:=TFileStream.Create(ExpandConstant('{app}\AIClockIn.exe'),$0042);Stream.Free;
    except Result:='原程序正在使用或目录不可写，请关闭程序后重试。';ReleaseGate;exit;end;
  end;
  if HadExe and not FileCopy(ExpandConstant('{app}\AIClockIn.exe'),OldExe,False) then Result := '无法备份原程序，请关闭程序后重试。';
  if HadManifest and not FileCopy(ExpandConstant('{app}\bundle-manifest.json'),OldManifest,False) then Result := '无法备份程序清单。';
  if HadInfo and not FileCopy(ExpandConstant('{app}\install-info.ini'),OldInfo,False) then Result := '无法备份安装设置。';
  if Result<>'' then ReleaseGate;
end;

procedure Diagnostic(Message: String);
var Lines: TArrayOfString;
begin
  Log(Message);
  if DiagnosticLog<>'' then begin
    SetArrayLength(Lines,1);Lines[0]:=GetDateTimeString('yyyy-mm-dd hh:nn:ss','-',':')+' '+Message;
    if not SaveStringsToUTF8File(DiagnosticLog,Lines,True) then Log('Cannot persist diagnostic log.');
  end;
end;

function RunHealthCheck: Integer;
var Process: THealthProcess; Startup: THealthStartup;
    Elapsed, Status, ExitCode, ErrorCode: Cardinal; Health: AnsiString; Executable: String;
begin
  Executable:=ExpandConstant('{app}\AIClockIn.exe');
  HealthZeroStartup(Startup,104);Startup.cb:=104;
  Diagnostic('Launching offline self-check: '+Executable+'; report='+HealthReport+'; timeout={#HealthTimeoutMs}ms');
  if not HealthCreateProcess(Executable,'"'+Executable+'" --self-test --report "'+HealthReport+'"',
      0,0,False,$08000000,0,ExpandConstant('{app}'),Startup,Process) then begin
    ErrorCode:=KernelLastError;
    RaiseException('无法启动离线自检，Win32='+IntToStr(ErrorCode)+' '+SysErrorMessage(ErrorCode));
  end;
  try
    Diagnostic('Self-check PID='+IntToStr(Process.ProcessId));
    Elapsed:=0;
    repeat
      Status:=WaitForSingleObject(Process.ProcessHandle,100);
      if Status=0 then break;
      if Status<>258 then RaiseException('等待离线自检失败，Win32='+IntToStr(KernelLastError));
      Elapsed:=Elapsed+100;
    until Elapsed>={#HealthTimeoutMs};
    if Status<>0 then begin
      if not HealthTerminate(Process.ProcessHandle,1460) then Diagnostic('Cannot terminate self-check; Win32='+IntToStr(KernelLastError));
      if WaitForSingleObject(Process.ProcessHandle,3000)<>0 then
        RaiseException('离线自检超时，进程仍在退出，PID='+IntToStr(Process.ProcessId)+'；恢复结果请查看日志。');
      RaiseException('离线自检超时（{#HealthTimeoutMs} ms），已终止本次自检进程。');
    end;
    if not HealthExitCode(Process.ProcessHandle,ExitCode) then RaiseException('无法读取自检进程退出码，Win32='+IntToStr(KernelLastError));
    Result:=Integer(ExitCode);
    Diagnostic('Self-check exit code='+IntToStr(Result));
    if LoadStringFromFile(HealthReport,Health) then Diagnostic('Self-check report: '+Utf8Decode(Health))
    else Diagnostic('Self-check report is missing; inspect dependency/permission/Defender events.');
    if Result<>0 then RaiseException('离线自检失败，进程退出码='+IntToStr(Result)+'。详情见 '+HealthReport);
  finally
    { Close native process/thread handles before rollback replaces its executable. }
    CloseHandle(Process.ThreadHandle);CloseHandle(Process.ProcessHandle);
  end;
end;

procedure CurStepChanged(CurStep: TSetupStep);
var Code: Integer; Health: AnsiString; Reason: String;
begin
  if CurStep=ssInstall then StartedFiles := True;
  if CurStep=ssPostInstall then begin
    try
      DiagnosticDir:=ExpandConstant('{app}\diagnostics\install-')+GetDateTimeString('yyyymmdd-hhnnss','-',':')+'-'+Copy(GetMD5OfUnicodeString(ExpandConstant('{tmp}')),1,8);
      if not ForceDirectories(DiagnosticDir) then RaiseException('无法创建 D 盘诊断目录：'+DiagnosticDir);
      DiagnosticLog:=AddBackslash(DiagnosticDir)+'install.log';
      HealthReport:=AddBackslash(DiagnosticDir)+'health.json';
      Diagnostic('AIClockIn expected version={#AppVersion}; setup log='+ExpandConstant('{log}'));
      Code:=RunHealthCheck;
      if not LoadStringFromFile(HealthReport,Health) then RaiseException('自检进程已退出但报告不存在。');
      if (Pos('"ok": true',String(Health))=0) then RaiseException('自检报告未确认成功。');
      if (Pos('"version": "{#AppVersion}"',String(Health))=0) then RaiseException('自检版本不符，期望 {#AppVersion}。');
#ifdef ForceHealthFailure
      RaiseException('Isolated test: health failure');
#endif
      if not RegWriteStringValue(HKCU64,'Software\{#AppId}','DataDirectory',DataDirectory('')) then
        RaiseException('无法保存当前用户的数据目录，请检查 Windows 用户权限。');
      InstallOK := True;
      Diagnostic('Offline validation passed.');
    except
      Reason:=GetExceptionMessage;
      Diagnostic('INSTALL FAILED: '+Reason);
      InstallFailure:='新版本检查失败。原因：'+Reason+#13#10+'诊断日志：'+DiagnosticLog+#13#10+'安装日志：'+ExpandConstant('{log}')+#13#10+'退出安装向导后将恢复原程序；账号和记录保留。';
      SuppressibleMsgBox(InstallFailure,mbError,MB_OK,IDOK);
    end;
  end;
end;

function CanLaunch: Boolean;
begin Result:=InstallOK;end;

function GetCustomSetupExitCode: Integer;
begin if StartedFiles and not InstallOK then Result:=10 else Result:=0;end;

procedure CurPageChanged(CurPageID: Integer);
begin
  if (CurPageID=wpFinished) and not InstallOK then begin
    WizardForm.FinishedHeadingLabel.Caption:='安装未完成';
    WizardForm.FinishedLabel.Caption:=InstallFailure;
    WizardForm.RunList.Visible:=False;
  end;
end;

function InitializeUninstall: Boolean;
var Code: Integer;
begin
  if not AcquireGate then begin Result:=False;exit;end;
  if CheckForMutexes(AppMutexName('')) then begin
    SuppressibleMsgBox('请先关闭 AIClockIn 并等待后台操作结束，再卸载。',mbError,MB_OK,IDOK);Result := False;ReleaseGate;exit;
  end;
  Result := Exec(ExpandConstant('{app}\AIClockIn.exe'),'--uninstall-task',ExpandConstant('{app}'),SW_HIDE,ewWaitUntilTerminated,Code) and (Code=0);
  if not Result then SuppressibleMsgBox('无法安全清理本软件的自动任务，卸载已停止；账号和记录未删除。',mbError,MB_OK,IDOK);
end;

procedure DeinitializeUninstall;
begin ReleaseGate;end;

procedure DeinitializeSetup;
var RestoreError: Cardinal;
begin
  if StartedFiles and not InstallOK then begin
    if HadExe then begin
      Diagnostic('Rollback source='+OldExe+'; exists='+IntToStr(Ord(FileExists(OldExe)))+'; target='+ExpandConstant('{app}\AIClockIn.exe'));
      if not KernelCopyFile(OldExe,ExpandConstant('{app}\AIClockIn.exe'),False) then begin
        RestoreError:=KernelLastError;
        Diagnostic('ROLLBACK FAILED: Win32='+IntToStr(RestoreError)+' '+SysErrorMessage(RestoreError));
        SuppressibleMsgBox('恢复原程序失败，请保留原数据并重新运行安装包。诊断日志：'+DiagnosticLog,mbError,MB_OK,IDOK);
      end else Diagnostic('Previous executable restored.');
    end else if not KernelDeleteFile(ExpandConstant('{app}\AIClockIn.exe')) then
      Diagnostic('ROLLBACK FAILED: could not remove failed first-install launcher; Win32='+IntToStr(KernelLastError));
    if HadManifest and not FileCopy(OldManifest,ExpandConstant('{app}\bundle-manifest.json'),False) then Diagnostic('ROLLBACK FAILED: could not restore previous manifest.');
    if HadInfo and not FileCopy(OldInfo,ExpandConstant('{app}\install-info.ini'),False) then Diagnostic('ROLLBACK FAILED: could not restore previous data location metadata.');
    if HadRegistration then RegWriteStringValue(HKCU64,'Software\Microsoft\Windows\CurrentVersion\Uninstall\{#AppId}_is1','DisplayVersion',PreviousVersion)
    else RegDeleteKeyIncludingSubkeys(HKCU64,'Software\Microsoft\Windows\CurrentVersion\Uninstall\{#AppId}_is1');
  end;
  ReleaseGate;
end;
