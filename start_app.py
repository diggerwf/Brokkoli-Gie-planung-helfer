# start_app.py
import sys
import subprocess
import tkinter as tk
from tkinter import messagebox
import os
import platform

# Liste der notwendigen Pakete im Format (Importname, Pip-Installationsname, Beschreibung)
REQUIRED_PACKAGES = [
    ("PIL", "Pillow", "für die Bildanzeige (Logo)"),
    ("mysql.connector", "mysql-connector-python", "für die Datenbankverbindung (MySQL)")
]

def check_and_install_packages():
    """
    Überprüft die erforderlichen Pakete (Pillow und MySQL-Connector) mit Tkinter-Dialogen.
    """
    
    # Initialisiere das Tkinter-Fenster einmalig für die Dialoge
    root = tk.Tk()
    root.withdraw() 
    
    all_installed = True

    for import_name, pip_name, description in REQUIRED_PACKAGES:
        try:
            # Versuch, das Modul zu importieren
            __import__(import_name)
            print(f"✅ Modul '{import_name}' ist bereits installiert.")
        except ImportError:
            print(f"❌ Modul '{import_name}' wurde nicht gefunden.")
            
            msg = (
                f"Die Bibliothek '{pip_name}' ({description}) ist erforderlich.\n\n"
                f"Möchten Sie diese jetzt automatisch über 'pip install {pip_name}' installieren?"
            )
            
            if messagebox.askyesno(f"Abhängigkeit fehlt: {pip_name}", msg):
                try:
                    print(f"Starte Installation von {pip_name}...")
                    # Stellt sicher, dass der richtige Python-Interpreter verwendet wird
                    subprocess.check_call([sys.executable, "-m", "pip", "install", pip_name])
                    print(f"✅ {pip_name} erfolgreich installiert.")
                except subprocess.CalledProcessError as e:
                    error_msg = f"FEHLER: Installation von {pip_name} fehlgeschlagen.\nBitte manuell ausführen: pip install {pip_name}\nDetails: {e}"
                    messagebox.showerror("Installationsfehler", error_msg)
                    print(error_msg)
                    all_installed = False
                    root.destroy()
                    return False
                except Exception as e:
                    error_msg = f"Ein unbekannter Fehler ist während der Installation von {pip_name} aufgetreten: {e}"
                    messagebox.showerror("Installationsfehler", error_msg)
                    print(error_msg)
                    all_installed = False
                    root.destroy()
                    return False
            else:
                messagebox.showwarning("Installation übersprungen", 
                                       f"Die Installation von '{pip_name}' wurde übersprungen. Das Programm wird möglicherweise fehlschlagen.")
                all_installed = False

    root.destroy() 
    return all_installed

def start_main_app():
    """Startet die Hauptanwendung."""
    try:
        import pflanzen_gui
        app = pflanzen_gui.PflanzenApp()
        app.mainloop()
    except Exception as e:
        error_msg = f"FEHLER beim Starten von pflanzen_gui.py:\n{e}"
        print(error_msg)
        temp_root = tk.Tk()
        temp_root.withdraw()
        messagebox.showerror("Programmstart-Fehler", error_msg)

if __name__ == "__main__":
    if check_and_install_packages():
        start_main_app()