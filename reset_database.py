"""
Dieses Skript setzt die SQLite-Datenbank des Trading-Bots zurück,
indem es die Datenbankdatei löscht.

WICHTIG: Alle gespeicherten Trades, Portfolio-Daten und Trainings-Samples
werden unwiderruflich gelöscht!
"""

import os
import sys

DB_FILE = 'trading_bot.db'

def reset_database():
    """Löscht die Datenbankdatei, falls sie existiert."""
    if os.path.exists(DB_FILE):
        try:
            os.remove(DB_FILE)
            print(f"✅ Datenbank '{DB_FILE}' erfolgreich zurückgesetzt.")
            print("   Der Bot wird beim nächsten Start eine neue, leere Datenbank erstellen.")
        except OSError as e:
            print(f"❌ Fehler beim Löschen der Datenbank: {e}")
            sys.exit(1)
    else:
        print(f"ℹ️ Datenbank '{DB_FILE}' existiert nicht. Nichts zu tun.")

if __name__ == "__main__":
    reset_database()