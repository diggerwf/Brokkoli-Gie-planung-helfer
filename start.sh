#!/bin/bash
# start.sh

echo "######################################"
echo "# Ueberpruefe Python und Abhaengigkeiten"
echo "######################################"

# --- 1. Python-Installation pruefen (Nutzt python3) ---
if ! command -v python3 &> /dev/null
then
    echo ""
    echo "❌ FEHLER: Der Befehl 'python3' wurde nicht gefunden."
    echo "Bitte installieren Sie Python 3."
    exit 1
else
    echo ""
    echo "✅ Python 3 ist installiert."
fi

# --- 2. Abhaengigkeiten pruefen und Hauptprogramm starten ---
echo ""
echo "Starte Abhaengigkeiten-Pruefung und GUI (start_app.py)..."
# start_app.py fuehrt die gesamte Logik (Pruefung/Installation von Pillow/MySQL) aus.

# Startet Python im Hintergrund, um das Terminal freizugeben
python3 start_app.py &

# Beendet das Shell-Skript sofort
exit 0