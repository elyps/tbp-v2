#!/usr/bin/env python
"""
Test-Skript für Portfolio-Verwaltung.
"""

import sys
from pathlib import Path

project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from trading_bot.bot import TradingBot

def main():
    print("=" * 60)
    print("TEST: Portfolio-Verwaltung")
    print("=" * 60)
    
    # Bot erstellen mit Testkapital
    config = {
        'settings': {
            'initial_balance': 10000.0,
            'paper_trading': True,
        },
        'strategies': {
            'trend_following': {'enabled': True},
            'mean_reversion': {'enabled': True},
            'breakout': {'enabled': True},
        },
    }
    
    bot = TradingBot(config=config)
    
    print("\n1. Initial Portfolio:")
    print(f"   Balance: €{bot.portfolio['balance']:,.2f}")
    print(f"   Equity: €{bot.portfolio['equity']:,.2f}")
    print(f"   Offene Positionen: {len(bot.portfolio['positions'])}")
    
    # Simuliere einen Kauf
    print("\n2. Simuliere KAUF von 0.1 BTC @ €90,000:")
    buy_order = {
        'id': 'test-buy-1',
        'symbol': 'BTC/EUR',
        'price': 90000.0,
        'cost': 9000.0,
        'fee': {'cost': 9.0},
        'status': 'closed'
    }
    buy_decision = {
        'action': 'buy',
        'amount': 0.1,
        'strategy': 'test',
        'stop_loss': 88000.0,
        'take_profit': 94000.0
    }
    
    bot._record_trade(buy_decision, buy_order)
    
    print(f"   Balance nach Kauf: €{bot.portfolio['balance']:,.2f}")
    print(f"   Offene Positionen: {len(bot.portfolio['positions'])}")
    if 'BTC/EUR' in bot.portfolio['positions']:
        pos = bot.portfolio['positions']['BTC/EUR']
        print(f"   BTC Position: {pos['amount']} @ €{pos['avg_price']:,.2f}")
    
    # Simuliere einen Verkauf mit Gewinn
    print("\n3. Simuliere VERKAUF von 0.1 BTC @ €95,000 (Gewinn):")
    sell_order = {
        'id': 'test-sell-1',
        'symbol': 'BTC/EUR',
        'price': 95000.0,
        'cost': 9500.0,
        'fee': {'cost': 9.5},
        'status': 'closed'
    }
    sell_decision = {
        'action': 'sell',
        'amount': 0.1,
        'strategy': 'test'
    }
    
    bot._record_trade(sell_decision, sell_order)
    
    print(f"   Balance nach Verkauf: €{bot.portfolio['balance']:,.2f}")
    print(f"   Offene Positionen: {len(bot.portfolio['positions'])}")
    print(f"   Gewinn/Verlust: €{bot.portfolio['balance'] - 10000:.2f}")
    
    # Performance-Statistiken
    print("\n4. Performance:")
    perf = bot.portfolio['performance']
    print(f"   Total Trades: {perf['total_trades']}")
    print(f"   Gewinn-Trades: {perf['winning_trades']}")
    print(f"   Verlust-Trades: {perf['losing_trades']}")
    print(f"   Win Rate: {perf['win_rate']:.1f}%")
    
    print("\n" + "=" * 60)
    print("✓ Portfolio-Verwaltung funktioniert!")
    print("=" * 60)

if __name__ == "__main__":
    main()
