# 🚀 Trading Bot - Ubuntu Homeserver Installation mit Docker

## 📋 Voraussetzungen

- Ubuntu 20.04+ Homeserver
- Mindestens 2GB RAM frei
- 10GB freier Speicherplatz
- Internet-Verbindung für Datenfeeds

---

## 🛠️ Schritt 1: Docker und Docker Compose installieren

```bash
# System aktualisieren
sudo apt update && sudo apt upgrade -y

# Docker installieren
sudo apt install -y apt-transport-https ca-certificates curl gnupg lsb-release

# Docker GPG Key hinzufügen
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg

# Docker Repository hinzufügen
echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

# Docker installieren
sudo apt update
sudo apt install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin

# Docker als Service starten
sudo systemctl start docker
sudo systemctl enable docker

# User zur docker Gruppe hinzufügen (für passwortlose Ausführung)
sudo usermod -aG docker $USER

# NEU ANMELDEN oder folgenden Befehl ausführen:
newgrp docker

# Installation prüfen
docker --version
docker compose version
```

---

## 📁 Schritt 2: Projekt auf Homeserver kopieren

### Option A: Git Clone (Empfohlen)
```bash
cd ~
git clone https://github.com/yourusername/trading-bot-pro.git trading-bot
cd trading-bot
```

### Option B: SCP von deinem Entwicklungs-PC
```bash
# Auf deinem Entwicklungs-PC:
scp -r /path/to/trading-bot-pro user@your-homeserver:/home/user/

# Auf dem Homeserver:
cd ~/trading-bot-pro
```

### Option C: ZIP Upload
```bash
# Erstelle ZIP auf Entwicklungs-PC:
cd /path/to/trading-bot-pro
zip -r trading-bot.zip .

# Kopiere ZIP auf Homeserver und entpacke:
unzip trading-bot.zip
cd trading-bot
```

---

## 🔑 Schritt 3: API Keys konfigurieren

```bash
# Template kopieren
cp .env.template .env

# API Keys editieren (ersetze die Platzhalter)
nano .env

# Inhalt sollte so aussehen:
KRAKEN_API_KEY=your_actual_kraken_api_key
KRAKEN_API_SECRET=your_actual_kraken_api_secret
BOT_MODE=paper_trading
INITIAL_BALANCE=10000.0
RISK_PER_TRADE=1.0
USE_ENHANCED_PIPELINE=true
LOG_LEVEL=INFO
```

### Kraken API Keys bekommen:
1. Gehe zu https://www.kraken.com/u/security/api
2. Erstelle neue API Key mit folgenden Permissions:
   - ✅ Query Funds
   - ✅ Query Open Orders & Trades
   - ✅ Query Closed Orders & Trades
   - ✅ Create & Modify Orders (nur für Live Trading)
   - ✅ Cancel & Close Orders
3. Kopiere Key und Secret in `.env` Datei

---

## 🐳 Schritt 4: Docker Container bauen und starten

```bash
# In das Projekt-Verzeichnis wechseln
cd ~/trading-bot

# Container bauen (erster Start dauert länger)
docker compose build

# Bot starten (im Hintergrund)
docker compose up -d trading-bot

# Status prüfen
docker compose ps

# Logs anzeigen
docker compose logs -f trading-bot
```

### Erwartete Ausgabe:
```
[+] Building 120.5s (12/12) FINISHED
[+] Running 1/1
 ✔ Container kraken-trading-bot  Started

# Logs sollten zeigen:
trading_bot | INFO - Enhanced Pipeline (Companion Codex) verfügbar
trading_bot | INFO - Trading-Bot erfolgreich initialisiert
trading_bot | INFO - Enhanced Signal für BTC/USD: LONG - Konfidenz: 65.3%
```

---

## 📊 Schritt 5: Monitoring aktivieren (Optional)

```bash
# Monitor parallel starten
docker compose --profile monitoring up -d bot-monitor

# Oder beide Services zusammen starten:
docker compose --profile monitoring up -d

# Monitor Logs anzeigen
docker compose logs -f bot-monitor
```

---

## 📁 Schritt 6: Datenverzeichnisse prüfen

Der Bot erstellt automatisch persistente Daten:

```bash
# Verzeichnis-Struktur prüfen
ls -la ~/trading-bot/

# Sollte folgende Ordner enthalten:
# logs/          - Trading Logs
# models/        - ML-Modelle
# portfolio/     - Portfolio Status

# Portfolio Status prüfen
cat ~/trading-bot/portfolio/portfolio_state.json
```

---

## 🔄 Schritt 7: Bot verwalten

### Status prüfen:
```bash
# Alle Services
docker compose ps

# Einzelne Container
docker stats kraken-trading-bot

# Logs anzeigen
docker compose logs trading-bot
docker compose logs bot-monitor
```

### Bot stoppen/erneut starten:
```bash
# Stoppen
docker compose down

# Erneut starten
docker compose up -d

# Nur Bot neustarten (ohne Rebuild)
docker compose restart trading-bot
```

### Updates durchführen:
```bash
# Code aktualisieren
git pull

# Container neu bauen
docker compose build --no-cache

# Starten
docker compose up -d
```

---

## 🛡️ Schritt 8: Sicherheit & Backup

### API Keys schützen:
```bash
# .env Datei nur für Owner lesbar machen
chmod 600 .env

# Backup der API Keys (NICHT in Git!)
cp .env .env.backup
```

### Automatische Backups:
```bash
# Cron-Job für tägliche Backups erstellen
crontab -e

# Füge hinzu:
0 2 * * * cd ~/trading-bot && tar -czf backup-$(date +\%Y\%m\%d).tar.gz logs/ models/ portfolio/

# Alte Backups löschen (behalte 7 Tage)
0 3 * * * find ~/trading-bot -name "backup-*.tar.gz" -mtime +7 -delete
```

### Log Rotation:
```bash
# Logrotate für große Log-Dateien
sudo nano /etc/logrotate.d/trading-bot

# Inhalt:
/home/*/trading-bot/logs/*.log {
    daily
    rotate 7
    compress
    missingok
    notifempty
    create 644 ubuntu ubuntu
}
```

---

## 📊 Schritt 9: Monitoring & Alerts

### System Monitoring:
```bash
# Docker Container überwachen
docker stats

# Speicherplatz prüfen
df -h

# RAM Usage
free -h
```

### Trading Performance:
```bash
# Live Portfolio
docker compose exec trading-bot cat portfolio/portfolio_state.json | jq .

# Aktuelle Logs
docker compose logs --tail=50 trading-bot
```

### Email Alerts (optional):
```bash
# ssmtp installieren für Email-Benachrichtigungen
sudo apt install ssmtp mailutils

# Konfiguration in /etc/ssmtp/ssmtp.conf
# Dann Cron-Job für tägliche Reports
```

---

## 🐛 Fehlerbehebung

### Bot startet nicht:
```bash
# Detaillierte Logs
docker compose logs trading-bot

# Container Shell
docker compose exec trading-bot bash

# Debug: Bot manuell starten
docker compose exec trading-bot python main.py
```

### API Fehler:
```bash
# API Keys prüfen
docker compose exec trading-bot env | grep KRAKEN

# Kraken API Test
docker compose exec trading-bot python -c "
import ccxt
exchange = ccxt.kraken()
print('API Verbindung:', exchange.has)
"
```

### Speicherprobleme:
```bash
# Docker System aufräumen
docker system prune -a

# Alte Images entfernen
docker image prune -f
```

### Häufige Probleme:
- **"Enhanced Pipeline nicht verfügbar"**: XGBoost Installation prüfen
- **API Errors**: Kraken API Keys überprüfen
- **Memory Error**: RAM erhöhen oder Container Limits anpassen

---

## 📈 Performance Optimierung

### Für besseren Homeserver Betrieb:
```bash
# Container Ressourcen anpassen in docker-compose.yml
deploy:
  resources:
    limits:
      memory: 2G    # Mehr RAM für ML-Training
      cpus: '1.0'   # Mehr CPU für Berechnungen
```

### Trading Schedule optimieren:
```bash
# Weniger häufige Updates für Homeserver
# In config.py: timeframe = '4h' statt '1h'
```

---

## 🔄 Updates & Wartung

### Wöchentliche Routine:
```bash
# Status prüfen
docker compose ps
docker stats

# Backups prüfen
ls -la ~/trading-bot/backup-*.tar.gz

# Logs rotieren
sudo logrotate /etc/logrotate.d/trading-bot
```

### Monatliche Wartung:
```bash
# System aktualisieren
sudo apt update && sudo apt upgrade

# Docker aktualisieren
sudo apt install docker-ce docker-compose-plugin

# Bot Code aktualisieren
cd ~/trading-bot && git pull
docker compose build --no-cache
docker compose up -d
```

---

## 🎯 Erfolgreiche Installation prüfen

✅ **Bot läuft:** `docker compose ps` zeigt "Up"
✅ **Logs generiert:** `ls logs/trading_bot.log` existiert
✅ **Portfolio erstellt:** `cat portfolio/portfolio_state.json` zeigt Daten
✅ **API Verbindung:** Keine API-Fehler in Logs
✅ **Enhanced Pipeline:** "Enhanced Pipeline verfügbar" in Logs
✅ **Trades ausgeführt:** Portfolio ändert sich über Zeit

---

## 📞 Support

Bei Problemen:
1. Logs prüfen: `docker compose logs trading-bot`
2. System Ressourcen prüfen: `docker stats`
3. API Keys verifizieren
4. GitHub Issues für bekannte Probleme

---

**🚀 Dein Trading Bot läuft jetzt 24/7 auf deinem Ubuntu Homeserver!**

Paper Trading ist aktiv - wechsle zu Live Trading nur nach erfolgreichen Tests.
