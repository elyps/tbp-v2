"""Prüft ob SELL-Signale generiert werden."""

with open('logs/trading_bot.log', 'r', encoding='utf-8') as f:
    lines = f.readlines()

sell_count = 0
buy_count = 0

print("=== SELL vs BUY Signale ===\n")

for line in lines[-200:]:  # Letzte 200 Zeilen
    if "SELL" in line and "Signal" in line:
        print(f"SELL: {line.strip()}")
        sell_count += 1
    elif "BUY" in line and "Signal" in line:
        buy_count += 1

print(f"\n=== Zusammenfassung ===")
print(f"BUY Signale:  {buy_count}")
print(f"SELL Signale: {sell_count}")

if sell_count == 0:
    print("\n❌ PROBLEM: Bot generiert keine SELL-Signale!")
    print("   Der Bot kauft nur und verkauft nie.")
