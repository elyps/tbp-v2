#!/usr/bin/env python
"""
Debug-Skript, um zu prüfen, warum keine Handelssignale generiert werden.
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from trading_bot.data_provider import DataProvider
from trading_bot.indicators import TechnicalIndicators
from trading_bot.ml_model import MLModel
from trading_bot.strategy import StrategyManager
from trading_bot.config import API_KEYS, DEFAULT_SETTINGS, INDICATORS, ML_SETTINGS, STRATEGIES

def main():
    print("=" * 60)
    print("DEBUG: Testing Trading Signal Generation")
    print("=" * 60)
    
    # 1. Initialize components
    print("\n1. Initializing components...")
    data_provider = DataProvider(API_KEYS, DEFAULT_SETTINGS)
    indicators = TechnicalIndicators(INDICATORS)
    ml_model = MLModel(ML_SETTINGS)
    strategy_manager = StrategyManager(STRATEGIES, indicators, ml_model)
    
    print(f"   Active strategies: {strategy_manager.active_strategies}")
    
    # 2. Get data
    print("\n2. Fetching BTC/EUR data...")
    df = data_provider.get_historical_data('BTC/EUR', '1d', 100)
    print(f"   Loaded {len(df)} candles")
    print(f"   Latest price: €{df['close'].iloc[-1]:,.2f}")
    
    # 3. Calculate indicators
    print("\n3. Calculating indicators...")
    df_with_indicators = indicators.calculate_all(df)
    print(f"   Total columns: {len(df_with_indicators.columns)}")
    print(f"   Available indicators: {[col for col in df_with_indicators.columns if col not in ['open', 'high', 'low', 'close', 'volume']]}")
    
    # Check if required indicators exist
    print("\n4. Checking required indicators:")
    required_indicators = ['sma_20', 'sma_50', 'rsi_14']
    for ind in required_indicators:
        if ind in df_with_indicators.columns:
            value = df_with_indicators[ind].iloc[-1]
            print(f"   ✓ {ind}: {value}")
        else:
            print(f"   ✗ {ind}: MISSING")
    
    # 4. Get ML predictions
    print("\n5. Getting ML predictions...")
    predictions = ml_model.predict(df_with_indicators)
    print(f"   Predictions: {predictions}")
    
    # 5. Evaluate strategies
    print("\n6. Evaluating strategies...")
    signals = strategy_manager.evaluate(df_with_indicators, predictions, 'BTC/EUR')
    
    if signals:
        print(f"   ✓ Generated {len(signals)} signals:")
        for i, signal in enumerate(signals, 1):
            print(f"      Signal {i}:")
            print(f"         Action: {signal['action']}")
            print(f"         Confidence: {signal['confidence']:.2%}")
            print(f"         Strategy: {signal['strategy']}")
            print(f"         Reason: {signal['reason']}")
    else:
        print(f"   ✗ NO SIGNALS GENERATED")
        print("\n   Analyzing why no signals...")
        
        # Check each strategy
        current = df_with_indicators.iloc[-1]
        price = current['close']
        
        print(f"\n   Trend Following Analysis:")
        if 'sma_20' in df_with_indicators.columns and 'sma_50' in df_with_indicators.columns:
            sma_20 = current['sma_20']
            sma_50 = current['sma_50']
            print(f"      Price: €{price:,.2f}")
            print(f"      SMA 20: €{sma_20:,.2f}")
            print(f"      SMA 50: €{sma_50:,.2f}")
            print(f"      Price > SMA20: {price > sma_20}")
            print(f"      SMA20 > SMA50: {sma_20 > sma_50}")
        
        print(f"\n   Mean Reversion Analysis:")
        if 'rsi_14' in df_with_indicators.columns:
            rsi = current['rsi_14']
            print(f"      RSI: {rsi:.1f}")
            print(f"      Oversold (RSI < 30): {rsi < 30}")
            print(f"      Overbought (RSI > 70): {rsi > 70}")
        
        print(f"\n   Breakout Analysis:")
        recent = df_with_indicators.tail(20)
        high_20 = recent['high'].max()
        low_20 = recent['low'].min()
        print(f"      Current price: €{price:,.2f}")
        print(f"      20-day high: €{high_20:,.2f}")
        print(f"      20-day low: €{low_20:,.2f}")
        print(f"      Near high (>99.9%): {price >= high_20 * 0.999}")
        print(f"      Near low (<100.1%): {price <= low_20 * 1.001}")
    
    print("\n" + "=" * 60)

if __name__ == "__main__":
    main()
