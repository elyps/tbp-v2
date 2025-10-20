from trading_bot.database import get_database

db = get_database()
trades = db.get_trades(limit=10)

print("=== TRADES IN DATABASE ===\n")
for i, t in enumerate(trades, 1):
    print(f"{i}. {t['symbol']} {t['action'].upper()} @ {t['price']:.2f}")
    print(f"   Status: {t['status']}")
    print(f"   Stop-Loss: {t.get('stop_loss')}")
    print(f"   Take-Profit: {t.get('take_profit')}")
    print()

print(f"\nTotal: {len(trades)} trades")
print(f"Open: {len([t for t in trades if t['status'] == 'open'])}")
print(f"Closed: {len([t for t in trades if t['status'] == 'closed'])}")
