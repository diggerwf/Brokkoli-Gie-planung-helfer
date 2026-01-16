# config_manager.py
# -*- coding: utf-8 -*-
from configparser import ConfigParser

CONFIG_FILE = 'db_config.ini'

def load_config():
    """Lädt die MySQL-Einstellungen aus der Konfigurationsdatei."""
    config = ConfigParser()
    # Versucht, die Datei db_config.ini zu lesen
    config.read(CONFIG_FILE, encoding='utf-8') # Explizit UTF-8 beim Lesen
    if 'mysql' not in config:
        # Standardwerte, falls die Datei fehlt
        return {
            'host': 'localhost',
            'user': 'root',
            'password': '',
            'database': 'pflanzendatenbank'
        }
    return dict(config['mysql'])

def save_config(settings):
    """Speichert die MySQL-Einstellungen in der Konfigurationsdatei."""
    config = ConfigParser()
    config['mysql'] = settings
    with open(CONFIG_FILE, 'w', encoding='utf-8') as configfile: # Explizit UTF-8 beim Schreiben
        config.write(configfile)