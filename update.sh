#!/bin/bash

# Name der Datei, die am Ende geprüft und ausgeführt werden soll
ENDSTART="start.sh"

# GitHub-Repository-URL und Branch definieren
REPO_URL="https://github.com/diggerwf/Brokkoli-Gie-planung-helfer.git"
BRANCH="main"

# Pfad zum Repository (aktueller Ordner)
REPO_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$REPO_DIR" || exit

# Dateien definieren
UPDATE_SCRIPT="$REPO_DIR/update.sh"

# --- NEU: Reparatur-Funktion ---
fix_format() {
    echo "🧹 Bereinige Skript-Formate..."
    # Entfernt Windows-Zeilenenden (\r) aus allen .sh Dateien
    sed -i 's/\r$//' "$REPO_DIR"/*.sh
    # Setzt Ausführungsrechte für alle .sh Dateien
    chmod +x "$REPO_DIR"/*.sh
}

# Funktion: aktueller Commit-Hash lokal
get_current_hash() {
    git rev-parse HEAD 2>/dev/null
}

# Funktion: Remote-Commit-Hash vom Repository
get_remote_hash() {
    git ls-remote "$REPO_URL" "$BRANCH" | awk '{print $1}'
}

# Prüfen, ob wir in einem Git-Repo sind
if [ -d "$REPO_DIR/.git" ]; then
    echo "🔍 Repository gefunden. Prüfe auf Updates..."
    
    git reset --hard
    git fetch origin

    LOCAL_HASH=$(get_current_hash)
    REMOTE_HASH=$(get_remote_hash)

    if [ "$LOCAL_HASH" != "$REMOTE_HASH" ]; then
        echo "📥 Update erkannt. Lade neue Version..."
        git pull origin "$BRANCH"
        
        # WICHTIG: Nach dem Pull sofort reparieren
        fix_format
        
        echo "⚙️  Das neue Script wird nun ausgeführt..."
        exec bash "$UPDATE_SCRIPT"
    else
        echo "✅ Alles aktuell."
        # Auch wenn aktuell, sicherheitshalber Rechte prüfen
        fix_format
    fi
else
    echo "⚠️  Ordner ist kein Repository. Initialisiere neu..."
    
    if [ "$(ls -A "$REPO_DIR")" ]; then
        echo "📂 Ordner ist nicht leer. Bereite Umgebung für Klonen vor..."
        git init
        git remote add origin "$REPO_URL"
        git fetch
        git checkout -t origin/"$BRANCH" -f
    else
        echo "📥 Klone Repository..."
        git clone "$REPO_URL" "."
    fi
    # Nach Initialisierung reparieren
    fix_format
fi

echo "✨ Update-Check beendet."

# Ausführung der Zieldatei
TARGET_FILE="$REPO_DIR/$ENDSTART"

if [ -f "$TARGET_FILE" ]; then
    echo "🏁 Starte: $TARGET_FILE"
    echo "--------------------------------------------------"
    # Wir rufen es explizit mit ./ auf
    ./"$ENDSTART"
else
    echo "❌ Fehler: $TARGET_FILE nicht gefunden!"
    exit 1
fi
