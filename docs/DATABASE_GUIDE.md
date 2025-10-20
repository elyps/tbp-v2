# 📊 SQLite Database Guide - Trading Bot

## Komplette Datenverwaltung mit SQLite

Der Trading-Bot nutzt **SQLite** als zentrale Datenbank für alle persistenten Daten.

---

## 🎯 Warum SQLite?

### **Vorteile:**
✅ **Keine Installation** - In Python eingebaut  
✅ **Keine Konfiguration** - Funktioniert out-of-the-box  
✅ **Single File** - Gesamte DB in einer Datei  
✅ **Schnell** - Optimiert für lokale Anwendungen  
✅ **ACID** - Transaktions-sicher  
✅ **SQL Queries** - Mächtige Datenabfragen  
✅ **Easy Backup** - Einfach Datei kopieren  

### **vs. JSON/CSV:**
| Feature | JSON/CSV | SQLite |
|---------|----------|--------|
| Struktur | ❌ Lose | ✅ Streng |
| Queries | ❌ Komplex | ✅ Einfach (SQL) |
| Performance | ❌ Langsam | ✅ Schnell |
| Integrität | ❌ Keine | ✅ ACID |
| Backup | ✅ Einfach | ✅ Einfach |
| Concurrent | ❌ Problematisch | ✅ Sicher |

---

## 📁 Datenbank-Schema

### **1. TRADES** - Alle ausgeführten Trades

```sql
CREATE TABLE trades (
    id INTEGER PRIMARY KEY,
    trade_id TEXT UNIQUE,           -- Eindeutige Trade-ID
    symbol TEXT,                    -- BTC/USD, ETH/USD, etc.
    action TEXT,                    -- buy / sell
    amount REAL,                    -- Handelsmenge
    price REAL,                     -- Einstiegspreis
    timestamp TEXT,                 -- Zeitpunkt
    status TEXT,                    -- open / closed
    strategy TEXT,                  -- trend_following, breakout, etc.
    confidence REAL,                -- KI-Konfidenz (0-1)
    reason TEXT,                    -- Handelsgrund
    pnl REAL,                      -- Profit/Loss in EUR
    pnl_percent REAL,              -- P&L in %
    exit_price REAL,               -- Ausstiegspreis
    exit_timestamp TEXT,           -- Exit-Zeitpunkt
    created_at TEXT                -- Erstellungszeitpunkt
)
```

**Beispiel:**
```sql
SELECT * FROM trades WHERE symbol = 'BTC/USD' AND status = 'closed' ORDER BY timestamp DESC LIMIT 10;
```

---

### **2. PORTFOLIO** - Aktueller Portfolio-Status

```sql
CREATE TABLE portfolio (
    id INTEGER PRIMARY KEY,
    balance REAL,                  -- Verfügbares Kapital
    equity REAL,                   -- Gesamtwert (Balance + Positionen)
    total_trades INTEGER,          -- Gesamtanzahl Trades
    winning_trades INTEGER,        -- Gewinn-Trades
    losing_trades INTEGER,         -- Verlust-Trades
    total_pnl REAL,               -- Gesamt P&L
    max_drawdown REAL,            -- Maximaler Drawdown
    sharpe_ratio REAL,            -- Sharpe Ratio
    updated_at TEXT               -- Letztes Update
)
```

**Beispiel:**
```sql
SELECT balance, equity, total_pnl, (winning_trades * 100.0 / total_trades) as win_rate 
FROM portfolio ORDER BY id DESC LIMIT 1;
```

---

### **3. POSITIONS** - Offene Positionen

```sql
CREATE TABLE positions (
    id INTEGER PRIMARY KEY,
    symbol TEXT UNIQUE,           -- Symbol
    amount REAL,                  -- Menge
    entry_price REAL,             -- Einstiegspreis
    current_price REAL,           -- Aktueller Preis
    pnl REAL,                    -- Unrealisierter P&L
    pnl_percent REAL,            -- P&L in %
    opened_at TEXT,              -- Eröffnungszeitpunkt
    updated_at TEXT              -- Letztes Update
)
```

**Beispiel:**
```sql
SELECT symbol, amount, pnl, pnl_percent FROM positions WHERE pnl > 0 ORDER BY pnl DESC;
```

---

### **4. TRAINING_DATA** - ML Training Daten

```sql
CREATE TABLE training_data (
    id INTEGER PRIMARY KEY,
    trade_id TEXT,                -- Referenz zu trades
    symbol TEXT,                  -- Symbol
    features TEXT,                -- JSON: Alle 38 Features
    label INTEGER,                -- 0=Verkauf, 1=Halten, 2=Kauf
    pnl REAL,                    -- Trade-Ergebnis
    timestamp TEXT,              -- Zeitpunkt
    created_at TEXT             -- Erstellungszeitpunkt
)
```

**Features Format (JSON):**
```json
{
  "sma_20": 95234.56,
  "rsi": 67.3,
  "macd": 234.12,
  "volume": 1234567.89,
  ...
}
```

**Beispiel:**
```sql
SELECT COUNT(*) as samples, label, AVG(pnl) as avg_pnl 
FROM training_data 
GROUP BY label;
```

---

### **5. MODEL_PERFORMANCE** - ML Model Tracking

```sql
CREATE TABLE model_performance (
    id INTEGER PRIMARY KEY,
    model_version TEXT,           -- v1.0.0, v1.1.0, etc.
    accuracy REAL,               -- Genauigkeit
    precision_score REAL,        -- Präzision
    recall REAL,                 -- Recall
    f1_score REAL,              -- F1-Score
    samples_count INTEGER,       -- Anzahl Trainingssamples
    training_duration REAL,      -- Training-Dauer in Sekunden
    timestamp TEXT,             -- Zeitpunkt
    notes TEXT                  -- Zusätzliche Infos
)
```

**Beispiel:**
```sql
SELECT model_version, accuracy, samples_count, timestamp 
FROM model_performance 
ORDER BY timestamp DESC LIMIT 10;
```

---

### **6. NEWS** - Gespeicherte News & Sentiment

```sql
CREATE TABLE news (
    id INTEGER PRIMARY KEY,
    symbol TEXT,                  -- Symbol
    title TEXT,                   -- Titel
    content TEXT,                 -- Inhalt
    source TEXT,                  -- Quelle (NewsAPI, CryptoCompare, etc.)
    url TEXT,                    -- URL zum Artikel
    sentiment_score REAL,        -- -1 bis +1
    sentiment_label TEXT,        -- positive / neutral / negative
    published_at TEXT,          -- Veröffentlichungsdatum
    fetched_at TEXT            -- Abfragezeitpunkt
)
```

**Beispiel:**
```sql
SELECT title, sentiment_score, published_at 
FROM news 
WHERE symbol = 'BTC' AND sentiment_score > 0.5 
ORDER BY published_at DESC LIMIT 20;
```

---

### **7. SIGNALS** - Generierte Trading-Signale

```sql
CREATE TABLE signals (
    id INTEGER PRIMARY KEY,
    symbol TEXT,                  -- Symbol
    action TEXT,                  -- buy / sell
    confidence REAL,             -- Konfidenz (0-1)
    strategy TEXT,               -- Strategie
    reason TEXT,                 -- Grund
    price REAL,                  -- Aktueller Preis
    executed BOOLEAN,            -- Wurde ausgeführt?
    timestamp TEXT              -- Zeitpunkt
)
```

**Beispiel:**
```sql
SELECT symbol, action, confidence, reason 
FROM signals 
WHERE executed = 0 AND confidence > 0.7 
ORDER BY timestamp DESC;
```

---

### **8. BOT_LOGS** - System Logs

```sql
CREATE TABLE bot_logs (
    id INTEGER PRIMARY KEY,
    level TEXT,                   -- INFO, WARNING, ERROR
    message TEXT,                 -- Log-Nachricht
    module TEXT,                  -- Modul (bot.py, ml_model.py, etc.)
    timestamp TEXT               -- Zeitpunkt
)
```

**Beispiel:**
```sql
SELECT * FROM bot_logs WHERE level = 'ERROR' ORDER BY timestamp DESC LIMIT 50;
```

---

## 🔧 Verwendung im Code

### **Initialisierung:**

```python
from trading_bot.database import get_database

# Singleton-Instanz holen
db = get_database('trading_bot.db')
```

### **Trade speichern:**

```python
trade = {
    'id': 'trade_123',
    'symbol': 'BTC/USD',
    'action': 'buy',
    'amount': 0.1,
    'price': 95234.56,
    'timestamp': datetime.utcnow().isoformat(),
    'status': 'open',
    'strategy': 'trend_following',
    'confidence': 0.75,
    'reason': 'Strong uptrend + positive RSI'
}

db.save_trade(trade)
```

### **Trade aktualisieren (schließen):**

```python
db.update_trade('trade_123', {
    'status': 'closed',
    'exit_price': 96123.45,
    'exit_timestamp': datetime.utcnow().isoformat(),
    'pnl': 88.89,
    'pnl_percent': 0.93
})
```

### **Trades abfragen:**

```python
# Alle offenen Trades
open_trades = db.get_open_trades()

# Trades für Symbol
btc_trades = db.get_trades(symbol='BTC/USD', limit=100)

# Trade-Statistiken
stats = db.get_trade_statistics()
print(f"Win Rate: {stats['win_rate']:.1f}%")
print(f"Total P&L: {stats['total_pnl']:.2f} EUR")
```

### **Portfolio speichern:**

```python
portfolio = {
    'balance': 10543.21,
    'equity': 11234.56,
    'total_trades': 245,
    'winning_trades': 152,
    'losing_trades': 93,
    'total_pnl': 1234.56,
    'max_drawdown': -234.56,
    'sharpe_ratio': 1.85
}

db.save_portfolio(portfolio)
```

### **Training Sample speichern:**

```python
features = {
    'sma_20': 95234.56,
    'rsi': 67.3,
    'macd': 234.12,
    # ... alle 38 Features
}

db.save_training_sample(
    trade_id='trade_123',
    symbol='BTC/USD',
    features=features,
    label=2,  # Kauf war richtig
    pnl=88.89
)
```

### **Training Data als DataFrame:**

```python
# Alle Training Data
df = db.get_training_data(limit=1000)

# Nur für BTC
df_btc = db.get_training_data(symbol='BTC', limit=500)

# Stats
stats = db.get_training_stats()
print(f"Total Samples: {stats['total_samples']}")
print(f"Buy/Hold/Sell: {stats['buy_samples']}/{stats['hold_samples']}/{stats['sell_samples']}")
```

### **News speichern:**

```python
news = {
    'symbol': 'BTC',
    'title': 'Bitcoin surges past $95k',
    'content': 'Bitcoin reached new highs...',
    'source': 'NewsAPI',
    'url': 'https://...',
    'sentiment_score': 0.85,
    'sentiment_label': 'positive',
    'published_at': datetime.utcnow().isoformat()
}

db.save_news(news)
```

---

## 📊 Nützliche SQL Queries

### **Top 10 profitable Trades:**

```sql
SELECT symbol, pnl, pnl_percent, strategy, timestamp 
FROM trades 
WHERE status = 'closed' 
ORDER BY pnl DESC 
LIMIT 10;
```

### **Performance pro Symbol:**

```sql
SELECT 
    symbol,
    COUNT(*) as total_trades,
    SUM(CASE WHEN pnl > 0 THEN 1 ELSE 0 END) as wins,
    SUM(pnl) as total_pnl,
    AVG(pnl) as avg_pnl,
    (SUM(CASE WHEN pnl > 0 THEN 1 ELSE 0 END) * 100.0 / COUNT(*)) as win_rate
FROM trades
WHERE status = 'closed'
GROUP BY symbol
ORDER BY total_pnl DESC;
```

### **Performance pro Strategie:**

```sql
SELECT 
    strategy,
    COUNT(*) as trades,
    SUM(pnl) as total_pnl,
    AVG(confidence) as avg_confidence
FROM trades
WHERE status = 'closed'
GROUP BY strategy
ORDER BY total_pnl DESC;
```

### **Trading Activity über Zeit:**

```sql
SELECT 
    DATE(timestamp) as date,
    COUNT(*) as trades,
    SUM(pnl) as daily_pnl
FROM trades
WHERE status = 'closed'
GROUP BY DATE(timestamp)
ORDER BY date DESC
LIMIT 30;
```

### **Sentiment-Korrelation mit Performance:**

```sql
SELECT 
    t.symbol,
    AVG(n.sentiment_score) as avg_sentiment,
    AVG(t.pnl) as avg_pnl,
    COUNT(t.id) as trades
FROM trades t
LEFT JOIN news n ON t.symbol = SUBSTR(n.symbol, 1, INSTR(n.symbol, '/') - 1)
WHERE t.status = 'closed'
GROUP BY t.symbol;
```

### **Model Performance Verbesserung:**

```sql
SELECT 
    model_version,
    accuracy,
    samples_count,
    timestamp,
    (accuracy - LAG(accuracy) OVER (ORDER BY timestamp)) * 100 as improvement_pct
FROM model_performance
ORDER BY timestamp DESC
LIMIT 10;
```

---

## 🔨 Management Tools

### **Database Viewer (in Python):**

```python
from trading_bot.database import get_database

db = get_database()

# Alle Tabellen anzeigen
cursor = db.conn.cursor()
cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = cursor.fetchall()
print("Tabellen:", [t[0] for t in tables])

# Tabellen-Info
cursor.execute("PRAGMA table_info(trades)")
columns = cursor.fetchall()
for col in columns:
    print(f"  {col[1]} ({col[2]})")
```

### **Backup erstellen:**

```python
import shutil
from datetime import datetime

# Manuelles Backup
backup_name = f"backup_trading_bot_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
db.backup_database(backup_name)
```

**Oder via Shell:**
```bash
# Backup
cp trading_bot.db backups/trading_bot_$(date +%Y%m%d).db

# Restore
cp backups/trading_bot_20250119.db trading_bot.db
```

### **Cleanup alte Daten:**

```python
# Lösche Daten älter als 90 Tage
db.cleanup_old_data(days=90)
```

### **Export zu CSV:**

```python
import pandas as pd

# Trades exportieren
trades_df = pd.DataFrame(db.get_trades(limit=10000))
trades_df.to_csv('trades_export.csv', index=False)

# Training Data exportieren
training_df = db.get_training_data(limit=5000)
training_df.to_csv('training_data_export.csv', index=False)
```

---

## 🛠️ Migration von JSON/CSV

Falls Sie alte JSON/CSV Daten haben:

```python
import json
import pandas as pd
from trading_bot.database import get_database

db = get_database()

# === Migrate Trades ===
with open('training_data/trades_history.json', 'r') as f:
    old_trades = json.load(f)
    
for trade in old_trades:
    db.save_trade(trade)

# === Migrate Training Data ===
features_df = pd.read_csv('training_data/features_history.csv')
labels_df = pd.read_csv('training_data/labels_history.csv')

merged = features_df.merge(labels_df, left_index=True, right_index=True)

for idx, row in merged.iterrows():
    features = row.drop(['label', 'timestamp']).to_dict()
    db.save_training_sample(
        trade_id=f'migrated_{idx}',
        symbol='UNKNOWN',  # Symbol nicht in alten Daten
        features=features,
        label=row['label'],
        pnl=0.0  # P&L nicht in alten Daten
    )

print("Migration abgeschlossen!")
```

---

## 📈 Performance Monitoring

### **Live Statistics:**

```python
# Trade Stats
stats = db.get_trade_statistics()
print(f"Total Trades: {stats['total_trades']}")
print(f"Win Rate: {stats['win_rate']:.1f}%")
print(f"Total P&L: €{stats['total_pnl']:.2f}")
print(f"Avg Profit: €{stats['avg_pnl']:.2f}")
print(f"Best Trade: €{stats['max_profit']:.2f}")
print(f"Worst Trade: €{stats['max_loss']:.2f}")

# Training Stats
training_stats = db.get_training_stats()
print(f"\nTraining Samples: {training_stats['total_samples']}")
print(f"Buy Signals: {training_stats['buy_samples']}")
print(f"Hold Signals: {training_stats['hold_samples']}")
print(f"Sell Signals: {training_stats['sell_samples']}")

# Portfolio
portfolio = db.get_portfolio()
print(f"\nBalance: €{portfolio['balance']:.2f}")
print(f"Equity: €{portfolio['equity']:.2f}")
print(f"Total P&L: €{portfolio['total_pnl']:.2f}")
```

---

## 🔍 Troubleshooting

### **Database locked:**

```python
# Erhöhe timeout
import sqlite3
conn = sqlite3.connect('trading_bot.db', timeout=30.0)
```

### **Corrupt Database:**

```bash
# Integrity Check
sqlite3 trading_bot.db "PRAGMA integrity_check;"

# Repair (via dump & restore)
sqlite3 trading_bot.db .dump > backup.sql
rm trading_bot.db
sqlite3 trading_bot.db < backup.sql
```

### **Database zu groß:**

```python
# Vacuum (komprimieren)
db.conn.execute("VACUUM")

# Alte Daten löschen
db.cleanup_old_data(days=60)
```

---

## 📚 Zusammenfassung

### **Vorteile der SQLite Integration:**

✅ **Zentrale Datenverwaltung** - Alles in einer DB  
✅ **Strukturierte Daten** - Klare Schemas  
✅ **Mächtige Queries** - SQL für komplexe Analysen  
✅ **Performance** - Schneller als JSON/CSV  
✅ **Datenintegrität** - ACID Transactions  
✅ **Easy Backup** - Single File  
✅ **No Config** - Funktioniert out-of-the-box  

### **Was wird gespeichert:**

- ✅ Alle Trades (Entry + Exit)
- ✅ Portfolio-Status (Live)
- ✅ Offene Positionen
- ✅ Training Data für ML
- ✅ Model Performance History
- ✅ News & Sentiment
- ✅ Trading Signale
- ✅ System Logs

---

**Die Datenbank ist das Herzstück Ihres Trading-Bots!** 💾🚀

Alle Funktionen sind bereits implementiert in `trading_bot/database.py`.
