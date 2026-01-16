#!/bin/bash

# Name der Datei, die am Ende geprüft und ausgeführt werden soll
ENDSTART="start.sh"  # 🚀 Hier kannst du den Dateinamen anpassen

# GitHub-Repository-URL und Branch definieren
REPO_URL="https://github.com/diggerwf/Brokkoli-Gie-planung-helfer.git"
BRANCH="main"

# Pfad zum Repository (aktueller Ordner)
REPO_DIR="$(cd "$(dirname "$0")" && pwd)"

cd "$REPO_DIR" || exit

# Dateien
UPDATE_SCRIPT="$REPO_DIR/update.sh"
TEMP_UPDATE_SCRIPT="$REPO_DIR/update.sh.2"

# Funktion: aktueller Commit-Hash lokal
get_current_hash() {
    git rev-parse HEAD 2>/dev/null
}

# Funktion: Remote-Commit-Hash vom Repository
get_remote_hash() {
    git ls-remote "$REPO_URL" "$BRANCH" | awk '{print $1}'
}

if [ -d "$REPO_DIR/.git" ]; then
    echo "🔍 Repository gefunden. Prüfe auf Updates..."

    # Optional: lokale Änderungen verwerfen
    git reset --hard

    # Nur fetch, kein push!
    git fetch origin

    LOCAL_HASH=$(get_current_hash)
    REMOTE_HASH=$(get_remote_hash)

    if [ "$LOCAL_HASH" != "$REMOTE_HASH" ]; then
        echo "📥 Update für update.sh erkannt. Lade neue Version..."

        # Update-Script kopieren, falls notwendig
        cp "$UPDATE_SCRIPT" "$TEMP_UPDATE_SCRIPT"

        # Pull aus dem Remote-Branch (ohne Push)
        git pull origin "$BRANCH"

        # Sicherstellen, dass das Script ausführbar ist
        chmod +x "$UPDATE_SCRIPT"

        echo "⚙️  Das neue Script wird nun ausgeführt..."
        # Das neue Script ausführen
        bash "$UPDATE_SCRIPT"

        # Temporäre Datei entfernen
        rm -f "$TEMP_UPDATE_SCRIPT"

        exit 0
    else
        echo "✅ Das Repository ist bereits aktuell."
    fi
else
    echo "📂 Repository nicht gefunden. Klone es von GitHub..."
    git clone "$REPO_URL" "$REPO_DIR"
fi

chmod +x "$UPDATE_SCRIPT"

echo "✨ Update abgeschlossen oder kein Update erforderlich."

# Am Ende: Prüfen, ob die festgelegte Datei existiert und ausführen

TARGET_FILE="$REPO_DIR/$ENDSTART"

if [ -f "$TARGET_FILE" ]; then
    echo "🏁 Gefundene Datei: $TARGET_FILE wird ausführbar gemacht und ausgeführt..."
    chmod +x "$TARGET_FILE"
    echo "--------------------------------------------------"
    "$TARGET_FILE"
else
    echo "❌ Die Datei $TARGET_FILE wurde nicht gefunden. Das Skript wird beendet."
    exit 1
fi
