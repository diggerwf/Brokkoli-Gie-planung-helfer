# db_connector.py
# -*- coding: utf-8 -*-
import mysql.connector
from mysql.connector import errorcode

PROTOKOLL_TABLE_NAME = 'pflanzenprotokoll'
PLANUNG_TABLE_NAME = 'pflanzenplanung' 

def get_db_connection(config, with_db=False):
    """Versucht, eine Verbindung zur Datenbank herzustellen (mit Port-Sicherung)."""
    # Sicherstellen, dass der Port eine Zahl ist
    port_raw = config.get('port')
    port = int(port_raw) if port_raw and str(port_raw).isdigit() else 3306
    
    db_args = {}
    if with_db and config.get('database'):
        db_args['database'] = config['database']
        
    try:
        cnx = mysql.connector.connect(
            user=config.get('user', 'root'),
            password=config.get('password', ''),
            host=config.get('host', 'localhost'),
            port=port,
            charset='utf8',
            **db_args
        )
        # Wir geben cnx und cursor zurück
        return cnx, cnx.cursor()

    except mysql.connector.Error as err:
        if err.errno == errorcode.ER_ACCESS_DENIED_ERROR:
            return None, "❌ Falscher Benutzername oder Passwort."
        elif err.errno == errorcode.CR_CONN_HOST_ERROR:
             return None, f"❌ Verbindung zum Host {config.get('host')} fehlgeschlagen."
        else:
            return None, f"❌ Fehler: {err}"

def setup_database_and_table(cursor, db_name):
    """Stellt sicher, dass Datenbank, Protokoll- und Planungstabelle existieren."""
    try:
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS {db_name} DEFAULT CHARACTER SET 'utf8'")
        cursor.execute(f"USE {db_name}")
    except mysql.connector.Error as err:
        return False, f"Fehler beim Erstellen der Datenbank: {err}"

    # Protokoll-Tabelle
    PROTOKOLL_DESCRIPTION = f"""
    CREATE TABLE IF NOT EXISTS {PROTOKOLL_TABLE_NAME} (
      id INT AUTO_INCREMENT PRIMARY KEY,
      pflanzen_name VARCHAR(50) NOT NULL,
      woche INT NOT NULL,
      phase VARCHAR(50),
      lichtzyklus_h INT,
      root_juice_ml_l FLOAT,
      calmag_ml_l FLOAT,
      bio_grow_ml_l FLOAT,
      acti_alc_ml_l FLOAT,
      bio_bloom_ml_l FLOAT,
      top_max_ml_l FLOAT,
      ph_wert_ziel FLOAT,
      ec_wert FLOAT,
      erstellungsdatum TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """
    
    # Planungstabelle
    PLANUNG_DESCRIPTION = f"""
    CREATE TABLE IF NOT EXISTS {PLANUNG_TABLE_NAME} (
      pflanzen_name VARCHAR(50) NOT NULL,
      woche INT NOT NULL,
      phase VARCHAR(50),
      lichtzyklus_h INT,
      root_juice_ml_l FLOAT,
      calmag_ml_l FLOAT,
      bio_grow_ml_l FLOAT,
      acti_alc_ml_l FLOAT,
      bio_bloom_ml_l FLOAT,
      top_max_ml_l FLOAT,
      ph_wert_ziel FLOAT,
      ec_wert FLOAT,
      PRIMARY KEY (pflanzen_name, woche)
    )
    """
    try:
        cursor.execute(PROTOKOLL_DESCRIPTION)
        cursor.execute(PLANUNG_DESCRIPTION)
        return True, "Datenbankstruktur bereit."
    except mysql.connector.Error as err:
        return False, f"Fehler: {err.msg}"

def insert_pflanzen_data(cnx, datensatz):
    """Fügt Messwerte (IST) ein."""
    cursor = cnx.cursor()
    query = (f"INSERT INTO {PROTOKOLL_TABLE_NAME} "
             "(pflanzen_name, woche, phase, lichtzyklus_h, root_juice_ml_l, "
             "calmag_ml_l, bio_grow_ml_l, acti_alc_ml_l, bio_bloom_ml_l, "
             "top_max_ml_l, ph_wert_ziel, ec_wert, erstellungsdatum) "
             "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)")
    try:
        cursor.execute(query, datensatz)
        cnx.commit()
        cursor.close()
        return True, "Messwerte gespeichert."
    except mysql.connector.Error as err:
        cursor.close()
        return False, f"Fehler: {err.msg}"

def save_pflanzen_plan(cnx, planungsdatensatz):
    """Speichert oder aktualisiert die Planung (SOLL)."""
    cursor = cnx.cursor()
    query = f"""
    INSERT INTO {PLANUNG_TABLE_NAME} 
    (pflanzen_name, woche, phase, lichtzyklus_h, root_juice_ml_l, 
     calmag_ml_l, bio_grow_ml_l, acti_alc_ml_l, bio_bloom_ml_l, 
     top_max_ml_l, ph_wert_ziel, ec_wert) 
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    ON DUPLICATE KEY UPDATE
    phase=VALUES(phase), lichtzyklus_h=VALUES(lichtzyklus_h), 
    root_juice_ml_l=VALUES(root_juice_ml_l), calmag_ml_l=VALUES(calmag_ml_l),
    bio_grow_ml_l=VALUES(bio_grow_ml_l), acti_alc_ml_l=VALUES(acti_alc_ml_l),
    bio_bloom_ml_l=VALUES(bio_bloom_ml_l), top_max_ml_l=VALUES(top_max_ml_l),
    ph_wert_ziel=VALUES(ph_wert_ziel), ec_wert=VALUES(ec_wert)
    """
    try:
        cursor.execute(query, planungsdatensatz)
        cnx.commit()
        cursor.close()
        return True, "Planung gespeichert."
    except mysql.connector.Error as err:
        cursor.close()
        return False, f"Fehler: {err.msg}"

def get_pflanzen_plan(config, plant_name, week):
    """Lädt den Plan für das automatische Ausfüllen der Soll-Werte."""
    cnx_res = get_db_connection(config, with_db=True)
    cnx = cnx_res[0]
    if cnx is None: return None, None 
    cursor = cnx.cursor()
    try:
        query = f"SELECT * FROM {PLANUNG_TABLE_NAME} WHERE pflanzen_name = %s AND woche = %s"
        cursor.execute(query, (plant_name, week))
        plan = cursor.fetchone()
        cols = [i[0] for i in cursor.description]
        cursor.close()
        cnx.close()
        return plan, cols
    except:
        return None, None

def get_all_plan_names(config):
    """NEU: Holt alle Pflanzennamen für das Dropdown-Menü."""
    cnx_res = get_db_connection(config, with_db=True)
    cnx = cnx_res[0]
    if cnx is None: return []
    cursor = cnx.cursor()
    try:
        cursor.execute(f"SELECT DISTINCT pflanzen_name FROM {PLANUNG_TABLE_NAME} ORDER BY pflanzen_name")
        names = [row[0] for row in cursor.fetchall()]
        cursor.close()
        cnx.close()
        return names
    except:
        return []

def fetch_all_data(config):
    """Holt alle Verlaufsdaten."""
    cnx_res = get_db_connection(config, with_db=True)
    cnx = cnx_res[0]
    if cnx is None: return None, cnx_res[1]
    cursor = cnx.cursor()
    try:
        cursor.execute(f"SELECT * FROM {PROTOKOLL_TABLE_NAME} ORDER BY erstellungsdatum DESC")
        data = cursor.fetchall()
        cols = [i[0] for i in cursor.description]
        cursor.close()
        cnx.close()
        return data, cols
    except mysql.connector.Error as err:
        return None, f"Fehler: {err.msg}"

def delete_data_by_id(config, record_id):
    """Löscht einen Eintrag im Verlauf."""
    cnx_res = get_db_connection(config, with_db=True)
    cnx = cnx_res[0]
    if cnx is None: return False, "Keine Verbindung"
    cursor = cnx.cursor()
    try:
        cursor.execute(f"DELETE FROM {PROTOKOLL_TABLE_NAME} WHERE id = %s", (record_id,))
        cnx.commit()
        cursor.close()
        cnx.close()
        return True, "Gelöscht."
    except:
        return False, "Fehler beim Löschen."

def test_db_connection(config):
    """Testet die Verbindung in den Einstellungen."""
    cnx_res = get_db_connection(config, with_db=True)
    if cnx_res[0]:
        cnx_res[0].close()
        return True, "✅ Verbindung erfolgreich!"
    return False, f"❌ {cnx_res[1]}"