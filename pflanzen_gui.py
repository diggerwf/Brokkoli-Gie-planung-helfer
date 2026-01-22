# pflanzen_gui.py
# -*- coding: utf-8 -*-
import tkinter as tk
from tkinter import messagebox, ttk, filedialog
import csv 
import os 
import platform  
import subprocess 
import sys
import pandas as pd
from datetime import datetime
from PIL import Image, ImageTk

# Importiere die Logik aus den Begleitdateien
from db_connector import (
    get_db_connection, 
    setup_database_and_table, 
    insert_pflanzen_data, 
    test_db_connection, 
    fetch_all_data, 
    delete_data_by_id, 
    save_pflanzen_plan, 
    get_pflanzen_plan
)
from config_manager import load_config, save_config

# Definierte Reihenfolge der Nährstofffelder (muss mit DB übereinstimmen)
PLANNING_FIELDS = [
    "phase", "lichtzyklus_h", "root_juice_ml_l", "calmag_ml_l", 
    "bio_grow_ml_l", "fish_mix_ml_l", "bio_heaven_ml_l", "acti_alc_ml_l", 
    "bio_bloom_ml_l", "top_max_ml_l", "ph_wert_ziel", "ec_wert"
]

# Optionen für Dropdowns
FIELD_OPTIONS = {
    "entry_phase": ["Anzucht", "Wachstum", "Blüte", "Spülen"],
    "phase": ["Anzucht", "Wachstum", "Blüte", "Spülen"]
}

class PflanzenApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("🌱 Pflanzenprotokoll Pro - Biobizz Edition")
        
        # Fenster maximieren
        self._set_maximized_state() 
        
        # Konfiguration laden
        self.db_config = load_config()
        
        # Initialisiere DB-Struktur beim Start
        self._initialize_db_structure()

        # Variablen für Steuerung
        self.is_auto_refresh_active = tk.BooleanVar(value=False)
        self.refresh_interval = tk.IntVar(value=60)
        self.after_id = None
        self.plan_labels = {}
        # Wichtig: Referenzen speichern, damit der Garbage Collector Bilder nicht löscht
        self.image_refs = [] 

        # Logo laden
        self._setup_logo("diggerwf.jpeg")

        # GUI-Komponenten aufbauen
        self.create_menu_bar()
        self.create_main_tabs()
        
        # Initialer Refresh der Plan-Liste im Dropdown
        self._refresh_plan_list()

    def __del__(self):
        """Stoppt Timer beim Beenden."""
        self._toggle_auto_refresh(stop=True)

    def _set_maximized_state(self):
        """Setzt das Fenster auf Vollbild je nach Betriebssystem."""
        if os.name == 'nt': 
            try: self.state('zoomed')
            except: self.attributes('-fullscreen', True)
        else:
            try: self.attributes('-zoomed', True)
            except: self.geometry("1200x800")

    def _initialize_db_structure(self):
        """Erstellt Datenbank und Tabellen, falls nicht vorhanden."""
        try:
            cnx, cursor = get_db_connection(self.db_config)
            if cnx:
                setup_database_and_table(cursor, self.db_config['database'])
                cnx.close()
        except Exception as e:
            print(f"DB-Fehler beim Start: {e}")

    def _setup_logo(self, image_path):
        """Lädt das Header-Logo."""
        if os.path.exists(image_path):
            try:
                img = Image.open(image_path)
                img = img.resize((150, 100), Image.Resampling.LANCZOS)
                self.logo_img = ImageTk.PhotoImage(img)
                tk.Label(self, image=self.logo_img).pack(pady=5)
            except: pass

    def create_menu_bar(self):
        menubar = tk.Menu(self)
        self.config(menu=menubar)
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Datei", menu=file_menu)
        file_menu.add_command(label="Beenden", command=self.quit)
        db_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Datenbank", menu=db_menu)
        db_menu.add_command(label="MySQL Einstellungen", command=self.show_db_settings)

    def create_main_tabs(self):
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(pady=10, padx=10, expand=True, fill="both")
        
        # TAB 0: INFO & GUIDE (Indoor / Outdoor / Substrate)
        self.tab_info = tk.Frame(self.notebook, padx=10, pady=10)
        self.notebook.add(self.tab_info, text="ℹ️ Info & Guide")
        self.create_info_tab_content(self.tab_info)

        # TAB 1: EINGABE
        self.tab_eingabe = tk.Frame(self.notebook, padx=10, pady=10)
        self.notebook.add(self.tab_eingabe, text="🌿 Daten eingeben")
        self.create_input_widgets(self.tab_eingabe)

        # TAB 2: ANZEIGE
        self.tab_anzeige = tk.Frame(self.notebook, padx=10, pady=10)
        self.notebook.add(self.tab_anzeige, text="📈 Daten anzeigen")
        self.create_display_widgets(self.tab_anzeige)

        # TAB 3: SETTINGS
        self.tab_settings = tk.Frame(self.notebook, padx=10, pady=10)
        self.notebook.add(self.tab_settings, text="⚙️ Einstellungen")
        self.create_settings_tab(self.tab_settings)
        
        # TAB 4: UPDATE
        self.tab_update = tk.Frame(self.notebook, padx=10, pady=10)
        self.notebook.add(self.tab_update, text="🔄 Update")
        self.create_update_tab(self.tab_update)

        self.notebook.bind("<<NotebookTabChanged>>", self._handle_tab_change)

    def create_info_tab_content(self, parent_frame):
        """Erstellt den Guide mit Indoor, Outdoor, Substraten und Düngeschema."""
        info_nb = ttk.Notebook(parent_frame)
        info_nb.pack(fill="both", expand=True)

        indoor_data = [
            ("Root·Juice", "Wurzelstimulator für explosive Bewurzelung bei jungen Pflanzen.", "1-4 ml/L. In den ersten 1-2 Wochen.", "Root-Juice.jpg"),
            ("Bio·Grow", "Flüssiger Wachstumsdünger. Aktiviert die Bakterienflora im Substrat.", "1-4 ml/L. Bei jedem Gießen.", "Bio-Grow.jpg"),
            ("Bio·Bloom", "Volldünger für die Blütephase. Enthält N-P-K.", "1-4 ml/L. Ab Blütebeginn.", "Bio-Bloom.jpg"),
            ("Top·Max", "Blütenstimulator. Erhöht Gewicht und Größe.", "1-4 ml/L. Blütephase.", "Top-Max.jpg"),
            ("Bio·Heaven", "Energie-Booster. Verbessert die Nährstoffaufnahme.", "2-5 ml/L. Gesamter Zyklus.", "Bio-Heaven.jpg"),
            ("Acti·Vera", "Pflanzenaktivator auf Aloe Vera Basis. Stärkt das Immunsystem.", "5 ml/L. Gießen oder als Blattspray.", "Acti-Vera.jpg"),
            ("Alg·A·Mic", "Vitalitäts-Booster aus Meeresalgen. Hilft bei Stress und Mangel.", "1-4 ml/L. Zur Erholung und Vorbeugung.", "Alg-A-Mic.jpg"),
            ("CALMAG", "Schutz vor Calcium- und Magnesiummängeln, besonders wichtig bei weichem Wasser oder Umkehrosmose.", "0.3 - 1 ml/L.", "calmagic.jpg"),
            ("Bio·Up", "Organischer pH-Regulator auf Huminsäurebasis. Erhöht den pH-Wert schonend, ohne das Bodenleben zu schädigen.", "0,1 ml/L hebt den pH-Wert um ca. 0,1 Punkte. Nach Bedarf anpassen.", "PH+.jpg"),
            ("Bio·Down", "Organischer pH-Senker auf Zitronensäurebasis. Senkt den pH-Wert schnell und effektiv, ohne die Mikroorganismen im Substrat zu beeinträchtigen.", "0,1 ml/L senkt den pH-Wert um ca. 0,1 Punkte. Schrittweise dosieren.", "ph-.jpg")
        ]

        outdoor_data = [
            ("Root·Juice", "Wurzelstimulator für explosive Bewurzelung bei jungen Pflanzen.", "1-4 ml/L. In den ersten 1-2 Wochen.", "Root-Juice.jpg"),
            ("Fish·Mix", "Outdoor-Spezialist. Konditioniert das Substrat und fördert Mikroorganismen.", "1-4 ml/L. Ersetzt Bio·Grow im Freiland.", "Fish-Mix.jpg"),
            ("Bio·Bloom", "Volldünger für die Blütephase. Enthält N-P-K.", "1-4 ml/L. Ab Blütebeginn.", "Bio-Bloom.jpg"),
            ("Top·Max", "Blütenstimulator. Erhöht Gewicht und Größe.", "1-4 ml/L. Blütephase.", "Top-Max.jpg"),
            ("Bio·Heaven", "Energie-Booster. Verbessert die Nährstoffaufnahme.", "2-5 ml/L. Gesamter Zyklus.", "Bio-Heaven.jpg"),
            ("Acti·Vera", "Pflanzenaktivator auf Aloe Vera Basis. Stärkt das Immunsystem.", "5 ml/L. Gießen oder als Blattspray.", "Acti-Vera.jpg"),
            ("Alg·A·Mic", "Vitalitäts-Booster aus Meeresalgen. Hilft bei Stress und Mangel.", "1-4 ml/L. Zur Erholung und Vorbeugung.", "Alg-A-Mic.jpg"),
            ("CALMAG", "Schutz vor Calcium- und Magnesiummängeln, besonders wichtig bei weichem Wasser oder Umkehrosmose.", "0.3 - 1 ml/L.", "calmagic.jpg"),
            ("Bio·Up", "Organischer pH-Regulator auf Huminsäurebasis. Erhöht den pH-Wert schonend, ohne das Bodenleben zu schädigen.", "0,1 ml/L hebt den pH-Wert um ca. 0,1 Punkte. Nach Bedarf anpassen.", "PH+.jpg"),
            ("Bio·Down", "Organischer pH-Senker auf Zitronensäurebasis. Senkt den pH-Wert schnell und effektiv, ohne die Mikroorganismen im Substrat zu beeinträchtigen.", "0,1 ml/L senkt den pH-Wert um ca. 0,1 Punkte. Schrittweise dosieren.", "ph-.jpg")
        ]

        substrate_data = [
            ("Light·Mix", "Leicht vorgedüngtes Substrat. Volle Kontrolle über die Düngung.", "Düngen ab der ersten Woche möglich.", "Light-Mix.jpg"),
            ("All·Mix", "Stark vorgedüngtes Substrat. Hoher Puffergehalt.", "Düngen meist erst nach 2-3 Wochen nötig.", "All-Mix.jpg"),
            ("Coco·Mix", "Kokosfaser-Substrat für optimale Belüftung der Wurzeln.", "Behandlung ähnlich wie Light·Mix, CalMag beachten.", "coco-mix.jpg")
        ]

        # Registerkarten erstellen
        in_frame = self._create_scrollable_frame(info_nb, "🏠 Indoor Guide")
        self._add_guide_section(in_frame, "Indoor Tipps", "Optimale Bedingungen: Lichtzyklus 18/6 (Vegi) oder 12/12 (Blüte). pH-Bereich: 6.2 - 6.5.")
        for name, desc, app, img in indoor_data:
            self._add_duenger_entry(in_frame, name, desc, app, img)

        out_frame = self._create_scrollable_frame(info_nb, "☀️ Outdoor Guide")
        self._add_guide_section(out_frame, "Outdoor Tipps", "Draußen ist Fish·Mix die beste Wahl als Basisdünger. Schützt Pflanzen vor extremen Wettereinflüssen mit Alg·A·Mic.")
        for name, desc, app, img in outdoor_data:
            self._add_duenger_entry(out_frame, name, desc, app, img)

        sub_frame = self._create_scrollable_frame(info_nb, "🌍 Substrate")
        self._add_guide_section(sub_frame, "Das richtige Medium", "Wähle dein Substrat passend zu deinem Dünge-Stil. All·Mix verzeiht mehr Fehler, Light·Mix erlaubt präzise Steuerung.")
        for name, desc, app, img in substrate_data:
            self._add_duenger_entry(sub_frame, name, desc, app, img)

        # NEUER UNTERREITER: Düngeschema aus PDF integriert
        schema_frame = self._create_scrollable_frame(info_nb, "📊 Düngeschema")
        self._add_guide_section(schema_frame, "Biobizz Düngeschema 2020", 
                                "Befolgen Sie dieses Schema basierend auf Ihrem Substrat. "
                                "Ideal ist ein pH-Wert zwischen 6.2 und 6.5. 2-3 mal pro Woche wässern.")
        
        # Tabelle ALL-MIX
        self._add_schema_table(schema_frame, "Schema für ALL-MIX", [
            ("Produkt (ml/L)", "WK 1", "WK 2", "WK 3", "WK 4", "WK 5", "WK 6", "WK 7", "WK 8", "WK 9", "WK 10", "WK 11", "WK 12"),
            ("Phasen", "Wuchs", "Wuchs", "Blüte", "Blüte", "Blüte", "Blüte", "Blüte", "Blüte", "Blüte", "Blüte", "Spülen", "Ernte"),
            ("Root·Juice", "4", "-", "-", "-", "-", "-", "-", "-", "-", "-", "-", "-"),
            ("Bio·Grow", "-", "1", "1", "1", "1", "1", "1", "1", "1", "1", "-", "-"),
            ("Fish Mix", "-", "1", "1", "1", "1", "1", "1", "1", "1", "1", "-", "-"),
            ("Bio·Bloom", "-", "-", "1", "2", "2", "3", "3", "4", "4", "4", "-", "-"),
            ("Top·Max", "-", "-", "1", "1", "1", "1", "1", "4", "4", "4", "-", "-"),
            ("Bio·Heaven", "2", "2", "2", "2", "3", "4", "4", "5", "5", "5", "-", "-"),
            ("Acti·Vera", "2", "2", "2", "2", "3", "4", "4", "5", "5", "5", "-", "-")
        ])

        # Tabelle LIGHT-MIX / COCO-MIX
        self._add_schema_table(schema_frame, "Schema für LIGHT-MIX / COCO-MIX", [
            ("Produkt (ml/L)", "WK 1", "WK 2", "WK 3", "WK 4", "WK 5", "WK 6", "WK 7", "WK 8", "WK 9", "WK 10", "WK 11", "WK 12"),
            ("Phasen", "Wuchs", "Wuchs", "Blüte", "Blüte", "Blüte", "Blüte", "Blüte", "Blüte", "Blüte", "Blüte", "Spülen", "Ernte"),
            ("Root·Juice", "4", "-", "-", "-", "-", "-", "-", "-", "-", "-", "-", "-"),
            ("Bio·Grow", "-", "2", "2", "2", "3", "3", "4", "4", "4", "4", "-", "-"),
            ("Fish Mix", "-", "1", "1", "1", "1", "1", "1", "1", "1", "1", "-", "-"),
            ("Bio·Bloom", "-", "-", "1", "2", "2", "3", "3", "4", "4", "4", "-", "-"),
            ("Top·Max", "-", "-", "1", "1", "1", "1", "1", "4", "4", "4", "-", "-"),
            ("Bio·Heaven", "2", "2", "2", "2", "3", "4", "4", "5", "5", "5", "-", "-"),
            ("Acti·A·MIC", "-", "-", "1", "2", "2", "3", "3", "4", "4", "4", "-", "-"),
            ("Acti·Vera", "2", "2", "2", "2", "3", "4", "4", "5", "5", "5", "-", "-")
        ])

    def _add_schema_table(self, parent, title, rows):
        """Erstellt eine formatiert Tabelle für das Düngeschema."""
        frame = tk.LabelFrame(parent, text=f" {title} ", font=('Arial', 10, 'bold'), padx=5, pady=5)
        frame.pack(fill="x", padx=10, pady=10)
        
        for r_idx, row_data in enumerate(rows):
            for c_idx, cell_text in enumerate(row_data):
                bg_color = "#e0e0e0" if r_idx == 0 else "white"
                weight = "bold" if r_idx == 0 or c_idx == 0 else "normal"
                lbl = tk.Label(frame, text=cell_text, font=('Arial', 8, weight), 
                               relief="groove", width=8, bg=bg_color, padx=2)
                lbl.grid(row=r_idx, column=c_idx, sticky="nsew")

    def _create_scrollable_frame(self, notebook, title):
        frame = tk.Frame(notebook)
        notebook.add(frame, text=title)
        canvas = tk.Canvas(frame, highlightthickness=0)
        vsb = ttk.Scrollbar(frame, orient="vertical", command=canvas.yview)
        scroll_f = tk.Frame(canvas)
        
        scroll_f.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=scroll_f, anchor="nw")
        canvas.configure(yscrollcommand=vsb.set)
        
        def _on_mousewheel(event):
            if event.num == 4 or event.delta > 0:
                canvas.yview_scroll(-1, "units")
            elif event.num == 5 or event.delta < 0:
                canvas.yview_scroll(1, "units")

        canvas.bind_all("<MouseWheel>", _on_mousewheel)
        canvas.bind_all("<Button-4>", _on_mousewheel)
        canvas.bind_all("<Button-5>", _on_mousewheel)

        canvas.pack(side="left", fill="both", expand=True)
        vsb.pack(side="right", fill="y")
        return scroll_f

    def _add_duenger_entry(self, parent, name, desc, app, img_name):
        f = tk.Frame(parent, pady=10, padx=5)
        f.pack(fill="x", expand=True)
        img_path = os.path.join("biobizz", img_name)
        if os.path.exists(img_path):
            try:
                img_obj = Image.open(img_path)
                img_obj.thumbnail((100, 100))
                photo = ImageTk.PhotoImage(img_obj)
                self.image_refs.append(photo)
                tk.Label(f, image=photo).grid(row=0, column=0, rowspan=4, padx=15)
            except: 
                tk.Label(f, text="[Bild Fehler]").grid(row=0, column=0, rowspan=4)
        else:
            tk.Label(f, text="[Kein Bild]").grid(row=0, column=0, rowspan=4)

        tk.Label(f, text=name, font=("Arial", 12, "bold")).grid(row=0, column=1, sticky="w")
        tk.Label(f, text=desc, wraplength=500, justify="left").grid(row=1, column=1, sticky="w")
        tk.Label(f, text=f"Anwendung: {app}", fg="#2E7D32", font=("Arial", 10, "italic")).grid(row=2, column=1, sticky="w")
        ttk.Separator(parent, orient="horizontal").pack(fill="x", padx=10, pady=5)

    def _add_guide_section(self, parent, title, text):
        f = tk.LabelFrame(parent, text=f" {title} ", font=('Arial', 11, 'bold'), padx=10, pady=10, bg="#f0f0f0")
        f.pack(fill="x", padx=10, pady=10)
        tk.Label(f, text=text, wraplength=600, justify="left", bg="#f0f0f0").pack(anchor="w")

    def create_input_widgets(self, parent_frame):
        main_f = tk.Frame(parent_frame)
        main_f.pack(padx=10, pady=10)

        input_frame = tk.LabelFrame(main_f, text="Aktuelle Messwerte (Ist)", padx=10, pady=10)
        input_frame.grid(row=0, column=0, padx=10, pady=5, sticky='n')

        plan_display_frame = tk.LabelFrame(main_f, text="Planung (Soll-Vorgabe)", padx=10, pady=10)
        plan_display_frame.grid(row=0, column=1, padx=10, pady=5, sticky='n')

        tk.Label(plan_display_frame, text="Plan laden:", font=('Arial', 8, 'bold')).grid(row=0, column=0, sticky='w')
        self.plan_auswahl_combobox = ttk.Combobox(plan_display_frame, state="readonly", width=25)
        self.plan_auswahl_combobox.grid(row=1, column=0, pady=(0, 5))
        self.plan_auswahl_combobox.bind("<<ComboboxSelected>>", self._on_plan_dropdown_select)

        tk.Label(plan_display_frame, text="Woche wählen:", font=('Arial', 8, 'bold')).grid(row=2, column=0, sticky='w')
        self.wochen_auswahl_combobox = ttk.Combobox(plan_display_frame, state="readonly", width=25)
        self.wochen_auswahl_combobox.grid(row=3, column=0, pady=(0, 10))
        self.wochen_auswahl_combobox.bind("<<ComboboxSelected>>", self._on_week_dropdown_select)

        self.fields = [
            ("Datum (JJJJ-MM-TT)", "entry_datum"), ("Name der Pflanze", "entry_name"),
            ("Woche", "entry_woche"), ("Phase", "entry_phase"), ("Lichtzyklus (h)", "entry_licht"),
            ("Root·Juice (ml/L)", "entry_root"), ("Calmag (ml/L)", "entry_calmag"),
            ("Bio·Grow (ml/L)", "entry_grow"), ("Fish·Mix (ml/L)", "entry_fish"),
            ("Bio·Heaven (ml/L)", "entry_heaven"), ("Acti·a•alc (ml/L)", "entry_acti"),
            ("Bio·Bloom (ml/L)", "entry_bloom"), ("Top·Max (ml/L)", "entry_topmax"),
            ("pH-Wert (Ziel)", "entry_ph"), ("EC-Wert", "entry_ec")
        ]
        
        self.entries = {}
        plan_display_row = 4
        for i, (label_text, key) in enumerate(self.fields):
            tk.Label(input_frame, text=f"{label_text}:").grid(row=i, column=0, padx=5, pady=2, sticky='w')
            if key == "entry_datum":
                date_frame = tk.Frame(input_frame)
                date_frame.grid(row=i, column=1, sticky='ew')
                entry = tk.Entry(date_frame, width=15)
                entry.pack(side=tk.LEFT, fill='x', expand=True)
                tk.Button(date_frame, text="📅", command=lambda e=entry: self._set_today_date(e), width=3).pack(side=tk.LEFT)
                self._set_today_date(entry)
            elif key in FIELD_OPTIONS:
                entry = ttk.Combobox(input_frame, values=FIELD_OPTIONS[key], state="readonly", width=23)
                entry.grid(row=i, column=1)
                entry.current(0)
            else:
                entry = tk.Entry(input_frame, width=25)
                entry.grid(row=i, column=1)
            self.entries[key] = entry
            if key in ["entry_name", "entry_woche"]:
                entry.bind("<KeyRelease>", self._load_plan_for_current_inputs)
            if key not in ["entry_datum", "entry_name", "entry_woche"]:
                row_f = tk.Frame(plan_display_frame)
                row_f.grid(row=plan_display_row, column=0, sticky='w', pady=2)
                tk.Label(row_f, text=f"{label_text}:", font=('Arial', 8), width=18, anchor='w').pack(side=tk.LEFT)
                l = tk.Label(row_f, text="---", anchor='w', font=('Arial', 10, 'bold'), width=10)
                l.pack(side=tk.LEFT)
                self.plan_labels[gui if 'gui' in locals() else key] = l
                plan_display_row += 1

        tk.Button(input_frame, text="Daten Speichern (IST)", command=self.save_data_to_db, bg='green', fg='white', font=('Arial', 10, 'bold')).grid(row=len(self.fields), columnspan=2, pady=15)
        bp_f = tk.Frame(plan_display_frame)
        bp_f.grid(row=plan_display_row, column=0, pady=15)
        tk.Button(bp_f, text="Planung Bearbeiten (SOLL)", command=self.open_plan_window, bg='orange', fg='white', font=('Arial', 9, 'bold')).pack(side=tk.LEFT, padx=5)
        tk.Button(bp_f, text="Planung Löschen", command=self._delete_plan_logic, bg='red', fg='white', font=('Arial', 9)).pack(side=tk.LEFT, padx=5)

    def _refresh_plan_list(self):
        try:
            cnx, _ = get_db_connection(self.db_config)
            if cnx:
                cursor = cnx.cursor()
                cursor.execute(f"USE {self.db_config['database']}")
                cursor.execute("SELECT DISTINCT pflanzen_name FROM pflanzenplanung ORDER BY pflanzen_name ASC")
                names = [row[0] for row in cursor.fetchall()]
                self.plan_auswahl_combobox['values'] = names
                cursor.close(); cnx.close()
        except: pass

    def _on_plan_dropdown_select(self, event):
        name = self.plan_auswahl_combobox.get()
        akt_w = self.wochen_auswahl_combobox.get()
        if name:
            self.entries['entry_name'].delete(0, tk.END)
            self.entries['entry_name'].insert(0, name)
            try:
                cnx, _ = get_db_connection(self.db_config)
                if cnx:
                    cursor = cnx.cursor()
                    cursor.execute(f"USE {self.db_config['database']}")
                    cursor.execute("SELECT woche FROM pflanzenplanung WHERE pflanzen_name = %s ORDER BY woche ASC", (name,))
                    weeks = [row[0] for row in cursor.fetchall()]
                    self.wochen_auswahl_combobox['values'] = weeks
                    if weeks:
                        if akt_w in [str(w) for w in weeks]: self.wochen_auswahl_combobox.set(akt_w)
                        else: self.wochen_auswahl_combobox.current(0)
                        self._on_week_dropdown_select(None)
                    cursor.close(); cnx.close()
            except: pass

    def _on_week_dropdown_select(self, event):
        w = self.wochen_auswahl_combobox.get()
        if w:
            self.entries['entry_woche'].delete(0, tk.END)
            self.entries['entry_woche'].insert(0, w)
            self._load_plan_for_current_inputs()

    def _delete_plan_logic(self):
        name = self.plan_auswahl_combobox.get()
        if not name: messagebox.showwarning("Hinweis", "Bitte wählen Sie erst einen Plan aus."); return
        if messagebox.askyesno("Löschen", f"Möchten Sie den Plan für '{name}' wirklich löschen?"):
            try:
                cnx, _ = get_db_connection(self.db_config)
                if cnx:
                    cursor = cnx.cursor()
                    cursor.execute(f"USE {self.db_config['database']}")
                    cursor.execute("DELETE FROM pflanzenplanung WHERE pflanzen_name = %s", (name,))
                    cnx.commit(); cnx.close()
                    messagebox.showinfo("Erfolg", f"Plan für {name} gelöscht.")
                    self._refresh_plan_list(); self._load_plan_for_current_inputs()
            except Exception as e: messagebox.showerror("Fehler", f"Konnte nicht löschen: {e}")

    def _set_today_date(self, entry_widget):
        today = datetime.now().strftime("%Y-%m-%d")
        entry_widget.delete(0, tk.END); entry_widget.insert(0, today)

    def _load_plan_for_current_inputs(self, event=None):
        name = self.entries['entry_name'].get().strip()
        w_t = self.entries['entry_woche'].get().strip()
        if not name or not w_t: self._update_plan_display(None, None); return
        try:
            w = int(w_t)
            v, c = get_pflanzen_plan(self.db_config, name, w)
            self._update_plan_display(v, c)
        except: self._update_plan_display(None, None)

    def _update_plan_display(self, values, columns):
        if values is None:
            for l in self.plan_labels.values(): l.config(text="---", fg="black")
            return
        data = dict(zip(columns, values))
        mapping = {
            'entry_phase': 'phase', 'entry_licht': 'lichtzyklus_h', 'entry_root': 'root_juice_ml_l',
            'entry_calmag': 'calmag_ml_l', 'entry_grow': 'bio_grow_ml_l', 'entry_fish': 'fish_mix_ml_l',
            'entry_heaven': 'bio_heaven_ml_l', 'entry_acti': 'acti_alc_ml_l', 'entry_bloom': 'bio_bloom_ml_l',
            'entry_topmax': 'top_max_ml_l', 'entry_ph': 'ph_wert_ziel', 'entry_ec': 'ec_wert'
        }
        for gui, db in mapping.items():
            if gui in self.plan_labels:
                val = data.get(db)
                if val is not None:
                    txt = f"{val:.2f}" if isinstance(val, float) else str(val)
                    self.plan_labels[gui].config(text=txt, fg="blue")
                else: self.plan_labels[gui].config(text="---", fg="black")

    def open_plan_window(self):
        pw = tk.Toplevel(self); pw.title("Planung (SOLL) bearbeiten"); pw.geometry("450x650")
        i_n = self.entries['entry_name'].get().strip()
        i_w = self.entries['entry_woche'].get().strip()
        tk.Label(pw, text="Pflanzenname:", font=('Arial', 10, 'bold')).pack(pady=(10,0))
        en = tk.Entry(pw, width=50); en.insert(0, i_n); en.pack(pady=5)
        tk.Label(pw, text="Woche:", font=('Arial', 10, 'bold')).pack()
        ew = tk.Entry(pw, width=50); ew.insert(0, i_w); ew.pack(pady=5)
        ff = tk.Frame(pw); ff.pack(pady=10)
        p_entries = {}
        fields = [
            ("phase", "Phase"), ("lichtzyklus_h", "Lichtzyklus (h)"), ("root_juice_ml_l", "Root·Juice (ml/L)"),
            ("calmag_ml_l", "Calmag (ml/L)"), ("bio_grow_ml_l", "Bio·Grow (ml/L)"), ("fish_mix_ml_l", "Fish·Mix (ml/L)"),
            ("bio_heaven_ml_l", "Bio·Heaven (ml/L)"), ("acti_alc_ml_l", "Acti·a•alc (ml/L)"),
            ("bio_bloom_ml_l", "Bio·Bloom (ml/L)"), ("top_max_ml_l", "Top·Max (ml/L)"),
            ("ph_wert_ziel", "pH-Wert (Ziel)"), ("ec_wert", "EC-Wert (Soll)")
        ]
        for i, (k, l) in enumerate(fields):
            tk.Label(ff, text=f"{l}:").grid(row=i, column=0, sticky='w', padx=5, pady=2)
            if k == "phase": e = ttk.Combobox(ff, values=FIELD_OPTIONS["phase"], width=18)
            else: e = tk.Entry(ff, width=20)
            e.grid(row=i, column=1, padx=5, pady=2); p_entries[k] = e
        
        def _load():
            try:
                n, w = en.get().strip(), int(ew.get())
                p, c = get_pflanzen_plan(self.db_config, n, w)
                if p:
                    d = dict(zip(c, p))
                    for k, ent in p_entries.items():
                        v = d.get(k, "")
                        if isinstance(ent, ttk.Combobox): ent.set(str(v))
                        else: ent.delete(0, tk.END); ent.insert(0, f"{v:.2f}" if isinstance(v, float) else str(v))
            except: pass
        _load()
        tk.Button(pw, text="Planung Speichern", bg='blue', fg='white', font=('Arial', 10, 'bold'),
                  command=lambda: self._save_plan_from_window(pw, en, ew, p_entries)).pack(pady=20)

    def _save_plan_from_window(self, win, n_ent, w_ent, f_entries):
        try:
            n, w = n_ent.get().strip(), int(w_ent.get())
            if not n: raise ValueError("Name fehlt")
            lst = [n, w]
            for fk in PLANNING_FIELDS:
                v = f_entries[fk].get().replace(',', '.').strip()
                if fk == "phase": lst.append(v)
                elif fk == "lichtzyklus_h": lst.append(int(float(v)) if v else 0)
                else: lst.append(float(v) if v else 0.0)
            cnx, _ = get_db_connection(self.db_config)
            if cnx:
                suc, msg = save_pflanzen_plan(cnx, tuple(lst))
                cnx.close()
                if suc: messagebox.showinfo("Erfolg", msg); win.destroy(); self._refresh_plan_list(); self._load_plan_for_current_inputs()
                else: messagebox.showerror("Fehler", msg)
        except Exception as e: messagebox.showerror("Fehler", f"Ungültig: {e}")

    def save_data_to_db(self):
        try:
            if not self.entries['entry_name'].get() or not self.entries['entry_woche'].get():
                messagebox.showwarning("Warnung", "Name und Woche sind Pflicht!"); return
            ds = (
                self.entries['entry_name'].get().strip(), int(self.entries['entry_woche'].get()),
                self.entries['entry_phase'].get().strip(), int(self.entries['entry_licht'].get() or 0),
                float(self.entries['entry_root'].get().replace(',', '.') or 0.0),
                float(self.entries['entry_calmag'].get().replace(',', '.') or 0.0),
                float(self.entries['entry_grow'].get().replace(',', '.') or 0.0),
                float(self.entries['entry_fish'].get().replace(',', '.') or 0.0),
                float(self.entries['entry_heaven'].get().replace(',', '.') or 0.0),
                float(self.entries['entry_acti'].get().replace(',', '.') or 0.0),
                float(self.entries['entry_bloom'].get().replace(',', '.') or 0.0),
                float(self.entries['entry_topmax'].get().replace(',', '.') or 0.0),
                float(self.entries['entry_ph'].get().replace(',', '.') or 0.0),
                float(self.entries['entry_ec'].get().replace(',', '.') or 0.0),
                self.entries['entry_datum'].get()
            )
            cnx, cursor = get_db_connection(self.db_config)
            if cnx:
                setup_database_and_table(cursor, self.db_config['database'])
                suc, msg = insert_pflanzen_data(cnx, ds); cnx.close()
                if suc: messagebox.showinfo("Erfolg", msg); self.load_data_into_treeview()
                else: messagebox.showerror("Fehler", msg)
        except Exception as e: messagebox.showerror("Fehler", f"Fehler: {e}")

    def create_display_widgets(self, parent_frame):
        cf = tk.Frame(parent_frame); cf.pack(fill='x', pady=(0, 10))
        rf = tk.LabelFrame(cf, text="Optionen", padx=10, pady=5); rf.pack(side=tk.LEFT)
        tk.Checkbutton(rf, text="Auto-Refresh", variable=self.is_auto_refresh_active, command=self._toggle_auto_refresh).pack(side=tk.LEFT)
        tk.Label(rf, text=" Intervall (s):").pack(side=tk.LEFT)
        tk.Entry(rf, textvariable=self.refresh_interval, width=5).pack(side=tk.LEFT, padx=5)
        tk.Button(cf, text="🔄 Jetzt Aktualisieren", command=self.load_data_into_treeview).pack(side=tk.LEFT, padx=20)
        tk.Button(cf, text="🗑️ Löschen", bg='#FFCDD2', command=self._delete_selected_data).pack(side=tk.RIGHT, padx=5)
        tk.Button(cf, text="📊 CSV Export", command=self.export_data_to_csv).pack(side=tk.RIGHT, padx=5)
        self.tree = ttk.Treeview(parent_frame, selectmode="browse"); self.tree.pack(side=tk.LEFT, fill='both', expand=True)
        sb = ttk.Scrollbar(parent_frame, orient="vertical", command=self.tree.yview); sb.pack(side=tk.RIGHT, fill='y')
        self.tree.configure(yscrollcommand=sb.set)

    def load_data_into_treeview(self):
        d, cols = fetch_all_data(self.db_config)
        if d is not None:
            self.tree["columns"] = cols; self.tree.column("#0", width=0, stretch=tk.NO)
            for c in cols: self.tree.heading(c, text=c.replace('_', ' ').title()); self.tree.column(c, width=85, anchor='center')
            for i in self.tree.get_children(): self.tree.delete(i)
            for r in d: self.tree.insert("", tk.END, values=r)

    def _delete_selected_data(self):
        it = self.tree.focus()
        if not it: messagebox.showwarning("Auswahl", "Bitte wählen Sie einen Datensatz."); return
        rid = self.tree.item(it, 'values')[0]
        if messagebox.askyesno("Löschen", f"ID {rid} löschen?"):
            suc, msg = delete_data_by_id(self.db_config, rid)
            if suc: self.load_data_into_treeview()
            else: messagebox.showerror("Fehler", msg)

    def export_data_to_csv(self):
        if not self.tree.get_children(): messagebox.showwarning("Export", "Keine Daten."); return
        path = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV Datei", "*.csv")])
        if path:
            try:
                with open(path, mode='w', newline='', encoding='utf-8') as f:
                    w = csv.writer(f, delimiter=';'); w.writerow(self.tree["columns"])
                    for ri in self.tree.get_children(): w.writerow(self.tree.item(ri, 'values'))
                messagebox.showinfo("Export", "Erfolg!")
            except Exception as e: messagebox.showerror("Fehler", str(e))

    def _toggle_auto_refresh(self, start=False, stop=False):
        if self.after_id: self.after_cancel(self.after_id); self.after_id = None
        if stop: return
        if self.is_auto_refresh_active.get() or start:
            self.after_id = self.after(self.refresh_interval.get() * 1000, self._auto_refresh_loop)
            
    def _auto_refresh_loop(self):
        if self.is_auto_refresh_active.get(): self.load_data_into_treeview(); self._toggle_auto_refresh(start=True)

    def create_settings_tab(self, parent_frame):
        sf = tk.Frame(parent_frame); sf.pack(pady=20)
        tk.Label(sf, text="MySQL Konfiguration", font=('Arial', 12, 'bold')).grid(row=0, columnspan=2, pady=10)
        self.settings_entries = {}
        flds = [('Host', 'host'), ('Port', 'port'), ('User', 'user'), ('Passwort', 'password'), ('Datenbank', 'database')]
        for i, (l, k) in enumerate(flds, start=1):
            tk.Label(sf, text=f"{l}:").grid(row=i, column=0, sticky='w', padx=5, pady=5)
            e = tk.Entry(sf, width=30, show='*' if k == 'password' else ''); e.grid(row=i, column=1, padx=5, pady=5)
            e.insert(0, str(self.db_config.get(k, ''))); self.settings_entries[k] = e
        tk.Button(sf, text="Speichern & Struktur anlegen", bg='green', fg='white', command=self._save_db_settings).grid(row=6, column=0, pady=20, padx=5)
        tk.Button(sf, text="Verbindung Testen", command=self._test_connection).grid(row=6, column=1, pady=20, padx=5)
        self.status_label = tk.Label(sf, text="Status: Unbekannt"); self.status_label.grid(row=7, columnspan=2)

    def _test_connection(self):
        conf = {k: e.get() for k, e in self.settings_entries.items()}
        try:
            conf['port'] = int(conf['port']); ok, msg = test_db_connection(conf)
            self.status_label.config(text=msg, fg='green' if ok else 'red')
        except: self.status_label.config(text="Status: Port ungültig", fg='red')

    def _save_db_settings(self):
        try:
            nc = {k: e.get() for k, e in self.settings_entries.items()}
            nc['port'] = int(nc['port']); save_config(nc); self.db_config = nc
            cnx, cursor = get_db_connection(self.db_config)
            if cnx: setup_database_and_table(cursor, self.db_config['database']); cnx.close(); messagebox.showinfo("Erfolg", "Gespeichert."); self._test_connection()
            else: messagebox.showerror("Fehler", "Verbindung fehlgeschlagen.")
        except Exception as e: messagebox.showerror("Fehler", str(e))

    def show_db_settings(self): self.notebook.select(self.tab_settings)

    def _handle_tab_change(self, event):
        tab = self.notebook.tab(self.notebook.select(), "text")
        if tab == "📈 Daten anzeigen": self.load_data_into_treeview(); self._toggle_auto_refresh(start=True)
        else: self._toggle_auto_refresh(stop=True)

    def create_update_tab(self, parent_frame):
        f = tk.Frame(parent_frame); f.pack(expand=True)
        tk.Label(f, text="System-Update", font=('Arial', 14, 'bold')).pack(pady=10)
        tk.Button(f, text="🚀 Update jetzt ausführen", command=self.run_update_process, bg='#2196F3', fg='white', font=('Arial', 10, 'bold'), padx=20, pady=10).pack(pady=20)

    def run_update_process(self):
        os_sys = platform.system()
        try:
            script = "update.bat" if os_sys == "Windows" else "./update.sh"
            if os.path.exists(script):
                if os_sys != "Windows": os.chmod(script, 0o755)
                subprocess.Popen([script], shell=True if os_sys == "Windows" else False)
                self.destroy(); sys.exit()
            else: messagebox.showerror("Fehler", f"{script} fehlt")
        except Exception as e: messagebox.showerror("Update Fehler", str(e))

if __name__ == "__main__":

    app = PflanzenApp(); app.mainloop()

