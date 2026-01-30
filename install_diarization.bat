@echo off
title Instalar Dependencias de Diarización
color 0B

echo.
echo ==================================================
echo   INSTALANDO MODULO DE DIARIZACION (Pyannote)
echo ==================================================
echo.
echo Esto puede tardar unos minutos porque es una librería grande...
echo.

pip install -r requirements.txt

echo.
echo ==================================================
echo   INSTALACION COMPLETADA
echo ==================================================
echo.
echo Ahora vamos a configurar la aplicación.
pause
