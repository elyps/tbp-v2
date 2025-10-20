# 📊 Trade Monitoring & Analyse

## Übersicht

Der Trading Bot bietet jetzt umfassende Trade-Monitoring und Analyse-Tools:

1. **Live Dashboard** - Echtzeit-Überwachung mit Trade-Historie
2. **Trade Viewer** - Detaillierte Analyse aller Trades
3. **CSV Export** - Exportieren für externe Analyse

---

## 🖥️ 1. Live Dashboard

**Starten:**
```bash
python monitor_bot.py
```

**Features:**
- ✅ Portfolio-Übersicht (Balance, Equity, Gewinn/Verlust)
- ✅ Offene Positionen mit aktuellem P&L
- ✅ Performance-Statistiken
- ✅ **NEU:** Letzte 10 Trades detailliert
  - Zeitstempel
  - Symbol & Seite (Buy/Sell)
  - Menge & Preis
  - P&L (bei Verkäufen)
  - Strategie
- ✅ Live-Logs der letzten Aktivitäten

**Dashboard aktualisiert sich alle 5 Sekunden automatisch!**

---

## 📋 2. Trade Viewer (Alle Trades anzeigen)

### Grundlegende Nutzung

**Alle Trades anzeigen:**
```bash
python view_trades.py
```

Zeigt:
- Zusammenfassung (Gesamt-Trades, P&L, Win Rate)
- Detaillierte Liste aller Trades (neueste zuerst)
- Vollständige Informationen pro Trade

### Filter-Optionen

**Nach Symbol filtern:**
```bash
python view_trades.py --symbol BTC/EUR
```

**Nach Seite filtern (nur Käufe oder Verkäufe):**
```bash
python view_trades.py --side buy
python view_trades.py --side sell
```

**Nach Strategie filtern:**
```bash
python view_trades.py --strategy trend_following
python view_trades.py --strategy mean_reversion
```

**Anzahl begrenzen:**
```bash
python view_trades.py --limit 20
```

**Kombinierte Filter:**
```bash
python view_trades.py --symbol ETH/EUR --side sell --limit 5
```

---

## 💾 3. CSV Export

**Alle Trades exportieren:**
```bash
python view_trades.py --export
```

Erstellt `trades_export.csv` mit allen Trade-Details.

**Custom Dateiname:**
```bash
python view_trades.py --export --output meine_trades.csv
```

**Gefilterte Trades exportieren:**
```bash
python view_trades.py --symbol BTC/EUR --side sell --export --output btc_verkaufe.csv
```

### CSV-Format

Die CSV-Datei enthält:
- Nummer
- Zeitstempel (ISO-Format)
- Seite (BUY/SELL)
- Symbol
- Menge
- Preis
- Kosten
- Gebühr
- P&L (für Verkäufe)
- Strategie
- Stop Loss
- Take Profit

**Öffnen mit:** Excel, Google Sheets, LibreOffice Calc

---

## 📈 Trade-Informationen

### Für jeden Trade wird gespeichert:

| Feld | Beschreibung |
|------|--------------|
| **ID** | Eindeutige Trade-ID |
| **Zeitstempel** | Exakte Ausführungszeit |
| **Symbol** | Gehandeltes Paar (z.B. BTC/EUR) |
| **Seite** | BUY oder SELL |
| **Menge** | Gehandelte Menge |
| **Preis** | Ausführungspreis |
| **Kosten** | Gesamtkosten (Preis × Menge) |
| **Gebühr** | Handelsgebühr |
| **P&L** | Gewinn/Verlust (nur bei Verkäufen) |
| **Strategie** | Verwendete Trading-Strategie |
| **Stop Loss** | Stop-Loss Level |
| **Take Profit** | Take-Profit Level |

### P&L Berechnung

Bei **Verkäufen** wird der Gewinn/Verlust automatisch berechnet:

```
P&L = (Verkaufspreis - Durchschnittlicher Kaufpreis) × Menge - Gebühren
```

**Beispiel:**
- Kauf: 0.1 BTC @ €90,000 (Kosten: €9,000 + €9 Gebühr)
- Verkauf: 0.1 BTC @ €95,000 (Erlös: €9,500 - €9.50 Gebühr)
- **P&L: +€481.50** ✅

---

## 🔄 Portfolio nach Fehlern zurücksetzen

Falls das Portfolio inkonsistent ist (alte Trades ohne P&L):

```bash
# Bot stoppen (Ctrl+C)

# Portfolio löschen
Remove-Item portfolio_state.json

# Bot neu starten
python main.py
```

Das Portfolio startet dann mit €10,000 neu und alle neuen Trades haben korrekte P&L-Berechnungen.

---

## 🎯 Beispiel-Workflow

### 1. Bot starten
```bash
python main.py
```

### 2. In neuem Terminal: Dashboard öffnen
```bash
python monitor_bot.py
```

### 3. Nach einiger Zeit: Trades analysieren
```bash
# Übersicht
python view_trades.py --limit 10

# Nur erfolgreiche Verkäufe
python view_trades.py --side sell

# BTC-Performance
python view_trades.py --symbol BTC/EUR

# Alles exportieren
python view_trades.py --export
```

---

## 📊 Dashboard-Beispiel

```
╔══════════════════════════════════════════════════════════════════════════════╗
║                    🚀 KRAKEN TRADING BOT MONITOR 🚀                         ║
╚══════════════════════════════════════════════════════════════════════════════╝

📅 Letzte Aktualisierung: 2025-10-19 10:25:15
🔄 Mode: PAPER TRADING (Simuliert)

┌─────────────────────────────────────────────────────────────────────────────┐
│ 💰 PORTFOLIO ÜBERSICHT                                                      │
├─────────────────────────────────────────────────────────────────────────────┤
│  Startkapital:               €10,000.00                                     │
│  Aktuelles Equity:           €10,481.50                                     │
│  Cash Balance:               €10,481.50                                     │
│  📈 Gewinn/Verlust:           +€481.50 ( +4.82%)                            │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│ 📋 TRADE HISTORIE (Letzte 10 Trades)                                       │
├─────────────────────────────────────────────────────────────────────────────┤
│  1. 🔴 SELL BTC/EUR      │ 19.10 10:23:45│ mean_reversion│
│     Menge: 0.100000 │ Preis:  95,000.00€ │ P&L: +490.50€        │
│─────────────────────────────────────────────────────────────────────────────│
│  2. 🟢 BUY  BTC/EUR      │ 19.10 10:20:30│ mean_reversion│
│     Menge: 0.100000 │ Preis:  90,000.00€ │ -                    │
└─────────────────────────────────────────────────────────────────────────────┘

📈 PERFORMANCE STATISTIKEN
  Gesamt Trades:          2
  Gewinn-Trades:          1
  Win Rate:          100.0%
```

---

## 💡 Tipps

1. **Dashboard im Hintergrund laufen lassen** für Live-Monitoring
2. **Trades regelmäßig exportieren** als Backup
3. **Filter nutzen** um spezifische Analysen durchzuführen
4. **CSV in Excel öffnen** für erweiterte Analyse und Diagramme

---

## 🆘 Hilfe

**Alle Optionen anzeigen:**
```bash
python view_trades.py --help
```

**Keine Trades sichtbar?**
- Stelle sicher, dass der Bot läuft (`python main.py`)
- Prüfe ob `portfolio_state.json` existiert
- Warte einige Minuten bis erste Signale generiert werden

**Dashboard zeigt alte Daten?**
- Dashboard aktualisiert automatisch alle 5 Sekunden
- Bot muss laufen für neue Updates
- Notfalls Bot und Dashboard neu starten
