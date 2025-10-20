#!/usr/bin/env python
"""
Reset Database - Löscht alle Trades und Positionen für einen Neustart.
WARNUNG: Dieser Befehl löscht alle Trading-Daten!
"""
import sqlite3
import sys

def reset_database(db_path='trading_bot.db'):
    """Setzt die Datenbank zurück."""
    
    print("\n" + "="*70)
    print("⚠️  WARNUNG: Diese Aktion löscht ALLE Trading-Daten!")
    print("="*70)
    
    response = input("\nMöchtest du fortfahren? (ja/nein): ")
    if response.lower() not in ['ja', 'j', 'yes', 'y']:
        print("❌ Abgebrochen.")
        return False
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        print("\n🔄 Lösche Daten...")
        
        # Lösche alle Trades
        cursor.execute("DELETE FROM trades")
        trades_deleted = cursor.rowcount
        print(f"  ✓ {trades_deleted} Trades gelöscht")
        
        # Lösche alle Positionen
        cursor.execute("DELETE FROM positions")
        positions_deleted = cursor.rowcount
        print(f"  ✓ {positions_deleted} Positionen gelöscht")
        
        # Setze Portfolio zurück
        cursor.execute("DELETE FROM portfolio")
        cursor.execute("""
            INSERT INTO portfolio (balance, equity, total_trades, winning_trades, losing_trades, total_pnl, max_drawdown, sharpe_ratio)
            VALUES (1000.0, 1000.0, 0, 0, 0, 0.0, 0.0, 0.0)
        """)
        print(f"  ✓ Portfolio zurückgesetzt (Balance: €1000)")
        
        # Lösche Training Data (optional)
        response = input("\nTraining-Daten auch löschen? (ja/nein): ")
        if response.lower() in ['ja', 'j', 'yes', 'y']:
            cursor.execute("DELETE FROM training_data")
            training_deleted = cursor.rowcount
            print(f"  ✓ {training_deleted} Training-Samples gelöscht")
        
        conn.commit()
        conn.close()
        
        print("\n✅ Datenbank erfolgreich zurückgesetzt!")
        print("\n💡 Du kannst den Bot jetzt neu starten mit: python main.py")
        print()
        return True
        
    except Exception as e:
        print(f"\n❌ Fehler beim Zurücksetzen: {e}")
        return False

if __name__ == "__main__":
    success = reset_database()
    sys.exit(0 if success else 1)
