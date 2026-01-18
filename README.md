🌿 🥦 Brokkoli-Gießplanung-Helfer: Dein Ultimativer Grow-Begleiter 🥦 🌿
Ein professionelles Desktop-Anwendungstool zur Protokollierung und Planung deiner Pflanzenzucht. Behalte den vollen Überblick über Nährstoffe, Lichtzyklen und Wasserwerte.
🌟 Features
	•	Soll-Planung: Erstelle detaillierte Wochenpläne für verschiedene Sorten (z.B. Blueberry Kush).
	•	Ist-Datenerfassung: Dokumentiere täglich Messwerte wie pH-Wert, EC-Wert, Calmag, Bio-Grow und mehr.
	•	Vergleichs-Ansicht: Sieh auf einen Blick, ob deine aktuellen Werte mit deiner Planung übereinstimmen.
	•	Datenbank-Verwaltung: Alle Daten werden zentral gespeichert und können jederzeit eingesehen werden.
	•	CSV-Export: Exportiere deine Daten für externe Analysen.
	•	Integrierte Update-Funktion: Halte die Software mit nur einem Klick aktuell.
🛠 Installation
🖥️ Für Windows (Empfohlen)
Die Installation unter Windows ist vollständig automatisiert:
	1	Lade die Datei installer.bat herunter.
	2	Führe die installer.bat per Doppelklick aus.
	3	Folge den Anweisungen im Terminal – das Programm startet nach Abschluss automatisch.
🐧 Für Linux / Raspberry Pi (In Entwicklung)
Da der native installer.sh noch in Arbeit ist, nutzt du am besten das update.sh Skript als Übergangslösung:
	1	Lade die Datei update.sh herunter.
	2	Öffne ein Terminal und mache das Skript ausführbar: chmod +x update.sh  
	3	Führe das Skript aus: ./update.sh  
Das Skript bereitet die Umgebung vor und startet die Anwendung.
⚠️ Wichtige Voraussetzung: Datenbank
Das Programm benötigt zwingend eine Datenbank-Anbindung, um Daten dauerhaft zu speichern.
Anforderungen:
	•	Ein laufender MySQL oder MariaDB Server (lokal auf dem Gerät oder extern im Netzwerk).
	•	Die Konfiguration erfolgt im Programm unter dem Reiter "Einstellungen".
	•	Pflichtangaben: Host-IP, Port (Standard: 3306), Benutzername, Passwort und Datenbankname.
[!CAUTION] Ohne eine korrekte Verbindung zu einer MySQL/MariaDB Datenbank können keine Daten gespeichert oder Pläne geladen werden.
📝 Kontakt & Support
Wenn du Feedback hast oder Fehler findest, erstelle bitte ein Issue hier auf GitHub.
Viel Erfolg bei deinem Projekt! 🍏🥦
