#!/bin/bash

# ==========================================
# KONFIGURATION
# ==========================================
# Das Skript, das nach der Reparatur gestartet werden soll
TARGET_TO_CALL="update.sh"
# Liste der benötigten Tools
REQUIRED_TOOLS=("git" "dos2unix" "curl")

echo "=================================================="
echo "⚙️  SYSTEM-REPARATUR (fix_scripts.sh)"
echo "=================================================="

# 1. TOOL-CHECK & AUTOMATISCHE INSTALLATION
echo "🔍 Prüfe benötigte Werkzeuge..."
MISSING_TOOLS=()

for tool in "${REQUIRED_TOOLS[@]}"; do
    if ! command -v "$tool" &> /dev/null; then
        MISSING_TOOLS+=("$tool")
    fi
done

if [ ${#MISSING_TOOLS[@]} -gt 0 ]; then
    echo "📦 Fehlende Tools gefunden: ${MISSING_TOOLS[*]}"
    echo "📥 Starte Installation..."
    sudo apt update
    for tool in "${MISSING_TOOLS[@]}"; do
        sudo apt install -y "$tool"
    done
    echo "✅ Tools erfolgreich installiert."
else
    echo "✅ Alle Werkzeuge (git, dos2unix, curl) sind bereit."
fi

# 2. GIT-KONFLIKT-LÖSUNG (Hard Reset)
# Dies löst den Fehler: "unversionierte Dateien würden überschrieben werden"
if [ -d ".git" ]; then
    echo "📦 Git-Repository erkannt. Erzwinge Update vom Server..."
    git fetch --all &> /dev/null
    # Reset auf den Stand des Servers (überschreibt lokale kaputte Skripte)
    git reset --hard origin/main
else
    echo "⚠️  Kein Git-Repository gefunden. Überspringe Git-Reset."
fi

# 3. FORMAT-REPARATUR (CRLF -> LF)
# Wir reparieren alle .sh Dateien im aktuellen Ordner
echo "🧹 Entferne Windows-Zeilenenden aus allen Skripten..."
dos2unix *.sh &> /dev/null

# 4. RECHTE SETZEN
echo "🔑 Setze Ausführungsrechte (chmod +x)..."
chmod +x *.sh

# 5. ABSCHLUSS & ÜBERGABE
if [ -f "./$TARGET_TO_CALL" ]; then
    echo "--------------------------------------------------"
    echo "🚀 Reparatur abgeschlossen! Starte nun: $TARGET_TO_CALL"
    echo "--------------------------------------------------"
    ./"$TARGET_TO_CALL"
else
    echo "--------------------------------------------------"
    echo "❌ Fehler: '$TARGET_TO_CALL' wurde nicht gefunden."
    echo "Vorhandene Skripte im Ordner:"
    ls -l *.sh
fi
