import sqlite3

conn = sqlite3.connect('trading_bot.db')
cursor = conn.cursor()

# Hole Schema für trades Tabelle
cursor.execute("PRAGMA table_info(trades)")
columns = cursor.fetchall()

print("=== TRADES TABLE SCHEMA ===\n")
for col in columns:
    print(f"{col[1]:<20} {col[2]:<10} {'NOT NULL' if col[3] else ''} {'PRIMARY KEY' if col[5] else ''}")

print(f"\n{'='*50}")
print("Checking for stop_loss and take_profit columns...")
print(f"{'='*50}\n")

column_names = [col[1] for col in columns]
if 'stop_loss' in column_names:
    print("✅ stop_loss column EXISTS")
else:
    print("❌ stop_loss column MISSING!")

if 'take_profit' in column_names:
    print("✅ take_profit column EXISTS")
else:
    print("❌ take_profit column MISSING!")

conn.close()
