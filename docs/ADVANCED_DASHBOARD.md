# 🚀 Advanced Trading Bot Dashboard

## Neues, ausführliches Dashboard mit vielen Details!

---

## ✨ Features:

### **1. Portfolio Übersicht**
```
✓ Startkapital: 20€
✓ Cash Balance (Live)
✓ Gesamt Equity
✓ Gesamt P&L (Gewinn/Verlust)
✓ ROI (Return on Investment) in %
✓ Max Drawdown
✓ Sharpe Ratio
```

### **2. Offene Positionen**
```
✓ Detaillierte Position-Informationen
✓ Eröffnungspreis vs. aktueller Preis
✓ Unrealisierter P&L (Gewinn/Verlust)
✓ Position-Wert in Euro
✓ "Vor X Minuten/Stunden" Anzeige
✓ Gesamt-Übersicht aller Positionen
```

### **3. Trade Statistiken**
```
✓ Gesamt Trades (Offen + Geschlossen)
✓ Gewinn-Trades vs. Verlust-Trades
✓ Win-Rate in %
✓ Durchschnittlicher P&L
✓ Bester Trade
✓ Schlechtester Trade
```

### **4. Performance pro Symbol**
```
✓ Top 10 Symbole nach P&L
✓ Anzahl Trades pro Symbol
✓ Wins/Losses pro Symbol
✓ Win-Rate pro Symbol
✓ Gesamt P&L pro Symbol
```

### **5. Letzte Trades (Top 10)**
```
✓ Chronologische Liste der letzten Trades
✓ Action (BUY/SELL) farblich markiert
✓ Status (OPEN/CLOSED) mit Symbol
✓ Zeitstempel + "vor X Min" Anzeige
✓ P&L für geschlossene Trades
```

### **6. Letzte Aktivitäten**
```
✓ Live Logs aus dem Bot
✓ Farbcodiert nach Level (ERROR, WARNING, INFO)
✓ Letzte 5 Einträge
```

---

## 🎨 Design:

### **Farbcodierung:**
- 🟢 **Grün** = Gewinn, Positive Werte
- 🔴 **Rot** = Verlust, Negative Werte
- 🟡 **Gelb** = Wichtige Informationen
- 🔵 **Blau** = Allgemeine Informationen
- ⚪ **Grau** = Logs, Zeitstempel

### **Übersichtlich:**
- Klare Sektionen mit Rahmen
- Einrückungen für bessere Lesbarkeit
- Symbole (🚀, 💰, 📊, 📈, 📋, 📝)
- "Vor X Min" statt ISO-Timestamps

---

## 🚀 Verwendung:

### **Starten:**

```powershell
# Advanced Dashboard
python monitor_bot_advanced.py
```

### **Altes Dashboard (einfach):**

```powershell
# Falls Sie das alte wollen
python monitor_bot.py
```

---

## 📊 Beispiel-Ausgabe:

```
╔════════════════════════════════════════════════════════════════════════════════════════╗
║                  🚀 KRAKEN TRADING BOT - ADVANCED MONITOR 🚀                           ║
╚════════════════════════════════════════════════════════════════════════════════════════╝

  🕐 Letzte Aktualisierung: 19.10.2025 22:35:12
  💡 Mode: PAPER TRADING (Simuliert)

┌─ 💰 PORTFOLIO ÜBERSICHT ────────────────────────────────────────────────────────────────┐
│
│  Kapital:
│    Startkapital:               €20.00
│    Cash Balance:               €19.95
│    Gesamt Equity:              €20.15
│
│  Performance:
│    Gesamt P&L:                 €+0.15
│    ROI:                        +0.75%
│    Max Drawdown:               -0.12%
│    Sharpe Ratio:                0.85
│
└─────────────────────────────────────────────────────────────────────────────────────────┘

┌─ 📊 OFFENE POSITIONEN ──────────────────────────────────────────────────────────────────┐
│
│  SOL/USD
│    Menge:                   52.837877
│    Entry:                   €189.26  (vor 15 Min)
│    Aktuell:                 €189.45
│    Position Wert:           €10.01
│    Unrealized P&L:          €+0.20 (+2.00%)
│
│  Gesamt:
│    Positionen:                    1
│    Gesamt Wert:             €10.01
│    Unrealized P&L:          €+0.20
│
└─────────────────────────────────────────────────────────────────────────────────────────┘

┌─ 📈 TRADE STATISTIKEN ──────────────────────────────────────────────────────────────────┐
│
│  Übersicht:
│    Gesamt Trades:                  1
│      ├─ Offen:                     1
│      └─ Geschlossen:               0
│
│  Performance (geschlossene Trades):
│    Gewinn-Trades:                  0
│    Verlust-Trades:                 0
│    Win Rate:                   0.00%
│
│  P&L Statistiken:
│    Durchschnitt:               €0.00
│    Bester Trade:               €0.00
│    Schlechtester:              €0.00
│
└─────────────────────────────────────────────────────────────────────────────────────────┘

┌─ 📋 LETZTE TRADES (Top 10) ─────────────────────────────────────────────────────────────┐
│
│   1. 🟢 SOL/USD
│      BUY 52.837877 @ €189.26
│      Status: OPEN  │  vor 15 Min
│      19.10.2025 22:29:09
│
└─────────────────────────────────────────────────────────────────────────────────────────┘

┌─ 📝 LETZTE AKTIVITÄTEN ─────────────────────────────────────────────────────────────────┐
│
│  2025-10-19 22:34:52 - trading_bot.bot - INFO - Verarbeitung für BTC/USD...
│  2025-10-19 22:34:53 - trading_bot.indicators - INFO - 22 Indikatoren berechnet
│  2025-10-19 22:34:54 - trading_bot.bot - INFO - Verarbeitung abgeschlossen
│
└─────────────────────────────────────────────────────────────────────────────────────────┘

──────────────────────────────────────────────────────────────────────────────────────────
  💡 Tastenkombinationen:
     CTRL+C  → Monitor beenden
     Q       → Beenden (falls CTRL+C nicht funktioniert)
```

---

## ⚙️ Konfiguration:

### **Startkapital ändern:**

**Option 1: In `.env` Datei:**
```env
INITIAL_BALANCE=20.0
```

**Option 2: In `main.py`:**
```python
config = {
    'settings': {
        'initial_balance': 20.0,
        ...
    }
}
```

### **Update-Intervall:**

Im Dashboard-Code ändern:
```python
time.sleep(5)  # Aktualisiere alle 5 Sekunden
```

---

## 🔧 Fehlerbehebung:

### **Farben werden nicht angezeigt:**

Windows Terminal oder PowerShell 7+ verwenden:
```powershell
# PowerShell 7 installieren
winget install Microsoft.PowerShell
```

### **Dashboard flackert:**

Update-Intervall erhöhen:
```python
time.sleep(10)  # Statt 5 Sekunden
```

### **Keine Daten:**

1. Bot läuft?
   ```powershell
   python main.py
   ```

2. Datenbank existiert?
   ```powershell
   dir trading_bot.db
   ```

---

## 📚 Vergleich:

| Feature | Altes Dashboard | Advanced Dashboard |
|---------|----------------|-------------------|
| **Portfolio** | Basis | ✅ Detailliert + ROI |
| **Positionen** | Einfach | ✅ Detailliert + P&L |
| **Statistiken** | Basic | ✅ Erweitert |
| **Performance/Symbol** | ❌ | ✅ Ja |
| **Trade Historie** | Text | ✅ Formatiert + Farben |
| **Logs** | Text | ✅ Farbcodiert |
| **Zeitanzeige** | ISO | ✅ "vor X Min" |
| **Farben** | ❌ | ✅ Ja |
| **Symbole** | ❌ | ✅ Ja |

---

## 🎯 Zusammenfassung:

✅ **Startkapital auf 20€** eingestellt  
✅ **Ausführliches Dashboard** mit allen Details  
✅ **Farbcodierung** für bessere Übersicht  
✅ **Performance pro Symbol** Tracking  
✅ **Unrealisierter P&L** für offene Positionen  
✅ **"Vor X Min"** statt Timestamps  
✅ **Live Updates** alle 5 Sekunden  

**Viel Erfolg mit dem Trading Bot! 🚀📈**
