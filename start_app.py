import sys
import subprocess
import tkinter as tk
from tkinter import messagebox
import os

# Konfiguration der benötigten Bibliotheken
# Format: (Modulname für import, Name für pip, Kurzbeschreibung)
REQUIRED_PACKAGES = [
    ("PIL", "Pillow", "fuer die Bildanzeige (Logo)"),
    ("mysql.connector", "mysql-connector-python", "fuer die Datenbankverbindung (MySQL)"),
    ("pandas", "pandas", "fuer die Datenverarbeitung und Tabellen")
]

def ensure_pip():
    """Stellt sicher, dass pip aktuell ist, bevor Pakete installiert werden."""
    try:
        print("🔍 Bereite Paket-Manager (pip) vor...")
        # Aktualisiert pip im Hintergrund (ohne Bestätigung)
        # Unter Linux wird hier --break-system-packages genutzt, um die PEP 668 Sperre zu umgehen
        cmd = [sys.executable, "-m", "pip", "install", "--upgrade", "pip"]
        if sys.platform.startswith('linux'):
            cmd.append("--break-system-packages")
            
        subprocess.check_call(cmd, stdout=subprocess.DEVNULL)
        return True
    except Exception as e:
        print(f"⚠️ Warnung beim pip-Update: {e}")
        return True # Wir versuchen es trotzdem weiter

def check_and_install_packages():
    """Prüft Abhängigkeiten einzeln und installiert sie bei Bedarf grafisch."""
    # Unsichtbares Tkinter-Hauptfenster für Dialoge
    root = tk.Tk()
    root.withdraw()
    
    all_ready = True

    for import_name, pip_name, description in REQUIRED_PACKAGES:
        try:
            # Gründliche Einzelprüfung: Versucht das Modul wirklich zu laden
            if import_name == "pandas":
                import pandas as pd
                # Kleiner Funktionstest für Pandas
                pd.DataFrame()
            elif import_name == "PIL":
                from PIL import Image, ImageTk
            else:
                __import__(import_name)
            
            print(f"✅ Modul vorhanden und funktionsfaehig: {import_name}")
        except (ImportError, ModuleNotFoundError, Exception):
            print(f"❌ Modul fehlt oder ist defekt: {import_name}")
            
            # Grafische Abfrage beim Nutzer
            is_linux = sys.platform.startswith('linux')
            zusatz_info = "\n(Nutzt --break-system-packages unter Linux)" if is_linux else ""
            
            frage = (f"Die Bibliothek '{pip_name}' ({description}) fehlt.\n\n"
                     f"Soll sie jetzt automatisch installiert werden?{zusatz_info}")
            
            if messagebox.askyesno("Abhängigkeit installieren", frage):
                try:
                    # Pip vorbereiten
                    ensure_pip()
                    
                    print(f"📥 Installiere {pip_name}...")
                    # Installation über den aktuellen Python-Interpreter
                    install_cmd = [sys.executable, "-m", "pip", "install", pip_name]
                    
                    # Fix für das 'externally-managed-environment' Problem unter Linux
                    if is_linux:
                        install_cmd.append("--break-system-packages")
                        
                    subprocess.check_call(install_cmd)
                    print(f"✅ {pip_name} erfolgreich installiert.")
                except Exception as e:
                    messagebox.showerror("Fehler", f"Installation von {pip_name} fehlgeschlagen:\n{e}")
                    all_ready = False
            else:
                messagebox.showwarning("Warnung", f"Ohne {pip_name} wird die App wahrscheinlich abstuerzen.")
                all_ready = False

    root.destroy()
    return all_ready

def start_main_app():
    """Startet die eigentliche GUI-Datei."""
    try:
        print("🚀 Lade Pflanzenprotokoll-Oberflaeche...")
        # Hier wird deine eigentliche Datei importiert und gestartet
        import pflanzen_gui
        app = pflanzen_gui.PflanzenApp()
        app.mainloop()
    except Exception as e:
        error_msg = f"Kritischer Fehler beim Starten von pflanzen_gui.py:\n{e}"
        print(error_msg)
        # Kurzes Notfall-Fenster für den Fehler
        temp_root = tk.Tk()
        temp_root.withdraw()
        messagebox.showerror("Programmfehler", error_msg)
        temp_root.destroy()

if __name__ == "__main__":
    # Schritt 1: Jedes Paket einzeln prüfen
    if check_and_install_packages():
        # Schritt 2: Wenn alles okay ist, Haupt-App starten
        start_main_app()
    else:
        print("❌ Start abgebrochen, da Komponenten fehlen.")
