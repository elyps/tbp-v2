#!/usr/bin/env python
"""Checks database for dashboard issues."""
import sqlite3

conn = sqlite3.connect('trading_bot.db')
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

# Check trades
cursor.execute('SELECT trade_id, symbol, action, status, timestamp FROM trades ORDER BY timestamp DESC LIMIT 10')
trades = cursor.fetchall()
print("="*60)
print("TRADES in Database:")
print("="*60)
for row in trades:
    print(f"  {dict(row)}")

# Count by status
cursor.execute("SELECT status, COUNT(*) as count FROM trades GROUP BY status")
status_counts = cursor.fetchall()
print("\nTrade Status Counts:")
for row in status_counts:
    print(f"  {row['status']}: {row['count']}")

# Check positions
cursor.execute('SELECT * FROM positions')
positions = cursor.fetchall()
print("\n" + "="*60)
print("POSITIONS in Database:")
print("="*60)
for row in positions:
    print(f"  {dict(row)}")

# Check portfolio
cursor.execute('SELECT * FROM portfolio ORDER BY id DESC LIMIT 1')
portfolio = cursor.fetchone()
print("\n" + "="*60)
print("PORTFOLIO in Database:")
print("="*60)
if portfolio:
    print(f"  {dict(portfolio)}")
else:
    print("  No portfolio data")

conn.close()
