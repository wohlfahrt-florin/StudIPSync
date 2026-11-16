$ErrorActionPreference = "Stop"

$projectRoot = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
Set-Location $projectRoot

$python = Join-Path $projectRoot ".venv\Scripts\python.exe"
if (-not (Test-Path $python)) {
    throw "Python-Umgebung nicht gefunden: $python"
}

$credentials = Join-Path $projectRoot "credentials.json"
if (-not (Test-Path $credentials)) {
    throw "credentials.json fehlt. Lege den Desktop-OAuth-Client in den Projektordner und starte den Build erneut."
}

& $python -m PyInstaller `
    --noconfirm `
    --clean `
    --windowed `
    --onefile `
    --name StudIPSync `
    --icon (Join-Path $projectRoot "assets\studipsync.ico") `
    --collect-all customtkinter `
    --add-data "$credentials;." `
    --add-data "$(Join-Path $projectRoot 'assets');assets" `
    (Join-Path $projectRoot "run_app.py")

if ($LASTEXITCODE -ne 0) {
    throw "PyInstaller wurde mit Exitcode $LASTEXITCODE beendet."
}

$innoCompiler = Get-Command ISCC.exe -ErrorAction SilentlyContinue
if (-not $innoCompiler) {
    $candidatePaths = @()
    if (${env:ProgramFiles(x86)}) {
        $candidatePaths += Join-Path ${env:ProgramFiles(x86)} "Inno Setup 6\ISCC.exe"
    }
    if ($env:ProgramFiles) {
        $candidatePaths += Join-Path $env:ProgramFiles "Inno Setup 6\ISCC.exe"
    }
    foreach ($candidatePath in $candidatePaths) {
        if (Test-Path $candidatePath) {
            $innoCompiler = Get-Item $candidatePath
            break
        }
    }
}
if (-not $innoCompiler) {
    throw "Inno Setup 6 wurde nicht gefunden. Installiere Inno Setup 6 oder füge ISCC.exe zum PATH hinzu."
}

$installerScript = Join-Path $PSScriptRoot "StudIPSync.iss"
$outputDirectory = Join-Path $projectRoot "dist"
& $innoCompiler.Source "/O$outputDirectory" $installerScript
if ($LASTEXITCODE -ne 0) {
    throw "Inno Setup wurde mit Exitcode $LASTEXITCODE beendet."
}
