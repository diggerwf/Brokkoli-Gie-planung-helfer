#!/bin/bash

# ==========================================
# KONFIGURATION
# ==========================================
# Hier die Datei definieren, die am Ende gestartet werden soll:
TARGET_TO_CALL="update.sh"
# ==========================================

echo "🔧 Starte System-Reparatur (fix_scripts.sh)..."

# 1. Prüfen und Installieren von dos2unix
if ! command -v dos2unix &> /dev/null; then
    echo "📦 'dos2unix' nicht gefunden. Versuche Installation..."
    sudo apt update && sudo apt install -y dos2unix
    if [ $? -ne 0 ]; then
        echo "❌ Fehler: Installation von dos2unix fehlgeschlagen. Prüfe deine Internetverbindung."
        exit 1
    fi
fi

# 2. Alle Skripte im Ordner reparieren
echo "🧹 Entferne Windows-Zeilenenden aus allen .sh Dateien..."
dos2unix *.sh &> /dev/null

# 3. Alle Skripte ausführbar machen
echo "🔑 Setze Ausführungsrechte (chmod +x)..."
chmod +x *.sh

# 4. Den Call ausführen
if [ -f "./$TARGET_TO_CALL" ]; then
    echo "🚀 Reparatur abgeschlossen. Rufe auf: $TARGET_TO_CALL"
    echo "--------------------------------------------------"
    ./"$TARGET_TO_CALL"
else
    echo "⚠️  Warnung: Die Datei '$TARGET_TO_CALL' wurde nicht gefunden."
    echo "Vorhandene Skripte:"
    ls *.sh
fi
