# 🐳 Docker Installation

## Schnellstart für Ubuntu Homeserver

```bash
# 1. Docker installieren
sudo apt update && sudo apt install -y docker.io docker-compose
sudo systemctl start docker && sudo systemctl enable docker
sudo usermod -aG docker $USER
newgrp docker

# 2. Projekt klonen
git clone <repository-url> trading-bot
cd trading-bot

# 3. API Keys konfigurieren
cp .env.template .env
nano .env  # API Keys eintragen

# 4. Bot starten
docker compose up -d

# 5. Status prüfen
docker compose logs -f trading-bot
```

## Vollständige Anleitung

Siehe `UBUNTU_INSTALLATION.md` für detaillierte Schritte.

## Management

```bash
# Interaktives Menü
./manage_bot.sh

# Oder direkte Befehle
./manage_bot.sh start    # Bot starten
./manage_bot.sh stop     # Bot stoppen
./manage_bot.sh logs     # Logs anzeigen
./manage_bot.sh backup   # Backup erstellen
```

## Services

- **trading-bot**: Haupt-Bot mit Enhanced Pipeline
- **bot-monitor**: Live Monitoring Dashboard (optional)

## Volumes

- `logs/`: Persistente Trading-Logs
- `models/`: ML-Modelle und Trainingsdaten
- `portfolio/`: Portfolio-Status und Trade-Historie

## Sicherheit

- ✅ Paper Trading als Standard
- ✅ API Keys in `.env` (nicht in Git)
- ✅ Automatische Backups
- ✅ Ressourcen-Limits für Homeserver
