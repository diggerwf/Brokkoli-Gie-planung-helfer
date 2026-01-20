@echo off
setlocal enabledelayedexpansion

:: --- KONFIGURATION ---
set "REPO_URL=https://github.com/diggerwf/Brokkoli-Gie-planung-helfer.git"
set "BRANCH=main"
set "START_FILE=start4.bat"
:: ---------------------

echo ===========================================
echo       Projekt-Installer ^& Updater
echo ===========================================

:CHOOSE_FOLDER
echo [1/4] Ordner-Auswahl...
:: PowerShell-Dialog aufrufen
set "psCmd=Add-Type -AssemblyName System.Windows.Forms; $f = New-Object System.Windows.Forms.FolderBrowserDialog; $f.Description = 'Zielordner waehlen'; if($f.ShowDialog() -eq 'OK'){ $f.SelectedPath }"
for /f "delims=" %%I in ('powershell -ExecutionPolicy Bypass -Command "%psCmd%"') do set "TARGET_DIR=%%I"

:: Falls Fenster geschlossen wurde
if "%TARGET_DIR%"=="" (
    echo [!] Abbruch: Kein Ordner gewaehlt oder Dialog geschlossen.
    echo Druecke eine beliebige Taste zum Beenden...
    pause
    exit /b
)

echo [+] Gewaehlter Pfad: "!TARGET_DIR!"

:: WECHSEL IN DEN ORDNER (mit Anführungszeichen für Pfade mit Leerzeichen)
cd /d "!TARGET_DIR!" || (
    echo [!] FEHLER: Konnte nicht in den Ordner wechseln.
    pause
    exit /b
)

:CHECK_GIT
echo [2/4] Pruefe Git-Status...
git --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [!] Git nicht gefunden. Installation wird gestartet...
    winget install --id Git.Git -e --source winget --accept-package-agreements --accept-source-agreements
    echo [i] Bitte das Skript nach der Installation neu starten.
    pause
    exit
)

:PROCESS
echo [3/4] Projekt-Verarbeitung...

if exist ".git" (
    echo [+] Update-Modus: Synchronisiere...
    git remote set-url origin "!REPO_URL!"
    git -c credential.helper= fetch origin %BRANCH% --progress
    
    for /f "tokens=*" %%a in ('git rev-parse HEAD') do set "LOCAL_HASH=%%a"
    for /f "tokens=1" %%a in ('git ls-remote origin %BRANCH%') do set "REMOTE_HASH=%%a"
    
    if "!LOCAL_HASH!"=="!REMOTE_HASH!" (
        echo [+] Status: Alles aktuell.
    ) else (
        echo [+] Status: Update wird heruntergeladen...
        git pull origin %BRANCH% --progress
    )
) else (
    echo [+] Installations-Modus...
    :: Prüfen ob leer
    dir /a /b | findstr . >nul 2>&1
    if %errorlevel% equ 0 (
        :: Nicht leer
        for %%F in ("%REPO_URL%") do set "DIR_NAME=%%~nF"
        echo [!] Ordner nicht leer. Klone in: !DIR_NAME!
        git -c credential.helper= clone -b %BRANCH% --progress "!REPO_URL!" "!DIR_NAME!"
        if exist "!DIR_NAME!" cd /d "!DIR_NAME!"
    ) else (
        :: Leer
        echo [+] Klone direkt in Zielverzeichnis...
        git -c credential.helper= clone -b %BRANCH% --progress "!REPO_URL!" .
    )
)

:START_LOGIC
echo [4/4] Start-Check...
echo [i] Pfad: %CD%

if exist "%START_FILE%" (
    echo [+] Starte %START_FILE%...
    echo -------------------------------------------
    call "%START_FILE%"
    echo -------------------------------------------
    echo Programm beendet.
    pause
    exit
) else (
    echo.
    echo [!] FEHLER: "%START_FILE%" wurde nicht gefunden.
    echo [i] Inhalt von %CD%:
    dir /b
    echo.
    echo Druecke eine beliebige Taste um zu beenden
    pause
    exit
)
