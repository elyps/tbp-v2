"""
Advanced Live-Monitoring Dashboard für den Trading Bot
Ausführliches Dashboard mit detaillierten Informationen und Statistiken
"""

import os
import sys
import time
from datetime import datetime, timedelta
from typing import Dict, List
from pathlib import Path

# Add trading_bot to path
sys.path.insert(0, str(Path(__file__).parent))

from trading_bot.database import get_database

# ANSI Farben für bessere Darstellung
class Colors:
    RESET = '\033[0m'
    BOLD = '\033[1m'
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    MAGENTA = '\033[95m'
    WHITE = '\033[97m'
    GRAY = '\033[90m'

def clear_screen():
    """Löscht den Bildschirm."""
    os.system('cls' if os.name == 'nt' else 'clear')


def format_currency(value: float, color: bool = False) -> str:
    """Formatiert Währungswerte mit optionaler Farbe."""
    formatted = f"€{value:,.2f}"
    if color:
        if value > 0:
            return f"{Colors.GREEN}{formatted}{Colors.RESET}"
        elif value < 0:
            return f"{Colors.RED}{formatted}{Colors.RESET}"
    return formatted


def format_percentage(value: float, color: bool = False, show_sign: bool = True) -> str:
    """Formatiert Prozentangaben mit optionaler Farbe."""
    sign = "+" if value > 0 and show_sign else ""
    formatted = f"{sign}{value:.2f}%"
    if color:
        if value > 0:
            return f"{Colors.GREEN}{formatted}{Colors.RESET}"
        elif value < 0:
            return f"{Colors.RED}{formatted}{Colors.RESET}"
    return formatted


def format_datetime(timestamp_str: str) -> str:
    """Formatiert ISO-Timestamp zu lesbarem Format."""
    try:
        dt = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
        return dt.strftime("%d.%m.%Y %H:%M:%S")
    except:
        return timestamp_str[:19] if len(timestamp_str) > 19 else timestamp_str


def format_time_ago(timestamp_str: str) -> str:
    """Berechnet 'vor X Minuten/Stunden'."""
    try:
        dt = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
        now = datetime.utcnow()
        delta = now - dt
        
        if delta.total_seconds() < 60:
            return "gerade eben"
        elif delta.total_seconds() < 3600:
            minutes = int(delta.total_seconds() / 60)
            return f"vor {minutes} Min"
        elif delta.total_seconds() < 86400:
            hours = int(delta.total_seconds() / 3600)
            return f"vor {hours} Std"
        else:
            days = int(delta.total_seconds() / 86400)
            return f"vor {days} Tagen"
    except:
        return "unbekannt"


def get_portfolio_data(db) -> Dict:
    """Holt Portfolio-Daten aus der Datenbank."""
    portfolio = db.get_portfolio()
    
    if not portfolio:
        portfolio = {
            'balance': 1000.0,
            'equity': 1000.0,
            'total_trades': 0,
            'winning_trades': 0,
            'losing_trades': 0,
            'total_pnl': 0.0,
            'max_drawdown': 0.0,
            'sharpe_ratio': 0.0,
        }
    
    # Positionen
    positions = db.get_all_positions()
    
    # Trades
    all_trades = db.get_trades(limit=200)
    
    # Statistiken
    stats = db.get_trade_statistics()
    
    return {
        'portfolio': portfolio,
        'positions': positions,
        'trades': all_trades,
        'stats': stats
    }


def print_header():
    """Druckt Header."""
    print()
    print(f"{Colors.BOLD}{Colors.CYAN}╔════════════════════════════════════════════════════════════════════════════════════════╗{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.CYAN}║{Colors.RESET}                  {Colors.BOLD}{Colors.YELLOW}🚀 KRAKEN TRADING BOT - ADVANCED MONITOR 🚀{Colors.RESET}                   {Colors.BOLD}{Colors.CYAN}║{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.CYAN}╚════════════════════════════════════════════════════════════════════════════════════════╝{Colors.RESET}")
    print()
    
    # Status-Zeile
    now = datetime.now().strftime("%d.%m.%Y %H:%M:%S")
    print(f"  {Colors.GRAY}🕐 Letzte Aktualisierung:{Colors.RESET} {now}")
    print(f"  {Colors.GRAY}💡 Mode:{Colors.RESET} {Colors.YELLOW}PAPER TRADING{Colors.RESET} (Simuliert)")
    print()


def print_portfolio_overview(data: Dict):
    """Druckt Portfolio-Übersicht."""
    portfolio = data['portfolio']
    stats = data['stats']
    
    balance = portfolio['balance']
    equity = portfolio['equity']
    total_pnl = stats.get('total_pnl', 0.0)
    pnl_percent = (total_pnl / 1000.0) * 100 if 1000.0 > 0 else 0.0
    
    print(f"{Colors.BOLD}{Colors.BLUE}┌─ 💰 PORTFOLIO ÜBERSICHT ────────────────────────────────────────────────────────────────┐{Colors.RESET}")
    print(f"{Colors.BLUE}│{Colors.RESET}")
    print(f"{Colors.BLUE}│{Colors.RESET}  {Colors.BOLD}Kapital:{Colors.RESET}")
    print(f"{Colors.BLUE}│{Colors.RESET}    Startkapital:          {format_currency(1000.0):>15}")
    print(f"{Colors.BLUE}│{Colors.RESET}    Cash Balance:          {format_currency(balance, True):>25}")
    print(f"{Colors.BLUE}│{Colors.RESET}    Gesamt Equity:         {format_currency(equity, True):>25}")
    print(f"{Colors.BLUE}│{Colors.RESET}")
    print(f"{Colors.BLUE}│{Colors.RESET}  {Colors.BOLD}Performance:{Colors.RESET}")
    print(f"{Colors.BLUE}│{Colors.RESET}    Gesamt P&L:            {format_currency(total_pnl, True):>25}")
    print(f"{Colors.BLUE}│{Colors.RESET}    ROI:                   {format_percentage(pnl_percent, True):>25}")
    print(f"{Colors.BLUE}│{Colors.RESET}    Max Drawdown:          {format_percentage(portfolio.get('max_drawdown', 0.0), True):>25}")
    print(f"{Colors.BLUE}│{Colors.RESET}    Sharpe Ratio:          {portfolio.get('sharpe_ratio', 0.0):>15.2f}")
    print(f"{Colors.BLUE}│{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BLUE}└─────────────────────────────────────────────────────────────────────────────────────────┘{Colors.RESET}")
    print()


def print_positions(data: Dict):
    """Druckt offene Positionen."""
    positions = data['positions']
    
    print(f"{Colors.BOLD}{Colors.MAGENTA}┌─ 📊 OFFENE POSITIONEN ──────────────────────────────────────────────────────────────────┐{Colors.RESET}")
    print(f"{Colors.MAGENTA}│{Colors.RESET}")
    
    if positions:
        total_position_value = 0
        total_unrealized_pnl = 0
        
        for pos in positions:
            symbol = pos['symbol']
            amount = pos['amount']
            entry_price = pos['entry_price']
            current_price = pos.get('current_price', entry_price)
            pnl = pos.get('pnl', 0.0)
            pnl_percent = pos.get('pnl_percent', 0.0)
            
            position_value = amount * current_price
            total_position_value += position_value
            total_unrealized_pnl += pnl
            
            opened_ago = format_time_ago(pos['opened_at'])
            
            print(f"{Colors.MAGENTA}│{Colors.RESET}  {Colors.BOLD}{symbol}{Colors.RESET}")
            print(f"{Colors.MAGENTA}│{Colors.RESET}    Menge:          {amount:>15.6f}")
            print(f"{Colors.MAGENTA}│{Colors.RESET}    Entry:          {format_currency(entry_price):>15}  ({opened_ago})")
            print(f"{Colors.MAGENTA}│{Colors.RESET}    Aktuell:        {format_currency(current_price):>15}")
            print(f"{Colors.MAGENTA}│{Colors.RESET}    Position Wert:  {format_currency(position_value):>15}")
            print(f"{Colors.MAGENTA}│{Colors.RESET}    Unrealized P&L: {format_currency(pnl, True):>25} ({format_percentage(pnl_percent, True)})")
            print(f"{Colors.MAGENTA}│{Colors.RESET}")
        
        print(f"{Colors.MAGENTA}│{Colors.RESET}  {Colors.BOLD}Gesamt:{Colors.RESET}")
        print(f"{Colors.MAGENTA}│{Colors.RESET}    Positionen:     {len(positions):>15}")
        print(f"{Colors.MAGENTA}│{Colors.RESET}    Gesamt Wert:    {format_currency(total_position_value):>15}")
        print(f"{Colors.MAGENTA}│{Colors.RESET}    Unrealized P&L: {format_currency(total_unrealized_pnl, True):>25}")
    else:
        print(f"{Colors.MAGENTA}│{Colors.RESET}  {Colors.GRAY}Keine offenen Positionen{Colors.RESET}")
    
    print(f"{Colors.MAGENTA}│{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.MAGENTA}└─────────────────────────────────────────────────────────────────────────────────────────┘{Colors.RESET}")
    print()


def print_trade_statistics(data: Dict):
    """Druckt Trade-Statistiken."""
    stats = data['stats']
    trades = data['trades']
    
    # Zähle offene Trades aus der Trade-Liste
    open_trades = len([t for t in trades if t['status'] == 'open'])
    
    # Geschlossene Trades aus Statistiken (nur closed trades werden gezählt)
    closed_trades = stats.get('total_trades', 0)
    
    # Gesamt = Offen + Geschlossen
    total_trades = open_trades + closed_trades
    
    winning_trades = stats.get('winning_trades', 0)
    losing_trades = stats.get('losing_trades', 0)
    win_rate = stats.get('win_rate', 0.0)
    avg_pnl = stats.get('avg_pnl', 0.0)
    max_profit = stats.get('max_profit', 0.0)
    max_loss = stats.get('max_loss', 0.0)
    
    print(f"{Colors.BOLD}{Colors.GREEN}┌─ 📈 TRADE STATISTIKEN ──────────────────────────────────────────────────────────────────┐{Colors.RESET}")
    print(f"{Colors.GREEN}│{Colors.RESET}")
    print(f"{Colors.GREEN}│{Colors.RESET}  {Colors.BOLD}Übersicht:{Colors.RESET}")
    print(f"{Colors.GREEN}│{Colors.RESET}    Gesamt Trades:      {total_trades:>15}")
    print(f"{Colors.GREEN}│{Colors.RESET}      ├─ Offen:          {Colors.YELLOW}{open_trades:>15}{Colors.RESET}")
    print(f"{Colors.GREEN}│{Colors.RESET}      └─ Geschlossen:    {closed_trades:>15}")
    print(f"{Colors.GREEN}│{Colors.RESET}")
    print(f"{Colors.GREEN}│{Colors.RESET}  {Colors.BOLD}Performance (geschlossene Trades):{Colors.RESET}")
    print(f"{Colors.GREEN}│{Colors.RESET}    Gewinn-Trades:      {Colors.GREEN}{winning_trades:>15}{Colors.RESET}")
    print(f"{Colors.GREEN}│{Colors.RESET}    Verlust-Trades:     {Colors.RED}{losing_trades:>15}{Colors.RESET}")
    print(f"{Colors.GREEN}│{Colors.RESET}    Win Rate:           {format_percentage(win_rate, True):>25}")
    print(f"{Colors.GREEN}│{Colors.RESET}")
    print(f"{Colors.GREEN}│{Colors.RESET}  {Colors.BOLD}P&L Statistiken:{Colors.RESET}")
    print(f"{Colors.GREEN}│{Colors.RESET}    Durchschnitt:       {format_currency(avg_pnl, True):>25}")
    print(f"{Colors.GREEN}│{Colors.RESET}    Bester Trade:       {format_currency(max_profit, True):>25}")
    print(f"{Colors.GREEN}│{Colors.RESET}    Schlechtester:      {format_currency(max_loss, True):>25}")
    print(f"{Colors.GREEN}│{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.GREEN}└─────────────────────────────────────────────────────────────────────────────────────────┘{Colors.RESET}")
    print()


def print_recent_trades(data: Dict):
    """Druckt letzte Trades."""
    trades = data['trades'][:10]  # Letzte 10
    
    print(f"{Colors.BOLD}{Colors.YELLOW}┌─ 📋 LETZTE TRADES (Top 10) ─────────────────────────────────────────────────────────────┐{Colors.RESET}")
    print(f"{Colors.YELLOW}│{Colors.RESET}")
    
    if trades:
        for i, trade in enumerate(trades, 1):
            symbol = trade['symbol']
            action = trade['action'].upper()
            amount = trade['amount']
            price = trade['price']
            status = trade['status'].upper()
            timestamp = format_datetime(trade['timestamp'])
            time_ago = format_time_ago(trade['timestamp'])
            
            # Action-Farbe
            action_color = Colors.GREEN if action == 'BUY' else Colors.RED
            
            # Status-Symbol
            status_symbol = "🟢" if status == "OPEN" else "🔵"
            
            # P&L wenn geschlossen
            pnl_display = ""
            if status == "CLOSED" and trade.get('pnl') is not None:
                pnl = trade['pnl']
                pnl_display = f"  P&L: {format_currency(pnl, True)}"
            
            print(f"{Colors.YELLOW}│{Colors.RESET}  {i:>2}. {status_symbol} {Colors.BOLD}{symbol}{Colors.RESET}")
            print(f"{Colors.YELLOW}│{Colors.RESET}      {action_color}{action}{Colors.RESET} {amount:.6f} @ {format_currency(price)}")
            print(f"{Colors.YELLOW}│{Colors.RESET}      Status: {status}  │  {time_ago}{pnl_display}")
            print(f"{Colors.YELLOW}│{Colors.RESET}      {Colors.GRAY}{timestamp}{Colors.RESET}")
            
            if i < len(trades):
                print(f"{Colors.YELLOW}│{Colors.RESET}      {Colors.GRAY}{'─' * 80}{Colors.RESET}")
    else:
        print(f"{Colors.YELLOW}│{Colors.RESET}  {Colors.GRAY}Noch keine Trades ausgeführt{Colors.RESET}")
    
    print(f"{Colors.YELLOW}│{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.YELLOW}└─────────────────────────────────────────────────────────────────────────────────────────┘{Colors.RESET}")
    print()


def print_performance_by_symbol(data: Dict):
    """Druckt Performance pro Symbol."""
    trades = data['trades']
    
    # Gruppiere nach Symbol
    symbol_stats = {}
    for trade in trades:
        if trade['status'] != 'closed':
            continue
        
        symbol = trade['symbol']
        pnl = trade.get('pnl', 0.0)
        
        if symbol not in symbol_stats:
            symbol_stats[symbol] = {
                'count': 0,
                'wins': 0,
                'losses': 0,
                'total_pnl': 0.0
            }
        
        symbol_stats[symbol]['count'] += 1
        symbol_stats[symbol]['total_pnl'] += pnl
        
        if pnl > 0:
            symbol_stats[symbol]['wins'] += 1
        elif pnl < 0:
            symbol_stats[symbol]['losses'] += 1
    
    if not symbol_stats:
        return
    
    # Sortiere nach P&L
    sorted_symbols = sorted(symbol_stats.items(), key=lambda x: x[1]['total_pnl'], reverse=True)
    
    print(f"{Colors.BOLD}{Colors.CYAN}┌─ 🎯 PERFORMANCE PRO SYMBOL ─────────────────────────────────────────────────────────────┐{Colors.RESET}")
    print(f"{Colors.CYAN}│{Colors.RESET}")
    print(f"{Colors.CYAN}│{Colors.RESET}  {'Symbol':<12} {'Trades':>8} {'Wins':>6} {'Losses':>7} {'P&L':>15} {'Win%':>10}")
    print(f"{Colors.CYAN}│{Colors.RESET}  {Colors.GRAY}{'─' * 80}{Colors.RESET}")
    
    for symbol, stats in sorted_symbols[:10]:  # Top 10
        count = stats['count']
        wins = stats['wins']
        losses = stats['losses']
        total_pnl = stats['total_pnl']
        win_rate = (wins / count * 100) if count > 0 else 0.0
        
        print(f"{Colors.CYAN}│{Colors.RESET}  {symbol:<12} {count:>8} {wins:>6} {losses:>7} {format_currency(total_pnl, True):>25} {format_percentage(win_rate, color=True, show_sign=False):>18}")
    
    print(f"{Colors.CYAN}│{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.CYAN}└─────────────────────────────────────────────────────────────────────────────────────────┘{Colors.RESET}")
    print()


def print_recent_logs(n: int = 5):
    """Druckt letzte Log-Einträge."""
    log_file = 'logs/trading_bot.log'
    
    print(f"{Colors.BOLD}{Colors.GRAY}┌─ 📝 LETZTE AKTIVITÄTEN ─────────────────────────────────────────────────────────────────┐{Colors.RESET}")
    print(f"{Colors.GRAY}│{Colors.RESET}")
    
    if os.path.exists(log_file):
        try:
            with open(log_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                recent = lines[-n:] if len(lines) > n else lines
                
                for line in recent:
                    line = line.strip()
                    if len(line) > 78:
                        line = line[:75] + "..."
                    
                    # Farbe basierend auf Level
                    if " ERROR " in line:
                        line = f"{Colors.RED}{line}{Colors.RESET}"
                    elif " WARNING " in line:
                        line = f"{Colors.YELLOW}{line}{Colors.RESET}"
                    elif " INFO " in line:
                        line = f"{Colors.WHITE}{line}{Colors.RESET}"
                    
                    print(f"{Colors.GRAY}│{Colors.RESET}  {line}")
        except Exception as e:
            print(f"{Colors.GRAY}│{Colors.RESET}  {Colors.RED}Fehler beim Lesen der Logs: {e}{Colors.RESET}")
    else:
        print(f"{Colors.GRAY}│{Colors.RESET}  Keine Logs gefunden")
    
    print(f"{Colors.GRAY}│{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.GRAY}└─────────────────────────────────────────────────────────────────────────────────────────┘{Colors.RESET}")
    print()


def print_footer():
    """Druckt Footer."""
    print(f"{Colors.GRAY}{'─' * 90}{Colors.RESET}")
    print(f"  {Colors.BOLD}💡 Tastenkombinationen:{Colors.RESET}")
    print(f"     {Colors.YELLOW}CTRL+C{Colors.RESET}  → Monitor beenden")
    print(f"     {Colors.YELLOW}Q{Colors.RESET}       → Beenden (falls CTRL+C nicht funktioniert)")
    print()


def print_dashboard(data: Dict):
    """Druckt das komplette Dashboard."""
    clear_screen()
    
    print_header()
    print_portfolio_overview(data)
    print_positions(data)
    print_trade_statistics(data)
    print_performance_by_symbol(data)
    print_recent_trades(data)
    print_recent_logs(5)
    print_footer()


def main():
    """Hauptfunktion."""
    print(f"\n{Colors.BOLD}{Colors.GREEN}🚀 Starte Advanced Trading Bot Monitor...{Colors.RESET}\n")
    print("Lade Daten aus SQLite Datenbank...")
    print("(Stelle sicher, dass der Bot mit 'python main.py' läuft)\n")
    
    # Datenbank verbinden
    try:
        db = get_database('trading_bot.db')
        print(f"{Colors.GREEN}✓ Datenbank verbunden: trading_bot.db{Colors.RESET}\n")
    except Exception as e:
        print(f"{Colors.RED}✗ Fehler bei Datenbankverbindung: {e}{Colors.RESET}\n")
        return
    
    time.sleep(2)
    
    try:
        while True:
            data = get_portfolio_data(db)
            print_dashboard(data)
            time.sleep(5)  # Aktualisiere alle 5 Sekunden
            
    except KeyboardInterrupt:
        print(f"\n\n{Colors.YELLOW}👋 Monitor wird beendet...{Colors.RESET}\n")
        db.close()


if __name__ == "__main__":
    main()
