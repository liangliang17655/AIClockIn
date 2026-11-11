param([string]$BuildPython = 'D:\Python\python.exe', [string]$Exe = '')
$ErrorActionPreference = 'Stop'
$version = (Get-Content -LiteralPath (Join-Path $PSScriptRoot 'VERSION') -Raw).Trim()
if ($version -notmatch '^(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)$') { throw 'Invalid VERSION' }
$output = Join-Path $PSScriptRoot "dist\release\v$version"
New-Item -ItemType Directory -Path $output -Force | Out-Null
if (-not $Exe) {
    & (Join-Path $PSScriptRoot 'build.ps1') -BuildPython $BuildPython -Destination $output
    if ($LASTEXITCODE -ne 0) { throw 'Build failed' }
    $Exe = Join-Path $output 'AIClockIn.exe'
}
$Exe = [IO.Path]::GetFullPath($Exe)
if (-not $Exe.StartsWith('D:\', [StringComparison]::OrdinalIgnoreCase)) { throw 'EXE must be on D drive' }
$env:PYTHONDONTWRITEBYTECODE = '1'
$env:PYTHONIOENCODING = 'utf-8'
$env:TEMP = 'D:\个人开发软件\AI工作区\temp\AIClockIn\runtime'
$env:TMP = $env:TEMP
$env:PYINSTALLER_RESET_ENVIRONMENT = '1'
$report = Join-Path $output 'selftest.json'
Remove-Item -LiteralPath $report -ErrorAction SilentlyContinue
$process = Start-Process -FilePath $Exe -ArgumentList @('--self-test', '--report', ('"' + $report + '"')) -WindowStyle Hidden -Wait -PassThru
if ($process.ExitCode -ne 0 -or -not (Test-Path -LiteralPath $report)) { throw 'EXE self-test failed' }
$health = Get-Content -LiteralPath $report -Raw -Encoding UTF8 | ConvertFrom-Json
if (-not $health.ok -or $health.version -ne $version) { throw 'EXE version does not match VERSION' }
$name = "AIClockIn-v$version-windows-x64.exe"
$asset = Join-Path $output $name
Copy-Item -LiteralPath $Exe -Destination $asset -Force
$sha = (Get-FileHash -LiteralPath $asset -Algorithm SHA256).Hash.ToLowerInvariant()
[IO.File]::WriteAllText((Join-Path $output 'SHA256SUMS.txt'), "$sha  $name`n", [Text.UTF8Encoding]::new($false))
Write-Host "Release files prepared: $output"
Write-Host 'No tag, commit, push or GitHub Release was created.'
