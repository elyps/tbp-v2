Hallo! Sehr gerne, ich helfe Ihnen dabei, den Trading-Bot auf Ihrer Ubuntu-VM ohne Docker zu installieren und zu betreiben. Das ist eine ausgezeichnete Wahl für eine dedizierte Server-Umgebung.

Hier ist eine detaillierte Schritt-für-Schritt-Anleitung, die Sie durch den gesamten Prozess führt.

🚀 Anleitung: Trading-Bot auf Ubuntu ohne Docker installieren
Diese Anleitung führt Sie durch die Installation des Bots direkt auf Ihrem Ubuntu-System mithilfe einer isolierten Python-Umgebung, was als bewährte Methode gilt.

Schritt 1: System vorbereiten und Python installieren
Zuerst stellen wir sicher, dass Ihr System auf dem neuesten Stand ist und alle notwendigen Werkzeuge wie git und python installiert sind.

bash
# 1. System-Pakete aktualisieren
sudo apt update && sudo apt upgrade -y

# 2. Notwendige Software installieren (Python, pip, venv und git)
sudo apt install -y python3 python3-pip python3-venv git
Schritt 2: Projekt-Code herunterladen
Wir klonen das Projekt-Repository von Git in ein Verzeichnis Ihrer Wahl, zum Beispiel in Ihr Home-Verzeichnis.

bash
 Show full code block 
# In Ihr Home-Verzeichnis wechseln
cd ~

# Projekt von Git klonen (ersetzen Sie die URL ggf. durch Ihre eigene)
git clone https://github.com/yourusername/trading-bot-pro.git trading-bot

# In das Projektverzeichnis wechseln
cd trading-bot
Schritt 3: Python Virtual Environment einrichten
Eine virtuelle Umgebung (venv) ist entscheidend, um die Python-Pakete des Bots von den System-Paketen zu isolieren. Das verhindert Konflikte.

bash
# 1. Eine virtuelle Umgebung im Projektordner erstellen
python3 -m venv .venv

# 2. Die virtuelle Umgebung aktivieren
# (Dieser Befehl muss in jeder neuen Terminalsitzung ausgeführt werden, in der Sie mit dem Bot arbeiten)
source .venv/bin/activate

# Ihr Terminal-Prompt sollte sich nun ändern und (.venv) am Anfang anzeigen
Schritt 4: Notwendige Python-Pakete installieren
Jetzt installieren wir alle Python-Abhängigkeiten, die der Bot benötigt, in unserer aktivierten virtuellen Umgebung.

bash
# 1. Pip (den Python-Paketmanager) aktualisieren
pip install --upgrade pip

# 2. Alle Pakete aus der requirements.txt Datei installieren
pip install -r requirements.txt

# 3. Zusätzliche Daten für die Sentiment-Analyse herunterladen (falls benötigt)
python -m textblob.download_corpora
Dieser Schritt kann einige Minuten dauern, da Pakete wie xgboost und pandas kompiliert und installiert werden.

Schritt 5: API-Keys und Konfiguration einrichten
Der Bot benötigt API-Schlüssel, um mit der Börse zu kommunizieren. Diese speichern wir sicher in einer .env-Datei.

bash
# 1. Die Vorlagedatei kopieren
cp .env.template .env

# 2. Die .env-Datei mit einem Texteditor wie nano bearbeiten
nano .env
Fügen Sie Ihre Kraken API-Schlüssel und andere gewünschte Einstellungen ein. Für den Start im Paper-Trading-Modus könnte es so aussehen:

env
 Show full code block 
# .env Datei
KRAKEN_API_KEY=your_actual_kraken_api_key
KRAKEN_API_SECRET=your_actual_kraken_api_secret
BOT_MODE=paper_trading
INITIAL_BALANCE=10000.0
RISK_PER_TRADE=1.0
LOG_LEVEL=INFO
Drücken Sie CTRL+O zum Speichern und CTRL+X zum Beenden von nano.

Schritt 6: ML-Modell trainieren (Empfohlen)
Bevor Sie den Bot starten, sollten Sie das KI-Modell mit historischen Daten trainieren.

bash
# Stellen Sie sicher, dass Ihre virtuelle Umgebung (.venv) noch aktiv ist
python train_model.py
Dieser Prozess lädt Marktdaten und trainiert das Modell. Das kann je nach Konfiguration 5-15 Minuten dauern.

Schritt 7: Den Bot starten!
Jetzt ist alles bereit, um den Bot zu starten. Da er kontinuierlich laufen soll, verwenden wir ein Tool wie screen oder tmux, damit der Prozess auch nach dem Schließen der SSH-Verbindung weiterläuft.

Option A: Mit screen (einfach und effektiv)

bash
# 1. Eine neue screen-Sitzung mit dem Namen "tradingbot" starten
screen -S tradingbot

# 2. Innerhalb der screen-Sitzung den Bot starten
python main.py

# 3. Die Sitzung verlassen (der Bot läuft im Hintergrund weiter)
# Drücken Sie: Strg+A, dann D (für Detach)
Wiederverbinden zur Sitzung: Um die Logs zu sehen oder den Bot zu stoppen, verbinden Sie sich einfach wieder: screen -r tradingbot

Bot stoppen: Verbinden Sie sich zur screen-Sitzung und drücken Sie Strg+C.

Schritt 8: Den Bot überwachen
Sie können den Zustand des Bots und Ihr Portfolio mit dem Monitoring-Skript überwachen.

bash
# 1. Öffnen Sie eine ZWEITE SSH-Verbindung zu Ihrem Server
# 2. Wechseln Sie in das Projektverzeichnis und aktivieren Sie die venv
cd ~/trading-bot
source .venv/bin/activate

# 3. Starten Sie das Dashboard
python monitor_bot.py
Das Dashboard zeigt Ihnen Live-Daten zu Ihrem Portfolio, offenen Positionen und der Performance.

Zusammenfassung der wichtigsten Befehle
Bot starten (in screen-Sitzung):

screen -S tradingbot
cd ~/trading-bot && source .venv/bin/activate
python main.py
Strg+A, dann D
Bot-Logs ansehen: screen -r tradingbot

Bot stoppen:

screen -r tradingbot
Strg+C
Dashboard ansehen (in neuem Terminal):

cd ~/trading-bot && source .venv/bin/activate
python monitor_bot.py
Damit haben Sie eine robuste, native Installation auf Ihrem Ubuntu-Server. Viel Erfolg mit Ihrem Trading-Bot!