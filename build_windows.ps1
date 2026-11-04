$ErrorActionPreference = "Stop"

$python = Join-Path $PSScriptRoot ".venv\Scripts\python.exe"
if (-not (Test-Path $python)) {
    throw "Python-Umgebung nicht gefunden: $python"
}

& $python -m PyInstaller `
    --noconfirm `
    --clean `
    --windowed `
    --onefile `
    --name StudIPSync `
    --collect-all customtkinter `
    (Join-Path $PSScriptRoot "app.py")

if ($LASTEXITCODE -ne 0) {
    throw "PyInstaller wurde mit Exitcode $LASTEXITCODE beendet."
}
