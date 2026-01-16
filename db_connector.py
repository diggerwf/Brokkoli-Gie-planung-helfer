# db_connector.py
# -*- coding: utf-8 -*-
import mysql.connector
from mysql.connector import errorcode

PROTOKOLL_TABLE_NAME = 'pflanzenprotokoll'
PLANUNG_TABLE_NAME = 'pflanzenplanung' 

def get_db_connection(config, with_db=False):
    """Versucht, eine Verbindung zur Datenbank herzustellen."""
    port = config.get('port', 3306)
    
    db_args = {}
    if with_db:
        db_args['database'] = config['database']
        
    try:
        cnx = mysql.connector.connect(
            user=config['user'],
            password=config['password'],
            host=config['host'],
            port=port,
            charset='utf8',
            **db_args
        )
        return cnx, cnx.cursor()

    except mysql.connector.Error as err:
        if err.errno == errorcode.ER_ACCESS_DENIED_ERROR:
            return None, "❌ Falscher Benutzername oder Passwort."
        elif err.errno == errorcode.CR_CONN_HOST_ERROR:
             return None, f"❌ Verbindung zum Host {config['host']} an Port {port} nicht möglich."
        else:
            return None, f"❌ Unbekannter Fehler bei der Verbindung: {err}"


def setup_database_and_table(cursor, db_name):
    """Stellt sicher, dass Datenbank, Protokoll- und Planungstabelle existieren."""
    
    try:
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS {db_name} DEFAULT CHARACTER SET 'utf8'")
        cursor.execute(f"USE {db_name}")
    except mysql.connector.Error as err:
        return False, f"Fehler beim Erstellen/Auswählen der Datenbank: {err}"

    # Protokoll-Tabelle (Bereits aktualisiert mit ec_wert)
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
    # Planungstabelle (NEUE Spalte: ec_wert)
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
      ec_wert FLOAT,                         -- NEU: EC-Wert
      PRIMARY KEY (pflanzen_name, woche)
    )
    """
    try:
        cursor.execute(PROTOKOLL_DESCRIPTION)
        cursor.execute(PLANUNG_DESCRIPTION)
        
        # Sicherstellen, dass neue Spalten in beiden Tabellen hinzugefügt werden, falls sie bereits existieren
        # Protokoll-Tabelle (falls EC-Wert in der vorherigen Runde vergessen wurde)
        try:
            cursor.execute(f"ALTER TABLE {PROTOKOLL_TABLE_NAME} ADD COLUMN ec_wert FLOAT AFTER ph_wert_ziel")
        except mysql.connector.Error as err:
            if err.errno != 1060: pass 
            
        # Planungstabelle (Hinzufügen des EC-Werts)
        try:
            cursor.execute(f"ALTER TABLE {PLANUNG_TABLE_NAME} ADD COLUMN ec_wert FLOAT AFTER ph_wert_ziel")
        except mysql.connector.Error as err:
            if err.errno != 1060: pass 
                
        return True, "Datenbankstruktur erfolgreich eingerichtet."
    except mysql.connector.Error as err:
        return False, f"Fehler beim Erstellen der Tabellen: {err.msg}"


def insert_pflanzen_data(cnx, datensatz):
    """Fügt einen neuen IST-Datensatz (Protokoll) in die Tabelle ein und committet."""
    cursor = cnx.cursor()
    
    add_log = (f"INSERT INTO {PROTOKOLL_TABLE_NAME} "
               "(pflanzen_name, woche, phase, lichtzyklus_h, root_juice_ml_l, "
               "calmag_ml_l, bio_grow_ml_l, acti_alc_ml_l, bio_bloom_ml_l, "
               "top_max_ml_l, ph_wert_ziel, ec_wert, erstellungsdatum) "
               "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)")

    try:
        cursor.execute(add_log, datensatz)
        last_id = cursor.lastrowid
        cnx.commit()
        cursor.close()
        return True, f"Datensatz erfolgreich eingefügt. (ID: {last_id})"
    except mysql.connector.Error as err:
        cursor.close()
        return False, f"Fehler beim Einfügen des Datensatzes: {err.msg}"

# NEUE FUNKTION: Planung speichern (Anpassung für EC-Wert)
def save_pflanzen_plan(cnx, planungsdatensatz):
    """Speichert oder aktualisiert einen SOLL-Datensatz (Planung) in der Tabelle."""
    cursor = cnx.cursor()
    
    # NEU: ec_wert in Spaltenliste und UPDATE-Klausel aufgenommen
    save_plan = f"""
    INSERT INTO {PLANUNG_TABLE_NAME} 
    (pflanzen_name, woche, phase, lichtzyklus_h, root_juice_ml_l, 
     calmag_ml_l, bio_grow_ml_l, acti_alc_ml_l, bio_bloom_ml_l, 
     top_max_ml_l, ph_wert_ziel, ec_wert) 
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    ON DUPLICATE KEY UPDATE
    phase = VALUES(phase),
    lichtzyklus_h = VALUES(lichtzyklus_h),
    root_juice_ml_l = VALUES(root_juice_ml_l),
    calmag_ml_l = VALUES(calmag_ml_l),
    bio_grow_ml_l = VALUES(bio_grow_ml_l),
    acti_alc_ml_l = VALUES(acti_alc_ml_l),
    bio_bloom_ml_l = VALUES(bio_bloom_ml_l),
    top_max_ml_l = VALUES(top_max_ml_l),
    ph_wert_ziel = VALUES(ph_wert_ziel),
    ec_wert = VALUES(ec_wert)
    """

    try:
        cursor.execute(save_plan, planungsdatensatz)
        cnx.commit()
        cursor.close()
        return True, "Planung erfolgreich gespeichert/aktualisiert."
    except mysql.connector.Error as err:
        cursor.close()
        return False, f"Fehler beim Speichern der Planung: {err.msg}"

def get_pflanzen_plan(config, plant_name, week):
    """Ruft den Plan für eine spezifische Pflanze und Woche ab."""
    cnx, result = get_db_connection(config, with_db=True)
    if cnx is None:
        return None, None 

    cursor = cnx.cursor()
    
    try:
        query = f"SELECT * FROM {PLANUNG_TABLE_NAME} WHERE pflanzen_name = %s AND woche = %s"
        cursor.execute(query, (plant_name, week))
        plan = cursor.fetchone()
        
        column_names = [i[0] for i in cursor.description]
        
        cursor.close()
        cnx.close()
        return plan, column_names
        
    except mysql.connector.Error:
        cursor.close()
        cnx.close()
        return None, None

def fetch_all_data(config):
    """Holt alle Protokolleinträge aus der Datenbank."""
    cnx, result = get_db_connection(config, with_db=True)
    if cnx is None:
        return None, result

    cursor = cnx.cursor()
    
    try:
        cursor.execute(f"SELECT * FROM {PROTOKOLL_TABLE_NAME} ORDER BY erstellungsdatum DESC")
        data = cursor.fetchall()
        column_names = [i[0] for i in cursor.description]
        cursor.close()
        cnx.close()
        return data, column_names
        
    except mysql.connector.Error as err:
        cursor.close()
        cnx.close()
        if err.errno == errorcode.ER_NO_SUCH_TABLE:
            return [], f"⚠️ Tabelle '{PROTOKOLL_TABLE_NAME}' existiert nicht. Speichern Sie zuerst einen Datensatz."
        elif err.errno == errorcode.ER_BAD_DB_ERROR:
             return [], f"⚠️ Datenbank '{config['database']}' existiert nicht."
        return None, f"Fehler beim Abrufen der Daten: {err.msg}"


def delete_data_by_id(config, record_id):
    """Löscht einen Datensatz anhand seiner ID."""
    cnx, result = get_db_connection(config, with_db=True)
    if cnx is None:
        return False, result

    cursor = cnx.cursor()
    
    try:
        delete_query = f"DELETE FROM {PROTOKOLL_TABLE_NAME} WHERE id = %s"
        cursor.execute(delete_query, (record_id,))
        cnx.commit()
        rows_affected = cursor.rowcount
        cursor.close()
        cnx.close()
        
        if rows_affected > 0:
            return True, f"Datensatz (ID: {record_id}) erfolgreich gelöscht."
        else:
            return False, f"Datensatz mit ID {record_id} nicht gefunden."
            
    except mysql.connector.Error as err:
        cursor.close()
        cnx.close()
        return False, f"Fehler beim Löschen des Datensatzes: {err.msg}"


def test_db_connection(config):
    """Testet die Verbindung zur Datenbank und gibt den Status zurück."""
    port = config.get('port', 3306)
    
    try:
        cnx = mysql.connector.connect(
            user=config['user'],
            password=config['password'],
            host=config['host'],
            port=port,
            charset='utf8',
            database=config['database']
        )
        cnx.close()
        return True, "✅ Verbindung erfolgreich hergestellt und Datenbank gefunden."

    except mysql.connector.Error as err:
        if err.errno == errorcode.ER_ACCESS_DENIED_ERROR:
            return False, "❌ Falscher Benutzername oder Passwort."
        elif err.errno == errorcode.CR_CONN_HOST_ERROR:
             return False, f"❌ Verbindung zum Host {config['host']} an Port {port} nicht möglich."
        elif err.errno == errorcode.ER_BAD_DB_ERROR:
             return False, f"⚠️ Datenbank '{config['database']}' existiert nicht. Wird beim Speichern erstellt."
        else:
            return False, f"❌ Unbekannter Verbindungsfehler: {err.msg}"
    except Exception as e:
        return False, f"❌ Allgemeiner Fehler: {e}"