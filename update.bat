@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

:: 🎨 Konfiguration
set "REPO_URL=https://github.com/diggerwf/Brokkoli-Gie-planung-helfer.git"
set "BRANCH=Pflanzenprotokoll-Beta-3"
set "REPO_DIR=%~dp0"
set "START_FILE=start4.bat"
set "SELF_NAME=update.bat"
set "TEMP_NAME=temp_updater.bat"

:: 🛡️ AUSNAHMEN-KONFIGURATION
set "SKIP_FILES=-e "config.json" -e "settings.txt" -e "db_config.ini""
set "SKIP_FOLDERS=-e "logs/" -e "saves/" -e "__pycache__""

cd /d "%REPO_DIR%"

:: 🔄 SCHRITT 0: BIN ICH DIE KOPIE?
if "%~nx0"=="%TEMP_NAME%" (
    echo 🛠️ Temp-Updater aktiv. Überschreibe Original...
    timeout /t 1 >nul
    git reset --hard origin/%BRANCH% --quiet
    git clean -fd %SKIP_FILES% %SKIP_FOLDERS% >nul
    echo ✅ Update abgeschlossen. Starte Hauptskript...
    start "" "%SELF_NAME%"
    exit
)

:: 🗑️ SCHRITT 1: AUFRÄUMEN (Falls eine Kopie existiert)
if exist "%TEMP_NAME%" del "%TEMP_NAME%"

echo 🔍 Prüfe auf Updates für: !REPO_URL!

:: 🛠️ 2. GIT CHECK
git --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Git nicht gefunden! Installiere...
    winget install --id Git.Git -e --source winget --accept-package-agreements --accept-source-agreements
)

:: 🔄 3. UPDATE & URL-SYNC LOGIK
if exist ".git\" (
    git remote set-url origin "!REPO_URL!"
    git fetch origin %BRANCH% --quiet

    for /f "tokens=*" %%a in ('git rev-parse HEAD') do set "LOCAL_HASH=%%a"
    for /f "tokens=1" %%a in ('git ls-remote origin %BRANCH%') do set "REMOTE_HASH=%%a"

    echo 🏠 Lokal:  !LOCAL_HASH:~0,7!
    echo 🌐 Online: !REMOTE_HASH:~0,7!

    if "!LOCAL_HASH!" neq "!REMOTE_HASH!" (
        echo 🆕 Selbst-Update erkannt! Starte Sicherheits-Prozess... 📥
        copy /y "%SELF_NAME%" "%TEMP_NAME%" >nul
        start "" "%TEMP_NAME%"
        exit
    ) else (
        echo ✅ Alles aktuell!
    )
) else (
    echo 🏗️ Ersteinrichtung läuft... 🔧
    git init --quiet
    git remote add origin "!REPO_URL!" 2>nul
    git fetch --all --quiet
    git reset --hard origin/%BRANCH% --quiet
    git clean -fd %SKIP_FILES% %SKIP_FOLDERS% >nul
    echo 🔗 Erfolgreich mit neuem Repo verbunden! 📦
)

echo.
echo ✨ Fertig! Repo ist synchron.
pause

:: 🚀 4. START DES HAUPTPROGRAMMS
if exist "!START_FILE!" (
    echo 🚀 Starte !START_FILE!...
    start "" "!START_FILE!"
) else (
    echo ⚠️ !START_FILE! wurde nicht gefunden.
)
::exit

