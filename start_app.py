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

def check_and_install_packages():
    """Prüft jede Bibliothek einzeln durch einen echten Import-Test."""
    root = tk.Tk()
    root.withdraw()
    
    all_ready = True

    for import_name, pip_name, description in REQUIRED_PACKAGES:
        try:
            # EINZELPRÜFUNG:
            if import_name == "pandas":
                import pandas as pd
                pd.DataFrame() # Testet, ob pandas wirklich funktioniert
            elif import_name == "PIL":
                from PIL import Image, ImageTk
            else:
                __import__(import_name)
            
            print(f"✅ OK: {import_name} ist einsatzbereit.")
            
        except (ImportError, ModuleNotFoundError, Exception):
            print(f"❌ FEHLER: {import_name} fehlt oder ist defekt.")
            
            # Entscheidungshilfe für Linux vs. Windows
            is_linux = sys.platform.startswith('linux')
            apt_cmd = f"sudo apt install python3-{pip_name.lower().replace('-python', '')}"
            
            frage = (f"Die Bibliothek '{pip_name}' ({description}) fehlt.\n\n"
                     f"Soll versucht werden, sie automatisch zu installieren?\n")
            
            if is_linux:
                frage += f"\nHinweis: Auf Linux ist oft dieser Befehl besser:\n{apt_cmd}"

            if messagebox.askyesno("Abhängigkeit fehlt", frage):
                try:
                    print(f"📥 Versuche Installation von {pip_name}...")
                    # --break-system-packages erlaubt pip die Installation trotz PEP 668 Schutz
                    subprocess.check_call([
                        sys.executable, "-m", "pip", "install", 
                        pip_name, "--break-system-packages"
                    ])
                    print(f"✅ {pip_name} wurde installiert.")
                except Exception as e:
                    error_text = f"Installation fehlgeschlagen: {e}"
                    if is_linux:
                        error_text += f"\n\nBitte nutze im Terminal:\n{apt_cmd}"
                    messagebox.showerror("Fehler", error_text)
                    all_ready = False
            else:
                all_ready = False

    root.destroy()
    return all_ready

def start_main_app():
    """Startet die pflanzen_gui.py."""
    try:
        print("🚀 Alle Prüfungen bestanden. Starte GUI...")
        import pflanzen_gui
        app = pflanzen_gui.PflanzenApp()
        app.mainloop()
    except Exception as e:
        error_msg = f"Fehler beim Starten der App: {e}"
        print(error_msg)
        temp_root = tk.Tk()
        temp_root.withdraw()
        messagebox.showerror("Programmfehler", error_msg)
        temp_root.destroy()

if __name__ == "__main__":
    # Schritt 1: Einzelprüfung aller Pakete
    if check_and_install_packages():
        # Schritt 2: Start bei Erfolg
        start_main_app()
    else:
        print("🛑 Start abgebrochen. Bitte installiere die fehlenden Pakete manuell.")
