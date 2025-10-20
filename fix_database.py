"""
Fügt stop_loss und take_profit Spalten zur trades Tabelle hinzu
"""

import sqlite3

conn = sqlite3.connect('trading_bot.db')
cursor = conn.cursor()

print("Füge stop_loss und take_profit Spalten hinzu...\n")

try:
    cursor.execute("ALTER TABLE trades ADD COLUMN stop_loss REAL")
    print("✅ stop_loss Spalte hinzugefügt")
except sqlite3.OperationalError as e:
    if "duplicate column" in str(e):
        print("⚠️  stop_loss Spalte existiert bereits")
    else:
        print(f"❌ Fehler: {e}")

try:
    cursor.execute("ALTER TABLE trades ADD COLUMN take_profit REAL")
    print("✅ take_profit Spalte hinzugefügt")
except sqlite3.OperationalError as e:
    if "duplicate column" in str(e):
        print("⚠️  take_profit Spalte existiert bereits")
    else:
        print(f"❌ Fehler: {e}")

conn.commit()
conn.close()

print("\n✅ Datenbank aktualisiert!")
print("\nJetzt kannst du den Bot neu starten.")
