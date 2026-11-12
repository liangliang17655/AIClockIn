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
var
  ExistingDir, ExistingData: String;
  OldExe, OldManifest, OldInfo: String;
  HadExe, HadManifest, HadInfo, StartedFiles, InstallOK, HadRegistration: Boolean;
  InstallFailure, PreviousVersion: String;
  GateHandle: Int64;

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

procedure CurStepChanged(CurStep: TSetupStep);
var Code: Integer; Health: AnsiString;
begin
  if CurStep=ssInstall then StartedFiles := True;
  if CurStep=ssPostInstall then begin
    try
    if not Exec(ExpandConstant('{app}\AIClockIn.exe'),'--self-test --report "'+ExpandConstant('{tmp}\health.json')+'"',ExpandConstant('{app}'),SW_HIDE,ewWaitUntilTerminated,Code) or (Code<>0) then
      RaiseException('新版本离线检查失败，将尝试恢复原程序。');
    if not LoadStringFromFile(ExpandConstant('{tmp}\health.json'),Health) or
       (Pos('"version": "{#AppVersion}"',String(Health))=0) then RaiseException('版本检查失败。');
#ifdef ForceHealthFailure
    RaiseException('Isolated test: health failure');
#endif
      if not RegWriteStringValue(HKCU64,'Software\{#AppId}','DataDirectory',DataDirectory('')) then
        RaiseException('无法保存当前用户的数据目录，请检查 Windows 用户权限。');
      InstallOK := True;
    except
      InstallFailure:='新版本检查失败。退出安装向导后将恢复原程序；账号和记录保留。';
      Log(InstallFailure);
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
begin
  if StartedFiles and not InstallOK then begin
    if HadExe then if not FileCopy(OldExe,ExpandConstant('{app}\AIClockIn.exe'),False) then
      SuppressibleMsgBox('恢复原程序失败，请保留原数据并重新运行安装包。',mbError,MB_OK,IDOK);
    if HadManifest then FileCopy(OldManifest,ExpandConstant('{app}\bundle-manifest.json'),False);
    if HadInfo then FileCopy(OldInfo,ExpandConstant('{app}\install-info.ini'),False);
    if HadRegistration then RegWriteStringValue(HKCU64,'Software\Microsoft\Windows\CurrentVersion\Uninstall\{#AppId}_is1','DisplayVersion',PreviousVersion)
    else RegDeleteKeyIncludingSubkeys(HKCU64,'Software\Microsoft\Windows\CurrentVersion\Uninstall\{#AppId}_is1');
  end;
  ReleaseGate;
end;
