"""
Konfigurationsdatei für den Trading-Bot
"""

# API-Schlüssel für Kraken (sollten in Produktion in Umgebungsvariablen gespeichert werden)
API_KEYS = {
    'kraken': {
        'api_key': 'YOUR_KRAKEN_API_KEY',
        'api_secret': 'YOUR_KRAKEN_API_SECRET'
    },
}

# Standardwerte für das Trading
DEFAULT_SETTINGS = {
    'timeframe': '1h',  # Standard-Zeitrahmen für die Analyse (1h = aktiver, 4h = mittel, 1d = langfristig)
    'initial_balance': 10000.0,  # Startkapital in USD
    'risk_per_trade': 1.0,  # Risiko pro Trade in % des Kontoguthabens
    'max_drawdown': 20.0,  # Maximaler Drawdown in %
    'trading_fee': 0.1,  # Handelsgebühr in %
    'slippage': 0.05,  # Erwarteter Slippage in %
    'paper_trading': True,  # Paper Trading aktiviert (kein echtes Geld)
}

# Standard-Indikatoren und ihre Parameter
INDICATORS = {
    'sma': [20, 50, 200],
    'ema': [9, 21, 50],
    'rsi': 14,
    'macd': {'fast': 12, 'slow': 26, 'signal': 9},
    'bollinger_bands': {'window': 20, 'std_dev': 2},
    'atr': 14,
}

# KI-Modell-Einstellungen (XGBoost - Best für Trading)
ML_SETTINGS = {
    'model_type': 'xgboost',  # 'xgboost', 'lightgbm', 'random_forest', 'gradient_boosting'
    'model_path': 'models/',
    'n_estimators': 200,
    'max_depth': 7,
    'learning_rate': 0.05,
    'subsample': 0.8,
    'colsample_bytree': 0.8,
    'train_test_split': 0.8,
    'sequence_length': 60,  # Anzahl der vergangenen Kerzen für die Vorhersage
    'prediction_length': 5,  # Anzahl der vorherzusagenden Kerzen
    'validation_split': 0.1,
}

# Risikomanagement (KONSERVATIV für konsistente Gewinne)
RISK_MANAGEMENT = {
    'max_risk_per_trade': 0.008,  # 0.8% des Kapitals pro Trade (sehr konservativ)
    'max_portfolio_risk': 0.03,  # 3% des Gesamtportfolios (streng begrenzt)
    'max_open_positions': 1,  # NUR 1 Position gleichzeitig (maximaler Fokus)
    'min_risk_reward_ratio': 3.0,  # Min 3:1 Risk-Reward (nur beste Setups)
    'min_confidence': 0.75,  # 75% Mindest-Konfidenz (hochwertige Signale nur)
    'stop_loss_pct': 0.012,  # Stop-Loss 1.2% (enger Schutz)
    'take_profit_pct': 0.036,  # Take-Profit 3.6% (3:1 Risk-Reward)
    'trailing_stop': True,
    'trailing_stop_distance': 0.003,  # Trailing Stop 0.3% (eng folgen)
    'partial_take_profit': True,  # Gewinne teilweise sichern
    'partial_tp_pct': 0.02,  # Bei 2% 50% der Position schließen
}

# Strategie-Einstellungen (Kraken-optimiert)
STRATEGIES = {
    'trend_following': {
        'enabled': True,
        'timeframes': ['1h', '4h', '1d'],
        'indicators': ['sma', 'macd', 'rsi'],
    },
    'mean_reversion': {
        'enabled': True,  # Aktiviert für Kraken
        'timeframes': ['15m', '1h'],
        'indicators': ['bollinger_bands', 'rsi'],
    },
    'breakout': {
        'enabled': True,
        'timeframes': ['1h', '4h'],
        'indicators': ['atr', 'volume'],
    },
    'ml_based': {
        'enabled': True,  # XGBoost-basierte Strategie
        'min_confidence': 0.65,
        'timeframes': ['1h', '4h'],
    },
}

# Logging-Konfiguration
LOGGING_CONFIG = {
    'level': 'INFO',
    'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    'file': 'logs/trading_bot.log'
}
