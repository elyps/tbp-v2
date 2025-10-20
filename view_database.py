"""
Database Viewer - Zeigt SQLite Datenbank-Statistiken an
"""

import sys
from pathlib import Path
from datetime import datetime
import pandas as pd

# Add trading_bot to path
sys.path.insert(0, str(Path(__file__).parent))

from trading_bot.database import get_database


def print_banner():
    """Druckt Banner."""
    banner = """
    ╔══════════════════════════════════════════════════════════╗
    ║                                                          ║
    ║          📊 TRADING BOT DATABASE VIEWER                 ║
    ║                                                          ║
    ╚══════════════════════════════════════════════════════════╝
    """
    print(banner)


def print_section(title):
    """Druckt Section Header."""
    print("\n" + "="*60)
    print(f"  {title}")
    print("="*60)


def show_trades_stats(db):
    """Zeigt Trade-Statistiken."""
    print_section("📈 TRADE STATISTIKEN")
    
    stats = db.get_trade_statistics()
    
    if stats.get('total_trades', 0) == 0:
        print("  Noch keine Trades vorhanden.")
        return
    
    print(f"  Total Trades:        {stats['total_trades']}")
    print(f"  Gewinn-Trades:       {stats['winning_trades']} ({stats['win_rate']:.1f}%)")
    print(f"  Verlust-Trades:      {stats['losing_trades']}")
    print(f"  \n  Total P&L:           €{stats['total_pnl']:,.2f}")
    print(f"  Durchschnitt P&L:    €{stats['avg_pnl']:,.2f}")
    print(f"  Bester Trade:        €{stats['max_profit']:,.2f}")
    print(f"  Schlechtester Trade: €{stats['max_loss']:,.2f}")
    
    # Performance pro Symbol
    print("\n  Performance pro Symbol:")
    cursor = db.conn.cursor()
    cursor.execute("""
        SELECT 
            symbol,
            COUNT(*) as trades,
            SUM(CASE WHEN pnl > 0 THEN 1 ELSE 0 END) as wins,
            SUM(pnl) as total_pnl,
            (SUM(CASE WHEN pnl > 0 THEN 1 ELSE 0 END) * 100.0 / COUNT(*)) as win_rate
        FROM trades
        WHERE status = 'closed'
        GROUP BY symbol
        ORDER BY total_pnl DESC
    """)
    
    rows = cursor.fetchall()
    if rows:
        print(f"  {'Symbol':<12} {'Trades':>8} {'Wins':>6} {'P&L':>12} {'Win%':>8}")
        print("  " + "-"*54)
        for row in rows:
            print(f"  {row[0]:<12} {row[1]:>8} {row[2]:>6} €{row[3]:>10,.2f} {row[4]:>7.1f}%")


def show_portfolio_stats(db):
    """Zeigt Portfolio-Status."""
    print_section("💰 PORTFOLIO")
    
    portfolio = db.get_portfolio()
    
    if not portfolio:
        print("  Noch kein Portfolio-Status vorhanden.")
        return
    
    print(f"  Balance:             €{portfolio['balance']:,.2f}")
    print(f"  Equity:              €{portfolio['equity']:,.2f}")
    print(f"  Total P&L:           €{portfolio['total_pnl']:,.2f}")
    print(f"  \n  Total Trades:        {portfolio['total_trades']}")
    print(f"  Gewinn-Trades:       {portfolio['winning_trades']}")
    print(f"  Verlust-Trades:      {portfolio['losing_trades']}")
    
    if portfolio['total_trades'] > 0:
        win_rate = (portfolio['winning_trades'] / portfolio['total_trades']) * 100
        print(f"  Win-Rate:            {win_rate:.1f}%")
    
    print(f"  \n  Max Drawdown:        {portfolio['max_drawdown']:.2f}%")
    print(f"  Sharpe Ratio:        {portfolio['sharpe_ratio']:.2f}")
    print(f"  \n  Letztes Update:      {portfolio['updated_at']}")


def show_positions(db):
    """Zeigt offene Positionen."""
    print_section("📊 OFFENE POSITIONEN")
    
    positions = db.get_all_positions()
    
    if not positions:
        print("  Keine offenen Positionen.")
        return
    
    print(f"  {'Symbol':<12} {'Menge':>12} {'Entry':>12} {'Aktuell':>12} {'P&L':>12} {'P&L%':>8}")
    print("  " + "-"*76)
    
    for pos in positions:
        print(f"  {pos['symbol']:<12} {pos['amount']:>12.4f} "
              f"€{pos['entry_price']:>10,.2f} €{pos['current_price']:>10,.2f} "
              f"€{pos['pnl']:>10,.2f} {pos['pnl_percent']:>7.2f}%")


def show_training_stats(db):
    """Zeigt Training Data Statistiken."""
    print_section("🧠 TRAINING DATA")
    
    stats = db.get_training_stats()
    
    if stats.get('total_samples', 0) == 0:
        print("  Noch keine Training Data vorhanden.")
        return
    
    print(f"  Total Samples:       {stats['total_samples']}")
    print(f"  Kauf-Signale (2):    {stats['buy_samples']}")
    print(f"  Halten-Signale (1):  {stats['hold_samples']}")
    print(f"  Verkauf-Signale (0): {stats['sell_samples']}")
    print(f"  Symbole:             {stats['symbols_count']}")
    
    # Label-Verteilung
    if stats['total_samples'] > 0:
        print("\n  Label-Verteilung:")
        buy_pct = (stats['buy_samples'] / stats['total_samples']) * 100
        hold_pct = (stats['hold_samples'] / stats['total_samples']) * 100
        sell_pct = (stats['sell_samples'] / stats['total_samples']) * 100
        
        print(f"    Kauf:    {buy_pct:>5.1f}% {'█' * int(buy_pct/2)}")
        print(f"    Halten:  {hold_pct:>5.1f}% {'█' * int(hold_pct/2)}")
        print(f"    Verkauf: {sell_pct:>5.1f}% {'█' * int(sell_pct/2)}")


def show_model_performance(db):
    """Zeigt Model Performance History."""
    print_section("🎯 MODEL PERFORMANCE")
    
    history = db.get_model_performance_history(limit=5)
    
    if not history:
        print("  Noch keine Performance-Daten vorhanden.")
        return
    
    print(f"  {'Version':<12} {'Accuracy':>10} {'Samples':>10} {'Datum':<20}")
    print("  " + "-"*58)
    
    for perf in history:
        timestamp = perf['timestamp'][:19] if perf['timestamp'] else 'N/A'
        print(f"  {perf['model_version']:<12} {perf['accuracy']:>9.2%} "
              f"{perf['samples_count']:>10} {timestamp:<20}")
    
    # Verbesserung anzeigen
    if len(history) >= 2:
        latest = history[0]
        previous = history[1]
        improvement = (latest['accuracy'] - previous['accuracy']) * 100
        
        print(f"\n  Letzte Verbesserung: {improvement:+.2f}%")


def show_news_stats(db):
    """Zeigt News-Statistiken."""
    print_section("📰 NEWS")
    
    cursor = db.conn.cursor()
    
    # Total News
    cursor.execute("SELECT COUNT(*) FROM news")
    total_news = cursor.fetchone()[0]
    
    if total_news == 0:
        print("  Noch keine News gespeichert.")
        return
    
    print(f"  Total Artikel:       {total_news}")
    
    # Pro Symbol
    cursor.execute("""
        SELECT 
            symbol,
            COUNT(*) as count,
            AVG(sentiment_score) as avg_sentiment
        FROM news
        GROUP BY symbol
        ORDER BY count DESC
        LIMIT 10
    """)
    
    rows = cursor.fetchall()
    if rows:
        print("\n  News pro Symbol:")
        print(f"  {'Symbol':<12} {'Artikel':>10} {'Sentiment':>12}")
        print("  " + "-"*38)
        for row in rows:
            sentiment_str = f"{row[2]:+.2f}" if row[2] else "N/A"
            print(f"  {row[0]:<12} {row[1]:>10} {sentiment_str:>12}")
    
    # Sentiment-Verteilung
    cursor.execute("""
        SELECT 
            sentiment_label,
            COUNT(*) as count
        FROM news
        GROUP BY sentiment_label
    """)
    
    rows = cursor.fetchall()
    if rows:
        print("\n  Sentiment-Verteilung:")
        for row in rows:
            pct = (row[1] / total_news) * 100
            print(f"    {row[0].capitalize():<10} {row[1]:>5} ({pct:>5.1f}%)")


def show_recent_activity(db):
    """Zeigt letzte Aktivitäten."""
    print_section("🕐 LETZTE AKTIVITÄT")
    
    # Letzte Trades
    recent_trades = db.get_trades(limit=5)
    
    if recent_trades:
        print("\n  Letzte 5 Trades:")
        print(f"  {'Symbol':<12} {'Aktion':<6} {'Preis':>12} {'Status':<8} {'Datum':<20}")
        print("  " + "-"*66)
        
        for trade in recent_trades:
            timestamp = trade['timestamp'][:19] if trade['timestamp'] else 'N/A'
            print(f"  {trade['symbol']:<12} {trade['action']:<6} "
                  f"€{trade['price']:>10,.2f} {trade['status']:<8} {timestamp:<20}")
    
    # Letzte Signale
    cursor = db.conn.cursor()
    cursor.execute("SELECT * FROM signals ORDER BY timestamp DESC LIMIT 5")
    signals = cursor.fetchall()
    
    if signals:
        print("\n  Letzte 5 Signale:")
        print(f"  {'Symbol':<12} {'Aktion':<6} {'Konfidenz':>10} {'Ausgeführt':<12} {'Datum':<20}")
        print("  " + "-"*68)
        
        for signal in signals:
            signal_dict = dict(signal)
            timestamp = signal_dict['timestamp'][:19] if signal_dict['timestamp'] else 'N/A'
            executed = '✓' if signal_dict['executed'] else '✗'
            print(f"  {signal_dict['symbol']:<12} {signal_dict['action']:<6} "
                  f"{signal_dict['confidence']:>9.1%} {executed:<12} {timestamp:<20}")


def show_database_info(db):
    """Zeigt allgemeine Datenbank-Informationen."""
    print_section("ℹ️  DATABASE INFO")
    
    import os
    
    # Dateigröße
    db_size = os.path.getsize(db.db_path) / (1024 * 1024)  # MB
    print(f"  Datei:               {db.db_path}")
    print(f"  Größe:               {db_size:.2f} MB")
    
    # Tabellen-Info
    cursor = db.conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
    tables = cursor.fetchall()
    
    print(f"\n  Tabellen ({len(tables)}):")
    for table in tables:
        cursor.execute(f"SELECT COUNT(*) FROM {table[0]}")
        count = cursor.fetchone()[0]
        print(f"    - {table[0]:<25} {count:>8} rows")


def main():
    """Hauptfunktion."""
    print_banner()
    
    # Database laden
    db = get_database('trading_bot.db')
    
    # Statistiken anzeigen
    show_database_info(db)
    show_portfolio_stats(db)
    show_positions(db)
    show_trades_stats(db)
    show_training_stats(db)
    show_model_performance(db)
    show_news_stats(db)
    show_recent_activity(db)
    
    print("\n" + "="*60)
    print("  ✅ Datenbank-Übersicht abgeschlossen")
    print("="*60)
    print()


if __name__ == "__main__":
    main()
