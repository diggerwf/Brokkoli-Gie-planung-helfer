#!/bin/bash
# start.sh - Linux/macOS Version

echo "######################################"
echo "# Ueberpruefe Python und Abhaengigkeiten"
echo "######################################"

# --- 1. System-Pakete prüfen (Tkinter & ImageTk) ---
echo "Prüfe System-Abhängigkeiten (Tkinter & PIL ImageTk)..."

# Prüfe Tkinter
python3 -c "import tkinter" &> /dev/null
TK_STATUS=$?

# Prüfe ImageTk
python3 -c "from PIL import ImageTk" &> /dev/null
IMAGETK_STATUS=$?

if [ $TK_STATUS -ne 0 ] || [ $IMAGETK_STATUS -ne 0 ]; then
    echo "--------------------------------------------------------------"
    echo "System-Komponenten (python3-tk oder pil.imagetk) fehlen."
    read -r -p "Sollen diese System-Pakete jetzt installiert werden? (J/N): " answer
    if [[ "$answer" =~ ^[Jj]$ ]]; then
        echo "Installiere System-Pakete (Sudo-Passwort erforderlich)..."
        sudo apt-get update
        sudo apt-get install -y python3-tk python3-pil.imagetk
    else
        echo "System-Installation übersprungen. Das Programm wird evtl. nicht starten."
    fi
else
    echo "? System-Komponenten sind bereit."
fi

# --- 2. Hilfsfunktion für Python-Module (PIP) ---
check_and_install_pip() {
    local import_name="$1"
    local pip_name="$2"
    local description="$3"

    echo ""
    echo "Prüfe, ob $description ($import_name) installiert ist..."
    python3 -c "import $import_name" &> /dev/null

    if [ $? -ne 0 ]; then
        echo "--------------------------------------------------------------"
        echo "Das Modul '$pip_name' ($description) fehlt."
        read -r -p "Soll es jetzt via pip installiert werden? (J/N): " answer
        if [[ "$answer" =~ ^[Jj]$ ]]; then
            pip3 install "$pip_name"
        else
            echo "Installation übersprungen."
        fi
    else
        echo "? $description ist bereits installiert."
    fi
}

# --- 3. Python Prüfung ---
if ! command -v python3 &> /dev/null; then
    echo "? FEHLER: python3 nicht gefunden!"
    exit 1
fi

# --- 4. PIP-Module prüfen ---
check_and_install_pip "mysql.connector" "mysql-connector-python" "Datenbank"
check_and_install_pip "PIL" "Pillow" "Bildanzeige"

# --- 5. Start ---
echo ""
echo "Starte Pflanzen-GUI..."
python3 pflanzen_gui.py &
exit 0