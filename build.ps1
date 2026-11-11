param([string]$BuildPython = 'D:\Python\python.exe', [string]$Destination = '')
$ErrorActionPreference = 'Stop'
if (-not $Destination) { $Destination = $PSScriptRoot }
$Destination = [IO.Path]::GetFullPath($Destination)
if (-not $Destination.StartsWith('D:\', [StringComparison]::OrdinalIgnoreCase)) { throw 'Output must be on D drive' }
$workspace = 'D:\个人开发软件\AI工作区'
$build = Join-Path $workspace 'temp\AIClockIn-build'
$runtime = Join-Path $workspace 'temp\AIClockIn\runtime'
$pipCache = Join-Path $workspace 'cache\pip'
$bundleCache = Join-Path $workspace 'cache\pyinstaller'
foreach ($path in @($build, $runtime, $pipCache, $bundleCache, $Destination)) {
    New-Item -ItemType Directory -Path $path -Force | Out-Null
}
$env:TEMP = $build
$env:TMP = $build
$env:TMPDIR = $build
$env:PIP_CACHE_DIR = $pipCache
$env:PYINSTALLER_CONFIG_DIR = $bundleCache
$env:PYTHONIOENCODING = 'utf-8'
$env:PYTHONDONTWRITEBYTECODE = '1'
$sid = [Security.Principal.WindowsIdentity]::GetCurrent().User.Value
& icacls.exe $runtime /inheritance:r /grant:r "*${sid}:(OI)(CI)F" | Out-Null
if ($LASTEXITCODE -ne 0) { throw 'Cannot secure runtime directory' }
& $BuildPython -B -c "import importlib.util,sys; sys.exit(0 if importlib.util.find_spec('PyInstaller') and __import__('PyInstaller').__version__ == '6.22.3' else 1)"
if ($LASTEXITCODE -ne 0) {
    $venv = Join-Path $build 'venv'
    if (-not (Test-Path -LiteralPath (Join-Path $venv 'Scripts\python.exe'))) {
        & $BuildPython -B -m venv $venv
        if ($LASTEXITCODE -ne 0) { throw 'Build environment creation failed' }
    }
    $BuildPython = Join-Path $venv 'Scripts\python.exe'
    & $BuildPython -B -m pip install --disable-pip-version-check -r (Join-Path $PSScriptRoot 'requirements-build.txt')
    if ($LASTEXITCODE -ne 0) { throw 'Build dependency installation failed' }
}
Push-Location $PSScriptRoot
try {
    & $BuildPython -B -m PyInstaller --noconfirm --onefile --windowed --noupx --name AIClockIn `
        --icon "$PSScriptRoot\assets\app.ico" --add-data "$PSScriptRoot\assets\app.ico;assets" `
        --add-data "$PSScriptRoot\VERSION;." --add-data "$PSScriptRoot\LICENSE;." --add-data "$PSScriptRoot\THIRD-PARTY-NOTICES.md;." `
        --runtime-tmpdir $runtime --distpath (Join-Path $build 'dist') --workpath (Join-Path $build 'work') --specpath $build main.py
    if ($LASTEXITCODE -ne 0) { throw 'EXE build failed' }
    Copy-Item -LiteralPath (Join-Path $build 'dist\AIClockIn.exe') -Destination (Join-Path $Destination 'AIClockIn.exe') -Force
    Get-FileHash -LiteralPath (Join-Path $Destination 'AIClockIn.exe') -Algorithm SHA256
} finally { Pop-Location }
