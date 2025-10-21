#!/bin/bash

# =================================================================
# ==      Automatisches Update-Skript für den Trading-Bot      ==
# =================================================================
#
# Dieses Skript automatisiert den gesamten Update-Prozess:
# 1. Stoppt den laufenden Bot (in der 'screen'-Sitzung).
# 2. Erstellt ein Backup des aktuellen Stands.
# 3. Zieht die neuesten Änderungen aus dem Git-Repository.
# 4. Aktualisiert die Python-Abhängigkeiten effizient.
# 5. Startet den Bot in einer neuen 'screen'-Sitzung.
#
# ANWENDUNG:
# Führen Sie das Skript einfach mit ./update_bot.sh aus.
# =================================================================

# --- Konfiguration ---
# Passen Sie diese Variablen bei Bedarf an
BOT_DIR="/home/elyps/tbp-v2" # Absoluter Pfad zu Ihrem Bot-Verzeichnis
VENV_PATH="$BOT_DIR/.venv/bin/activate" # Pfad zur virtuellen Umgebung
SCREEN_NAME="tradingbot" # Name der screen-Sitzung
BACKUP_DIR="/home/elyps/bot_backups" # Verzeichnis für Backups
GIT_BRANCH="dev" # Der Git-Branch, der aktualisiert werden soll

# --- Skript-Logik ---
# Beendet das Skript bei Fehlern
set -e

# Funktion für farbige Ausgaben
print_info() {
    echo -e "\n\e[1;34m[INFO]\e[0m $1"
}

print_success() {
    echo -e "\e[1;32m[SUCCESS]\e[0m $1"
}

print_error() {
    echo -e "\e[1;31m[ERROR]\e[0m $1" >&2
    exit 1
}

# --- Start des Updates ---
print_info "Starte Update-Prozess für den Trading-Bot..."
cd "$BOT_DIR"

# 1. Bot stoppen
print_info "Suche und stoppe laufende Bot-Sitzungen mit dem Namen '$SCREEN_NAME'..."
# Finde alle screen-Sitzungen, die den Namen tragen, und extrahiere ihre IDs
SESSION_IDS=$(screen -ls | grep -o "[0-9]*\.$SCREEN_NAME" | awk -F. '{print $1}')

if [ -n "$SESSION_IDS" ]; then
    for SESSION_ID in $SESSION_IDS; do
        print_info "Sende Stopp-Signal (Strg+C) an Sitzung $SESSION_ID.$SCREEN_NAME..."
        screen -S "$SESSION_ID.$SCREEN_NAME" -X stuff $'\003'
    done

    print_info "Warte 5 Sekunden, damit die Prozesse sich beenden können..."
    sleep 5

    for SESSION_ID in $SESSION_IDS; do
        if screen -list | grep -q "$SESSION_ID.$SCREEN_NAME"; then
            print_info "Beende verbleibende Sitzung $SESSION_ID.$SCREEN_NAME..."
            screen -S "$SESSION_ID.$SCREEN_NAME" -X quit
        fi
    done
    print_success "Alle Bot-Sitzungen wurden gestoppt."
else
    print_info "Keine laufenden Sitzungen mit dem Namen '$SCREEN_NAME' gefunden. Überspringe Stopp."
fi

# 2. Backup erstellen
print_info "Erstelle ein Backup des aktuellen Zustands..."
mkdir -p "$BACKUP_DIR"
BACKUP_FILE="$BACKUP_DIR/bot_backup_$(date +%Y%m%d_%H%M%S).tar.gz"
tar -czf "$BACKUP_FILE" -C "$BOT_DIR" .
print_success "Backup erstellt unter: $BACKUP_FILE"

# 3. Code aus Git aktualisieren
print_info "Ziehe die neuesten Änderungen aus dem Git-Repository (Branch: $GIT_BRANCH)..."
if ! git pull origin "$GIT_BRANCH"; then
    print_error "Git Pull fehlgeschlagen. Bitte beheben Sie die Konflikte manuell."
fi
print_success "Code erfolgreich aktualisiert."

# 4. Python-Abhängigkeiten aktualisieren
print_info "Aktualisiere Python-Abhängigkeiten..."
# Aktiviere die virtuelle Umgebung für diesen Teil des Skripts
source "$VENV_PATH"
if ! pip install -r requirements.txt; then
    deactivate
    print_error "Installation der Abhängigkeiten fehlgeschlagen."
fi
# Optional: Zusätzliche Daten herunterladen, falls nötig
# python -m textblob.download_corpora
deactivate
print_success "Abhängigkeiten sind auf dem neuesten Stand."

# 5. Bot neu starten
print_info "Starte den Bot in einer neuen screen-Sitzung '$SCREEN_NAME'..."
# Startet eine "detached" screen-Sitzung und führt den Bot darin aus
screen -dmS "$SCREEN_NAME" bash -c "cd $BOT_DIR && source $VENV_PATH && python main.py"

# Überprüfen, ob die Sitzung gestartet wurde
sleep 2
if screen -list | grep -q "$SCREEN_NAME"; then
    print_success "Bot wurde erfolgreich im Hintergrund gestartet."
    echo "Verwenden Sie 'screen -r $SCREEN_NAME', um die Logs anzuzeigen."
else
    print_error "Der Bot konnte nicht gestartet werden. Bitte prüfen Sie die Logs."
fi

echo -e "\n\e[1;32m✅ Update-Prozess erfolgreich abgeschlossen!\e[0m"
