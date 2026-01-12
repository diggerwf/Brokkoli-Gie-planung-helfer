# pflanzen_gui.py
# -*- coding: utf-8 -*-
import tkinter as tk
from tkinter import messagebox, ttk, filedialog
import csv 
import os 
from datetime import datetime

# WICHTIG: Import für Bildbearbeitung (Pillow)
from PIL import Image, ImageTk 

# Importiere die Logik 
from db_connector import get_db_connection, setup_database_and_table, insert_pflanzen_data, test_db_connection, fetch_all_data, delete_data_by_id, save_pflanzen_plan, get_pflanzen_plan
from config_manager import load_config, save_config

# Definierte Reihenfolge der Nährstofffelder (muss mit DB übereinstimmen)
PLANNING_FIELDS = [
    "phase", "lichtzyklus_h", "ec_wert", "root_juice_ml_l", "calmag_ml_l", 
    "bio_grow_ml_l", "acti_alc_ml_l", "bio_bloom_ml_l", "top_max_ml_l", 
    "ph_wert_ziel"
]

class PflanzenApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("🌱 Pflanzenprotokoll Desktop-Anwendung")
        
        # NEU: Automatische Maximierung des Fensters je nach OS
        self._set_maximized_state() 
        
        self.db_config = load_config()
        
        self.is_auto_refresh_active = tk.BooleanVar(value=False)
        self.refresh_interval = tk.IntVar(value=60)
        self.after_id = None
        
        self.plan_labels = {} 
        self.current_data_columns = None 
        
        # NEU: Erstellt den Hauptrahmen für Logo und Tabs
        self.main_container = tk.Frame(self)
        self.main_container.pack(expand=True, fill="both")
        
        self._load_and_display_logo(self.main_container) # Logo wird geladen und platziert
        self.create_menu_bar()
        self.create_main_tabs(self.main_container) # Tabs werden in den Container gelegt

    def __del__(self):
        """Stoppt den Auto-Refresh-Loop beim Schließen der App."""
        self._toggle_auto_refresh(stop=True)

    def _load_and_display_logo(self, parent):
        """Lädt das Logo von der Festplatte und platziert es in einem Label."""
        logo_path = "diggerwf.jpeg" # <--- Stellen Sie sicher, dass Ihr Bild so heißt und im gleichen Ordner liegt
        
        try:
            # 1. Bild öffnen und auf eine passende Größe skalieren (z.B. 70x70)
            img = Image.open(logo_path)
            img = img.resize((70, 70), Image.Resampling.LANCZOS)
            self.logo_img = ImageTk.PhotoImage(img) # Muss als Instanzvariable gespeichert werden!

            # 2. Label erstellen und Bild anzeigen
            logo_label = tk.Label(parent, image=self.logo_img)
            # Platziert das Logo links über den Tabs
            logo_label.pack(pady=5, padx=10, anchor='nw') 

        except FileNotFoundError:
            print(f"WARNUNG: Logo-Datei nicht gefunden unter {logo_path}")
            # Optional: Platzhalter-Label einfügen
            tk.Label(parent, text="[Logo nicht gefunden]").pack(pady=5, padx=10, anchor='nw')
        except Exception as e:
            print(f"FEHLER beim Laden des Logos: {e}")
            tk.Label(parent, text="[Logo Fehler]").pack(pady=5, padx=10, anchor='nw')

    def _set_maximized_state(self):
        # ... (Methode ist unverändert)
        """Maximiert das Fenster je nach Betriebssystem."""
        
        current_os = os.name
        
        if current_os == 'nt':
            try:
                self.state('zoomed')
            except tk.TclError:
                self.attributes('-fullscreen', True) 
                
        elif current_os == 'posix':
            if 'darwin' in os.uname().sysname.lower():
                 self.attributes('-zoomed', True)
            else:
                try:
                    self.attributes('-zoomed', True)
                except tk.TclError:
                    screen_width = self.winfo_screenwidth()
                    screen_height = self.winfo_screenheight()
                    self.geometry(f"{screen_width}x{screen_height}+0+0")
        
    def create_menu_bar(self):
        """Erstellt die obere Menüleiste (Datei-Menü)."""
        menubar = tk.Menu(self)
        self.config(menu=menubar)

        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Datei", menu=file_menu)
        file_menu.add_command(label="Beenden", command=self.quit)
        
        db_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Datenbank", menu=db_menu)
        db_menu.add_command(label="MySQL Einstellungen", command=self.show_db_settings)

    def create_main_tabs(self, parent_frame):
        """Erstellt das Hauptmenü als Notizbuch (Tabs) im übergeordneten Frame."""
        self.notebook = ttk.Notebook(parent_frame) # <--- Platziert die Tabs nun im Container
        self.notebook.pack(pady=10, padx=10, expand=True, fill="both")
        
        self.notebook.bind("<<NotebookTabChanged>>", self._handle_tab_change)

        # --- Tab 1: DATEN EINGEBEN ---
        self.tab_eingabe = tk.Frame(self.notebook, padx=10, pady=10)
        self.notebook.add(self.tab_eingabe, text="🌿 Daten eingeben")
        self.create_input_widgets(self.tab_eingabe)

        # --- Tab 2: DATEN ANZEIGEN ---
        self.tab_anzeige = tk.Frame(self.notebook, padx=10, pady=10)
        self.notebook.add(self.tab_anzeige, text="📈 Daten anzeigen")
        self.create_display_widgets(self.tab_anzeige)
        
        # --- Tab 3: EINSTELLUNGEN ---
        self.tab_settings = tk.Frame(self.notebook, padx=10, pady=10)
        self.notebook.add(self.tab_settings, text="⚙️ Einstellungen")
        self.create_settings_tab(self.tab_settings)

    def _handle_tab_change(self, event):
        # ... (Methode ist unverändert)
        """Behandelt den Wechsel der Tabs."""
        selected_tab = self.notebook.tab(self.notebook.select(), "text")
        
        if selected_tab == "📈 Daten anzeigen":
            self.load_data_into_treeview()
            self._toggle_auto_refresh(start=True)
        else:
            self._toggle_auto_refresh(stop=True)

    # --- DATEN EINGABE LOGIK ---

    def create_input_widgets(self, parent_frame):
        # ... (Methode ist unverändert)
        """Erstellt die Eingabefelder für die Pflanzendaten und die Soll-Anzeige."""
        
        main_frame = tk.Frame(parent_frame)
        main_frame.pack(padx=10, pady=10)

        # Frame für die Eingabe (Ist)
        input_frame = tk.LabelFrame(main_frame, text="Aktuelle Messwerte (Ist)", padx=10, pady=10)
        input_frame.grid(row=0, column=0, padx=10, pady=5, sticky='n')
        
        # Frame für die Soll-Anzeige (Planung)
        plan_display_frame = tk.LabelFrame(main_frame, text="Planung (Soll)", padx=10, pady=10)
        plan_display_frame.grid(row=0, column=1, padx=10, pady=5, sticky='n')

        # Felderliste mit Datum und EC-Wert
        self.fields = [
            ("Datum (JJJJ-MM-TT)", "entry_datum"),
            ("Name der Pflanze", "entry_name"),
            ("Woche", "entry_woche"),
            ("Phase", "entry_phase"),
            ("Lichtzyklus (h)", "entry_licht"),
            ("EC-Wert", "entry_ec"), 
            ("Root·Juice (ml/L)", "entry_root"),
            ("Calmag (ml/L)", "entry_calmag"),
            ("Bio·Grow (ml/L)", "entry_grow"),
            ("Acti·a•alc (ml/L)", "entry_acti"),
            ("Bio·Bloom (ml/L)", "entry_bloom"),
            ("Top·Max (ml/L)", "entry_topmax"),
            ("pH-Wert (Ziel)", "entry_ph")
        ]
        
        self.entries = {}
        self.plan_labels = {}
        
        # Zähler für Planungsfelder
        plan_display_row = 0 
        
        for i, (label_text, key) in enumerate(self.fields):
            label = tk.Label(input_frame, text=f"{label_text}:")
            label.grid(row=i, column=0, padx=5, pady=2, sticky='w')
            
            # Spezielle Behandlung für Datum (mit Button)
            if key == "entry_datum":
                date_frame = tk.Frame(input_frame)
                date_frame.grid(row=i, column=1, padx=5, pady=2, sticky='ew')
                
                entry = tk.Entry(date_frame, width=15)
                entry.pack(side=tk.LEFT, fill='x', expand=True)
                
                # Button mit Kalender-Emoji
                tk.Button(date_frame, text="📅", 
                          command=lambda: self._set_today_date(entry), 
                          width=3).pack(side=tk.LEFT, padx=(5, 0))
                
                # Standardmäßig auf heutiges Datum setzen
                self._set_today_date(entry)

            else:
                entry = tk.Entry(input_frame, width=25)
                entry.grid(row=i, column=1, padx=5, pady=2)

            self.entries[key] = entry
            
            # Binding, um Planung bei Änderung von Name/Woche neu zu laden
            if key in ["entry_name", "entry_woche"]:
                entry.bind("<FocusOut>", self._load_plan_for_current_inputs)
                entry.bind("<Return>", self._load_plan_for_current_inputs)
            
            # Anzeige Planung (Soll) - Schließt Datum, Name, Woche aus
            if key not in ["entry_datum", "entry_name", "entry_woche"]: 
                plan_label = tk.Label(plan_display_frame, text="---", anchor='w', width=25)
                plan_label.grid(row=plan_display_row, column=0, padx=5, pady=2, sticky='w')
                self.plan_labels[key] = plan_label
                plan_display_row += 1

        # Speichern Button für IST-Werte
        save_button = tk.Button(input_frame, text="Daten Speichern (IST)", command=self.save_data_to_db, bg='green', fg='white')
        save_button.grid(row=len(self.fields), columnspan=2, pady=15)
        
        # Planung Bearbeiten Button 
        plan_button = tk.Button(plan_display_frame, text="Planung Bearbeiten (SOLL)", command=self.open_plan_window, bg='orange', fg='white')
        plan_button.grid(row=plan_display_row, columnspan=1, pady=15)

    def _set_today_date(self, entry_widget):
        # ... (Methode ist unverändert)
        """Setzt das aktuelle Datum im Format YYYY-MM-DD in das Eingabefeld."""
        today = datetime.now().strftime("%Y-%m-%d")
        entry_widget.delete(0, tk.END)
        entry_widget.insert(0, today)

    def _load_plan_for_current_inputs(self, event=None):
        # ... (Methode ist unverändert)
        """Lädt die Planung für die aktuell eingegebene Pflanze und Woche."""
        try:
            plant_name = self.entries['entry_name'].get().strip()
            week = int(self.entries['entry_woche'].get())
        except ValueError:
            self._update_plan_display(None, None)
            return

        if not plant_name or week <= 0:
            self._update_plan_display(None, None)
            return
            
        plan_values_tuple, plan_columns = get_pflanzen_plan(self.db_config, plant_name, week)
        self._update_plan_display(plan_values_tuple, plan_columns)

    def _update_plan_display(self, plan_values_tuple, plan_columns):
        # ... (Methode ist unverändert)
        """Aktualisiert die Soll-Werte im Eingabe-Tab."""
        
        plan_data = {}
        
        if plan_values_tuple and plan_columns:
            plan_data = dict(zip(plan_columns, plan_values_tuple))
            
        for ist_key in self.plan_labels.keys():
            db_key = ist_key.replace('entry_', '')
            
            if db_key in plan_data:
                value = plan_data[db_key]
                if isinstance(value, float) and value is not None:
                    # Spezieller Fall für EC-Wert (Anzeige Einheit)
                    if db_key == 'ec_wert':
                         display_value = f"({value:.2f} S/m)"
                    else:
                         display_value = f"{value:.2f}"
                elif value is None:
                    display_value = "---"
                else:
                    display_value = str(value)
            else:
                display_value = "---"

            self.plan_labels[ist_key].config(text=display_value)

    # --- PLANUNGS-FENSTER LOGIK ---

    def open_plan_window(self):
        # ... (Methode ist unverändert)
        """Öffnet ein separates Fenster zur Eingabe der Planung."""
        plan_window = tk.Toplevel(self)
        plan_window.title("Planung Speichern/Bearbeiten (SOLL)")
        
        try:
            initial_name = self.entries['entry_name'].get().strip()
            initial_woche = self.entries['entry_woche'].get().strip()
        except Exception:
            initial_name = ""
            initial_woche = ""
            
        plan_window.geometry("450x550")
        
        plan_entries = {}
        
        tk.Label(plan_window, text="Pflanzenname:", font=('Arial', 10, 'bold')).pack(pady=(10, 0))
        entry_name = tk.Entry(plan_window, width=50)
        entry_name.insert(0, initial_name)
        entry_name.pack(pady=2)
        
        tk.Label(plan_window, text="Woche (Gültigkeitsbereich):", font=('Arial', 10, 'bold')).pack(pady=(10, 0))
        entry_woche = tk.Entry(plan_window, width=50)
        entry_woche.insert(0, initial_woche)
        entry_woche.pack(pady=2)
        
        def load_plan_on_change(event):
            self._load_plan_in_window(entry_name, entry_woche, plan_entries)
            
        entry_name.bind("<FocusOut>", load_plan_on_change)
        entry_woche.bind("<FocusOut>", load_plan_on_change)

        tk.Label(plan_window, text="Planungswerte (SOLL):", font=('Arial', 10, 'bold')).pack(pady=(10, 0))
        
        # fields_map mit EC-Wert
        fields_map = {
            "phase": "Phase", "lichtzyklus_h": "Lichtzyklus (h)", "ec_wert": "EC-Wert (Soll)", 
            "root_juice_ml_l": "Root·Juice (ml/L)", "calmag_ml_l": "Calmag (ml/L)", 
            "bio_grow_ml_l": "Bio·Grow (ml/L)", "acti_alc_ml_l": "Acti·a•alc (ml/L)", 
            "bio_bloom_ml_l": "Bio·Bloom (ml/L)", "top_max_ml_l": "Top·Max (ml/L)", 
            "ph_wert_ziel": "pH-Wert (Ziel)"
        }
        
        plan_frame = tk.Frame(plan_window)
        plan_frame.pack(padx=10)

        for i, (key, label_text) in enumerate(fields_map.items()):
            tk.Label(plan_frame, text=f"{label_text}:", anchor='w').grid(row=i, column=0, padx=5, pady=2, sticky='w')
            entry = tk.Entry(plan_frame, width=20)
            entry.grid(row=i, column=1, padx=5, pady=2)
            plan_entries[key] = entry

        tk.Button(plan_window, text="Planung Speichern (SOLL)", 
                  command=lambda: self._save_plan_from_window(plan_window, entry_name, entry_woche, plan_entries), 
                  bg='blue', fg='white').pack(pady=15)
                  
        self._load_plan_in_window(entry_name, entry_woche, plan_entries)


    def _load_plan_in_window(self, entry_name, entry_woche, plan_entries):
        # ... (Methode ist unverändert)
        """Hilfsfunktion: Lädt Plan in die Felder des Planungsfensters."""
        try:
            plant_name = entry_name.get().strip()
            week = int(entry_woche.get())
        except:
            return 

        plan_values_tuple, plan_columns = get_pflanzen_plan(self.db_config, plant_name, week)
        
        for key, entry in plan_entries.items():
            entry.delete(0, tk.END)
            
            if plan_values_tuple and plan_columns:
                if key in plan_columns:
                    index = plan_columns.index(key)
                    value = plan_values_tuple[index]
                    
                    if value is not None:
                        if isinstance(value, float):
                            display_value = f"{value:.2f}"
                        else:
                            display_value = str(value)
                            
                        entry.insert(0, display_value)
                        
    def _save_plan_from_window(self, window, entry_name, entry_woche, plan_entries):
        # ... (Methode ist unverändert)
        """Speichert die Planungswerte aus dem Planungsfenster in die DB."""
        try:
            plant_name = entry_name.get().strip()
            week = int(entry_woche.get())
        except ValueError:
            messagebox.showerror("Eingabefehler", "Pflanzenname und Woche müssen gültig sein.")
            return

        if not plant_name or week <= 0:
             messagebox.showerror("Eingabefehler", "Pflanzenname und Woche dürfen nicht leer sein oder 0 sein.")
             return
             
        plan_list = [plant_name, week]
        # PLANNING_FIELDS enthält nun 'ec_wert'
        for key in PLANNING_FIELDS:
            try:
                value = plan_entries[key].get().replace(',', '.').strip()
                if value == "":
                    plan_list.append(None) 
                elif key in ["phase"]:
                    plan_list.append(value)
                elif key in ["lichtzyklus_h"]:
                    plan_list.append(int(value))
                else:
                    plan_list.append(float(value))
            except ValueError:
                messagebox.showerror("Eingabefehler", f"Bitte korrigieren Sie das Feld '{key}' (muss eine Zahl sein).")
                return

        planungsdatensatz = tuple(plan_list)

        cnx, result = get_db_connection(self.db_config)
        if cnx is None:
            messagebox.showerror("Verbindungsfehler", result)
            return

        cursor = cnx.cursor()
        success, message = setup_database_and_table(cursor, self.db_config['database'])
        cursor.close()
        
        if not success:
            messagebox.showerror("DB Setup Fehler", message)
            cnx.close()
            return
            
        success, message = save_pflanzen_plan(cnx, planungsdatensatz)
        
        cnx.close()
        
        if success:
            messagebox.showinfo("Erfolg", message)
            window.destroy()
            self._load_plan_for_current_inputs() 
        else:
            messagebox.showerror("Speicherfehler", message)

    # --- DATEN SPEICHERN LOGIK ---
    
    def save_data_to_db(self):
        # ... (Methode ist unverändert)
        """Sammelt und speichert Daten unter Verwendung von db_connector."""
        
        try:
            # Manuelles Datum prüfen
            log_date_str = self.entries['entry_datum'].get()
            datetime.strptime(log_date_str, "%Y-%m-%d") # Überprüft Format: JJJJ-MM-TT

            datensatz = (
                self.entries['entry_name'].get().strip(),
                int(self.entries['entry_woche'].get()),
                self.entries['entry_phase'].get().strip(),
                int(self.entries['entry_licht'].get()),
                float(self.entries['entry_root'].get() or 0.0),
                float(self.entries['entry_calmag'].get() or 0.0),
                float(self.entries['entry_grow'].get() or 0.0),
                float(self.entries['entry_acti'].get() or 0.0),
                float(self.entries['entry_bloom'].get() or 0.0),
                float(self.entries['entry_topmax'].get() or 0.0),
                float(self.entries['entry_ph'].get()),
                float(self.entries['entry_ec'].get()),
                log_date_str 
            )
        except ValueError as e:
            if "time data" in str(e):
                messagebox.showerror("Eingabefehler", "Datumsformat ist ungültig. Bitte verwenden Sie JJJJ-MM-TT (z.B. 2024-03-15).")
            else:
                messagebox.showerror("Eingabefehler", f"Bitte korrigieren Sie die numerischen Felder. (z.B. Woche, ml/L, pH-Wert, EC-Wert)")
            return

        if not datensatz[0].strip():
            messagebox.showerror("Eingabefehler", "Der Name der Pflanze darf nicht leer sein.")
            return

        cnx, result = get_db_connection(self.db_config)
        if cnx is None:
            messagebox.showerror("Verbindungsfehler", result)
            return

        cursor = cnx.cursor()
        success, message = setup_database_and_table(cursor, self.db_config['database'])
        cursor.close()
        
        if not success:
            messagebox.showerror("DB Setup Fehler", message)
            cnx.close()
            return
        
        success, message = insert_pflanzen_data(cnx, datensatz)
        
        if success:
            messagebox.showinfo("Speichern erfolgreich", message)
            # Felder löschen und neues heutiges Datum setzen
            for key in self.entries:
                if key != 'entry_datum':
                    self.entries[key].delete(0, tk.END)
                else:
                    self._set_today_date(self.entries[key])

            selected_tab_text = self.notebook.tab(self.notebook.select(), "text")
            if selected_tab_text == "📈 Daten anzeigen":
                self.load_data_into_treeview()
        else:
            messagebox.showerror("Speicherfehler", message)

        cnx.close()

    # --- DATEN ANZEIGE LOGIK ---

    def create_display_widgets(self, parent_frame):
        # ... (Methode ist unverändert)
        """Erstellt die Tabelle und die Steuerelemente für die Datenanzeige."""
        
        control_frame = tk.Frame(parent_frame)
        control_frame.pack(fill='x', padx=5, pady=5)

        # --- REFRESH EINSTELLUNGEN ---
        refresh_frame = tk.LabelFrame(control_frame, text="Aktualisierung", padx=10, pady=5)
        refresh_frame.pack(side=tk.LEFT, padx=10)

        tk.Checkbutton(refresh_frame, 
                       text="Automatischer Refresh aktiv", 
                       variable=self.is_auto_refresh_active, 
                       command=self._toggle_auto_refresh).grid(row=0, column=0, columnspan=2, sticky='w')

        tk.Label(refresh_frame, text="Intervall (Sekunden):").grid(row=1, column=0, sticky='w')
        vcmd = (self.register(lambda P: P.isdigit() or P == ""), '%P')
        entry_interval = tk.Entry(refresh_frame, textvariable=self.refresh_interval, width=5, validate='key', validatecommand=vcmd)
        entry_interval.grid(row=1, column=1, padx=5, sticky='w')
        
        # --- AKTION BUTTONS ---
        action_frame = tk.Frame(control_frame)
        action_frame.pack(side=tk.RIGHT, padx=10)

        tk.Button(action_frame, 
                  text="Daten aktualisieren", 
                  command=self.load_data_into_treeview).pack(side=tk.LEFT, padx=5)

        tk.Button(action_frame, 
                  text="Daten exportieren (CSV)", 
                  command=self.export_data_to_csv).pack(side=tk.LEFT, padx=5)
                  
        tk.Button(action_frame, 
                  text="Eintrag löschen", 
                  command=self._delete_selected_data, 
                  bg='red', 
                  fg='white').pack(side=tk.LEFT, padx=5)

        # --- DATEN TABELLE (Treeview) ---
        
        tree_frame = tk.Frame(parent_frame)
        tree_frame.pack(fill='both', expand=True, padx=5, pady=5)
        
        yscrollbar = ttk.Scrollbar(tree_frame, orient="vertical")
        yscrollbar.pack(side=tk.RIGHT, fill="y")
        
        xscrollbar = ttk.Scrollbar(tree_frame, orient="horizontal")
        xscrollbar.pack(side=tk.BOTTOM, fill="x")

        self.tree = ttk.Treeview(tree_frame, 
                                 yscrollcommand=yscrollbar.set, 
                                 xscrollcommand=xscrollbar.set,
                                 selectmode="browse")
        self.tree.pack(fill='both', expand=True)
        
        yscrollbar.config(command=self.tree.yview)
        xscrollbar.config(command=self.tree.xview)

    def load_data_into_treeview(self):
        # ... (Methode ist unverändert)
        """Holt die Daten aus der DB und füllt die Treeview."""
        data, columns_or_error = fetch_all_data(self.db_config)
        self.current_data_columns = columns_or_error if isinstance(columns_or_error, list) else None

        for item in self.tree.get_children():
            self.tree.delete(item)
            
        if data is None:
            messagebox.showerror("Datenbankfehler", columns_or_error)
            self.tree["columns"] = ("Status",)
            self.tree.heading("#0", text="", anchor='w')
            self.tree.heading("Status", text="Fehler beim Laden")
            self.tree.insert("", tk.END, values=(columns_or_error,))
            return

        if self.current_data_columns and data:
            self.tree["columns"] = self.current_data_columns
            self.tree.column("#0", width=0, stretch=tk.NO) 
            
            for col in self.current_data_columns:
                # Benutzerfreundliche Spaltenüberschriften
                display_col = col.replace('_', ' ').title().replace('Ml L', 'ml/L').replace('H', '(h)').replace('Ph Wert Ziel', 'pH-Wert (Ziel)').replace('Ec Wert', 'EC-Wert')
                self.tree.heading(col, text=display_col, anchor='w')
                if col in ('id', 'woche'):
                    self.tree.column(col, width=50, stretch=tk.NO)
                elif col == 'pflanzen_name':
                    self.tree.column(col, width=150)
                elif col == 'erstellungsdatum':
                    self.tree.column(col, width=150)
                elif col == 'ec_wert':
                    self.tree.column(col, width=70, anchor='center')
                else:
                    self.tree.column(col, width=100, anchor='center')

            for row in data:
                self.tree.insert("", tk.END, values=row)
            
            if not data:
                 self.tree.insert("", tk.END, values=("---", "Keine Daten gefunden. Speichern Sie Ihren ersten Eintrag!", "---", "---"))
        
        elif not data and columns_or_error:
            self.tree["columns"] = ("Meldung",)
            self.tree.heading("#0", text="", anchor='w')
            self.tree.heading("Meldung", text="Datenbank-Status")
            self.tree.insert("", tk.END, values=(columns_or_error,))
            
    def _delete_selected_data(self):
        # ... (Methode ist unverändert)
        """Löscht den in der Treeview ausgewählten Datensatz."""
        selected_item = self.tree.focus()
        if not selected_item:
            messagebox.showwarning("Aktion erforderlich", "Bitte wählen Sie einen Datensatz zum Löschen aus.")
            return

        values = self.tree.item(selected_item, 'values')
        if not values or len(values) == 0:
            return

        record_id = int(values[0])
        
        confirm = messagebox.askyesno(
            "Löschen bestätigen",
            f"Wollen Sie den Datensatz für ID: {record_id} ('{values[1]}') WIRKLICH löschen? Diese Aktion kann nicht rückgängig gemacht werden."
        )

        if confirm:
            success, message = delete_data_by_id(self.db_config, record_id)
            
            if success:
                messagebox.showinfo("Erfolg", message)
                self.load_data_into_treeview()
            else:
                messagebox.showerror("Fehler", message)
                
    def export_data_to_csv(self):
        # ... (Methode ist unverändert)
        """Exportiert die aktuell angezeigten Daten in eine CSV-Datei."""
        if not self.current_data_columns:
            messagebox.showwarning("Keine Daten", "Es sind keine Daten zum Exportieren verfügbar.")
            return
            
        filename = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV-Dateien", "*.csv")],
            initialfile=f"Pflanzenprotokoll_Export_{datetime.now().strftime('%Y%m%d')}.csv"
        )
        
        if not filename:
            return

        try:
            all_records = []
            for item in self.tree.get_children():
                values = self.tree.item(item, 'values')
                if isinstance(values, tuple) and len(values) > 4:
                    all_records.append(values)

            headers = [col.replace('_', ' ').title().replace('Ml L', 'ml/L').replace('H', '(h)').replace('Ph Wert Ziel', 'pH-Wert (Ziel)').replace('Ec Wert', 'EC-Wert') for col in self.current_data_columns]

            with open(filename, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f, delimiter=';')
                writer.writerow(headers)
                writer.writerows(all_records)

            messagebox.showinfo("Export erfolgreich", f"Daten erfolgreich exportiert nach:\n{filename}")
            
            if messagebox.askyesno("Datei öffnen", "Möchten Sie die exportierte Datei jetzt öffnen?"):
                if os.name == 'nt':
                    os.startfile(filename) 
                elif os.name == 'posix':
                    os.system(f'xdg-open "{filename}"') if 'Linux' in os.uname().sysname else os.system(f'open "{filename}"')
                
        except Exception as e:
            messagebox.showerror("Exportfehler", f"Fehler beim Exportieren der Daten: {e}")

    def _toggle_auto_refresh(self, start=False, stop=False):
        # ... (Methode ist unverändert)
        """Startet oder stoppt den automatischen Aktualisierungs-Loop."""
        
        if self.after_id is not None:
            self.after_cancel(self.after_id)
            self.after_id = None
            
        if (self.is_auto_refresh_active.get() or start) and not stop:
            try:
                interval_ms = max(1, self.refresh_interval.get()) * 1000
            except:
                interval_ms = 60000 
                self.refresh_interval.set(60)
                
            self.after_id = self.after(interval_ms, self._auto_refresh_loop)
            
    def _auto_refresh_loop(self):
        # ... (Methode ist unverändert)
        """Wird durch tk.after() periodisch aufgerufen."""
        if self.is_auto_refresh_active.get():
            self.load_data_into_treeview()
            self._toggle_auto_refresh(start=True)

    # --- EINSTELLUNGEN LOGIK ---

    def create_settings_tab(self, parent_frame):
        # ... (Methode ist unverändert)
        """Erstellt die Felder für die MySQL-Einstellungen und die Statusanzeige im 'Einstellungen'-Tab."""
        
        settings_frame = tk.Frame(parent_frame)
        settings_frame.pack(padx=10, pady=10)
        
        tk.Label(settings_frame, text="Datenbank-Verbindungsdaten:", font=('Arial', 10, 'bold')).grid(row=0, columnspan=2, pady=(10, 5), sticky='w')

        fields = ['Host', 'Port', 'Benutzer', 'Passwort', 'Datenbank']
        self.settings_entries = {}
        current_values = self.db_config
        
        for i, field in enumerate(fields):
            label = tk.Label(settings_frame, text=f"{field}:")
            label.grid(row=i+1, column=0, padx=5, pady=2, sticky='w')
            
            show_char = '*' if field == 'Passwort' else ''
            entry = tk.Entry(settings_frame, width=30, show=show_char)
            entry.grid(row=i+1, column=1, padx=5, pady=2)
            self.settings_entries[field] = entry
            
            key = field.lower().replace('ä', 'a').replace('ö', 'o').replace('ü', 'u')
            default_value = str(current_values.get('port', 3306)) if key == 'port' else current_values.get(key, '')
            entry.insert(0, default_value)
        
        # Speichern Button
        save_button = tk.Button(settings_frame, text="Einstellungen Speichern", command=self._save_db_settings)
        save_button.grid(row=len(fields)+1, column=0, pady=10, sticky='w')
        
        # Test Button
        test_button = tk.Button(settings_frame, text="Verbindung testen", command=self._test_connection)
        test_button.grid(row=len(fields)+1, column=1, pady=10, sticky='e')
        
        ttk.Separator(settings_frame, orient='horizontal').grid(row=len(fields)+2, columnspan=2, sticky='ew', pady=(15, 5))
        
        tk.Label(settings_frame, text="Aktueller Verbindungsstatus:", font=('Arial', 10, 'bold')).grid(row=len(fields)+3, columnspan=2, sticky='w')
        
        self.status_label_text = tk.StringVar(value="Status noch nicht geprüft.")
        self.status_label = tk.Label(settings_frame, textvariable=self.status_label_text, justify=tk.LEFT, fg='gray')
        self.status_label.grid(row=len(fields)+4, columnspan=2, sticky='w', padx=5)
        
        self._update_connection_status(self.db_config)
        
    def show_db_settings(self):
        # ... (Methode ist unverändert)
        """Navigiert bei Klick auf das obere Menü 'Datenbank' direkt zum Einstellungs-Tab."""
        self.notebook.select(self.tab_settings)
        messagebox.showinfo("Hinweis", "Sie wurden zum 'Einstellungen'-Tab weitergeleitet, um die MySQL-Daten zu überprüfen.")

    def _test_connection(self):
        # ... (Methode ist unverändert)
        """Ruft die Testfunktion des Connectors mit den aktuellen Werten auf."""
        self._save_db_settings(silent=True) 
        self._update_connection_status(self.db_config, show_message=True)

    def _update_connection_status(self, config_data, show_message=False):
        # ... (Methode ist unverändert)
        """Führt den Datenbanktest durch und aktualisiert das Status-Label."""
        
        is_successful, message = test_db_connection(config_data)
        
        if is_successful:
            color = 'green'
        elif "⚠️ Datenbank" in message: 
            color = 'orange'
        else:
            color = 'red'

        self.status_label.config(fg=color)
        self.status_label_text.set(message)
        
        if show_message:
            if is_successful:
                messagebox.showinfo("Verbindungstest", message)
            else:
                messagebox.showerror("Verbindungstest", message)

    def _save_db_settings(self, silent=False):
        # ... (Methode ist unverändert)
        """Speichert die Einstellungen aus dem Einstellungs-Tab und aktualisiert den Status."""
        try:
            port_value = int(self.settings_entries['Port'].get())
        except ValueError:
            messagebox.showerror("Eingabefehler", "Port muss eine gültige Zahl sein.")
            return

        new_settings = {
            'host': self.settings_entries['Host'].get(),
            'port': port_value,
            'user': self.settings_entries['Benutzer'].get(),
            'password': self.settings_entries['Passwort'].get(),
            'database': self.settings_entries['Datenbank'].get()
        }
        
        save_config(new_settings)
        self.db_config = new_settings
        
        self._update_connection_status(self.db_config)
        
        if not silent:
            messagebox.showinfo("Erfolg", "MySQL-Einstellungen gespeichert.")
    
if __name__ == '__main__':
    app = PflanzenApp()
    app.mainloop()