"""
Reset Bot: Löscht alle Trades und setzt Portfolio zurück
Notwendig nach Database-Schema Änderungen
"""

import sqlite3

conn = sqlite3.connect('trading_bot.db')
cursor = conn.cursor()

print("🔄 RESET TRADING BOT\n")
print("="*50)

# Zähle alte Trades
cursor.execute("SELECT COUNT(*) FROM trades")
old_count = cursor.fetchone()[0]
print(f"Alte Trades: {old_count}")

# Lösche alle Trades
cursor.execute("DELETE FROM trades")
print("✅ Alle Trades gelöscht")

# Lösche alle Positionen
cursor.execute("DELETE FROM positions")
print("✅ Alle Positionen gelöscht")

# Reset Portfolio
cursor.execute("DELETE FROM portfolio")
cursor.execute("""
    INSERT INTO portfolio (balance, equity, total_trades, winning_trades, losing_trades, total_pnl)
    VALUES (1000.0, 1000.0, 0, 0, 0, 0.0)
""")
print("✅ Portfolio zurückgesetzt auf 1000€")

conn.commit()
conn.close()

print("="*50)
print("\n✅ Bot wurde zurückgesetzt!")
print("\n📊 Neuer Status:")
print("   - Balance: 1000€")
print("   - Trades: 0")
print("   - Positionen: 0")
print("\n🚀 Du kannst jetzt den Bot neu starten:")
print("   python main.py")
