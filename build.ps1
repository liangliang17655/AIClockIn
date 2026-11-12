param([string]$BuildPython = 'D:\Python\python.exe', [string]$Destination = '', [string]$VersionFile = '')
$ErrorActionPreference = 'Stop'
if (-not $VersionFile) { $VersionFile = Join-Path $PSScriptRoot 'VERSION' }
$VersionFile=[IO.Path]::GetFullPath($VersionFile)
if (-not $VersionFile.StartsWith('D:\',[StringComparison]::OrdinalIgnoreCase) -or [IO.Path]::GetFileName($VersionFile) -ne 'VERSION') { throw 'Version resource must be a VERSION file on D drive' }
$version = (Get-Content -LiteralPath $VersionFile -Raw).Trim()
$runtimeName = '_runtime-v'+$version+'-'+[Guid]::NewGuid().ToString('N').Substring(0,12)
if ($version -notmatch '^\d+\.\d+\.\d+$') { throw 'Invalid bundle version' }
if (-not $Destination) { $Destination = Join-Path $PSScriptRoot "dist\bundle\v$version" }
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
    & $BuildPython -B -m PyInstaller --noconfirm --onedir --contents-directory $runtimeName --windowed --noupx --name AIClockIn `
        --icon "$PSScriptRoot\assets\app.ico" --add-data "$PSScriptRoot\assets\app.ico;assets" `
        --add-data "$VersionFile;." --add-data "$PSScriptRoot\LICENSE;." --add-data "$PSScriptRoot\THIRD-PARTY-NOTICES.md;." `
        --distpath (Join-Path $build 'folder-dist') --workpath (Join-Path $build 'folder-work') --specpath $build main.py
    if ($LASTEXITCODE -ne 0) { throw 'EXE build failed' }
    $bundle = Join-Path $Destination 'AIClockIn'
    if (Test-Path -LiteralPath (Join-Path $bundle 'data')) { throw 'Build output must not contain user data' }
    New-Item -ItemType Directory -Path $bundle -Force | Out-Null
    Copy-Item -Path (Join-Path $build 'folder-dist\AIClockIn\*') -Destination $bundle -Recurse -Force
    & $BuildPython -B -c "from aiclockin.package import write_manifest; import sys; write_manifest(sys.argv[1],sys.argv[2],sys.argv[3])" $bundle $version $runtimeName
    if ($LASTEXITCODE -ne 0) { throw 'Bundle manifest failed' }
    Get-FileHash -LiteralPath (Join-Path $bundle 'AIClockIn.exe') -Algorithm SHA256
} finally { Pop-Location }
