@echo off
title Audio a Texto - Launcher
color 0A

echo ========================================
echo   Audio a Texto - Transcriptor AI
echo ========================================
echo.
echo Iniciando servidores...
echo.

REM Obtener la ruta del directorio del script
set "SCRIPT_DIR=%~dp0"
cd /d "%SCRIPT_DIR%"

REM Verificar que Python está instalado
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python no encontrado. Por favor instala Python 3.8 o superior.
    echo.
    pause
    exit /b 1
)

echo [OK] Python encontrado
echo.

REM Crear directorios si no existen
if not exist "backend\uploads" mkdir "backend\uploads"
if not exist "backend\transcriptions" mkdir "backend\transcriptions"

echo [1/3] Iniciando servidor Backend (Flask)...
start "Audio a Texto - Backend" cmd /k "cd /d "%SCRIPT_DIR%backend" && python app.py"

REM Esperar a que el backend se inicie
timeout /t 3 /nobreak >nul

echo [2/3] Iniciando servidor Frontend (HTTP)...
start "Audio a Texto - Frontend" cmd /k "cd /d "%SCRIPT_DIR%frontend" && python -m http.server 8080 --bind 127.0.0.1"

REM Esperar a que el frontend se inicie
timeout /t 2 /nobreak >nul

echo [3/3] Abriendo navegador...
timeout /t 1 /nobreak >nul

REM Abrir el navegador
start http://127.0.0.1:8080

echo.
echo ========================================
echo   Aplicacion iniciada correctamente
echo ========================================
echo.
echo Backend:  http://127.0.0.1:5000
echo Frontend: http://127.0.0.1:8080
echo.
echo IMPORTANTE:
echo - NO cierres las ventanas del Backend y Frontend
echo - Para detener la aplicacion, cierra todas las ventanas
echo.
echo Presiona cualquier tecla para cerrar este launcher...
pause >nul
