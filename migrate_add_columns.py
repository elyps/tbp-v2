#!/usr/bin/env python
"""
Migration: Add stop_loss and take_profit columns to trades table.
"""
import sqlite3
import sys

def migrate_database(db_path='trading_bot.db'):
    """Adds missing columns to the trades table."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    print("Starting database migration...")
    print(f"Database: {db_path}")
    
    try:
        # Check if columns already exist
        cursor.execute("PRAGMA table_info(trades)")
        columns = [row[1] for row in cursor.fetchall()]
        
        needs_stop_loss = 'stop_loss' not in columns
        needs_take_profit = 'take_profit' not in columns
        
        if not needs_stop_loss and not needs_take_profit:
            print("✓ Columns already exist. No migration needed.")
            return True
        
        # Add missing columns
        if needs_stop_loss:
            print("  Adding column: stop_loss...")
            cursor.execute("ALTER TABLE trades ADD COLUMN stop_loss REAL")
            print("  ✓ stop_loss added")
        
        if needs_take_profit:
            print("  Adding column: take_profit...")
            cursor.execute("ALTER TABLE trades ADD COLUMN take_profit REAL")
            print("  ✓ take_profit added")
        
        conn.commit()
        print("\n✅ Migration completed successfully!")
        return True
        
    except Exception as e:
        print(f"\n❌ Migration failed: {e}")
        conn.rollback()
        return False
    
    finally:
        conn.close()

if __name__ == "__main__":
    success = migrate_database()
    sys.exit(0 if success else 1)
