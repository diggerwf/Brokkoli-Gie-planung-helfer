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
        subprocess.check_call([sys.executable, "-m", "pip", "install", "--upgrade", "pip"], 
                              stdout=subprocess.DEVNULL)
        return True
    except Exception as e:
        print(f"⚠️ Warnung beim pip-Update: {e}")
        return True # Wir versuchen es trotzdem weiter

def check_and_install_packages():
    """Prüft Abhängigkeiten und installiert sie bei Bedarf grafisch."""
    # Unsichtbares Tkinter-Hauptfenster für Dialoge
    root = tk.Tk()
    root.withdraw()
    
    all_ready = True

    for import_name, pip_name, description in REQUIRED_PACKAGES:
        try:
            # Versuch, das Modul zu importieren
            __import__(import_name)
        except ImportError:
            # Wenn es fehlt, fragen wir den Nutzer
            user_decision = messagebox.askyesno(
                "Fehlende Bibliothek",
                f"Die Bibliothek '{pip_name}' ({description}) fehlt.\n\n"
                "Soll sie jetzt automatisch installiert werden?"
            )
            
            if user_decision:
                try:
                    ensure_pip()
                    print(f"📥 Installiere {pip_name}...")
                    subprocess.check_call([sys.executable, "-m", "pip", "install", pip_name])
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
    # Schritt 1: Pakete prüfen
    if check_and_install_packages():
        # Schritt 2: Wenn alles da ist, Haupt-App starten
        start_main_app()
    else:
        print("❌ Start abgebrochen, da nicht alle Pakete vorhanden sind.")
