"""
Umfassendes Training-Skript für die KI.
Trainiert mit historischen Daten (15 Jahre), News-Sentiment und Live-Trades.
"""

import sys
import logging
from pathlib import Path
from datetime import datetime, timedelta

# Füge trading_bot zum Path hinzu
sys.path.insert(0, str(Path(__file__).parent))

from trading_bot.data_provider import DataProvider
from trading_bot.indicators import TechnicalIndicators
from trading_bot.ml_model import MLModel
from trading_bot.news_provider import NewsProvider
from trading_bot.historical_trainer import HistoricalTrainer
from trading_bot.config import API_KEYS, DEFAULT_SETTINGS, INDICATORS, ML_SETTINGS

# Logging einrichten
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('comprehensive_training.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


def print_banner():
    """Druckt Banner."""
    banner = """
    ╔══════════════════════════════════════════════════════════════╗
    ║                                                              ║
    ║         🧠 COMPREHENSIVE AI TRAINING SYSTEM 🧠              ║
    ║                                                              ║
    ║   Trainiert die KI mit maximalen Datenquellen:              ║
    ║   • 15 Jahre historische Chart-Daten                        ║
    ║   • Live News & Sentiment-Analyse                           ║
    ║   • Technische Indikatoren & Patterns                       ║
    ║                                                              ║
    ╚══════════════════════════════════════════════════════════════╝
    """
    print(banner)


def train_comprehensive_model(
    symbols=None,
    years=15,
    timeframe='15m', # Standard auf 15m für hochfrequente Strategie
    use_news=False,  # News für kurzfristiges Trading weniger relevant, beschleunigt Training
    run_backtest=True
):
    """
    Hauptfunktion für umfassendes Training.
    
    Args:
        symbols: Liste von Symbolen (None = Standard-Symbole)
        years: Jahre historische Daten
        timeframe: Zeitrahmen ('1h', '4h', '1d')
        use_news: Ob News-Sentiment verwendet werden soll
        run_backtest: Ob Backtest durchgeführt werden soll
    """
    print_banner()
    logger.info("="*70)
    logger.info("STARTE COMPREHENSIVE TRAINING")
    logger.info("="*70)
    
    # Standard-Symbole wenn nicht angegeben
    if symbols is None:
        symbols = [
            'BTC/USD', 'ETH/USD', 'SOL/USD', 'XRP/USD', 'ADA/USD',
            'BNB/USD', 'DOGE/USD', 'MATIC/USD', 'DOT/USD', 'AVAX/USD'
        ]
    
    logger.info(f"Symbole: {', '.join(symbols)}")
    logger.info(f"Historische Daten: {years} Jahre")
    logger.info(f"Timeframe: {timeframe}")
    logger.info(f"News-Integration: {'✓ Aktiviert' if use_news else '✗ Deaktiviert'}")
    logger.info("")
    
    # 1. Komponenten initialisieren
    logger.info("📦 Initialisiere Komponenten...")
    
    data_provider = DataProvider(
        api_keys=API_KEYS,
        settings=DEFAULT_SETTINGS
    )
    
    indicators = TechnicalIndicators(config=INDICATORS)
    
    ml_model = MLModel(settings=ML_SETTINGS)
    
    news_provider = None
    if use_news:
        try:
            news_provider = NewsProvider(config=API_KEYS)
            logger.info("✓ NewsProvider initialisiert")
        except Exception as e:
            logger.warning(f"NewsProvider konnte nicht initialisiert werden: {e}")
            logger.info("  → Training ohne News-Features")
            use_news = False
    
    historical_trainer = HistoricalTrainer(
        data_provider=data_provider,
        indicators=indicators,
        ml_model=ml_model,
        news_provider=news_provider if use_news else None
    )
    
    logger.info("✓ Alle Komponenten initialisiert")
    logger.info("")
    
    # 2. Historical Training
    logger.info("="*70)
    logger.info("📊 PHASE 1: HISTORICAL DATA TRAINING")
    logger.info("="*70)
    logger.info(f"Lade und verarbeite {years} Jahre Daten für {len(symbols)} Symbole...")
    logger.info("Dies kann einige Minuten dauern...")
    logger.info("")
    
    try:
        stats = historical_trainer.train_on_historical_data(
            symbols=symbols, # Verwendet jetzt die Standardwerte aus der Methode
            years=3,         # 3 Jahre 15m-Daten sind optimal
            timeframe=timeframe, # '15m'
            forward_window=12,   # 3 Stunden auf 15m-Chart
            profit_threshold=0.005, # 0.5% für kurzfristige Chancen
            use_news=use_news
        )
        
        logger.info("")
        logger.info("="*70)
        logger.info("📈 TRAINING RESULTS")
        logger.info("="*70)
        logger.info(f"Verarbeitete Symbole: {stats['symbols_processed']}/{len(symbols)}")
        logger.info(f"Total Samples: {stats['total_samples']:,}")
        logger.info(f"  • Kauf-Signale:   {stats['positive_samples']:,} ({stats['positive_samples']/max(stats['total_samples'],1)*100:.1f}%)")
        logger.info(f"  • Halten-Signale: {stats['neutral_samples']:,} ({stats['neutral_samples']/max(stats['total_samples'],1)*100:.1f}%)")
        logger.info(f"  • Verkauf-Signale: {stats['negative_samples']:,} ({stats['negative_samples']/max(stats['total_samples'],1)*100:.1f}%)")
        logger.info(f"Training Accuracy: {stats.get('training_accuracy', 0):.2%}")
        
        if stats['errors']:
            logger.warning(f"\n⚠ Fehler bei {len(stats['errors'])} Symbol(en):")
            for error in stats['errors'][:5]:  # Zeige nur erste 5
                logger.warning(f"  - {error}")
        
        logger.info("")
        
    except Exception as e:
        logger.error(f"❌ Fehler beim Historical Training: {e}", exc_info=True)
        return False
    
    # 3. News-Sentiment Integration (falls aktiviert)
    if use_news and news_provider:
        logger.info("="*70)
        logger.info("📰 PHASE 2: NEWS SENTIMENT ANALYSIS")
        logger.info("="*70)
        
        for symbol in symbols[:3]:  # Nur Top 3 für Demo
            try:
                # Extrahiere Basis-Symbol (BTC von BTC/USD)
                base_symbol = symbol.split('/')[0]
                
                sentiment = news_provider.get_aggregated_sentiment(base_symbol)
                
                logger.info(f"\n{symbol}:")
                logger.info(f"  Sentiment-Score: {sentiment['avg_score']:+.2f}")
                logger.info(f"  Overall: {sentiment['overall_sentiment'].upper()}")
                logger.info(f"  News-Artikel: {sentiment['article_count']}")
                logger.info(f"  Positiv/Neutral/Negativ: {sentiment['distribution']['positive']}/{sentiment['distribution']['neutral']}/{sentiment['distribution']['negative']}")
                
                # Speichere News für historische Analyse
                news_provider.save_news_to_history(base_symbol)
                
            except Exception as e:
                logger.warning(f"  News-Sentiment für {symbol} nicht verfügbar: {e}")
        
        logger.info("")
    
    # 4. Backtest (optional)
    if run_backtest:
        logger.info("="*70)
        logger.info("🔍 PHASE 3: BACKTESTING")
        logger.info("="*70)
        logger.info("Teste das trainierte Modell auf historischen Daten...")
        logger.info("")
        
        # Backtest auf dem Hauptsymbol
        main_symbol = symbols[0]
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=90)  # Backtest für die letzten 90 Tage
        
        try:
            results = historical_trainer.backtest_on_historical_data(
                symbol=main_symbol,
                start_date=start_date.strftime('%Y-%m-%d'),
                end_date=end_date.strftime('%Y-%m-%d'),
                timeframe=timeframe,
                initial_balance=10000.0
            )
            
            logger.info(f"Backtest Ergebnisse für {main_symbol}:")
            logger.info(f"  Zeitraum (1h-Kerzen): {start_date.strftime('%Y-%m-%d')} bis {end_date.strftime('%Y-%m-%d')}")
            logger.info(f"  Start-Kapital: ${results['initial_balance']:,.2f}")
            logger.info(f"  End-Kapital: ${results['final_balance']:,.2f}")
            logger.info(f"  Total Return: {results['total_return']:+.2f}%")
            logger.info(f"  Total Trades: {results['total_trades']}")
            logger.info(f"  Win-Rate: {results['win_rate']:.1f}%")
            logger.info(f"  Gewinn/Verlust: {results['winning_trades']}/{results['losing_trades']}")
            logger.info(f"  Avg. Gewinn: ${results['avg_profit']:,.2f}")
            logger.info(f"  Avg. Verlust: ${results['avg_loss']:,.2f}")
            logger.info("")
            
            # Performance-Bewertung
            if results['total_return'] > 20:
                logger.info("  ✓ Exzellente Performance! 🎉")
            elif results['total_return'] > 0:
                logger.info("  ✓ Positive Performance")
            else:
                logger.warning("  ⚠ Negative Performance - Modell könnte Optimierung benötigen")
            
        except Exception as e:
            logger.error(f"Fehler beim Backtest: {e}")
    
    # 5. Zusammenfassung
    logger.info("")
    logger.info("="*70)
    logger.info("✅ COMPREHENSIVE TRAINING ABGESCHLOSSEN")
    logger.info("="*70)
    logger.info("")
    logger.info("📁 Gespeicherte Modelle:")
    logger.info("  • models/trading_model.pkl - Hauptmodell")
    logger.info("  • models/scaler.pkl - Feature Scaler")
    logger.info("  • models/versions/ - Backups")
    
    if use_news:
        logger.info("  • news_data/ - Gespeicherte News-Artikel")
    
    logger.info("")
    logger.info("🚀 Das Modell ist jetzt bereit für Live-Trading!")
    logger.info("")
    logger.info("Nächste Schritte:")
    logger.info("  1. Starte den Bot: python main.py")
    logger.info("  2. Monitor Learning: python monitor_learning.py")
    logger.info("  3. Die KI lernt kontinuierlich aus Live-Trades weiter")
    logger.info("")
    
    return True


def main():
    """Hauptfunktion."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Comprehensive AI Training')
    parser.add_argument('--years', type=int, default=15, help='Jahre historische Daten (default: 15)')
    parser.add_argument('--timeframe', type=str, default='1h', choices=['1h', '4h', '1d', '1w'], help='Timeframe (default: 1h)')
    parser.add_argument('--no-news', action='store_true', help='News-Integration deaktivieren')
    parser.add_argument('--no-backtest', action='store_true', help='Backtest überspringen')
    parser.add_argument('--symbols', type=str, nargs='+', help='Spezifische Symbole (z.B. BTC/USD ETH/USD)')
    
    args = parser.parse_args()
    
    try:
        success = train_comprehensive_model(
            symbols=args.symbols,
            years=args.years,
            timeframe=args.timeframe,
            use_news=not args.no_news,
            run_backtest=not args.no_backtest
        )
        
        if success:
            logger.info("Training erfolgreich abgeschlossen! ✓")
            sys.exit(0)
        else:
            logger.error("Training fehlgeschlagen! ✗")
            sys.exit(1)
    
    except KeyboardInterrupt:
        logger.info("\nTraining abgebrochen durch Benutzer")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unerwarteter Fehler: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
