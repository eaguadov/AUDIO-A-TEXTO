@echo off
title Matando servidores Python...
color 0C

echo.
echo ==================================================
echo   LIMPIEZA DE PROCESOS PYTHON (AUDIO A TEXTO)
echo ==================================================
echo.
echo Cerrando procesos que puedan estar bloqueando los puertos...
echo.

taskkill /F /IM python.exe /T 2>nul
taskkill /F /IM "Audio a Texto - Backend" 2>nul
taskkill /F /IM "Audio a Texto - Frontend" 2>nul

echo.
echo ==================================================
echo   LIMPIEZA COMPLETADA
echo ==================================================
echo.
echo Ya puedes ejecutar start_app.bat de nuevo sin problemas.
echo.
pause
