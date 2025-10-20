# 🚀 Quick Start Guide - Kraken Trading Bot

## Paper Trading ist AKTIV ✅

Dein Bot läuft im **sicheren Modus** ohne echtes Geld. Perfekt zum Testen!

---

## 📋 3 einfache Schritte zum Start:

### 1️⃣ **ML-Modell trainieren** (Empfohlen, optional)

Trainiere das XGBoost KI-Modell mit historischen Kraken-Daten:

```powershell
python train_model.py
```

**Was passiert:**
- Lädt 5000+ historische Kerzen von Kraken
- Berechnet 14+ technische Indikatoren
- Trainiert XGBoost auf BTC/EUR, ETH/EUR, XRP/EUR
- Speichert Modell in `models/` Ordner

**Dauer:** ~5-10 Minuten

---

### 2️⃣ **Bot starten**

Starte den Trading Bot:

```powershell
python main.py
```

**Was der Bot macht:**
- ✅ Holt Live-Daten von Kraken (alle 60 Sekunden)
- ✅ Analysiert BTC/EUR, ETH/EUR, XRP/EUR
- ✅ Generiert Trading-Signale mit 4 Strategien
- ✅ Simuliert Trades (Paper Trading)
- ✅ Loggt alle Aktivitäten in `logs/trading_bot.log`

**Der Bot läuft kontinuierlich. Drücke `Ctrl+C` zum Beenden.**

---

### 3️⃣ **Bot überwachen** (Neues Terminal öffnen!)

Während der Bot läuft, öffne ein **zweites Terminal** und starte das Dashboard:

```powershell
python monitor_bot.py
```

**Du siehst:**
- 💰 Portfolio (Balance, Equity, Gewinn/Verlust)
- 📊 Offene Positionen
- 📈 Performance (Win-Rate, Trades, Drawdown)
- 📝 Live-Logs der letzten Aktivitäten

**Dashboard aktualisiert sich alle 5 Sekunden automatisch.**

---

## 🎯 Typischer Workflow:

```
Terminal 1: python main.py        ← Bot läuft
Terminal 2: python monitor_bot.py ← Dashboard überwacht
```

---

## 📊 Wo finde ich was?

### **Logs ansehen:**
```powershell
# Live-Logs (folgt neuen Einträgen)
Get-Content logs/trading_bot.log -Wait -Tail 50

# Oder öffne die Datei direkt:
logs/trading_bot.log
```

### **Portfolio-Status:**
```json
portfolio_state.json  ← Aktueller Status (Balance, Positionen, Performance)
```

### **Trainiertes Modell:**
```
models/ml_model.pkl  ← XGBoost Modell
models/scaler.pkl    ← Feature Scaler
```

---

## ⚙️ Trading-Symbole ändern

Bearbeite `trading_bot/bot.py` (Zeile ~371):

```python
# Aktuelle Symbole:
bot.run(symbols=['BTC/EUR', 'ETH/EUR', 'XRP/EUR'])

# Andere Kraken-Paare:
bot.run(symbols=['BTC/USD', 'ETH/USD', 'ADA/EUR', 'DOT/EUR'])
```

**Beste Kraken-Paare (hohe Liquidität):**
- EUR: `BTC/EUR`, `ETH/EUR`, `XRP/EUR`, `ADA/EUR`, `DOT/EUR`
- USD: `BTC/USD`, `ETH/USD`, `XRP/USD`, `LTC/USD`

---

## 🧠 Was macht der Bot genau?

### **Jede Minute (60 Sekunden):**

1. **Daten holen** von Kraken
   - 1000 historische Kerzen (1 Tag Timeframe)
   - Für jedes Symbol (BTC/EUR, ETH/EUR, XRP/EUR)

2. **Indikatoren berechnen** (14 technische Indikatoren)
   - SMA (20, 50, 200)
   - EMA (9, 21, 50)
   - RSI (14)
   - MACD
   - Bollinger Bands
   - ATR, Stochastic, etc.

3. **KI-Vorhersage** (falls trainiert)
   - XGBoost analysiert Marktmuster
   - Gibt Kauf/Verkauf/Halten Signal

4. **4 Strategien prüfen:**
   - **Trend Following** - Folgt starken Trends
   - **Mean Reversion** - Kauft bei Überverkauft
   - **Breakout** - Handelt bei Ausbrüchen
   - **ML-Based** - Nutzt XGBoost KI

5. **Risikomanagement**
   - Prüft Stop-Loss, Take-Profit
   - Berechnet Position Size (1% Risiko pro Trade)
   - Max 3 offene Positionen gleichzeitig

6. **Trade ausführen** (simuliert im Paper Trading)
   - Loggt alle Orders
   - Aktualisiert Portfolio
   - Speichert Performance

---

## 🔍 Warum sehe ich keine Trades?

**3 häufigste Gründe:**

### 1. **ML-Modell nicht trainiert** ⚠️
```
WARNING - Modell ist noch nicht trainiert
```
**Lösung:** 
```powershell
python train_model.py
```

### 2. **Keine klaren Trading-Signale** 
Der Markt muss bestimmte Bedingungen erfüllen:
- Starker Trend (für Trend-Following)
- Überverkauft/Überkauft (für Mean Reversion)
- Ausbruch aus Range (für Breakout)

**Das ist normal!** Professionelle Trading-Bots handeln nur bei guten Gelegenheiten.

### 3. **Risikomanagement blockt Trades**
- Zu hohes Risiko
- Zu viele offene Positionen (max 3)
- Schlechtes Risk-Reward-Verhältnis (<2:1)

**Das ist gut!** Schützt dein virtuelles Kapital.

---

## 📈 Wie lange testen?

### **Empfehlung:**

1. **Woche 1-2:** Paper Trading beobachten
   - Schaue ob Signale generiert werden
   - Prüfe Win-Rate und Drawdown

2. **Woche 3-4:** Parameter optimieren
   - Passe Strategien an (`trading_bot/config.py`)
   - Teste verschiedene Symbole

3. **Ab Woche 4:** Erwäge Live Trading
   - **NUR** wenn Win-Rate >55% und Drawdown <15%
   - Starte mit **SEHR kleinen** Beträgen (100-500€)

---

## ⚠️ Wichtige Hinweise

### **Paper Trading (aktuell):**
- ✅ Vollkommen sicher, kein echtes Geld
- ✅ Nutzt echte Kraken Live-Daten
- ✅ Simuliert realistische Orders

### **Für Live Trading (später):**
1. Setze `paper_trading: False` in `trading_bot/config.py`
2. Füge Kraken API-Keys ein (mit Trading-Berechtigung)
3. **Starte mit MINIMAL-Beträgen!**
4. Aktiviere 2FA bei Kraken
5. Setze Exchange-seitige Stop-Loss Limits

### **90% Win-Rate?**
❌ **Unrealistisch auf Dauer**

Realistisches Ziel:
- ✅ Win-Rate: 55-65%
- ✅ Risk-Reward: 2:1 oder besser
- ✅ Max Drawdown: <20%
- ✅ Sharpe Ratio: >1.5

---

## 🆘 Probleme?

### **Bot startet nicht:**
```powershell
# Prüfe Dependencies:
pip list | Select-String "xgboost|pandas|ccxt"

# Installiere fehlende:
pip install -r requirements.txt
```

### **"Keine Daten für Symbol":**
- Prüfe Kraken Status: https://status.kraken.com/
- Verwende korrekte Symbol-Notation: `BTC/EUR` nicht `BTCEUR`

### **"ModuleNotFoundError":**
```powershell
pip install xgboost lightgbm scikit-learn pandas numpy ccxt pandas-ta
```

### **Logs ansehen:**
```powershell
Get-Content logs/trading_bot.log -Tail 100
```

---

## 📚 Nächste Schritte

1. ✅ **Trainiere ML-Modell:** `python train_model.py`
2. ✅ **Starte Bot:** `python main.py`
3. ✅ **Öffne Dashboard:** `python monitor_bot.py` (neues Terminal)
4. ✅ **Beobachte 1-2 Wochen** im Paper Trading
5. ✅ **Optimiere Parameter** in `trading_bot/config.py`

---

## 💡 Tipps

- **Geduld!** Trading-Bots brauchen Zeit für gute Gelegenheiten
- **Logs lesen!** Verstehe was der Bot macht
- **Parameter testen!** Experimentiere mit verschiedenen Settings
- **Risiko managen!** Nie mehr als 1-2% pro Trade riskieren

---

**Viel Erfolg mit deinem Kraken Trading Bot! 🚀**

Bei Fragen: Schaue in `README_KRAKEN.md` für Details.
