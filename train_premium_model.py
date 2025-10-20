#!/usr/bin/env python
"""
Trainiert ein Premium-KI-Modell mit allen verfügbaren Indikatoren
für maximale Vorhersagegenauigkeit und konsistente Gewinne.
"""

import sys
from pathlib import Path
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
import xgboost as xgb
from sklearn.ensemble import RandomForestClassifier
import joblib
import logging

project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from trading_bot.data_provider import DataProvider
from trading_bot.indicators import TechnicalIndicators
from trading_bot.config import API_KEYS, DEFAULT_SETTINGS, INDICATORS

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def prepare_premium_features(df: pd.DataFrame) -> pd.DataFrame:
    """Bereitet ALLE verfügbaren Features für das Premium-Modell vor."""
    
    # Basis-Indikatoren
    base_features = [
        # Moving Averages
        'sma_20', 'sma_50', 'ema_9', 'ema_21',
        # Momentum
        'rsi_14', 'macd_line', 'macd_signal', 'macd_hist', 'momentum',
        'stoch_k', 'stoch_d',
        # Volatilität
        'bb_upper', 'bb_middle', 'bb_lower', 'atr',
        # Trend
        'adx', 'plus_di', 'minus_di',
        # Volumen
        'volume', 'obv'
    ]
    
    available = [col for col in base_features if col in df.columns]
    
    print(f"   Debug: {len(available)}/{len(base_features)} Basis-Features gefunden")
    
    if len(available) < 10:
        print(f"   ⚠️  Zu wenig Features! Verfügbare Spalten:")
        print(f"   {list(df.columns)[:20]}...")
        # Erstelle Features trotzdem mit dem was da ist
    
    # Erstelle DataFrame mit Index vom Original-DF
    features_df = pd.DataFrame(index=df.index)
    
    # Füge verfügbare Basis-Features hinzu
    for col in available:
        if col in df.columns:
            features_df[col] = df[col]
    
    # Abgeleitete Features (erhöhen Vorhersagegenauigkeit)
    if 'close' in df.columns:
        # Preis-Ratios
        if 'sma_20' in df.columns:
            features_df['price_sma20_ratio'] = df['close'] / df['sma_20']
            features_df['price_distance_sma20'] = (df['close'] - df['sma_20']) / df['sma_20']
        
        if 'sma_50' in df.columns:
            features_df['price_sma50_ratio'] = df['close'] / df['sma_50']
        
        # Bollinger Band Position (0-1)
        if all(col in df.columns for col in ['bb_lower', 'bb_upper']):
            bb_range = df['bb_upper'] - df['bb_lower']
            features_df['bb_position'] = (df['close'] - df['bb_lower']) / bb_range.replace(0, 1)
            features_df['bb_width'] = bb_range / df['bb_middle'].replace(0, 1)
    
    # Trend-Features
    if 'sma_20' in df.columns and 'sma_50' in df.columns:
        features_df['sma20_sma50_ratio'] = df['sma_20'] / df['sma_50']
        features_df['trend_alignment'] = np.where(df['sma_20'] > df['sma_50'], 1, -1)
    
    # Momentum-Features
    if 'rsi_14' in df.columns:
        features_df['rsi_normalized'] = (df['rsi_14'] - 50) / 50  # -1 bis +1
        features_df['rsi_oversold'] = np.where(df['rsi_14'] < 30, 1, 0)
        features_df['rsi_overbought'] = np.where(df['rsi_14'] > 70, 1, 0)
    
    # Volumen-Features
    if 'volume' in df.columns:
        features_df['volume_ratio'] = df['volume'] / df['volume'].rolling(20).mean()
        features_df['volume_trend'] = df['volume'].pct_change(5, fill_method=None)
    
    if 'obv' in df.columns:
        features_df['obv_trend'] = df['obv'].pct_change(5, fill_method=None)
    
    # ADX Trend-Stärke (kritisch für Qualität!)
    if 'adx' in df.columns:
        features_df['trend_strong'] = np.where(df['adx'] > 25, 1, 0)
        features_df['trend_weak'] = np.where(df['adx'] < 20, 1, 0)
    
    # Stochastic Momentum
    if 'stoch_k' in df.columns and 'stoch_d' in df.columns:
        features_df['stoch_signal'] = np.where(df['stoch_k'] > df['stoch_d'], 1, -1)
    
    # MACD Signal
    if 'macd_hist' in df.columns:
        features_df['macd_positive'] = np.where(df['macd_hist'] > 0, 1, 0)
        features_df['macd_momentum'] = df['macd_hist'].rolling(3).mean()
    
    return features_df

def create_conservative_labels(df: pd.DataFrame, future_periods: int = 5, threshold: float = 0.02) -> pd.Series:
    """
    Erstellt Labels mit KONSERVATIVEM Ansatz für konsistente Gewinne.
    
    Threshold 2% = Nur sichere Bewegungen traden
    
    Returns:
        0 = Verkaufen (Preis fällt > 2%)
        1 = Halten (unsichere Bewegung < 2%)
        2 = Kaufen (Preis steigt > 2%)
    """
    future_return = df['close'].shift(-future_periods) / df['close'] - 1
    
    labels = pd.Series(1, index=df.index)  # Default: Halten
    labels[future_return < -threshold] = 0  # Verkaufen bei > 2% Verlust
    labels[future_return > threshold] = 2   # Kaufen bei > 2% Gewinn
    
    return labels

def train_ensemble_model():
    """Trainiert ein Ensemble-Modell (XGBoost + RandomForest) für robuste Vorhersagen."""
    print("\n" + "="*70)
    print("🤖 PREMIUM KI-MODELL TRAINING")
    print("   Ziel: Konsistente Gewinne durch hochwertige Signale")
    print("="*70)
    
    # 1. Daten laden
    print("\n📊 1. Lade erweiterte historische Daten...")
    data_provider = DataProvider(API_KEYS, DEFAULT_SETTINGS)
    indicators = TechnicalIndicators(INDICATORS)
    
    # Nutze die NEUEN 7 Währungspaare (wie im Bot)
    symbols = [
        'BTC/USD', 'ETH/USD', 'SOL/USD', 'XRP/USD', 'ADA/USD',  # Top 5 USD
        'BTC/EUR', 'ETH/EUR'  # EUR
    ]
    all_data = []
    
    for symbol in symbols:
        print(f"   • {symbol}...")
        try:
            df = data_provider.get_historical_data(symbol, '1h', limit=2000)
            df_with_indicators = indicators.calculate_all(df)
            all_data.append(df_with_indicators)
        except Exception as e:
            print(f"   ⚠️  Fehler bei {symbol}: {e}")
            continue
    
    if not all_data:
        print("   ❌ Keine Daten geladen! Prüfe Symbole und Verbindung.")
        return
    
    combined_df = pd.concat(all_data, ignore_index=True)
    print(f"   ✓ {len(combined_df)} Kerzen von {len(all_data)} Paaren")
    
    # 2. Features vorbereiten
    print("\n🔧 2. Erstelle erweiterte Features...")
    features_df = prepare_premium_features(combined_df)
    
    if features_df.empty or len(features_df) == 0:
        print("   ❌ Feature-Erstellung fehlgeschlagen!")
        return
    
    labels = create_conservative_labels(combined_df, future_periods=5, threshold=0.02)
    
    print(f"   Pre-Clean: {len(features_df)} Feature-Zeilen, {len(labels)} Label-Zeilen")
    print(f"   Features NaN: {features_df.isna().sum().sum()}, Labels NaN: {labels.isna().sum()}")
    
    # Bereinigen - nur Zeilen mit zu vielen NaN entfernen
    # Erlaube ein paar NaN-Werte (werden mit 0 gefüllt)
    features_df = features_df.fillna(0)
    valid_mask = ~labels.isna()
    features_df = features_df[valid_mask]
    labels = labels[valid_mask]
    
    if len(features_df) == 0:
        print("   ❌ Alle Samples wurden gefiltert! Prüfe Datenqualität.")
        return
    
    print(f"   ✓ {len(features_df)} Samples, {len(features_df.columns)} Features")
    print(f"\n   📈 Label-Verteilung (2% Threshold):")
    sell_pct = (labels == 0).mean()
    hold_pct = (labels == 1).mean()
    buy_pct = (labels == 2).mean()
    print(f"      Verkaufen: {(labels == 0).sum():4} ({sell_pct:.1%})")
    print(f"      Halten:    {(labels == 1).sum():4} ({hold_pct:.1%})")
    print(f"      Kaufen:    {(labels == 2).sum():4} ({buy_pct:.1%})")
    
    # 3. Train/Test Split
    print("\n✂️  3. Teile Daten auf (zeitlich korrekt)...")
    X_train, X_test, y_train, y_test = train_test_split(
        features_df, labels, test_size=0.2, shuffle=False
    )
    
    # 4. Skalierung
    print("\n📏 4. Skaliere Features...")
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)
    
    # 5. Ensemble Training
    print("\n🧠 5. Trainiere ENSEMBLE-Modell (XGBoost + RandomForest)...")
    
    # XGBoost (stark bei nicht-linearen Mustern)
    print("   • XGBoost...")
    xgb_model = xgb.XGBClassifier(
        n_estimators=400,
        max_depth=7,
        learning_rate=0.02,
        subsample=0.8,
        colsample_bytree=0.8,
        random_state=42,
        objective='multi:softprob',
        eval_metric='mlogloss'
    )
    xgb_model.fit(X_train_scaled, y_train, verbose=False)
    
    # RandomForest (robust gegen Overfitting)
    print("   • RandomForest...")
    rf_model = RandomForestClassifier(
        n_estimators=300,
        max_depth=15,
        min_samples_split=20,
        min_samples_leaf=10,
        random_state=42
    )
    rf_model.fit(X_train_scaled, y_train)
    
    # 6. Evaluierung
    print("\n📊 6. Evaluiere Ensemble...")
    xgb_score = xgb_model.score(X_test_scaled, y_test)
    rf_score = rf_model.score(X_test_scaled, y_test)
    
    print(f"   XGBoost Accuracy:      {xgb_score:.2%}")
    print(f"   RandomForest Accuracy: {rf_score:.2%}")
    print(f"   Durchschnitt:          {(xgb_score + rf_score)/2:.2%}")
    
    # Feature Importance (XGBoost)
    feature_importance = pd.DataFrame({
        'feature': X_train.columns,
        'importance': xgb_model.feature_importances_
    }).sort_values('importance', ascending=False)
    
    print("\n   🔝 Top 15 wichtigste Features:")
    for idx, row in feature_importance.head(15).iterrows():
        print(f"      {row['feature']:25} {'█' * int(row['importance'] * 100)}")
    
    # 7. Modelle speichern
    print("\n💾 7. Speichere Ensemble-Modelle...")
    model_dir = Path('models')
    model_dir.mkdir(exist_ok=True)
    
    joblib.dump(xgb_model, model_dir / 'trading_model.pkl')  # Primary
    joblib.dump(rf_model, model_dir / 'trading_model_rf.pkl')  # Backup
    joblib.dump(scaler, model_dir / 'scaler.pkl')
    
    # Speichere auch Feature-Namen für Debugging
    with open(model_dir / 'feature_names.txt', 'w') as f:
        f.write('\n'.join(X_train.columns))
    
    print(f"   ✓ Modelle gespeichert in {model_dir}/")
    
    print("\n" + "="*70)
    print("✅ ENSEMBLE-TRAINING ABGESCHLOSSEN!")
    print("="*70)
    print(f"\n💎 Premium-Modell Statistiken:")
    print(f"   • Features: {len(X_train.columns)}")
    print(f"   • Genauigkeit: {xgb_score:.1%}")
    print(f"   • Conservative Threshold: 2% (nur sichere Trades)")
    print(f"\n🚀 Starte den Bot neu für KI-gesteuerte Trades!\n")

if __name__ == "__main__":
    train_ensemble_model()
