#!/bin/bash
# start.sh - Linux/macOS Version

echo "######################################"
echo "# Ueberpruefe Python und Abhaengigkeiten"
echo "######################################"

# --- Hilfsfunktion ---
check_and_install() {
    local import_name="$1"
    local pip_name="$2"
    local description="$3"

    echo ""
    echo "Prüfe, ob $description ($import_name) installiert ist..."
    python3 -c "import $import_name" &> /dev/null

    if [ $? -ne 0 ]; then
        echo "--------------------------------------------------------------"
        echo "Das Modul '$pip_name' ($description) fehlt."
        read -r -p "Soll es jetzt installiert werden? (J/N): " answer
        if [[ "$answer" =~ ^[Jj]$ ]]; then
            pip3 install "$pip_name"
        else
            echo "Installation übersprungen."
        fi
    else
        echo "✅ $description ist bereits installiert."
    fi
}

# --- Python Prüfung ---
if ! command -v python3 &> /dev/null; then
    echo "❌ FEHLER: python3 nicht gefunden!"
    exit 1
fi

# --- Module prüfen ---
check_and_install "mysql.connector" "mysql-connector-python" "Datenbank"
check_and_install "PIL" "Pillow" "Bildanzeige"

# --- Start ---
echo ""
echo "Starte Pflanzen-GUI..."
python3 pflanzen_gui.py &
exit 0
