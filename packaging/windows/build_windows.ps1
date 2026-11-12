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
