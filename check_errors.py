with open('logs/trading_bot.log', 'r', encoding='utf-8') as f:
    lines = f.readlines()

print("=== LETZTE 30 ZEILEN (Trade, ERROR, Fehler) ===\n")

relevant = [l for l in lines[-100:] if any(word in l for word in ['Trade', 'ERROR', 'Fehler', 'trade', 'BUY', 'SELL'])]

for line in relevant[-30:]:
    print(line.strip())
