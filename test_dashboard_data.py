from trading_bot.database import get_database

db = get_database()

print("=== TEST DASHBOARD DATA LOADING ===\n")

# Was get_portfolio() zurückgibt
portfolio = db.get_portfolio()
print("📊 db.get_portfolio():")
if portfolio:
    print(f"  Balance: €{portfolio.get('balance', 'N/A')}")
    print(f"  Equity: €{portfolio.get('equity', 'N/A')}")
    print(f"  Total Trades: {portfolio.get('total_trades', 'N/A')}")
    print(f"  Total P&L: €{portfolio.get('total_pnl', 'N/A')}")
else:
    print("  ❌ NONE/EMPTY!")

print()

# Positionen
positions = db.get_all_positions()
print(f"📍 Positionen: {len(positions)}")
if positions:
    for p in positions:
        print(f"  {p['symbol']}: {p['amount']:.4f} @ €{p['entry_price']:.2f}")

print()

# Trades
trades = db.get_trades(limit=5)
print(f"📋 Trades: {len(trades)}")

print()

# Statistiken
stats = db.get_trade_statistics()
print("📈 Statistiken:")
print(f"  Total: {stats.get('total_trades', 0)}")
print(f"  Wins: {stats.get('winning_trades', 0)}")
print(f"  P&L: €{stats.get('total_pnl', 0):.2f}")
