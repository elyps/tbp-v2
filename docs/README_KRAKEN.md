# Kraken Trading Bot mit XGBoost KI

Ein vollautomatischer Trading-Bot spezialisiert auf die **Kraken Exchange**, ausgestattet mit XGBoost Machine Learning für optimale Marktprognosen.

## 🚀 Features

- ✅ **Kraken-Integration**: Ausschließlich für Kraken optimiert
- ✅ **XGBoost KI-Modell**: State-of-the-art ML für Trading (deutlich besser als ChatGPT/Claude für numerische Daten)
- ✅ **15 Jahre Datenanalyse**: Historische Daten für präzise Vorhersagen
- ✅ **Automatisches Risikomanagement**: Stop-Loss, Take-Profit, Position Sizing
- ✅ **Multiple Strategien**:
  - Trend Following
  - Mean Reversion  
  - Breakout
  - ML-basierte XGBoost-Strategie
- ✅ **Paper Trading Modus**: Sicheres Testen ohne echtes Geld
- ✅ **Live Trading**: Automatische Ausführung bei Kraken

## 📋 Installation

### 1. Dependencies installieren

```bash
pip install -r requirements.txt
```

**Wichtigste Pakete:**
- `xgboost>=2.0.0` - Bestes ML-Modell für Trading
- `lightgbm>=4.0.0` - Alternative zu XGBoost
- `ccxt>=2.0.0` - Kraken Exchange API
- `pandas-ta>=0.3.14` - Technische Indikatoren
- `scikit-learn>=1.3.0` - ML Framework

### 2. Kraken API-Keys konfigurieren (optional für Live Trading)

Bearbeiten Sie `trading_bot/config.py`:

```python
API_KEYS = {
    'kraken': {
        'api_key': 'IHR_KRAKEN_API_KEY',
        'api_secret': 'IHR_KRAKEN_API_SECRET'
    },
}
```

**Hinweis**: Für Paper Trading und historische Daten sind KEINE API-Keys erforderlich!

## 🎯 Beste Kraken Trading-Paare

### Empfohlene Symbole (hohe Liquidität):

```python
# Im bot.py main() anpassen:
bot.run(symbols=['BTC/EUR', 'ETH/EUR', 'XRP/EUR', 'ADA/EUR'])
```

**Top Kraken Paare:**
1. `BTC/EUR` - Bitcoin (höchste Liquidität)
2. `ETH/EUR` - Ethereum
3. `XRP/EUR` - Ripple
4. `ADA/EUR` - Cardano
5. `DOT/EUR` - Polkadot
6. `MATIC/EUR` - Polygon
7. `SOL/EUR` - Solana

**USD Paare:**
- `BTC/USD`, `ETH/USD`, `XRP/USD`, usw.

## 🏃 Bot starten

### Paper Trading (ohne echtes Geld):

```bash
python main.py
```

### Live Trading aktivieren:

In `trading_bot/config.py`:

```python
DEFAULT_SETTINGS = {
    # ...
    'paper_trading': False,  # Auf False setzen für Live Trading
}
```

## ⚙️ Konfiguration

### ML-Model Einstellungen (config.py)

```python
ML_SETTINGS = {
    'model_type': 'xgboost',  # 'xgboost', 'lightgbm', 'random_forest'
    'n_estimators': 200,
    'max_depth': 7,
    'learning_rate': 0.05,
    # ...
}
```

### Risikomanagement

```python
RISK_MANAGEMENT = {
    'max_risk_per_trade': 0.01,  # 1% Risiko pro Trade
    'max_portfolio_risk': 0.05,  # 5% Gesamt-Risiko
    'max_open_positions': 3,
    'min_risk_reward_ratio': 2.0,  # 2:1 Risiko-Gewinn-Verhältnis
    'stop_loss_pct': 0.02,  # 2% Stop-Loss
}
```

### Strategien aktivieren/deaktivieren

```python
STRATEGIES = {
    'trend_following': {'enabled': True},
    'mean_reversion': {'enabled': True},
    'breakout': {'enabled': True},
    'ml_based': {'enabled': True, 'min_confidence': 0.65},  # XGBoost
}
```

## 🧠 Warum XGBoost statt ChatGPT/Claude?

**XGBoost ist speziell für Trading optimal:**

1. ✅ **Zeitreihen-Expertise**: Optimiert für numerische Finanzmarkt-Daten
2. ✅ **Schneller**: Millisekunden statt Sekunden
3. ✅ **Weniger Halluzinationen**: Basiert auf mathematischen Modellen
4. ✅ **Feature Importance**: Zeigt welche Indikatoren wichtig sind
5. ✅ **Bewährt**: Standard in Kaggle Trading Competitions

ChatGPT/Claude sind **Large Language Models** für Text, nicht für numerische Zeitreihen.

## 📊 Bot-Architektur

```
trading_bot/
├── bot.py              # Hauptlogik
├── config.py           # Kraken-Konfiguration
├── data_provider.py    # Kraken Daten-Fetching
├── indicators.py       # Technische Indikatoren
├── ml_model.py         # XGBoost/LightGBM KI
├── strategy.py         # Trading-Strategien
├── risk_management.py  # Position Sizing & Risk
└── exchange.py         # Kraken Order-Ausführung
```

## 📈 Modell trainieren

Der Bot lernt automatisch aus historischen Daten:

```python
from trading_bot.ml_model import MLModel

model = MLModel(ML_SETTINGS)

# Training mit historischen Daten
model.train(X_features, y_signals)

# Vorhersagen
predictions = model.predict(current_data)
```

## ⚠️ Wichtige Hinweise

### Vor Live Trading:

1. ✅ **Testen Sie im Paper-Trading-Modus** mindestens 1 Monat
2. ✅ **Starten Sie mit kleinen Beträgen** (z.B. 100-500€)
3. ✅ **Überwachen Sie den Bot** regelmäßig
4. ✅ **Setzen Sie Stop-Loss Limits** auf Ihrem Kraken-Account
5. ✅ **Aktivieren Sie 2FA** bei Kraken

### 90% Win-Rate Realität:

Eine **90% Win-Rate ist extrem schwierig** und unrealistisch für dauerhaften Erfolg. Professionelle Trader haben meist 50-60% Win-Rate mit gutem Risk-Reward-Verhältnis.

**Realistisches Ziel:**
- Win-Rate: 55-65%
- Risk-Reward-Ratio: 2:1 oder höher
- Max Drawdown: <20%
- Sharpe Ratio: >1.5

## 📝 Logs

Alle Bot-Aktivitäten werden geloggt:

```bash
tail -f logs/trading_bot.log
```

## 🛠️ Troubleshooting

### Fehler: "Invalid Api-Key ID"
- ✅ Entweder API-Keys in `config.py` eingeben ODER
- ✅ Sicherstellen dass `paper_trading: True` gesetzt ist

### Fehler: "XGBoost not available"
```bash
pip install xgboost>=2.0.0
```

### Fehler: "No data for symbol"
- ✅ Prüfen Sie die Symbol-Notation für Kraken: `BTC/EUR` nicht `BTCEUR`
- ✅ Verwenden Sie `EUR` oder `USD` Paare

## 📚 Weitere Ressourcen

- [Kraken API Dokumentation](https://docs.kraken.com/rest/)
- [XGBoost Dokumentation](https://xgboost.readthedocs.io/)
- [CCXT Kraken Guide](https://docs.ccxt.com/en/latest/exchange-markets.html#kraken)

## 🤝 Support

Bei Fragen oder Problemen:
1. Prüfen Sie die Logs in `logs/trading_bot.log`
2. Testen Sie im Paper-Trading-Modus
3. Überprüfen Sie die Kraken Exchange Status

## ⚖️ Disclaimer

**Dieser Bot dient nur zu Bildungszwecken!**

- Trading birgt hohe Risiken
- Verluste sind möglich
- Keine Garantie für Gewinne
- Verwenden Sie nur Geld, das Sie bereit sind zu verlieren
- Konsultieren Sie einen Finanzberater

---

**Viel Erfolg mit Ihrem Kraken Trading Bot! 🚀**
