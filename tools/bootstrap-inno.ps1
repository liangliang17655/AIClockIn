param([string]$Destination = 'D:\个人开发软件\AI工作区\temp\AIClockIn-tools\InnoSetup-7.1.1')
$ErrorActionPreference = 'Stop'
if (-not ([IO.Path]::GetFullPath($Destination)).StartsWith('D:\',[StringComparison]::OrdinalIgnoreCase)) { throw 'Compiler destination must be on D drive' }
$cache = 'D:\个人开发软件\AI工作区\cache\installers'
$temporary = 'D:\个人开发软件\AI工作区\temp\AIClockIn-tools'
New-Item -ItemType Directory -Path $cache,$temporary -Force | Out-Null
$env:TEMP=$temporary; $env:TMP=$temporary
$installer=Join-Path $cache 'innosetup-7.1.1-x64.exe'
if (-not (Test-Path -LiteralPath $installer)) {
    Invoke-WebRequest -UseBasicParsing -Uri 'https://github.com/jrsoftware/issrc/releases/download/is-7_1_1/innosetup-7.1.1-x64.exe' -OutFile $installer
}
$expected='8a5a6711c3766a6e5fb74f280ba0e3551e719ce94538d901fdbd1f8f9920b3f0'
if ((Get-FileHash -LiteralPath $installer -Algorithm SHA256).Hash.ToLowerInvariant() -ne $expected) { throw 'Inno download SHA256 mismatch' }
$signature=Get-AuthenticodeSignature -LiteralPath $installer
if ($signature.Status -ne 'Valid' -or $signature.SignerCertificate.Subject -notlike '*Pyrsys B.V.*') { throw 'Inno publisher signature not valid' }
$arguments=@('/VERYSILENT','/SUPPRESSMSGBOXES','/NORESTART','/CURRENTUSER','/PORTABLE=1','/NOICONS',('/DIR="'+$Destination+'"'),('/LOG="'+(Join-Path $temporary 'inno-bootstrap.log')+'"'))
$process=Start-Process -FilePath $installer -ArgumentList $arguments -WindowStyle Hidden -Wait -PassThru
if ($process.ExitCode -ne 0) { throw "Inno bootstrap failed: $($process.ExitCode)" }
Write-Output (Join-Path $Destination 'ISCC.exe')
