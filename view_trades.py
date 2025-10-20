#!/usr/bin/env python
"""
Trade-Viewer: Zeigt alle Trades detailliert an oder exportiert sie als CSV
"""

import json
import os
import csv
from datetime import datetime
from typing import List, Dict
import argparse


def load_portfolio() -> Dict:
    """Lädt das Portfolio mit allen Trades."""
    portfolio_file = 'portfolio_state.json'
    
    if not os.path.exists(portfolio_file):
        print("❌ Keine Portfolio-Datei gefunden!")
        return {'trades': []}
    
    try:
        with open(portfolio_file, 'r') as f:
            return json.load(f)
    except Exception as e:
        print(f"❌ Fehler beim Laden: {e}")
        return {'trades': []}


def format_datetime(timestamp_str: str) -> str:
    """Formatiert ISO-Timestamp."""
    try:
        dt = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
        return dt.strftime("%Y-%m-%d %H:%M:%S")
    except:
        return timestamp_str


def print_trade_summary(trades: List[Dict]):
    """Druckt eine Zusammenfassung der Trades."""
    if not trades:
        print("\n📭 Noch keine Trades vorhanden.\n")
        return
    
    total_trades = len(trades)
    buy_trades = sum(1 for t in trades if t.get('side') == 'buy')
    sell_trades = sum(1 for t in trades if t.get('side') == 'sell')
    
    # Berechne Gesamt-P&L
    total_pnl = sum(t.get('pnl', 0) for t in trades if t.get('side') == 'sell')
    winning_trades = sum(1 for t in trades if t.get('side') == 'sell' and t.get('pnl', 0) > 0)
    losing_trades = sum(1 for t in trades if t.get('side') == 'sell' and t.get('pnl', 0) < 0)
    
    print("\n" + "="*80)
    print("📊 TRADE ZUSAMMENFASSUNG")
    print("="*80)
    print(f"Gesamt Trades:       {total_trades}")
    print(f"  └─ Käufe:          {buy_trades}")
    print(f"  └─ Verkäufe:       {sell_trades}")
    print(f"\nGesamt P&L:          {total_pnl:+,.2f} €")
    print(f"Gewinn-Trades:       {winning_trades}")
    print(f"Verlust-Trades:      {losing_trades}")
    if winning_trades + losing_trades > 0:
        win_rate = (winning_trades / (winning_trades + losing_trades)) * 100
        print(f"Win Rate:            {win_rate:.1f}%")
    print("="*80 + "\n")


def print_all_trades(trades: List[Dict], limit: int = None):
    """Druckt alle Trades detailliert."""
    if not trades:
        print("\n📭 Noch keine Trades vorhanden.\n")
        return
    
    print("\n" + "="*120)
    print("📋 VOLLSTÄNDIGE TRADE-LISTE")
    print("="*120)
    print(f"{'#':<4} {'Zeit':<20} {'Seite':<6} {'Symbol':<12} {'Menge':<12} {'Preis':<14} {'Kosten':<14} {'P&L':<12} {'Strategie':<15}")
    print("-"*120)
    
    # Neueste zuerst
    display_trades = trades[::-1]
    if limit:
        display_trades = display_trades[:limit]
    
    for i, trade in enumerate(display_trades, 1):
        trade_time = format_datetime(trade.get('timestamp', 'N/A'))
        side = trade.get('side', 'N/A').upper()
        symbol = trade.get('symbol', 'N/A')
        amount = trade.get('amount', 0)
        price = trade.get('price', 0)
        cost = trade.get('cost', 0)
        pnl = trade.get('pnl', 0)
        strategy = trade.get('strategy', 'N/A')[:14]
        
        # Formatierung
        side_str = f"{'🟢' if side == 'BUY' else '🔴'} {side}"
        pnl_str = f"{pnl:+,.2f} €" if side == 'SELL' else "-"
        
        print(f"{i:<4} {trade_time:<20} {side_str:<8} {symbol:<12} {amount:<12.6f} "
              f"{price:>12,.2f} € {cost:>12,.2f} € {pnl_str:<12} {strategy:<15}")
    
    print("="*120 + "\n")


def export_to_csv(trades: List[Dict], filename: str = 'trades_export.csv'):
    """Exportiert Trades als CSV."""
    if not trades:
        print("\n❌ Keine Trades zum Exportieren.\n")
        return
    
    try:
        with open(filename, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            
            # Header
            writer.writerow([
                'Nummer', 'Zeitstempel', 'Seite', 'Symbol', 'Menge', 'Preis', 
                'Kosten', 'Gebühr', 'P&L', 'Strategie', 'Stop Loss', 'Take Profit'
            ])
            
            # Trades (chronologisch)
            for i, trade in enumerate(trades, 1):
                writer.writerow([
                    i,
                    trade.get('timestamp', ''),
                    trade.get('side', '').upper(),
                    trade.get('symbol', ''),
                    trade.get('amount', 0),
                    trade.get('price', 0),
                    trade.get('cost', 0),
                    trade.get('fee', 0),
                    trade.get('pnl', 0) if trade.get('side') == 'sell' else '',
                    trade.get('strategy', ''),
                    trade.get('stop_loss', ''),
                    trade.get('take_profit', '')
                ])
        
        print(f"\n✅ {len(trades)} Trades erfolgreich nach '{filename}' exportiert!\n")
        
    except Exception as e:
        print(f"\n❌ Fehler beim Exportieren: {e}\n")


def filter_trades(trades: List[Dict], symbol: str = None, side: str = None, 
                 strategy: str = None) -> List[Dict]:
    """Filtert Trades nach Kriterien."""
    filtered = trades
    
    if symbol:
        filtered = [t for t in filtered if t.get('symbol', '').upper() == symbol.upper()]
    
    if side:
        filtered = [t for t in filtered if t.get('side', '').upper() == side.upper()]
    
    if strategy:
        filtered = [t for t in filtered if strategy.lower() in t.get('strategy', '').lower()]
    
    return filtered


def main():
    parser = argparse.ArgumentParser(description='Trade-Viewer für Trading Bot')
    parser.add_argument('--export', '-e', action='store_true', help='Exportiere Trades als CSV')
    parser.add_argument('--output', '-o', default='trades_export.csv', help='Output-Dateiname für CSV')
    parser.add_argument('--limit', '-l', type=int, help='Begrenze Anzahl angezeigter Trades')
    parser.add_argument('--symbol', '-s', help='Filtere nach Symbol (z.B. BTC/EUR)')
    parser.add_argument('--side', help='Filtere nach Seite (buy/sell)')
    parser.add_argument('--strategy', help='Filtere nach Strategie')
    
    args = parser.parse_args()
    
    # Lade Portfolio
    portfolio = load_portfolio()
    trades = portfolio.get('trades', [])
    
    # Filter anwenden
    if args.symbol or args.side or args.strategy:
        original_count = len(trades)
        trades = filter_trades(trades, args.symbol, args.side, args.strategy)
        print(f"\n🔍 Filter angewendet: {len(trades)} von {original_count} Trades")
    
    # Zusammenfassung anzeigen
    print_trade_summary(trades)
    
    # Exportieren oder anzeigen
    if args.export:
        export_to_csv(trades, args.output)
    else:
        print_all_trades(trades, args.limit)


if __name__ == "__main__":
    main()
