param([string]$BuildPython='D:\Python\python.exe', [string]$Bundle='', [string]$ISCC='D:\个人开发软件\AI工作区\temp\AIClockIn-tools\InnoSetup-7.1.1\ISCC.exe')
$ErrorActionPreference='Stop'
$version=(Get-Content -LiteralPath (Join-Path $PSScriptRoot 'VERSION') -Raw).Trim()
if ($version -notmatch '^(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)$') { throw 'Invalid VERSION' }
if (-not (Test-Path -LiteralPath $ISCC)) { throw 'Inno Setup not found. Run tools/bootstrap-inno.ps1 or pass -ISCC.' }
$output=Join-Path $PSScriptRoot "dist\release\v$version"
$bundleOutput=Join-Path $PSScriptRoot "dist\bundle\v$version"
New-Item -ItemType Directory -Path $output -Force | Out-Null
if (-not $Bundle) {
    & (Join-Path $PSScriptRoot 'build.ps1') -BuildPython $BuildPython -Destination $bundleOutput
    if ($LASTEXITCODE -ne 0) { throw 'Folder build failed' }
    $Bundle=Join-Path $bundleOutput 'AIClockIn'
}
$Bundle=[IO.Path]::GetFullPath($Bundle)
if (-not $Bundle.StartsWith('D:\',[StringComparison]::OrdinalIgnoreCase)) { throw 'Bundle must be on D drive' }
$env:TEMP='D:\个人开发软件\AI工作区\temp\AIClockIn\runtime';$env:TMP=$env:TEMP
$env:PYINSTALLER_RESET_ENVIRONMENT='1';$env:PYTHONIOENCODING='utf-8';$env:PYTHONDONTWRITEBYTECODE='1'
$report=Join-Path $output 'selftest.json'
Remove-Item -LiteralPath $report -ErrorAction SilentlyContinue
$p=Start-Process -FilePath (Join-Path $Bundle 'AIClockIn.exe') -ArgumentList @('--self-test','--report',('"'+$report+'"')) -WindowStyle Hidden -Wait -PassThru
if ($p.ExitCode -ne 0 -or -not (Test-Path -LiteralPath $report)) { throw 'Bundle offline self-test failed' }
$health=Get-Content -LiteralPath $report -Raw -Encoding UTF8 | ConvertFrom-Json
if (-not $health.ok -or $health.version -ne $version) { throw 'Bundle version mismatch' }
$runtimeName=(Get-Content -LiteralPath (Join-Path $Bundle 'bundle-manifest.json') -Raw -Encoding UTF8 | ConvertFrom-Json).runtime
& $ISCC ("/DAppVersion=$version") ("/DRuntimeDir=$runtimeName") ("/DBundleDir=$Bundle") ("/DReleaseDir=$output") (Join-Path $PSScriptRoot 'installer\AIClockIn.iss')
if ($LASTEXITCODE -ne 0) { throw 'Inno Setup compilation failed' }
$name="AIClockIn-v$version-Setup-windows-x64.exe"
$asset=Join-Path $output $name
$alias=Join-Path $output 'AIClockInSetup.exe'
Copy-Item -LiteralPath $asset -Destination $alias -Force
$sha=(Get-FileHash -LiteralPath $asset -Algorithm SHA256).Hash.ToLowerInvariant()
[IO.File]::WriteAllText((Join-Path $output 'SHA256SUMS.txt'), "$sha  $name`n$sha  AIClockInSetup.exe`n",[Text.UTF8Encoding]::new($false))
Write-Output "Setup prepared: $asset"
Write-Output 'No GitHub Release was published.'
