$ErrorActionPreference = "Stop"
Set-Location -LiteralPath $PSScriptRoot

function Stop-WithMessage {
    param([string]$Message)

    Write-Host ""
    Write-Host "BLAD: $Message" -ForegroundColor Red
    Write-Host ""
    Read-Host "Nacisnij Enter, aby zakonczyc"
    exit 1
}

Write-Host "=========================================="
Write-Host "Steam Game Recommender"
Write-Host "=========================================="
Write-Host ""

$pythonCommand = Get-Command python -ErrorAction SilentlyContinue
if (-not $pythonCommand) {
    Stop-WithMessage "Nie znaleziono Pythona. Zainstaluj Python 3.11 lub 3.12 i zaznacz opcje Add Python to PATH."
}

$versionOutput = (& python --version 2>&1 | Out-String).Trim()
Write-Host "Wykryto: $versionOutput"

if ($versionOutput -notmatch "Python\s+(3\.(11|12))(\.|$)") {
    Stop-WithMessage "Wymagany jest Python 3.11 lub 3.12. Wykryto: $versionOutput"
}

$venvPython = Join-Path $PSScriptRoot ".venv\Scripts\python.exe"

if (-not (Test-Path -LiteralPath $venvPython)) {
    Write-Host "[1/5] Tworzenie srodowiska wirtualnego..."
    & python -m venv .venv

    if ($LASTEXITCODE -ne 0) {
        Stop-WithMessage "Nie udalo sie utworzyc srodowiska wirtualnego."
    }
}
else {
    Write-Host "[1/5] Srodowisko wirtualne juz istnieje."
}

Write-Host "[2/5] Aktualizacja pip..."
& $venvPython -m pip install --upgrade pip
if ($LASTEXITCODE -ne 0) {
    Stop-WithMessage "Nie udalo sie zaktualizowac pip."
}

if (-not (Test-Path -LiteralPath "requirements.txt")) {
    Stop-WithMessage "Nie znaleziono pliku requirements.txt w katalogu projektu."
}

Write-Host "[3/5] Instalowanie zaleznosci..."
& $venvPython -m pip install -r requirements.txt
if ($LASTEXITCODE -ne 0) {
    Stop-WithMessage "Instalacja zaleznosci nie powiodla sie."
}

if (-not (Test-Path -LiteralPath "data\raw\steam-200k.csv")) {
    Stop-WithMessage "Brakuje pliku data\raw\steam-200k.csv."
}

Write-Host "[4/5] Uruchamianie pipeline Kedro..."
& $venvPython -m kedro run
if ($LASTEXITCODE -ne 0) {
    Stop-WithMessage "Pipeline Kedro zakonczyl sie niepowodzeniem."
}

Write-Host "[5/5] Uruchamianie aplikacji..."

$backendArguments = @(
    "-m",
    "uvicorn",
    "app.main:app",
    "--host",
    "127.0.0.1",
    "--port",
    "8000"
)

$backendProcess = Start-Process `
    -FilePath $venvPython `
    -ArgumentList $backendArguments `
    -WorkingDirectory $PSScriptRoot `
    -PassThru

Start-Sleep -Seconds 3

if ($backendProcess.HasExited) {
    Stop-WithMessage "Backend FastAPI nie uruchomil sie poprawnie."
}

Write-Host ""
Write-Host "Backend:      http://localhost:8000"
Write-Host "Swagger API:  http://localhost:8000/docs"
Write-Host "Frontend:     http://localhost:8501"
Write-Host ""
Write-Host "Aby zatrzymac aplikacje, nacisnij Ctrl+C."
Write-Host ""

try {
    & $venvPython -m streamlit run frontend/app.py

    if ($LASTEXITCODE -ne 0) {
        Stop-WithMessage "Frontend Streamlit zakonczyl sie bledem."
    }
}
finally {
    if ($backendProcess -and -not $backendProcess.HasExited) {
        Stop-Process -Id $backendProcess.Id -Force -ErrorAction SilentlyContinue
    }
}
