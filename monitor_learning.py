"""
Monitor für das Continuous Learning System.
Zeigt Statistiken über gesammelte Daten und Modell-Verbesserungen.
"""

import json
import os
from datetime import datetime
from pathlib import Path
import pandas as pd

def print_header(title):
    """Druckt einen formatierten Header."""
    print("\n" + "="*60)
    print(f"  {title}")
    print("="*60)

def load_training_stats():
    """Lädt Trainings-Statistiken."""
    stats = {
        'total_samples': 0,
        'total_trades': 0,
        'successful_trades': 0,
        'failed_trades': 0,
        'oldest_sample': None,
        'newest_sample': None
    }
    
    # Features
    features_file = 'training_data/features_history.csv'
    if os.path.exists(features_file):
        df = pd.read_csv(features_file)
        stats['total_samples'] = len(df)
        if 'timestamp' in df.columns and len(df) > 0:
            stats['oldest_sample'] = df['timestamp'].iloc[0]
            stats['newest_sample'] = df['timestamp'].iloc[-1]
    
    # Trades
    trades_file = 'training_data/trades_history.json'
    if os.path.exists(trades_file):
        with open(trades_file, 'r') as f:
            trades = json.load(f)
            stats['total_trades'] = len(trades)
            
            for trade in trades:
                pnl = trade.get('outcome', {}).get('pnl', 0)
                if pnl > 0:
                    stats['successful_trades'] += 1
                else:
                    stats['failed_trades'] += 1
    
    return stats

def load_performance_history():
    """Lädt Performance-Historie."""
    perf_file = 'models/versions/performance_history.json'
    if os.path.exists(perf_file):
        with open(perf_file, 'r') as f:
            return json.load(f)
    return []

def calculate_improvement(history):
    """Berechnet Modell-Verbesserung."""
    if len(history) < 2:
        return None
    
    first = history[0]
    latest = history[-1]
    
    improvement = {
        'first_accuracy': first['accuracy'],
        'current_accuracy': latest['accuracy'],
        'absolute_improvement': latest['accuracy'] - first['accuracy'],
        'relative_improvement': ((latest['accuracy'] - first['accuracy']) / first['accuracy'] * 100),
        'total_retrains': len(history)
    }
    
    return improvement

def plot_performance(history):
    """Zeigt Performance-Entwicklung als ASCII-Graph."""
    if not history:
        print("Keine Performance-Daten verfügbar")
        return
    
    print("\n📈 Performance-Entwicklung:")
    print("-" * 60)
    
    # Extrahiere Accuracies
    accuracies = [h['accuracy'] for h in history]
    min_acc = min(accuracies)
    max_acc = max(accuracies)
    
    # Normalisiere für ASCII-Graph (0-50 Zeichen breit)
    width = 50
    
    for i, h in enumerate(history):
        acc = h['accuracy']
        date = datetime.fromisoformat(h['timestamp']).strftime('%Y-%m-%d')
        
        # Berechne Balken-Länge
        if max_acc > min_acc:
            bar_length = int(((acc - min_acc) / (max_acc - min_acc)) * width)
        else:
            bar_length = width
        
        bar = "█" * bar_length
        print(f"{i+1:2d}. {date}  {acc:.1%} {bar}")
    
    print("-" * 60)

def main():
    """Hauptfunktion."""
    print_header("🧠 CONTINUOUS LEARNING MONITOR")
    
    # 1. Trainingsdaten-Statistiken
    print_header("📊 Gesammelte Trainingsdaten")
    stats = load_training_stats()
    
    print(f"\n  Total Samples:        {stats['total_samples']:,}")
    print(f"  Total Trades:         {stats['total_trades']:,}")
    print(f"  Erfolgreiche Trades:  {stats['successful_trades']:,} ({stats['successful_trades']/(stats['total_trades'] or 1)*100:.1f}%)")
    print(f"  Fehlgeschlagene Trades: {stats['failed_trades']:,} ({stats['failed_trades']/(stats['total_trades'] or 1)*100:.1f}%)")
    
    if stats['oldest_sample']:
        print(f"\n  Älteste Daten:        {stats['oldest_sample']}")
        print(f"  Neueste Daten:        {stats['newest_sample']}")
    
    # 2. Performance-Historie
    print_header("📈 Modell-Performance")
    history = load_performance_history()
    
    if history:
        # Zeige letzte Performance
        latest = history[-1]
        print(f"\n  Aktuelle Genauigkeit:  {latest['accuracy']:.2%}")
        print(f"  Sample Count:          {latest['sample_count']:,}")
        print(f"  Letztes Training:      {datetime.fromisoformat(latest['timestamp']).strftime('%Y-%m-%d %H:%M')}")
        
        # Verbesserung berechnen
        improvement = calculate_improvement(history)
        if improvement:
            print(f"\n  Total Retrainings:     {improvement['total_retrains']}")
            print(f"  Erste Genauigkeit:     {improvement['first_accuracy']:.2%}")
            print(f"  Verbesserung:          {improvement['absolute_improvement']:+.2%} ({improvement['relative_improvement']:+.1f}%)")
            
            if improvement['absolute_improvement'] > 0:
                print(f"\n  ✓ Modell hat sich verbessert! 🎉")
            elif improvement['absolute_improvement'] < 0:
                print(f"\n  ⚠ Modell-Performance gesunken")
            else:
                print(f"\n  → Performance stabil")
        
        # ASCII-Graph
        plot_performance(history)
    else:
        print("\n  Noch keine Performance-Daten verfügbar.")
        print("  Das Modell wurde noch nie retrained.")
    
    # 3. Modell-Backups
    print_header("💾 Modell-Backups")
    backups_dir = Path('models/versions')
    
    if backups_dir.exists():
        backups = [d for d in backups_dir.iterdir() if d.is_dir() and d.name.startswith('backup_')]
        
        if backups:
            print(f"\n  Verfügbare Backups: {len(backups)}")
            print("\n  Letzte 5 Backups:")
            for backup in sorted(backups, reverse=True)[:5]:
                # Parse Timestamp aus Verzeichnisname
                try:
                    ts_str = backup.name.replace('backup_', '')
                    ts = datetime.strptime(ts_str, '%Y%m%d_%H%M%S')
                    print(f"    - {ts.strftime('%Y-%m-%d %H:%M:%S')} ({backup.name})")
                except:
                    print(f"    - {backup.name}")
        else:
            print("\n  Keine Backups gefunden.")
    else:
        print("\n  Backup-Verzeichnis existiert nicht.")
    
    # 4. Empfehlungen
    print_header("💡 Empfehlungen")
    
    if stats['total_samples'] < 100:
        print("\n  ⚠ Noch nicht genug Trainingsdaten (< 100 Samples)")
        print(f"    Sammle noch {100 - stats['total_samples']} Samples für das erste Retraining")
    elif stats['total_samples'] < 500:
        print("\n  ✓ Grundlegende Datenbasis vorhanden")
        print("    Empfehlung: Weiter Daten sammeln für bessere Genauigkeit")
    else:
        print("\n  ✓ Gute Datenbasis für zuverlässiges Training")
    
    if history:
        if improvement and improvement['total_retrains'] < 3:
            print("\n  → Noch in früher Lernphase")
            print("    Das Modell wird sich mit mehr Retrainings weiter verbessern")
        elif improvement and improvement['absolute_improvement'] > 0.05:
            print("\n  ✓ Starke Verbesserung festgestellt!")
            print("    Das Continuous Learning System funktioniert gut")
    
    # Win-Rate
    if stats['total_trades'] > 0:
        win_rate = stats['successful_trades'] / stats['total_trades']
        print(f"\n  Win-Rate: {win_rate:.1%}")
        
        if win_rate > 0.6:
            print("    ✓ Sehr gute Win-Rate!")
        elif win_rate > 0.5:
            print("    ✓ Positive Win-Rate")
        else:
            print("    ⚠ Win-Rate könnte besser sein")
            print("      Überprüfen Sie Ihre Strategien")
    
    print("\n" + "="*60 + "\n")

if __name__ == "__main__":
    main()
