$ErrorActionPreference = "Stop"

$python = Join-Path $PSScriptRoot ".venv\Scripts\python.exe"
if (-not (Test-Path $python)) {
    throw "Python-Umgebung nicht gefunden: $python"
}

$credentials = Join-Path $PSScriptRoot "credentials.json"
if (-not (Test-Path $credentials)) {
    throw "credentials.json fehlt. Lege den Desktop-OAuth-Client in den Projektordner und starte den Build erneut."
}

& $python -m PyInstaller `
    --noconfirm `
    --clean `
    --windowed `
    --onefile `
    --name StudIPSync `
    --collect-all customtkinter `
    --add-data "$credentials;." `
    (Join-Path $PSScriptRoot "app.py")

if ($LASTEXITCODE -ne 0) {
    throw "PyInstaller wurde mit Exitcode $LASTEXITCODE beendet."
}
