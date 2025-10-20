"""
Script zum Trainieren des XGBoost ML-Modells mit historischen Kraken-Daten
"""

import sys
import os
import logging
from trading_bot.data_provider import DataProvider
from trading_bot.indicators import TechnicalIndicators
from trading_bot.ml_model import MLModel
from trading_bot.config import API_KEYS, ML_SETTINGS, INDICATORS
import pandas as pd

# Logging konfigurieren
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def prepare_training_data(df_with_indicators):
    """
    Bereitet Trainingsdaten vor und generiert Labels.
    
    Args:
        df_with_indicators: DataFrame mit Indikatoren
        
    Returns:
        X (Features), y (Labels)
    """
    # Features: Alle Indikatoren außer OHLCV
    feature_columns = [col for col in df_with_indicators.columns 
                      if col not in ['open', 'high', 'low', 'close', 'volume', 'timestamp']]
    
    X = df_with_indicators[feature_columns].copy()
    
    # Labels erstellen: 1 = Kauf, -1 = Verkauf, 0 = Halten
    # Basierend auf zukünftigen Preisbewegungen
    df_with_indicators['future_return'] = df_with_indicators['close'].pct_change(periods=5).shift(-5)
    
    y = pd.Series(0, index=df_with_indicators.index)
    y[df_with_indicators['future_return'] > 0.02] = 1   # Kauf wenn >2% Gewinn
    y[df_with_indicators['future_return'] < -0.02] = -1  # Verkauf wenn >2% Verlust
    
    # NaN-Werte entfernen
    valid_idx = ~(X.isna().any(axis=1) | y.isna())
    X = X[valid_idx]
    y = y[valid_idx]
    
    return X, y


def train_model_for_symbol(symbol: str, timeframe: str = '1h'):
    """
    Trainiert das ML-Modell für ein spezifisches Symbol.
    
    Args:
        symbol: Trading-Paar (z.B. 'BTC/EUR')
        timeframe: Zeitrahmen ('1h', '4h', '1d')
    """
    logger.info(f"Starte Training für {symbol} ({timeframe})...")
    
    # 1. Komponenten initialisieren
    data_provider = DataProvider(api_keys=API_KEYS, settings={'exchange': 'kraken'})
    indicators = TechnicalIndicators(config=INDICATORS)
    ml_model = MLModel(settings=ML_SETTINGS)
    
    # 2. Historische Daten laden (maximal verfügbar)
    logger.info(f"Lade historische Daten für {symbol}...")
    df = data_provider.get_historical_data(
        symbol=symbol,
        timeframe=timeframe,
        limit=5000  # Mehr Daten für besseres Training
    )
    
    if df is None or len(df) < 100:
        logger.error(f"Nicht genug Daten für {symbol} ({len(df) if df is not None else 0} Kerzen)")
        return False
    
    logger.info(f"Erfolgreich {len(df)} Kerzen geladen")
    
    # 3. Indikatoren berechnen
    logger.info("Berechne technische Indikatoren...")
    df_with_indicators = indicators.calculate_all(df)
    
    # 4. Trainingsdaten vorbereiten
    logger.info("Bereite Trainingsdaten vor...")
    X, y = prepare_training_data(df_with_indicators)
    
    logger.info(f"Trainingsdaten: {len(X)} Samples, {X.shape[1]} Features")
    logger.info(f"Label-Verteilung: Kauf={sum(y==1)}, Verkauf={sum(y==-1)}, Halten={sum(y==0)}")
    
    # 5. Modell trainieren
    logger.info("Starte Modell-Training...")
    ml_model.train(X, y)
    
    logger.info(f"✅ Training für {symbol} erfolgreich abgeschlossen!")
    return True


def train_universal_model():
    """Trainiert ein universelles Modell mit Daten von mehreren Symbolen."""
    
    print("\n" + "="*60)
    print("  XGBoost ML-Modell Training für Kraken Trading Bot")
    print("="*60 + "\n")
    
    # Symbole zum Trainieren
    symbols = ['BTC/EUR', 'ETH/EUR', 'XRP/EUR']
    timeframe = '1d'  # 1-Tages-Daten (wie im Bot)
    
    print(f"Trainiere UNIVERSELLES Modell mit {len(symbols)} Symbolen...")
    print(f"Zeitrahmen: {timeframe}")
    print(f"Dies kann 5-10 Minuten dauern...\n")
    
    # Komponenten initialisieren
    data_provider = DataProvider(api_keys=API_KEYS, settings={'exchange': 'kraken'})
    indicators = TechnicalIndicators(config=INDICATORS)
    ml_model = MLModel(settings=ML_SETTINGS)
    
    # Daten von allen Symbolen sammeln
    all_X = []
    all_y = []
    
    for i, symbol in enumerate(symbols, 1):
        print(f"\n[{i}/{len(symbols)}] Lade Daten für {symbol}...")
        print("-" * 60)
        
        try:
            # Historische Daten laden
            df = data_provider.get_historical_data(
                symbol=symbol,
                timeframe=timeframe,
                limit=1000  # Genug Daten für gutes Training
            )
            
            if df is None or len(df) < 100:
                logger.warning(f"Nicht genug Daten für {symbol}")
                print(f"⚠️  {symbol}: Nicht genug Daten ({len(df) if df is not None else 0} Kerzen)")
                continue
            
            print(f"✅ {len(df)} Kerzen geladen")
            
            # Indikatoren berechnen
            df_with_indicators = indicators.calculate_all(df)
            print(f"✅ Indikatoren berechnet")
            
            # Trainingsdaten vorbereiten
            X, y = prepare_training_data(df_with_indicators)
            
            if len(X) > 0:
                all_X.append(X)
                all_y.append(y)
                print(f"✅ {len(X)} Training-Samples erstellt")
                print(f"   Kauf: {sum(y==1)}, Verkauf: {sum(y==-1)}, Halten: {sum(y==0)}")
            
        except Exception as e:
            logger.error(f"Fehler bei {symbol}: {str(e)}", exc_info=True)
            print(f"❌ {symbol}: Fehler - {str(e)}")
            continue
    
    # Alle Daten kombinieren
    if not all_X:
        print("\n❌ Keine Trainingsdaten verfügbar!")
        return False
    
    print("\n" + "="*60)
    print("Kombiniere Daten und starte Training...")
    print("="*60)
    
    X_combined = pd.concat(all_X, ignore_index=True)
    y_combined = pd.concat(all_y, ignore_index=True)
    
    print(f"\n📊 Gesamt-Trainingsdaten:")
    print(f"   Samples: {len(X_combined)}")
    print(f"   Features: {X_combined.shape[1]}")
    print(f"   Kauf: {sum(y_combined==1)} ({sum(y_combined==1)/len(y_combined)*100:.1f}%)")
    print(f"   Verkauf: {sum(y_combined==-1)} ({sum(y_combined==-1)/len(y_combined)*100:.1f}%)")
    print(f"   Halten: {sum(y_combined==0)} ({sum(y_combined==0)/len(y_combined)*100:.1f}%)")
    
    print("\n🚀 Trainiere XGBoost Modell...")
    print("   (Dies kann einige Minuten dauern...)\n")
    
    # Labels für XGBoost anpassen: -1,0,1 -> 0,1,2
    # -1 (Verkauf) -> 0
    #  0 (Halten)  -> 1
    #  1 (Kauf)    -> 2
    y_combined_mapped = y_combined.copy()
    y_combined_mapped = y_combined_mapped + 1  # Verschiebt -1,0,1 zu 0,1,2
    
    print("📝 Label-Mapping für XGBoost: -1→0 (Verkauf), 0→1 (Halten), 1→2 (Kauf)\n")
    
    # Modell trainieren
    ml_model.train(X_combined, y_combined_mapped)
    
    # Prüfen ob gespeichert wurde
    model_file = os.path.join(ML_SETTINGS.get('model_path', 'models/'), 'trading_model.pkl')
    scaler_file = os.path.join(ML_SETTINGS.get('model_path', 'models/'), 'scaler.pkl')
    
    if os.path.exists(model_file) and os.path.exists(scaler_file):
        print("\n" + "="*60)
        print("  ✅ TRAINING ERFOLGREICH ABGESCHLOSSEN!")
        print("="*60)
        print(f"\n📁 Modell gespeichert:")
        print(f"   - {model_file}")
        print(f"   - {scaler_file}")
        print(f"\n💡 Nächster Schritt:")
        print(f"   1. Starte (oder neu starte) den Bot: python main.py")
        print(f"   2. Das Modell wird automatisch geladen")
        print(f"   3. Überwache mit: python monitor_bot.py")
        return True
    else:
        print("\n❌ Modell wurde nicht gespeichert!")
        print(f"   Erwartete Dateien nicht gefunden:")
        print(f"   - {model_file}")
        print(f"   - {scaler_file}")
        return False


def main():
    """Hauptfunktion zum Trainieren des Modells."""
    try:
        success = train_universal_model()
        if not success:
            print("\n⚠️  Training fehlgeschlagen. Prüfe die Logs für Details.")
            sys.exit(1)
    except Exception as e:
        logger.error(f"Kritischer Fehler: {str(e)}", exc_info=True)
        print(f"\n❌ Kritischer Fehler: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nTraining abgebrochen.")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Kritischer Fehler: {str(e)}", exc_info=True)
        sys.exit(1)
