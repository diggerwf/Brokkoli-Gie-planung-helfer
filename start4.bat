@echo off
title Pflanzenprotokoll Starter

echo ######################################
echo # Ueberpruefe Python und Abhaengigkeiten
echo ######################################

REM --- 1. Python-Installation pruefen ---
python --version 2>NUL
if %errorlevel% NEQ 0 (
    echo.
    echo ❌ FEHLER: Python wurde nicht gefunden.
    echo Bitte installieren Sie Python 3 und fuegen Sie es dem PATH hinzu.
    pause
    exit /b 1
) else (
    echo.
    echo ✅ Python ist installiert.
)

REM --- 2. Abhaengigkeiten pruefen und Hauptprogramm starten ---
echo.
echo Starte Abhaengigkeiten-Pruefung und GUI (start_app.py)...

REM start_app.py fuehrt die gesamte Logik (Pruefung/Installation von Pillow/MySQL) aus.
start "" python start_app.py

REM Beendet die Batch-Datei.
exit