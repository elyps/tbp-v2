"""
Live-Monitoring Dashboard für den Trading Bot
Zeigt Portfolio, Performance und aktuelle Signale in Echtzeit
Nutzt SQLite Datenbank für alle Daten
"""

import os
import sys
import time
import json
from datetime import datetime
from typing import Dict
from pathlib import Path

# Add trading_bot to path
sys.path.insert(0, str(Path(__file__).parent))

from trading_bot.database import get_database

def clear_screen():
    """Löscht den Bildschirm."""
    os.system('cls' if os.name == 'nt' else 'clear')


def load_portfolio(db) -> Dict:
    """Lädt das aktuelle Portfolio aus der SQLite Datenbank."""
    # Portfolio aus DB
    portfolio = db.get_portfolio()
    
    if not portfolio:
        # Fallback: Standard-Portfolio
        return {
            'balance': 10000.0,
            'equity': 10000.0,
            'positions': {},
            'trades': [],
            'performance': {
                'total_trades': 0,
                'winning_trades': 0,
                'losing_trades': 0,
                'win_rate': 0.0,
                'profit_factor': 0.0,
                'max_drawdown': 0.0,
            }
        }
    
    # Positionen aus DB
    positions_list = db.get_all_positions()
    positions = {pos['symbol']: pos for pos in positions_list}
    
    # Trades aus DB (ALLE Trades - offen + geschlossen)
    all_trades = db.get_trades(limit=100)
    
    # Stats aus DB (nur geschlossene Trades)
    closed_stats = db.get_trade_statistics()
    
    # Berechne Gesamt-Trades (inkl. offene)
    total_trades_count = len(all_trades)
    open_trades_count = len([t for t in all_trades if t['status'] == 'open'])
    
    return {
        'balance': portfolio['balance'],
        'equity': portfolio['equity'],
        'positions': positions,
        'trades': all_trades,
        'performance': {
            'total_trades': total_trades_count,
            'open_trades': open_trades_count,
            'closed_trades': closed_stats.get('total_trades', 0),
            'winning_trades': closed_stats.get('winning_trades', 0),
            'losing_trades': closed_stats.get('losing_trades', 0),
            'win_rate': closed_stats.get('win_rate', 0.0),
            'profit_factor': 0.0,
            'max_drawdown': portfolio.get('max_drawdown', 0.0),
        }
    }


def get_recent_logs(n: int = 10) -> list:
    """Holt die letzten N Log-Zeilen."""
    log_file = 'logs/trading_bot.log'
    
    if not os.path.exists(log_file):
        return ["Keine Logs gefunden"]
    
    try:
        with open(log_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            return lines[-n:] if len(lines) > n else lines
    except:
        return ["Fehler beim Lesen der Logs"]


def format_currency(value: float) -> str:
    """Formatiert Währungswerte."""
    return f"€{value:,.2f}"


def format_percentage(value: float) -> str:
    """Formatiert Prozentangaben."""
    return f"{value:.2f}%"


def format_datetime(timestamp_str: str) -> str:
    """Formatiert ISO-Timestamp zu lesbarem Format."""
    try:
        dt = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
        return dt.strftime("%d.%m %H:%M:%S")
    except:
        return timestamp_str[:16] if len(timestamp_str) > 16 else timestamp_str


def print_dashboard(portfolio: Dict):
    """Druckt das Dashboard."""
    clear_screen()
    
    # Header
    print("╔" + "="*78 + "╗")
    print("║" + " "*20 + "🚀 KRAKEN TRADING BOT MONITOR 🚀" + " "*25 + "║")
    print("╚" + "="*78 + "╝")
    print()
    
    # Aktualisierungszeit
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"📅 Letzte Aktualisierung: {now}")
    print(f"🔄 Mode: PAPER TRADING (Simuliert)")
    print()
    
    # Portfolio-Übersicht
    print("┌─────────────────────────────────────────────────────────────────────────────┐")
    print("│ 💰 PORTFOLIO ÜBERSICHT                                                      │")
    print("├─────────────────────────────────────────────────────────────────────────────┤")
    
    balance = portfolio.get('balance', 0)
    equity = portfolio.get('equity', 0)
    profit = equity - 10000.0  # Startkapital war 10000
    profit_pct = (profit / 10000.0) * 100 if profit != 0 else 0
    
    profit_symbol = "📈" if profit >= 0 else "📉"
    profit_color = "+" if profit >= 0 else ""
    
    print(f"│  Startkapital:     {format_currency(10000.0):>20}                          │")
    print(f"│  Aktuelles Equity: {format_currency(equity):>20}                          │")
    print(f"│  Cash Balance:     {format_currency(balance):>20}                          │")
    print(f"│  {profit_symbol} Gewinn/Verlust: {profit_color}{format_currency(profit):>20} ({format_percentage(profit_pct):>8})       │")
    print("└─────────────────────────────────────────────────────────────────────────────┘")
    print()
    
    # Offene Positionen
    positions = portfolio.get('positions', {})
    print("┌─────────────────────────────────────────────────────────────────────────────┐")
    print("│ 📊 OFFENE POSITIONEN                                                        │")
    print("├─────────────────────────────────────────────────────────────────────────────┤")
    
    if positions:
        for symbol, position in positions.items():
            amount = position.get('amount', 0)
            entry_price = position.get('entry_price', 0)
            current_price = position.get('current_price', entry_price)
            pnl = (current_price - entry_price) * amount
            pnl_pct = ((current_price / entry_price) - 1) * 100 if entry_price > 0 else 0
            
            pnl_symbol = "+" if pnl >= 0 else ""
            print(f"│  {symbol:12} │ Menge: {amount:8.4f} │ Entry: {format_currency(entry_price):>12} │")
            print(f"│               │ P&L: {pnl_symbol}{format_currency(pnl):>10} ({format_percentage(pnl_pct):>8})      │")
    else:
        print("│  Keine offenen Positionen                                                  │")
    
    print("└─────────────────────────────────────────────────────────────────────────────┘")
    print()
    
    # Performance-Statistiken
    perf = portfolio.get('performance', {})
    print("┌─────────────────────────────────────────────────────────────────────────────┐")
    print("│ 📈 PERFORMANCE STATISTIKEN                                                  │")
    print("├─────────────────────────────────────────────────────────────────────────────┤")
    
    total_trades = perf.get('total_trades', 0)
    open_trades = perf.get('open_trades', 0)
    closed_trades = perf.get('closed_trades', 0)
    winning_trades = perf.get('winning_trades', 0)
    losing_trades = perf.get('losing_trades', 0)
    win_rate = perf.get('win_rate', 0)
    max_dd = perf.get('max_drawdown', 0)
    
    print(f"│  Gesamt Trades:     {total_trades:>8} (Offen: {open_trades}, Geschlossen: {closed_trades}){'':>{42-len(str(total_trades))-len(str(open_trades))-len(str(closed_trades))-23}}│")
    print(f"│  Gewinn-Trades:     {winning_trades:>8}                                          │")
    print(f"│  Verlust-Trades:    {losing_trades:>8}                                          │")
    print(f"│  Win Rate:          {format_percentage(win_rate):>8}                                     │")
    print(f"│  Max Drawdown:      {format_percentage(max_dd):>8}                                     │")
    print("└─────────────────────────────────────────────────────────────────────────────┘")
    print()
    
    # Trade-Historie
    print("┌─────────────────────────────────────────────────────────────────────────────┐")
    print("│ 📋 TRADE HISTORIE (Letzte 10 Trades)                                       │")
    print("├─────────────────────────────────────────────────────────────────────────────┤")
    
    trades = portfolio.get('trades', [])
    if trades:
        # Zeige die letzten 10 Trades in umgekehrter Reihenfolge (neueste zuerst)
        recent_trades = trades[-10:]
        recent_trades.reverse()
        
        for i, trade in enumerate(recent_trades, 1):
            trade_time = format_datetime(trade.get('timestamp', ''))
            symbol = trade.get('symbol', 'N/A')
            side = trade.get('side', '').upper()
            amount = trade.get('amount', 0)
            price = trade.get('price', 0)
            cost = trade.get('cost', 0)
            pnl = trade.get('pnl', 0)
            strategy = trade.get('strategy', 'N/A')
            
            # Side mit Emoji
            side_emoji = "🟢" if side == "BUY" else "🔴"
            
            # P&L Formatierung
            if side == "SELL" and pnl != 0:
                pnl_str = f"{'+' if pnl > 0 else ''}{pnl:.2f}€"
                pnl_display = f"P&L: {pnl_str}"
            else:
                pnl_display = "-"
            
            # Erste Zeile: Zeit, Symbol, Side
            print(f"│ {i:2}. {side_emoji} {side:4} {symbol:10} │ {trade_time:13} │ {strategy[:12]:12} │")
            # Zweite Zeile: Menge, Preis, Kosten, P&L
            print(f"│     Menge: {amount:8.6f} │ Preis: {price:>10,.2f}€ │ {pnl_display:20} │")
            
            if i < len(recent_trades):  # Trennlinie zwischen Trades
                print("│" + "─"*77 + "│")
    else:
        print("│  Noch keine Trades ausgeführt                                              │")
    
    print("└─────────────────────────────────────────────────────────────────────────────┘")
    print()
    
    # Letzte Aktivitäten (aus Logs)
    print("┌─────────────────────────────────────────────────────────────────────────────┐")
    print("│ 📝 LETZTE AKTIVITÄTEN                                                       │")
    print("├─────────────────────────────────────────────────────────────────────────────┤")
    
    recent_logs = get_recent_logs(6)
    for log_line in recent_logs:
        # Kürze lange Zeilen
        log_line = log_line.strip()
        if len(log_line) > 75:
            log_line = log_line[:72] + "..."
        print(f"│ {log_line:<75} │")
    
    print("└─────────────────────────────────────────────────────────────────────────────┘")
    print()
    
    # Footer
    print("💡 Drücke Ctrl+C zum Beenden")


def main():
    """Hauptfunktion für das Live-Monitoring."""
    print("\n🚀 Starte Trading Bot Monitor...\n")
    print("Überwache Bot-Aktivitäten in Echtzeit...")
    print("Nutzt SQLite Datenbank: trading_bot.db")
    print("(Stelle sicher, dass der Bot mit 'python main.py' läuft)\n")
    
    # SQLite Datenbank initialisieren
    db = get_database('trading_bot.db')
    print("✓ Datenbank verbunden\n")
    
    time.sleep(2)
    
    try:
        while True:
            portfolio = load_portfolio(db)
            print_dashboard(portfolio)
            time.sleep(5)  # Aktualisiere alle 5 Sekunden
            
    except KeyboardInterrupt:
        print("\n\n👋 Monitor wird beendet...\n")
        db.close()


if __name__ == "__main__":
    main()
