@echo off
chcp 65001 > nul
title DocuExtract AI - Lanzador de la Plataforma

echo =====================================================================
echo           DocuExtract AI - Micro-SaaS B2B Extractor
echo =====================================================================
echo.

if not exist ".env" (
    echo [AVISO] Creando archivo .env desde .env.example...
    copy .env.example .env > nul
)

if not exist "venv\Scripts\python.exe" (
    echo [ERROR] No se encontro el entorno virtual en 'venv'.
    echo Creando entorno virtual e instalando dependencias...
    python -m venv venv
    call .\venv\Scripts\activate.bat
    pip install -r requirements.txt
)

echo [1/2] Iniciando Servidor Backend FastAPI en puerto 8008...
start "DocuExtract - Backend FastAPI (Puerto 8008)" cmd /k ".\venv\Scripts\activate.bat && uvicorn app.main:app --host 0.0.0.0 --port 8008 --reload"

echo [2/2] Esperando 3 segundos e iniciando Frontend Streamlit en puerto 8505...
timeout /t 3 /nobreak > nul
start "DocuExtract - Frontend Streamlit (Puerto 8505)" cmd /k ".\venv\Scripts\activate.bat && streamlit run frontend/app.py --server.port 8505"

echo.
echo =====================================================================
echo   Plataforma iniciada con exito en puertos libres:
echo   - Backend API:    http://localhost:8008/docs
echo   - Frontend Panel: http://localhost:8505
echo =====================================================================
echo.
pause
