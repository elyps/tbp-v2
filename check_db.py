from trading_bot.database import get_database

db = get_database()

trades = db.get_trades(limit=10)
positions = db.get_all_positions()

print(f"Trades in DB: {len(trades)}")
print(f"Positionen in DB: {len(positions)}")
print()

if trades:
    print("Trades:")
    for t in trades:
        print(f"  - {t['symbol']} {t['action']} {t['amount']} @ {t['price']} - Status: {t['status']}")
else:
    print("Keine Trades in DB!")

print()

if positions:
    print("Positionen:")
    for p in positions:
        print(f"  - {p['symbol']}: {p['amount']} @ {p['entry_price']}")
else:
    print("Keine Positionen in DB!")
