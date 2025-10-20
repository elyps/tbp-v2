#!/usr/bin/env python
"""
Trainiert ein optimiertes ML-Modell für bessere Trading-Vorhersagen.
"""

import sys
from pathlib import Path
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
import xgboost as xgb
import joblib
import logging

project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from trading_bot.data_provider import DataProvider
from trading_bot.indicators import TechnicalIndicators
from trading_bot.config import API_KEYS, DEFAULT_SETTINGS, INDICATORS

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def prepare_features(df: pd.DataFrame) -> pd.DataFrame:
    """Bereitet Features für das Modell vor."""
    feature_columns = [
        # Preis-Indikatoren
        'sma_20', 'sma_50', 'ema_9', 'ema_21',
        # Momentum
        'rsi_14', 'macd_line', 'macd_signal', 'macd_hist',
        # Volatilität
        'bb_upper', 'bb_middle', 'bb_lower', 'atr',
        # Zusätzliche Features
        'volume'
    ]
    
    # Filtere nur vorhandene Spalten
    available = [col for col in feature_columns if col in df.columns]
    
    # Erstelle zusätzliche Features
    df['price_sma20_ratio'] = df['close'] / df['sma_20']
    df['price_sma50_ratio'] = df['close'] / df['sma_50']
    df['sma20_sma50_ratio'] = df['sma_20'] / df['sma_50']
    df['bb_position'] = (df['close'] - df['bb_lower']) / (df['bb_upper'] - df['bb_lower'])
    df['volume_ratio'] = df['volume'] / df['volume'].rolling(20).mean()
    
    available.extend(['price_sma20_ratio', 'price_sma50_ratio', 'sma20_sma50_ratio', 'bb_position', 'volume_ratio'])
    
    return df[available]

def create_labels(df: pd.DataFrame, future_periods: int = 5) -> pd.Series:
    """
    Erstellt Labels basierend auf zukünftiger Preisentwicklung.
    
    Returns:
        0 = Verkaufen (Preis fällt > 1.5%)
        1 = Halten (Preis ändert sich < 1.5%)
        2 = Kaufen (Preis steigt > 1.5%)
    """
    future_return = df['close'].shift(-future_periods) / df['close'] - 1
    
    labels = pd.Series(1, index=df.index)  # Default: Halten
    labels[future_return < -0.015] = 0  # Verkaufen bei > 1.5% Verlust
    labels[future_return > 0.015] = 2   # Kaufen bei > 1.5% Gewinn
    
    return labels

def train_model():
    """Trainiert das ML-Modell mit historischen Daten."""
    print("\n" + "="*60)
    print("KI-MODELL TRAINING")
    print("="*60)
    
    # 1. Daten laden
    print("\n1. Lade historische Daten...")
    data_provider = DataProvider(API_KEYS, DEFAULT_SETTINGS)
    indicators = TechnicalIndicators(INDICATORS)
    
    # Lade Daten für mehrere Symbole
    symbols = ['BTC/EUR', 'ETH/EUR', 'XRP/EUR']
    all_data = []
    
    for symbol in symbols:
        print(f"   • Lade {symbol}...")
        df = data_provider.get_historical_data(symbol, '1h', limit=2000)
        df_with_indicators = indicators.calculate_all(df)
        all_data.append(df_with_indicators)
    
    # Kombiniere alle Daten
    combined_df = pd.concat(all_data, ignore_index=True)
    print(f"   ✓ {len(combined_df)} Kerzen geladen")
    
    # 2. Features und Labels vorbereiten
    print("\n2. Bereite Features vor...")
    features_df = prepare_features(combined_df)
    labels = create_labels(combined_df, future_periods=5)
    
    # Entferne NaN-Zeilen
    valid_mask = ~(features_df.isna().any(axis=1) | labels.isna())
    features_df = features_df[valid_mask]
    labels = labels[valid_mask]
    
    print(f"   ✓ {len(features_df)} Samples, {len(features_df.columns)} Features")
    print(f"   • Label-Verteilung:")
    print(f"     - Verkaufen (0): {(labels == 0).sum()} ({(labels == 0).mean():.1%})")
    print(f"     - Halten (1):    {(labels == 1).sum()} ({(labels == 1).mean():.1%})")
    print(f"     - Kaufen (2):    {(labels == 2).sum()} ({(labels == 2).mean():.1%})")
    
    # 3. Train/Test Split
    print("\n3. Teile Daten auf...")
    X_train, X_test, y_train, y_test = train_test_split(
        features_df, labels, test_size=0.2, shuffle=False  # Keine Shuffle für Zeitreihen!
    )
    
    print(f"   • Training: {len(X_train)} Samples")
    print(f"   • Test: {len(X_test)} Samples")
    
    # 4. Skalierung
    print("\n4. Skaliere Features...")
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)
    
    # 5. Modell trainieren
    print("\n5. Trainiere XGBoost-Modell...")
    model = xgb.XGBClassifier(
        n_estimators=300,
        max_depth=6,
        learning_rate=0.03,
        subsample=0.8,
        colsample_bytree=0.8,
        random_state=42,
        objective='multi:softprob',
        eval_metric='mlogloss'
    )
    
    model.fit(
        X_train_scaled, y_train,
        eval_set=[(X_test_scaled, y_test)],
        verbose=False
    )
    
    # 6. Evaluierung
    print("\n6. Evaluiere Modell...")
    train_score = model.score(X_train_scaled, y_train)
    test_score = model.score(X_test_scaled, y_test)
    
    print(f"   • Training Accuracy: {train_score:.2%}")
    print(f"   • Test Accuracy:     {test_score:.2%}")
    
    # Feature Importance
    feature_importance = pd.DataFrame({
        'feature': X_train.columns,
        'importance': model.feature_importances_
    }).sort_values('importance', ascending=False)
    
    print("\n   Top 10 wichtigste Features:")
    for idx, row in feature_importance.head(10).iterrows():
        print(f"     {row['feature']:20} {row['importance']:.4f}")
    
    # 7. Modell speichern
    print("\n7. Speichere Modell...")
    model_dir = Path('models')
    model_dir.mkdir(exist_ok=True)
    
    joblib.dump(model, model_dir / 'trading_model.pkl')
    joblib.dump(scaler, model_dir / 'scaler.pkl')
    
    print(f"   ✓ Modell gespeichert in {model_dir}/")
    
    print("\n" + "="*60)
    print("✅ TRAINING ABGESCHLOSSEN!")
    print("="*60)
    print(f"\n💡 Das Modell hat eine Test-Genauigkeit von {test_score:.1%}")
    print("   Starte den Bot neu, um das neue Modell zu nutzen.\n")

if __name__ == "__main__":
    train_model()
