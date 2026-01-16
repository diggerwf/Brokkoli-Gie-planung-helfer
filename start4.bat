@echo off
setlocal enabledelayedexpansion
title Pflanzenprotokoll Starter - Diagnose Modus

echo ######################################
echo # Ueberpruefe Systemumgebung...
echo ######################################

REM --- 1. Python-Installation pruefen ---
echo Suche nach Python...
python --version >nul 2>&1
if %errorlevel% NEQ 0 (
    echo.
    echo ❌ Python wurde nicht gefunden.
    echo 🛠️ Versuche Installation via Winget...
    
    REM Wir nutzen hier die ID fuer Python 3.12, die vorhin bei dir funktioniert hat
    winget install --id 9NCVDN91XZQP --source msstore --accept-package-agreements --accept-source-agreements
    
    if !errorlevel! EQU 0 (
        echo.
        echo ✅ Installation erfolgreich eingeleitet!
        echo ⚠️ WICHTIG: Schließe dieses Fenster jetzt und starte es NEU.
        echo Erst beim Neustart erkennt Windows das neue Python.
        pause
        exit
    ) else (
        echo.
        echo ❌ Winget-Installation ist fehlgeschlagen.
        echo 📥 Oeffne den Microsoft Store manuell fuer dich...
        start ms-windows-store://pdp/?ProductId=9NCVDN91XZQP
        echo.
        echo Bitte installiere Python im Store und starte diese Batch danach neu.
        pause
        exit
    )
)

REM --- 2. Hauptprogramm starten ---
echo ✅ Python gefunden:
python --version
echo.
echo 🚀 Starte start_app.py...

REM Prüfen ob die Datei überhaupt existiert
if not exist "start_app.py" (
    echo ❌ FEHLER: Die Datei 'start_app.py' wurde im Ordner nicht gefunden!
    echo Aktueller Ordner: %cd%
    pause
    exit
)

python start_app.py

if %errorlevel% NEQ 0 (
    echo.
    echo ❌ Das Python-Programm wurde mit Fehlern beendet (Code: %errorlevel%).
    pause
)