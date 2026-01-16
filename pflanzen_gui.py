# pflanzen_gui.py
# -*- coding: utf-8 -*-
import tkinter as tk
from tkinter import messagebox, ttk, filedialog
import csv 
import os 
from datetime import datetime
from PIL import Image, ImageTk  # Wichtig für das Logo

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
        
        # Automatische Maximierung des Fensters
        self._set_maximized_state() 
        
        self.db_config = load_config()
        
        self.is_auto_refresh_active = tk.BooleanVar(value=False)
        self.refresh_interval = tk.IntVar(value=60)
        self.after_id = None
        
        self.plan_labels = {} 
        self.current_data_columns = None 

        # --- LOGO INITIALISIERUNG ---
        self._setup_logo("diggerwf.jpeg")
        
        self.create_menu_bar()
        self.create_main_tabs()

    def _setup_logo(self, image_path):
        """Lädt das Bild, skaliert es und zeigt es oben an."""
        if os.path.exists(image_path):
            try:
                img = Image.open(image_path)
                # Skalierung: Höhe auf 100 Pixel fixieren, Breite proportional
                base_height = 100
                w_percent = (base_height / float(img.size[1]))
                w_size = int((float(img.size[0]) * float(w_percent)))
                img = img.resize((w_size, base_height), Image.Resampling.LANCZOS)
                
                self.logo_img = ImageTk.PhotoImage(img)
                self.logo_label = tk.Label(self, image=self.logo_img)
                self.logo_label.pack(pady=10) # Abstand um das Logo
            except Exception as e:
                print(f"Logo konnte nicht geladen werden: {e}")

    def __del__(self):
        """Stoppt den Auto-Refresh-Loop beim Schließen der App."""
        self._toggle_auto_refresh(stop=True)

    def _set_maximized_state(self):
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
        """Erstellt die obere Menüleiste."""
        menubar = tk.Menu(self)
        self.config(menu=menubar)
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Datei", menu=file_menu)
        file_menu.add_command(label="Beenden", command=self.quit)
        db_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Datenbank", menu=db_menu)
        db_menu.add_command(label="MySQL Einstellungen", command=self.show_db_settings)

    def create_main_tabs(self):
        """Erstellt das Hauptmenü (Tabs)."""
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(pady=10, padx=10, expand=True, fill="both")
        self.notebook.bind("<<NotebookTabChanged>>", self._handle_tab_change)

        self.tab_eingabe = tk.Frame(self.notebook, padx=10, pady=10)
        self.notebook.add(self.tab_eingabe, text="🌿 Daten eingeben")
        self.create_input_widgets(self.tab_eingabe)

        self.tab_anzeige = tk.Frame(self.notebook, padx=10, pady=10)
        self.notebook.add(self.tab_anzeige, text="📈 Daten anzeigen")
        self.create_display_widgets(self.tab_anzeige)
        
        self.tab_settings = tk.Frame(self.notebook, padx=10, pady=10)
        self.notebook.add(self.tab_settings, text="⚙️ Einstellungen")
        self.create_settings_tab(self.tab_settings)

    def _handle_tab_change(self, event):
        selected_tab = self.notebook.tab(self.notebook.select(), "text")
        if selected_tab == "📈 Daten anzeigen":
            self.load_data_into_treeview()
            self._toggle_auto_refresh(start=True)
        else:
            self._toggle_auto_refresh(stop=True)

    def create_input_widgets(self, parent_frame):
        main_frame = tk.Frame(parent_frame)
        main_frame.pack(padx=10, pady=10)

        input_frame = tk.LabelFrame(main_frame, text="Aktuelle Messwerte (Ist)", padx=10, pady=10)
        input_frame.grid(row=0, column=0, padx=10, pady=5, sticky='n')
        
        plan_display_frame = tk.LabelFrame(main_frame, text="Planung (Soll)", padx=10, pady=10)
        plan_display_frame.grid(row=0, column=1, padx=10, pady=5, sticky='n')

        self.fields = [
            ("Datum (JJJJ-MM-TT)", "entry_datum"),
            ("Name der Pflanze", "entry_name"),
            ("Woche", "entry_woche"),
            ("Phase", "entry_phase"),
            ("Lichtzyklus (h)", "entry_licht"), 
            ("Root·Juice (ml/L)", "entry_root"),
            ("Calmag (ml/L)", "entry_calmag"),
            ("Bio·Grow (ml/L)", "entry_grow"),
            ("Acti·a•alc (ml/L)", "entry_acti"),
            ("Bio·Bloom (ml/L)", "entry_bloom"),
            ("Top·Max (ml/L)", "entry_topmax"),
            ("pH-Wert (Ziel)", "entry_ph"),
            ("EC-Wert", "entry_ec")
        ]
        
        self.entries = {}
        plan_display_row = 0 
        
        for i, (label_text, key) in enumerate(self.fields):
            tk.Label(input_frame, text=f"{label_text}:").grid(row=i, column=0, padx=5, pady=2, sticky='w')
            
            if key == "entry_datum":
                date_frame = tk.Frame(input_frame)
                date_frame.grid(row=i, column=1, padx=5, pady=2, sticky='ew')
                entry = tk.Entry(date_frame, width=15)
                entry.pack(side=tk.LEFT, fill='x', expand=True)
                tk.Button(date_frame, text="📅", command=lambda: self._set_today_date(entry), width=3).pack(side=tk.LEFT, padx=(5, 0))
                self._set_today_date(entry)
            else:
                entry = tk.Entry(input_frame, width=25)
                entry.grid(row=i, column=1, padx=5, pady=2)

            self.entries[key] = entry
            
            if key in ["entry_name", "entry_woche"]:
                entry.bind("<FocusOut>", self._load_plan_for_current_inputs)
                entry.bind("<Return>", self._load_plan_for_current_inputs)
            
            if key not in ["entry_datum", "entry_name", "entry_woche"]: 
                plan_label = tk.Label(plan_display_frame, text="---", anchor='w', width=25)
                plan_label.grid(row=plan_display_row, column=0, padx=5, pady=2, sticky='w')
                self.plan_labels[key] = plan_label
                plan_display_row += 1

        tk.Button(input_frame, text="Daten Speichern (IST)", command=self.save_data_to_db, bg='green', fg='white').grid(row=len(self.fields), columnspan=2, pady=15)
        tk.Button(plan_display_frame, text="Planung Bearbeiten (SOLL)", command=self.open_plan_window, bg='orange', fg='white').grid(row=plan_display_row, columnspan=1, pady=15)

    def _set_today_date(self, entry_widget):
        today = datetime.now().strftime("%Y-%m-%d")
        entry_widget.delete(0, tk.END)
        entry_widget.insert(0, today)

    def _load_plan_for_current_inputs(self, event=None):
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
        plan_data = {}
        if plan_values_tuple and plan_columns:
            plan_data = dict(zip(plan_columns, plan_values_tuple))
            
        for ist_key in self.plan_labels.keys():
            db_key = ist_key.replace('entry_', '')
            if db_key in plan_data:
                value = plan_data[db_key]
                if isinstance(value, float) and value is not None:
                    display_value = f"({value:.2f} S/m)" if db_key == 'ec_wert' else f"{value:.2f}"
                elif value is None:
                    display_value = "---"
                else:
                    display_value = str(value)
            else:
                display_value = "---"
            self.plan_labels[ist_key].config(text=display_value)

    def open_plan_window(self):
        plan_window = tk.Toplevel(self)
        plan_window.title("Planung Speichern/Bearbeiten (SOLL)")
        
        try:
            initial_name = self.entries['entry_name'].get().strip()
            initial_woche = self.entries['entry_woche'].get().strip()
        except Exception:
            initial_name = ""; initial_woche = ""
            
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
        
        entry_name.bind("<FocusOut>", lambda e: self._load_plan_in_window(entry_name, entry_woche, plan_entries))
        entry_woche.bind("<FocusOut>", lambda e: self._load_plan_in_window(entry_name, entry_woche, plan_entries))

        tk.Label(plan_window, text="Planungswerte (SOLL):", font=('Arial', 10, 'bold')).pack(pady=(10, 0))
        
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
        try:
            plant_name = entry_name.get().strip()
            week = int(entry_woche.get())
        except: return 

        plan_values_tuple, plan_columns = get_pflanzen_plan(self.db_config, plant_name, week)
        for key, entry in plan_entries.items():
            entry.delete(0, tk.END)
            if plan_values_tuple and plan_columns:
                if key in plan_columns:
                    index = plan_columns.index(key)
                    value = plan_values_tuple[index]
                    if value is not None:
                        entry.insert(0, f"{value:.2f}" if isinstance(value, float) else str(value))
                        
    def _save_plan_from_window(self, window, entry_name, entry_woche, plan_entries):
        try:
            plant_name = entry_name.get().strip()
            week = int(entry_woche.get())
        except ValueError:
            messagebox.showerror("Eingabefehler", "Pflanzenname und Woche müssen gültig sein.")
            return

        plan_list = [plant_name, week]
        for key in PLANNING_FIELDS:
            try:
                value = plan_entries[key].get().replace(',', '.').strip()
                if value == "": plan_list.append(None) 
                elif key == "phase": plan_list.append(value)
                elif key == "lichtzyklus_h": plan_list.append(int(value))
                else: plan_list.append(float(value))
            except ValueError:
                messagebox.showerror("Eingabefehler", f"Feld '{key}' muss eine Zahl sein.")
                return

        cnx, result = get_db_connection(self.db_config)
        if cnx is None:
            messagebox.showerror("Verbindungsfehler", result); return

        cursor = cnx.cursor()
        setup_database_and_table(cursor, self.db_config['database'])
        cursor.close()
        success, message = save_pflanzen_plan(cnx, tuple(plan_list))
        cnx.close()
        
        if success:
            messagebox.showinfo("Erfolg", message); window.destroy(); self._load_plan_for_current_inputs() 
        else:
            messagebox.showerror("Speicherfehler", message)

    def save_data_to_db(self):
        try:
            log_date_str = self.entries['entry_datum'].get()
            datetime.strptime(log_date_str, "%Y-%m-%d")
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
        except ValueError:
            messagebox.showerror("Eingabefehler", "Bitte korrigieren Sie die numerischen Felder und das Datum.")
            return

        cnx, result = get_db_connection(self.db_config)
        if cnx:
            cursor = cnx.cursor()
            setup_database_and_table(cursor, self.db_config['database'])
            cursor.close()
            success, message = insert_pflanzen_data(cnx, datensatz)
            cnx.close()
            if success:
                messagebox.showinfo("Erfolg", message)
                for key in self.entries:
                    if key != 'entry_datum': self.entries[key].delete(0, tk.END)
                    else: self._set_today_date(self.entries[key])
                if self.notebook.tab(self.notebook.select(), "text") == "📈 Daten anzeigen": self.load_data_into_treeview()
            else: messagebox.showerror("Speicherfehler", message)

    def create_display_widgets(self, parent_frame):
        control_frame = tk.Frame(parent_frame)
        control_frame.pack(fill='x', padx=5, pady=5)
        refresh_frame = tk.LabelFrame(control_frame, text="Aktualisierung", padx=10, pady=5)
        refresh_frame.pack(side=tk.LEFT, padx=10)
        tk.Checkbutton(refresh_frame, text="Auto-Refresh", variable=self.is_auto_refresh_active, command=self._toggle_auto_refresh).grid(row=0, column=0, columnspan=2)
        tk.Entry(refresh_frame, textvariable=self.refresh_interval, width=5).grid(row=1, column=1)
        
        action_frame = tk.Frame(control_frame)
        action_frame.pack(side=tk.RIGHT, padx=10)
        tk.Button(action_frame, text="Refresh", command=self.load_data_into_treeview).pack(side=tk.LEFT, padx=5)
        tk.Button(action_frame, text="Export CSV", command=self.export_data_to_csv).pack(side=tk.LEFT, padx=5)
        tk.Button(action_frame, text="Löschen", command=self._delete_selected_data, bg='red', fg='white').pack(side=tk.LEFT, padx=5)

        tree_frame = tk.Frame(parent_frame)
        tree_frame.pack(fill='both', expand=True)
        self.tree = ttk.Treeview(tree_frame, selectmode="browse")
        self.tree.pack(side=tk.LEFT, fill='both', expand=True)
        sb = ttk.Scrollbar(tree_frame, orient="vertical", command=self.tree.yview)
        sb.pack(side=tk.RIGHT, fill='y')
        self.tree.configure(yscrollcommand=sb.set)

    def load_data_into_treeview(self):
        data, columns_or_error = fetch_all_data(self.db_config)
        for item in self.tree.get_children(): self.tree.delete(item)
        if data is not None:
            self.tree["columns"] = columns_or_error
            self.tree.column("#0", width=0, stretch=tk.NO)
            for col in columns_or_error:
                self.tree.heading(col, text=col.replace('_', ' ').title())
                self.tree.column(col, width=100)
            for row in data: self.tree.insert("", tk.END, values=row)

    def _delete_selected_data(self):
        selected = self.tree.focus()
        if selected:
            val = self.tree.item(selected, 'values')
            if messagebox.askyesno("Löschen", f"ID {val[0]} wirklich löschen?"):
                delete_data_by_id(self.db_config, int(val[0]))
                self.load_data_into_treeview()

    def export_data_to_csv(self):
        filename = filedialog.asksaveasfilename(defaultextension=".csv")
        if filename:
            try:
                with open(filename, 'w', newline='', encoding='utf-8') as f:
                    writer = csv.writer(f, delimiter=';')
                    writer.writerow(self.tree["columns"])
                    for item in self.tree.get_children(): writer.writerow(self.tree.item(item, 'values'))
                messagebox.showinfo("Export", "Erfolgreich!")
            except Exception as e: messagebox.showerror("Fehler", str(e))

    def _toggle_auto_refresh(self, start=False, stop=False):
        if self.after_id: self.after_cancel(self.after_id); self.after_id = None
        if (self.is_auto_refresh_active.get() or start) and not stop:
            self.after_id = self.after(self.refresh_interval.get() * 1000, self._auto_refresh_loop)
            
    def _auto_refresh_loop(self):
        if self.is_auto_refresh_active.get(): self.load_data_into_treeview(); self._toggle_auto_refresh(start=True)

    def create_settings_tab(self, parent_frame):
        sf = tk.Frame(parent_frame); sf.pack(padx=10, pady=10)
        self.settings_entries = {}
        for i, field in enumerate(['Host', 'Port', 'Benutzer', 'Password', 'Database']):
            tk.Label(sf, text=f"{field}:").grid(row=i, column=0, sticky='w')
            e = tk.Entry(sf, width=30, show='*' if field == 'Password' else '')
            e.grid(row=i, column=1)
            self.settings_entries[field] = e
            key = field.lower().replace('benutzer', 'user')
            e.insert(0, str(self.db_config.get(key, '')))
        
        tk.Button(sf, text="Speichern", command=self._save_db_settings).grid(row=5, column=0)
        tk.Button(sf, text="Testen", command=self._test_connection).grid(row=5, column=1)
        self.status_label = tk.Label(sf, text="Status: Unbekannt"); self.status_label.grid(row=6, columnspan=2)

    def _test_connection(self):
        ok, msg = test_db_connection(self.db_config)
        self.status_label.config(text=msg, fg='green' if ok else 'red')

    def _save_db_settings(self):
        new_conf = {k.lower().replace('benutzer', 'user'): v.get() for k, v in self.settings_entries.items()}
        new_conf['port'] = int(new_conf['port'])
        save_config(new_conf); self.db_config = new_conf; self._test_connection()

    def show_db_settings(self): self.notebook.select(self.tab_settings)

if __name__ == '__main__':
    app = PflanzenApp()
    app.mainloop()