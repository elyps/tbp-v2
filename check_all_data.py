from trading_bot.database import get_database

db = get_database()

print("=== DATABASE STATUS ===\n")

# Portfolio
portfolio = db.get_portfolio()
print("📊 PORTFOLIO:")
if portfolio:
    print(f"  Balance: €{portfolio['balance']:.2f}")
    print(f"  Equity: €{portfolio['equity']:.2f}")
else:
    print("  ❌ LEER!")

print()

# Positionen
positions = db.get_all_positions()
print(f"📍 POSITIONEN: {len(positions)}")
for p in positions:
    print(f"  {p['symbol']}: {p['amount']:.6f} @ €{p['entry_price']:.2f}")

print()

# Trades
trades = db.get_trades(limit=10)
print(f"📋 TRADES: {len(trades)}")
for t in trades:
    print(f"  {t['symbol']} {t['action'].upper()} @ €{t['price']:.2f} - {t['status']}")
    if t.get('stop_loss'):
        print(f"    SL: €{t['stop_loss']:.2f}, TP: €{t.get('take_profit', 0):.2f}")

print()

# Prüfe ob Bot läuft
import os
if os.path.exists('logs/trading_bot.log'):
    with open('logs/trading_bot.log', 'r') as f:
        lines = f.readlines()
        if lines:
            last_line = lines[-1]
            print(f"📝 LETZTER LOG: {last_line.strip()[:80]}...")
