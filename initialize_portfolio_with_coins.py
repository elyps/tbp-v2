#!/usr/bin/env python
"""
Initialisiert das Portfolio mit einer Ausgangsposition.
Nützlich, um dem Bot zu erlauben, sofort zu verkaufen.
"""

import json
import os
from datetime import datetime

def initialize_portfolio():
    """Erstellt ein Portfolio mit Startpositionen."""
    
    # Definiere Startkapital und Positionen
    initial_balance = 10000.0  # €10,000 Startkapital
    
    # Beispiel: Kaufe zu aktuellen Preisen
    # Verteile das Kapital: 30% BTC, 30% ETH, 30% XRP, 10% Cash Reserve
    positions = {
        'BTC/EUR': {
            'amount': 0.03,  # 0.03 BTC
            'avg_price': 91800.0,  # Beispiel-Einstiegspreis
            'total_cost': 2754.0,  # 0.03 * 91800
            'side': 'long',
            'entry_time': datetime.utcnow().isoformat()
        },
        'ETH/EUR': {
            'amount': 0.9,  # 0.9 ETH
            'avg_price': 3400.0,
            'total_cost': 3060.0,  # 0.9 * 3400
            'side': 'long',
            'entry_time': datetime.utcnow().isoformat()
        },
        'XRP/EUR': {
            'amount': 1000.0,  # 1000 XRP
            'avg_price': 2.10,
            'total_cost': 2100.0,  # 1000 * 2.10
            'side': 'long',
            'entry_time': datetime.utcnow().isoformat()
        }
    }
    
    # Berechne verbleibende Balance
    total_invested = sum(pos['total_cost'] for pos in positions.values())
    remaining_balance = initial_balance - total_invested
    
    portfolio = {
        'balance': remaining_balance,
        'equity': initial_balance,
        'initial_balance': initial_balance,
        'positions': positions,
        'trades': [],
        'performance': {
            'total_trades': 0,
            'winning_trades': 0,
            'losing_trades': 0,
            'win_rate': 0.0,
            'profit_factor': 0.0,
            'max_drawdown': 0.0,
        },
        'last_updated': datetime.utcnow().isoformat()
    }
    
    # Speichern
    with open('portfolio_state.json', 'w') as f:
        json.dump(portfolio, f, indent=2)
    
    print("\n" + "="*60)
    print("✅ Portfolio mit Startpositionen initialisiert!")
    print("="*60)
    print(f"\nStartkapital:        €{initial_balance:,.2f}")
    print(f"Investiert:          €{total_invested:,.2f}")
    print(f"Cash Reserve:        €{remaining_balance:,.2f}")
    print("\nPositionen:")
    for symbol, pos in positions.items():
        print(f"  • {symbol:12} {pos['amount']:>10.6f} @ €{pos['avg_price']:>10,.2f}  (€{pos['total_cost']:>8,.2f})")
    print("\n" + "="*60)
    print("\n💡 Du kannst den Bot jetzt starten mit: python main.py")
    print("   Der Bot kann jetzt sofort Verkaufssignale ausführen!\n")

if __name__ == "__main__":
    # Prüfe ob Portfolio bereits existiert
    if os.path.exists('portfolio_state.json'):
        response = input("⚠️  Portfolio existiert bereits. Überschreiben? (ja/nein): ")
        if response.lower() not in ['ja', 'j', 'yes', 'y']:
            print("❌ Abgebrochen.")
            exit(0)
    
    initialize_portfolio()
