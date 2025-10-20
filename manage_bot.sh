#!/bin/bash
# Trading Bot - Homeserver Management Script

set -e

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$PROJECT_DIR"

# Farben für Output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Hilfsfunktionen
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Status prüfen
check_status() {
    log_info "Prüfe Bot Status..."
    if docker compose ps | grep -q "Up"; then
        log_success "Bot läuft!"
        docker compose ps
    else
        log_warning "Bot läuft nicht"
        docker compose ps
    fi
}

# Bot starten
start_bot() {
    log_info "Starte Trading Bot..."

    # Prüfe ob .env existiert
    if [ ! -f .env ]; then
        log_error ".env Datei nicht gefunden! Kopiere .env.template und konfiguriere API Keys."
        exit 1
    fi

    # Container bauen falls nötig
    if [ "$1" = "--build" ]; then
        log_info "Baue Container neu..."
        docker compose build --no-cache
    fi

    # Bot starten
    docker compose up -d trading-bot
    log_success "Bot gestartet!"

    # Warte kurz und zeige Status
    sleep 3
    check_status
}

# Bot stoppen
stop_bot() {
    log_info "Stoppe Trading Bot..."
    docker compose down
    log_success "Bot gestoppt!"
}

# Logs anzeigen
show_logs() {
    if [ "$1" = "--monitor" ]; then
        log_info "Starte Live Monitoring..."
        docker compose up bot-monitor
    else
        log_info "Zeige Bot Logs..."
        docker compose logs -f trading-bot
    fi
}

# Backup erstellen
create_backup() {
    TIMESTAMP=$(date +%Y%m%d_%H%M%S)
    BACKUP_FILE="backup_${TIMESTAMP}.tar.gz"

    log_info "Erstelle Backup: $BACKUP_FILE"
    tar -czf "$BACKUP_FILE" logs/ models/ portfolio/ .env

    log_success "Backup erstellt: $BACKUP_FILE"

    # Alte Backups löschen (behalte letzte 5)
    log_info "Räume alte Backups auf..."
    ls -t backup_*.tar.gz 2>/dev/null | tail -n +6 | xargs -r rm
}

# System info
show_info() {
    echo "=== Trading Bot System Info ==="
    echo "Projekt: $PROJECT_DIR"
    echo "Docker Version: $(docker --version)"
    echo "Compose Version: $(docker compose version)"
    echo ""
    echo "Container Status:"
    docker compose ps
    echo ""
    echo "Festplattenspeicher:"
    df -h "$PROJECT_DIR"
    echo ""
    echo "RAM Usage:"
    free -h
}

# Update durchführen
update_bot() {
    log_info "Aktualisiere Trading Bot..."

    # Backup vor Update
    create_backup

    # Code aktualisieren
    if [ -d .git ]; then
        git pull
        log_success "Code aktualisiert"
    else
        log_warning "Kein Git Repository - manuelles Update erforderlich"
    fi

    # Container neu bauen
    docker compose build --no-cache
    log_success "Container neu gebaut"

    # Bot neustarten
    docker compose up -d trading-bot
    log_success "Bot neugestartet"
}

# Hauptmenü
show_menu() {
    echo "=== Trading Bot Management ==="
    echo "1) Status prüfen"
    echo "2) Bot starten"
    echo "3) Bot stoppen"
    echo "4) Logs anzeigen"
    echo "5) Live Monitoring"
    echo "6) Backup erstellen"
    echo "7) System Info"
    echo "8) Update durchführen"
    echo "9) Bot mit neuem Build starten"
    echo "0) Beenden"
    echo ""
}

# Hauptlogik
case "${1:-}" in
    "status")
        check_status
        ;;
    "start")
        start_bot "$2"
        ;;
    "stop")
        stop_bot
        ;;
    "logs")
        show_logs
        ;;
    "monitor")
        show_logs --monitor
        ;;
    "backup")
        create_backup
        ;;
    "info")
        show_info
        ;;
    "update")
        update_bot
        ;;
    "rebuild")
        start_bot --build
        ;;
    "menu"|*)
        while true; do
            show_menu
            read -p "Wähle Option (0-9): " choice
            case $choice in
                1) check_status ;;
                2) start_bot ;;
                3) stop_bot ;;
                4) show_logs ;;
                5) show_logs --monitor ;;
                6) create_backup ;;
                7) show_info ;;
                8) update_bot ;;
                9) start_bot --build ;;
                0) exit 0 ;;
                *) log_error "Ungültige Option" ;;
            esac
            echo ""
            read -p "Drücke Enter für Hauptmenü..."
        done
        ;;
esac
