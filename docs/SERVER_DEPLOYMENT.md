# 🚀 Server Deployment Guide - Trading Bot

## Komplette Anleitung zur Installation auf einem Linux-Server

---

## 📋 Voraussetzungen

### **Server Requirements:**
- Linux Server (Ubuntu 20.04+, Debian 11+, oder ähnlich)
- Mind. 2 GB RAM (4 GB empfohlen)
- Mind. 10 GB freier Speicher
- Docker & Docker Compose installiert
- SSH-Zugang zum Server

### **Optional aber empfohlen:**
- Reverse Proxy (Nginx) für Web-Interface
- SSL-Zertifikat (Let's Encrypt)
- Firewall konfiguriert

---

## 🛠️ Installation

### **Schritt 1: Docker installieren (falls nicht vorhanden)**

```bash
# Update System
sudo apt update && sudo apt upgrade -y

# Docker installieren
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Docker Compose installieren
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Benutzer zur Docker-Gruppe hinzufügen
sudo usermod -aG docker $USER

# Logout/Login für Gruppenänderung
# oder: newgrp docker
```

**Verifizieren:**
```bash
docker --version
docker-compose --version
```

---

### **Schritt 2: Bot auf Server hochladen**

**Option A: Via Git (empfohlen)**

```bash
# Auf dem Server
cd /opt  # oder /home/username
git clone <your-repo-url> trading-bot
cd trading-bot/tbp-v2
```

**Option B: Via SCP (von lokalem PC)**

```bash
# Von lokalem PC
cd C:\dev\private\apps\trading-bot-pro\CascadeProjects\
scp -r tbp-v2 user@your-server:/opt/trading-bot/
```

**Option C: Via SFTP/FileZilla**

1. Verbinde zu Server via SFTP
2. Upload kompletten `tbp-v2` Ordner nach `/opt/trading-bot/`

---

### **Schritt 3: Umgebungsvariablen konfigurieren**

```bash
cd /opt/trading-bot/tbp-v2

# Kopiere .env Template
cp .env.example .env

# Editiere .env
nano .env
```

**Mindest-Konfiguration:**

```env
# EXCHANGE API KEYS (ERFORDERLICH)
KRAKEN_API_KEY=your_actual_kraken_api_key
KRAKEN_API_SECRET=your_actual_kraken_secret

# NEWS API KEYS (Optional - verbessert Performance)
NEWSAPI_KEY=your_newsapi_key
CRYPTOCOMPARE_KEY=your_cryptocompare_key

# BOT CONFIGURATION
PAPER_TRADING=true              # true = Demo, false = Live
INITIAL_BALANCE=10000.0
RISK_PER_TRADE=1.0

# CONTINUOUS LEARNING
CONTINUOUS_LEARNING=true
MIN_SAMPLES_RETRAIN=100
RETRAIN_FREQUENCY_HOURS=24

# ENHANCED FEATURES
USE_ENHANCED_PIPELINE=true
```

**Speichern:** `CTRL+O`, Enter, `CTRL+X`

---

### **Schritt 4: Verzeichnisse erstellen**

```bash
# Erstelle persistente Daten-Verzeichnisse
mkdir -p logs models models/versions training_data news_data portfolio

# Setze Berechtigungen
chmod -R 755 logs models training_data news_data portfolio
```

---

### **Schritt 5: Initial Training durchführen**

**Vor dem ersten Start des Bots:**

```bash
# Training mit Docker Compose
docker-compose --profile training up training

# ODER direkt mit Docker
docker-compose build
docker-compose run --rm trading python train_comprehensive_model.py --years 15
```

**Erwartete Dauer:** 10-20 Minuten

**Output:**
```
✓ 15 Jahre historische Daten geladen
✓ News-Sentiment analysiert
✓ Modell trainiert - Accuracy: ~75%
✓ Backtest durchgeführt
✓ Modell gespeichert in /app/models/
```

---

### **Schritt 6: Bot starten**

```bash
# Hauptbot starten (im Hintergrund)
docker-compose up -d trading-bot

# Logs anschauen
docker-compose logs -f trading-bot
```

**Erwartete Logs:**
```
✓ Kontinuierliches Lernsystem aktiviert
✓ Enhanced Pipeline aktiviert
✓ Verarbeite Symbol: BTC/USD
✓ 721 Kerzen geladen
✓ Verarbeitung abgeschlossen
```

---

## 📊 Management & Monitoring

### **Bot-Status prüfen:**

```bash
# Status aller Container
docker-compose ps

# Logs live verfolgen
docker-compose logs -f trading-bot

# Letzte 100 Zeilen
docker-compose logs --tail=100 trading-bot
```

### **Learning Monitor:**

```bash
# Einmalig ausführen
docker-compose run --rm learning-monitor

# Output:
# ✓ Gesammelte Samples: 245
# ✓ Modell Accuracy: 77%
# ✓ Total Retrainings: 3
```

### **Bot stoppen/neustarten:**

```bash
# Stoppen
docker-compose stop trading-bot

# Neustarten
docker-compose restart trading-bot

# Komplett runterfahren
docker-compose down

# Neu starten
docker-compose up -d trading-bot
```

---

## 🔧 Wartung & Updates

### **Code-Updates:**

```bash
# Via Git
cd /opt/trading-bot/tbp-v2
git pull

# Container neu bauen
docker-compose build

# Bot mit neuem Code starten
docker-compose up -d trading-bot
```

### **Modell Re-Training:**

```bash
# Manuelles Retraining
docker-compose --profile training up training

# ODER mit Custom-Parametern
docker-compose run --rm training python train_comprehensive_model.py --years 10 --timeframe 4h
```

### **Logs bereinigen:**

```bash
# Alte Logs archivieren
cd /opt/trading-bot/tbp-v2
tar -czf logs_backup_$(date +%Y%m%d).tar.gz logs/
rm logs/*.log

# Docker Logs rotieren
docker-compose down
docker system prune -f
docker-compose up -d trading-bot
```

---

## 🛡️ Sicherheit

### **Firewall konfigurieren:**

```bash
# UFW aktivieren (wenn noch nicht)
sudo ufw enable

# Nur SSH erlauben
sudo ufw allow ssh

# Optional: Port 8080 für Monitoring (nur von bestimmten IPs)
sudo ufw allow from YOUR_IP to any port 8080

# Status prüfen
sudo ufw status
```

### **API Keys schützen:**

```bash
# .env Berechtigungen einschränken
chmod 600 .env

# Sicherstellen dass .env nicht in Git ist
echo ".env" >> .gitignore
```

### **Auto-Updates (optional):**

```bash
# Watchtower für automatische Container-Updates
docker run -d \
  --name watchtower \
  --restart unless-stopped \
  -v /var/run/docker.sock:/var/run/docker.sock \
  containrrr/watchtower \
  --interval 86400  # Täglich prüfen
```

---

## 📈 Monitoring & Alerts

### **Container-Health prüfen:**

```bash
# Healthcheck Status
docker inspect trading-bot | grep -A 10 Health

# Automatisches Restart bei Crash
# (bereits in docker-compose.yml: restart: unless-stopped)
```

### **Systemd Service (Alternative zu Docker Compose):**

Erstelle: `/etc/systemd/system/trading-bot.service`

```ini
[Unit]
Description=Trading Bot
Requires=docker.service
After=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=/opt/trading-bot/tbp-v2
ExecStart=/usr/local/bin/docker-compose up -d trading-bot
ExecStop=/usr/local/bin/docker-compose down
TimeoutStartSec=0

[Install]
WantedBy=multi-user.target
```

**Aktivieren:**
```bash
sudo systemctl daemon-reload
sudo systemctl enable trading-bot
sudo systemctl start trading-bot
```

### **Prometheus Monitoring (Advanced):**

```bash
# Füge zu docker-compose.yml hinzu
# (Separate Anleitung bei Bedarf)
```

---

## 🐛 Troubleshooting

### **Problem: Container startet nicht**

```bash
# Detaillierte Logs
docker-compose logs trading-bot

# Container Inspect
docker inspect trading-bot

# Manuell starten für Debugging
docker-compose run --rm trading-bot bash
```

### **Problem: Nicht genug RAM**

```bash
# RAM-Nutzung prüfen
docker stats trading-bot

# Memory Limit erhöhen in docker-compose.yml:
# memory: 4G
```

### **Problem: API Connection Fehler**

```bash
# Teste Kraken Connection
docker-compose run --rm trading-bot python -c "
import ccxt
exchange = ccxt.kraken()
print(exchange.fetch_ticker('BTC/USD'))
"

# Prüfe .env Keys
cat .env | grep KRAKEN
```

### **Problem: Training schlägt fehl**

```bash
# Mehr CPU/RAM für Training
# In docker-compose.yml training service:
deploy:
  resources:
    limits:
      memory: 6G
      cpus: '3.0'

# Weniger Jahre trainieren
docker-compose run --rm training python train_comprehensive_model.py --years 5
```

---

## 📊 Performance-Optimierung

### **Für Server mit wenig RAM (<2GB):**

```yaml
# docker-compose.yml anpassen:
deploy:
  resources:
    limits:
      memory: 512M
      cpus: '0.5'
```

```bash
# Training überspringen - nutze vortrainiertes Modell
# (Modell von lokalem PC hochladen)
scp -r models/ user@server:/opt/trading-bot/tbp-v2/
```

### **Für High-Performance Server (8GB+ RAM):**

```yaml
# Aggressivere Settings
deploy:
  resources:
    limits:
      memory: 8G
      cpus: '4.0'
```

```bash
# Mehr Daten trainieren
docker-compose run --rm training python train_comprehensive_model.py \
  --years 15 \
  --timeframe 4h \
  --symbols BTC/USD ETH/USD SOL/USD XRP/USD ADA/USD BNB/USD DOGE/USD
```

---

## 🔄 Automatisierung

### **Cron Job für tägliches Monitoring:**

```bash
# Crontab editieren
crontab -e

# Täglich um 8 Uhr Learning Stats
0 8 * * * cd /opt/trading-bot/tbp-v2 && docker-compose run --rm learning-monitor >> /var/log/trading-bot-stats.log 2>&1

# Wöchentliches Backup
0 0 * * 0 cd /opt/trading-bot/tbp-v2 && tar -czf /backup/trading-bot-$(date +\%Y\%m\%d).tar.gz models/ training_data/ portfolio/
```

### **Auto-Restart bei System-Reboot:**

```bash
# Bereits konfiguriert durch: restart: unless-stopped
# Container starten automatisch nach Server-Neustart

# Testen:
sudo reboot
# Nach Neustart:
docker ps  # Bot sollte laufen
```

---

## 📞 Nützliche Kommandos

```bash
# === BOT MANAGEMENT ===
docker-compose up -d trading-bot                 # Start
docker-compose stop trading-bot                  # Stop
docker-compose restart trading-bot               # Restart
docker-compose logs -f trading-bot               # Live Logs
docker-compose ps                                # Status

# === MONITORING ===
docker-compose run --rm learning-monitor         # Learning Stats
docker stats trading-bot                         # Resource Usage
docker inspect trading-bot                       # Detaillierte Infos

# === TRAINING ===
docker-compose --profile training up training    # Full Training
docker-compose run --rm training python train_comprehensive_model.py --years 10

# === MAINTENANCE ===
docker-compose down                              # Alles stoppen
docker-compose build                             # Neu bauen
docker system prune -a                           # Cleanup
docker volume ls                                 # Volumes anzeigen

# === DEBUGGING ===
docker-compose run --rm trading-bot bash         # Container Shell
docker-compose exec trading-bot bash             # In laufenden Container
docker logs trading-bot --tail 200               # Letzte 200 Zeilen
```

---

## ✅ Deployment Checklist

```
□ Docker & Docker Compose installiert
□ Bot-Code auf Server hochgeladen
□ .env konfiguriert mit API Keys
□ Verzeichnisse erstellt (logs, models, etc.)
□ Initial Training durchgeführt
□ Bot gestartet mit docker-compose up -d
□ Logs geprüft - keine Fehler
□ Health-Check läuft
□ Firewall konfiguriert
□ Backups eingerichtet
□ Monitoring funktioniert
□ Auto-Restart getestet
```

---

## 🎉 Quick Start Kommandos

```bash
# 1. Docker installieren
curl -fsSL https://get.docker.com | sh

# 2. Code hochladen (via Git)
cd /opt && git clone <repo> trading-bot
cd trading-bot/tbp-v2

# 3. Environment konfigurieren
cp .env.example .env
nano .env  # API Keys eintragen

# 4. Verzeichnisse erstellen
mkdir -p logs models training_data news_data portfolio

# 5. Initial Training
docker-compose --profile training up training

# 6. Bot starten
docker-compose up -d trading-bot

# 7. Logs checken
docker-compose logs -f trading-bot

# 8. Monitoring
docker-compose run --rm learning-monitor
```

---

## 🌐 Web-Interface (Optional)

Falls Sie ein Web-Dashboard möchten, können wir später hinzufügen:

```bash
# FastAPI Dashboard auf Port 8080
# Nginx Reverse Proxy
# SSL mit Let's Encrypt
# Auth mit JWT
```

---

## 📚 Weitere Ressourcen

- **Logs:** `/opt/trading-bot/tbp-v2/logs/trading_bot.log`
- **Modelle:** `/opt/trading-bot/tbp-v2/models/`
- **Training Data:** `/opt/trading-bot/tbp-v2/training_data/`
- **News Data:** `/opt/trading-bot/tbp-v2/news_data/`

---

**Viel Erfolg mit dem Server-Deployment! 🚀**

Bei Fragen: Siehe Troubleshooting-Sektion oder Docker Logs prüfen.
