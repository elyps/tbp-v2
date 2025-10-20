"""
Migrations-Script: JSON/CSV → SQLite
Migriert bestehende Daten zur neuen SQLite-Datenbank.
"""

import json
import os
import sys
import pandas as pd
import logging
from pathlib import Path
from datetime import datetime

# Add trading_bot to path
sys.path.insert(0, str(Path(__file__).parent))

from trading_bot.database import get_database

# Logging setup
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def print_banner():
    """Druckt Banner."""
    banner = """
    ╔══════════════════════════════════════════════════════════╗
    ║                                                          ║
    ║       📊 MIGRATION: JSON/CSV → SQLite                   ║
    ║                                                          ║
    ║   Migriert alle bestehenden Daten zur SQLite-DB         ║
    ║                                                          ║
    ╚══════════════════════════════════════════════════════════╝
    """
    print(banner)


def migrate_trades(db):
    """Migriert Trades aus JSON."""
    trades_file = 'training_data/trades_history.json'
    
    if not os.path.exists(trades_file):
        logger.warning(f"Keine Trades gefunden: {trades_file}")
        return 0
    
    logger.info(f"Migriere Trades aus {trades_file}...")
    
    with open(trades_file, 'r') as f:
        trades = json.load(f)
    
    migrated = 0
    for trade in trades:
        try:
            db.save_trade(trade)
            migrated += 1
        except Exception as e:
            logger.error(f"Fehler bei Trade-Migration: {e}")
    
    logger.info(f"✓ {migrated} Trades migriert")
    return migrated


def migrate_training_data(db):
    """Migriert Training Data aus CSV."""
    features_file = 'training_data/features_history.csv'
    labels_file = 'training_data/labels_history.csv'
    
    if not os.path.exists(features_file) or not os.path.exists(labels_file):
        logger.warning("Keine Training Data gefunden")
        return 0
    
    logger.info("Migriere Training Data aus CSV...")
    
    try:
        features_df = pd.read_csv(features_file)
        labels_df = pd.read_csv(labels_file)
        
        # Merge
        merged = features_df.merge(labels_df, left_index=True, right_index=True, how='inner')
        
        migrated = 0
        for idx, row in merged.iterrows():
            try:
                # Features als Dict
                feature_cols = [col for col in row.index if col not in ['label', 'timestamp', 'symbol']]
                features = {col: float(row[col]) for col in feature_cols if pd.notna(row[col])}
                
                # Speichern
                db.save_training_sample(
                    trade_id=f'migrated_{idx}',
                    symbol=row.get('symbol', 'UNKNOWN'),
                    features=features,
                    label=int(row['label']) if pd.notna(row['label']) else None,
                    pnl=float(row['pnl']) if 'pnl' in row and pd.notna(row['pnl']) else 0.0
                )
                migrated += 1
            except Exception as e:
                logger.error(f"Fehler bei Training Data Migration (Row {idx}): {e}")
        
        logger.info(f"✓ {migrated} Training Samples migriert")
        return migrated
        
    except Exception as e:
        logger.error(f"Fehler beim Laden der Training Data: {e}")
        return 0


def migrate_portfolio(db):
    """Migriert Portfolio aus JSON."""
    portfolio_file = 'portfolio/portfolio_state.json'
    
    if not os.path.exists(portfolio_file):
        logger.warning(f"Kein Portfolio gefunden: {portfolio_file}")
        return False
    
    logger.info(f"Migriere Portfolio aus {portfolio_file}...")
    
    try:
        with open(portfolio_file, 'r') as f:
            portfolio = json.load(f)
        
        db.save_portfolio(portfolio)
        logger.info(f"✓ Portfolio migriert")
        return True
    except Exception as e:
        logger.error(f"Fehler bei Portfolio-Migration: {e}")
        return False


def migrate_news(db):
    """Migriert News aus JSON files."""
    news_dir = 'news_data'
    
    if not os.path.exists(news_dir):
        logger.warning(f"Kein News-Verzeichnis gefunden: {news_dir}")
        return 0
    
    logger.info(f"Migriere News aus {news_dir}...")
    
    migrated = 0
    for filename in os.listdir(news_dir):
        if filename.endswith('.json'):
            filepath = os.path.join(news_dir, filename)
            
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    news_data = json.load(f)
                
                # Symbol aus Filename extrahieren (z.B. BTC_news_20250119.json)
                symbol = filename.split('_')[0]
                
                for article in news_data if isinstance(news_data, list) else [news_data]:
                    try:
                        news_entry = {
                            'symbol': symbol,
                            'title': article.get('title', ''),
                            'content': article.get('description', ''),
                            'source': article.get('source', {}).get('name', 'Unknown'),
                            'url': article.get('url', ''),
                            'sentiment_score': article.get('sentiment_score', 0.0),
                            'sentiment_label': article.get('sentiment_label', 'neutral'),
                            'published_at': article.get('publishedAt', datetime.utcnow().isoformat())
                        }
                        
                        db.save_news(news_entry)
                        migrated += 1
                    except Exception as e:
                        logger.debug(f"Fehler bei News-Item: {e}")
            
            except Exception as e:
                logger.error(f"Fehler beim Laden von {filename}: {e}")
    
    logger.info(f"✓ {migrated} News-Artikel migriert")
    return migrated


def migrate_model_performance(db):
    """Migriert Model Performance History."""
    perf_file = 'models/versions/performance_history.json'
    
    if not os.path.exists(perf_file):
        logger.warning(f"Keine Performance History gefunden: {perf_file}")
        return 0
    
    logger.info(f"Migriere Model Performance aus {perf_file}...")
    
    try:
        with open(perf_file, 'r') as f:
            performance_history = json.load(f)
        
        migrated = 0
        for version, perf in performance_history.items():
            try:
                db.save_model_performance({
                    'version': version,
                    'accuracy': perf.get('accuracy', 0.0),
                    'precision': perf.get('precision', 0.0),
                    'recall': perf.get('recall', 0.0),
                    'f1_score': perf.get('f1_score', 0.0),
                    'samples_count': perf.get('samples_count', 0),
                    'training_duration': perf.get('training_duration', 0.0),
                    'notes': perf.get('notes', '')
                })
                migrated += 1
            except Exception as e:
                logger.error(f"Fehler bei Performance Migration ({version}): {e}")
        
        logger.info(f"✓ {migrated} Performance-Einträge migriert")
        return migrated
        
    except Exception as e:
        logger.error(f"Fehler beim Laden der Performance History: {e}")
        return 0


def verify_migration(db):
    """Verifiziert Migration."""
    logger.info("\n" + "="*60)
    logger.info("VERIFIZIERUNG:")
    logger.info("="*60)
    
    # Trade Stats
    trade_stats = db.get_trade_statistics()
    logger.info(f"Trades: {trade_stats.get('total_trades', 0)}")
    
    # Training Stats
    training_stats = db.get_training_stats()
    logger.info(f"Training Samples: {training_stats.get('total_samples', 0)}")
    
    # Portfolio
    portfolio = db.get_portfolio()
    if portfolio:
        logger.info(f"Portfolio: Balance={portfolio['balance']:.2f}, Equity={portfolio['equity']:.2f}")
    else:
        logger.info("Portfolio: Keine Daten")
    
    # News
    cursor = db.conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM news")
    news_count = cursor.fetchone()[0]
    logger.info(f"News-Artikel: {news_count}")
    
    # Performance
    perf_history = db.get_model_performance_history(limit=5)
    logger.info(f"Performance-Einträge: {len(perf_history)}")
    
    logger.info("="*60)


def main():
    """Hauptfunktion."""
    print_banner()
    
    logger.info("Starte Migration...")
    logger.info("")
    
    # Database initialisieren
    db = get_database('trading_bot.db')
    logger.info(f"✓ Datenbank initialisiert: trading_bot.db")
    logger.info("")
    
    # Migrations durchführen
    stats = {
        'trades': 0,
        'training_data': 0,
        'portfolio': 0,
        'news': 0,
        'performance': 0
    }
    
    try:
        # 1. Trades
        logger.info("=" * 60)
        logger.info("1. TRADES MIGRATION")
        logger.info("=" * 60)
        stats['trades'] = migrate_trades(db)
        logger.info("")
        
        # 2. Training Data
        logger.info("=" * 60)
        logger.info("2. TRAINING DATA MIGRATION")
        logger.info("=" * 60)
        stats['training_data'] = migrate_training_data(db)
        logger.info("")
        
        # 3. Portfolio
        logger.info("=" * 60)
        logger.info("3. PORTFOLIO MIGRATION")
        logger.info("=" * 60)
        stats['portfolio'] = 1 if migrate_portfolio(db) else 0
        logger.info("")
        
        # 4. News
        logger.info("=" * 60)
        logger.info("4. NEWS MIGRATION")
        logger.info("=" * 60)
        stats['news'] = migrate_news(db)
        logger.info("")
        
        # 5. Model Performance
        logger.info("=" * 60)
        logger.info("5. MODEL PERFORMANCE MIGRATION")
        logger.info("=" * 60)
        stats['performance'] = migrate_model_performance(db)
        logger.info("")
        
        # Verifizierung
        verify_migration(db)
        
        # Zusammenfassung
        logger.info("\n" + "="*60)
        logger.info("✅ MIGRATION ABGESCHLOSSEN")
        logger.info("="*60)
        logger.info(f"Trades:           {stats['trades']}")
        logger.info(f"Training Data:    {stats['training_data']}")
        logger.info(f"Portfolio:        {'✓' if stats['portfolio'] else '✗'}")
        logger.info(f"News:             {stats['news']}")
        logger.info(f"Performance:      {stats['performance']}")
        logger.info("="*60)
        logger.info("")
        logger.info("Die Datenbank 'trading_bot.db' ist bereit!")
        logger.info("Alte JSON/CSV Dateien können archiviert werden.")
        logger.info("")
        
    except Exception as e:
        logger.error(f"\n❌ Fehler bei der Migration: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
