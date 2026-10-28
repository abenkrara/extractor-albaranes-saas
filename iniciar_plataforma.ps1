# Script PowerShell para iniciar la plataforma DocuExtract AI

Write-Host "=====================================================================" -ForegroundColor Cyan
Write-Host "          DocuExtract AI - Micro-SaaS B2B Extractor" -ForegroundColor Cyan
Write-Host "=====================================================================" -ForegroundColor Cyan
Write-Host ""

if (-not (Test-Path ".env")) {
    Write-Host "[INFO] Creando archivo .env a partir de .env.example..." -ForegroundColor Yellow
    Copy-Item .env.example .env
}

# 1. Iniciar Backend FastAPI en nueva ventana (Puerto 8008)
Write-Host "[1/2] Iniciando Backend FastAPI en http://localhost:8008..." -ForegroundColor Green
Start-Process powershell -ArgumentList "-NoExit", "-Command", ".\venv\Scripts\Activate.ps1; uvicorn app.main:app --host 0.0.0.0 --port 8008 --reload"

# 2. Esperar 2 segundos
Start-Sleep -Seconds 2

# 3. Iniciar Frontend Streamlit en nueva ventana (Puerto 8505)
Write-Host "[2/2] Iniciando Frontend Streamlit en http://localhost:8505..." -ForegroundColor Green
Start-Process powershell -ArgumentList "-NoExit", "-Command", ".\venv\Scripts\Activate.ps1; streamlit run frontend/app.py --server.port 8505"

Write-Host ""
Write-Host "=====================================================================" -ForegroundColor Cyan
Write-Host "  Plataforma iniciada exitosamente!" -ForegroundColor Green
Write-Host "  - Swagger API:    http://localhost:8008/docs" -ForegroundColor Yellow
Write-Host "  - Interfaz Web:   http://localhost:8505" -ForegroundColor Yellow
Write-Host "=====================================================================" -ForegroundColor Cyan
