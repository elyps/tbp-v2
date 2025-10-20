#!/bin/bash

# =============================================================================
# Trading Bot - Automatisches Server Deployment Script
# =============================================================================

set -e  # Exit bei Fehler

echo "============================================================"
echo "  🚀 Trading Bot - Server Deployment"
echo "============================================================"
echo ""

# Farben für Output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Variablen
INSTALL_DIR="/opt/trading-bot/tbp-v2"
CURRENT_USER=$(whoami)
SCRIPT_DIR=$(cd "$(dirname "$0")" && pwd)

# Funktionen
print_success() {
    echo -e "${GREEN}✓${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

check_command() {
    if command -v $1 &> /dev/null; then
        print_success "$1 ist installiert"
        return 0
    else
        print_warning "$1 ist NICHT installiert"
        return 1
    fi
}

# =============================================================================
# Schritt 1: Voraussetzungen prüfen
# =============================================================================

echo "Schritt 1: Prüfe Voraussetzungen..."
echo ""

# Docker prüfen
if ! check_command docker; then
    echo ""
    echo "Docker wird installiert..."
    curl -fsSL https://get.docker.com -o get-docker.sh
    sudo sh get-docker.sh
    sudo usermod -aG docker $CURRENT_USER
    rm get-docker.sh
    print_success "Docker installiert"
fi

# Docker Compose prüfen
if ! check_command docker-compose; then
    echo ""
    echo "Docker Compose wird installiert..."
    sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    sudo chmod +x /usr/local/bin/docker-compose
    print_success "Docker Compose installiert"
fi

echo ""
print_success "Alle Voraussetzungen erfüllt"
echo ""

# =============================================================================
# Schritt 2: Verzeichnisse erstellen
# =============================================================================

echo "Schritt 2: Erstelle Verzeichnisse und synchronisiere Dateien..."
echo ""

sudo mkdir -p $INSTALL_DIR
sudo chown -R $CURRENT_USER:$CURRENT_USER $INSTALL_DIR

echo "Synchronisiere Projektdateien..."
if command -v rsync &> /dev/null; then
    rsync -a --delete \
        --exclude '.git' \
        --exclude '.env' \
        --exclude '__pycache__' \
        "$SCRIPT_DIR/" "$INSTALL_DIR/"
else
    tar --exclude='.git' --exclude='.env' --exclude='__pycache__' \
        -C "$SCRIPT_DIR" -cf - . | tar -C "$INSTALL_DIR" -xf -
fi

cd $INSTALL_DIR

# Persistente Daten-Verzeichnisse
mkdir -p logs models models/versions training_data news_data portfolio
chmod -R 755 logs models training_data news_data portfolio

print_success "Verzeichnisse erstellt: $INSTALL_DIR"
echo ""

# =============================================================================
# Schritt 3: .env konfigurieren
# =============================================================================

echo "Schritt 3: Konfiguriere Umgebungsvariablen..."
echo ""

if [ ! -f .env ]; then
    echo "Suche nach .env Vorlage-Dateien..."

    # Debug: Zeige aktuelles Verzeichnis und SCRIPT_DIR
    echo "Aktuelles Verzeichnis: $(pwd)"
    echo "SCRIPT_DIR: $SCRIPT_DIR"

    TEMPLATE_FOUND=false

    # 1. Versuche env.example.txt aus dem Quellverzeichnis
    if [ -f "$SCRIPT_DIR/env.example.txt" ]; then
        echo "✓ Gefunden: $SCRIPT_DIR/env.example.txt"
        cp "$SCRIPT_DIR/env.example.txt" .env
        TEMPLATE_FOUND=true
    fi

    # 2. Versuche lokale env.example.txt
    if [ ! "$TEMPLATE_FOUND" = true ] && [ -f "env.example.txt" ]; then
        echo "✓ Gefunden: $(pwd)/env.example.txt"
        cp "env.example.txt" .env
        TEMPLATE_FOUND=true
    fi

    # 3. Versuche .env.example aus dem Quellverzeichnis
    if [ ! "$TEMPLATE_FOUND" = true ] && [ -f "$SCRIPT_DIR/.env.example" ]; then
        echo "✓ Gefunden: $SCRIPT_DIR/.env.example"
        cp "$SCRIPT_DIR/.env.example" .env
        TEMPLATE_FOUND=true
    fi

    # 4. Versuche lokale .env.example
    if [ ! "$TEMPLATE_FOUND" = true ] && [ -f ".env.example" ]; then
        echo "✓ Gefunden: $(pwd)/.env.example"
        cp ".env.example" .env
        TEMPLATE_FOUND=true
    fi

    # 5. Versuche .env.template (als letzten Ausweg)
    if [ ! "$TEMPLATE_FOUND" = true ] && [ -f "$SCRIPT_DIR/.env.template" ]; then
        echo "✓ Gefunden: $SCRIPT_DIR/.env.template"
        cp "$SCRIPT_DIR/.env.template" .env
        TEMPLATE_FOUND=true
    fi

    if [ "$TEMPLATE_FOUND" = true ]; then
        print_warning ".env Datei erstellt - BITTE API KEYS EINTRAGEN!"
        echo ""
        echo "  Editiere .env:"
        echo "  nano $INSTALL_DIR/.env"
        echo ""
        echo "  Mindestens erforderlich:"
        echo "  - KRAKEN_API_KEY"
        echo "  - KRAKEN_API_SECRET"
        echo ""
    else
        print_error "Keine .env Vorlage gefunden!"
        echo ""
        echo "Debug-Informationen:"
        echo "  Script-Verzeichnis: $SCRIPT_DIR"
        echo "  Install-Verzeichnis: $(pwd)"
        echo "  Gesucht nach:"
        ls -la "$SCRIPT_DIR" | grep -E "(env\.example|\.env\.template)" || echo "  Keine Template-Dateien im Script-Verzeichnis gefunden"
        ls -la . | grep -E "(env\.example|\.env\.template)" || echo "  Keine Template-Dateien im aktuellen Verzeichnis gefunden"
        echo ""
        echo "Bitte stellen Sie sicher, dass eine Template-Datei existiert."
        exit 1
    fi
else
    print_success ".env bereits vorhanden"
fi

# =============================================================================
# Schritt 4: Docker Image bauen
# =============================================================================

echo "Schritt 4: Baue Docker Image..."
echo ""

sudo docker-compose build --no-cache

print_success "Docker Image gebaut"
echo ""

# =============================================================================
# Schritt 5: Initial Training (Optional)
# =============================================================================

echo "Schritt 5: Initial Training..."
echo ""

read -p "Möchten Sie jetzt das Initial Training durchführen? (15-20 Min) [y/N]: " -n 1 -r
echo ""

if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "Starte Training (dies kann 15-20 Minuten dauern)..."
    sudo docker-compose --profile training up training
    print_success "Training abgeschlossen"
else
    print_warning "Training übersprungen"
    echo "  Sie können es später manuell starten:"
    echo "  docker-compose --profile training up training"
fi

echo ""

# =============================================================================
# Schritt 6: Bot starten
# =============================================================================

echo "Schritt 6: Starte Trading Bot..."
echo ""

sudo docker-compose up -d trading-bot

sleep 5

# Status prüfen
if sudo docker ps | grep -q "kraken-trading-bot"; then
    print_success "Trading Bot läuft!"
    echo ""
    echo "  Container Status:"
    sudo docker-compose ps
    echo ""
    echo "  Logs anzeigen:"
    echo "  sudo docker-compose logs -f trading-bot"
else
    print_error "Trading Bot konnte nicht gestartet werden!"
    echo ""
    echo "  Prüfe Logs:"
    echo "  sudo docker-compose logs trading-bot"
    exit 1
fi

echo ""

# =============================================================================
# Fertig!
# =============================================================================

echo "============================================================"
echo "  ✅ Deployment abgeschlossen!"
echo "============================================================"
echo ""
echo "📊 Nützliche Kommandos:"
echo ""
echo "  Logs anzeigen:"
echo "    docker-compose logs -f trading-bot"
echo ""
echo "  Learning Monitor:"
echo "    docker-compose run --rm learning-monitor"
echo ""
echo "  Bot stoppen:"
echo "    docker-compose stop trading-bot"
echo ""
echo "  Bot neustarten:"
echo "    docker-compose restart trading-bot"
echo ""
echo "  Status prüfen:"
echo "    docker-compose ps"
echo ""
echo "📁 Installationsverzeichnis:"
echo "  $INSTALL_DIR"
echo ""
echo "🎉 Viel Erfolg mit dem Trading Bot!"
echo ""
