@echo off
echo ========================================
echo  Iniciando Ripsy - Sistema de Auditoria
echo ========================================
echo.

REM Verificar si Docker Desktop esta corriendo
echo [1/5] Verificando Docker Desktop...
docker info >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Docker Desktop no esta corriendo.
    echo Por favor, inicia Docker Desktop y espera a que este listo.
    echo Presiona cualquier tecla para intentar iniciar Docker Desktop...
    pause >nul
    start "" "C:\Program Files\Docker\Docker\Docker Desktop.exe"
    echo Esperando 30 segundos para que Docker Desktop inicie...
    timeout /t 30 /nobreak
)

echo [OK] Docker Desktop esta corriendo
echo.

REM Detener contenedores existentes
echo [2/5] Deteniendo contenedores existentes...
docker compose down
echo.

REM Construir imagenes
echo [3/5] Construyendo imagenes Docker...
docker compose build --no-cache
if %errorlevel% neq 0 (
    echo [ERROR] Fallo la construccion de imagenes
    pause
    exit /b 1
)
echo.

REM Iniciar servicios
echo [4/5] Iniciando servicios...
docker compose up -d
if %errorlevel% neq 0 (
    echo [ERROR] Fallo al iniciar servicios
    pause
    exit /b 1
)
echo.

REM Esperar a que los servicios esten listos
echo [5/5] Esperando a que los servicios esten listos...
timeout /t 15 /nobreak
echo.

REM Verificar estado
echo ========================================
echo  Estado de los Servicios
echo ========================================
docker compose ps
echo.

echo ========================================
echo  URLs de Acceso
echo ========================================
echo  - Frontend Streamlit: http://localhost:8501
echo  - API FastAPI:        http://localhost:8200
echo  - MinIO Console:      http://localhost:9001
echo  - PostgreSQL:         localhost:5432
echo ========================================
echo.

echo Ripsy esta listo! Presiona cualquier tecla para ver los logs...
pause >nul

docker compose logs -f
