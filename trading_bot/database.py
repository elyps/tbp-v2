"""
SQLite Database Manager für Trading Bot
Verwaltet alle persistenten Daten: Trades, Portfolio, Training Data, News, etc.
"""

import sqlite3
import json
import logging
import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
import pandas as pd

logger = logging.getLogger(__name__)


class DatabaseManager:
    """Zentrale SQLite Datenbank für alle Bot-Daten."""
    
    def __init__(self, db_path: str = "trading_bot.db"):
        """
        Initialisiert Database Manager.
        
        Args:
            db_path: Pfad zur SQLite Datenbank
        """
        self.db_path = db_path
        self.conn = None
        self._initialize_database()
    
    def _initialize_database(self):
        """Erstellt Datenbank und alle Tabellen."""
        self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row  # Dict-like rows
        
        logger.info(f"SQLite Datenbank initialisiert: {self.db_path}")
        
        # Erstelle alle Tabellen
        self._create_tables()
    
    def _create_tables(self):
        """Erstellt alle benötigten Tabellen."""
        cursor = self.conn.cursor()
        
        # =====================================================================
        # TRADES TABLE - Alle ausgeführten Trades
        # =====================================================================
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS trades (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                trade_id TEXT UNIQUE NOT NULL,
                symbol TEXT NOT NULL,
                action TEXT NOT NULL,
                amount REAL NOT NULL,
                price REAL NOT NULL,
                timestamp TEXT NOT NULL,
                status TEXT DEFAULT 'open',
                strategy TEXT,
                confidence REAL,
                reason TEXT,
                pnl REAL DEFAULT 0.0,
                pnl_percent REAL DEFAULT 0.0,
                exit_price REAL,
                exit_timestamp TEXT,
                stop_loss REAL,
                take_profit REAL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Index für schnelle Queries
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_trades_symbol ON trades(symbol)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_trades_status ON trades(status)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_trades_timestamp ON trades(timestamp)")
        
        # =====================================================================
        # PORTFOLIO TABLE - Aktueller Portfolio-Status
        # =====================================================================
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS portfolio (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                balance REAL NOT NULL,
                equity REAL NOT NULL,
                total_trades INTEGER DEFAULT 0,
                winning_trades INTEGER DEFAULT 0,
                losing_trades INTEGER DEFAULT 0,
                total_pnl REAL DEFAULT 0.0,
                max_drawdown REAL DEFAULT 0.0,
                sharpe_ratio REAL DEFAULT 0.0,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # =====================================================================
        # POSITIONS TABLE - Offene Positionen
        # =====================================================================
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS positions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                symbol TEXT UNIQUE NOT NULL,
                amount REAL NOT NULL,
                entry_price REAL NOT NULL,
                current_price REAL,
                pnl REAL DEFAULT 0.0,
                pnl_percent REAL DEFAULT 0.0,
                opened_at TEXT NOT NULL,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # =====================================================================
        # TRAINING_DATA TABLE - Features & Labels für Continuous Learning
        # =====================================================================
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS training_data (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                trade_id TEXT NOT NULL,
                symbol TEXT NOT NULL,
                features TEXT NOT NULL,
                label INTEGER,
                pnl REAL,
                timestamp TEXT NOT NULL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (trade_id) REFERENCES trades(trade_id)
            )
        """)
        
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_training_symbol ON training_data(symbol)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_training_timestamp ON training_data(timestamp)")
        
        # =====================================================================
        # MODEL_PERFORMANCE TABLE - ML Model Performance Tracking
        # =====================================================================
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS model_performance (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                model_version TEXT NOT NULL,
                accuracy REAL,
                precision_score REAL,
                recall REAL,
                f1_score REAL,
                samples_count INTEGER,
                training_duration REAL,
                timestamp TEXT NOT NULL,
                notes TEXT
            )
        """)
        
        # =====================================================================
        # NEWS TABLE - Gespeicherte News & Sentiment
        # =====================================================================
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS news (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                symbol TEXT NOT NULL,
                title TEXT NOT NULL,
                content TEXT,
                source TEXT,
                url TEXT,
                sentiment_score REAL,
                sentiment_label TEXT,
                published_at TEXT,
                fetched_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_news_symbol ON news(symbol)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_news_published ON news(published_at)")
        
        # =====================================================================
        # SIGNALS TABLE - Generierte Trading Signale
        # =====================================================================
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS signals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                symbol TEXT NOT NULL,
                action TEXT NOT NULL,
                confidence REAL NOT NULL,
                strategy TEXT,
                reason TEXT,
                price REAL,
                executed BOOLEAN DEFAULT 0,
                timestamp TEXT NOT NULL
            )
        """)
        
        # =====================================================================
        # BOT_LOGS TABLE - System Logs
        # =====================================================================
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS bot_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                level TEXT NOT NULL,
                message TEXT NOT NULL,
                module TEXT,
                timestamp TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        self.conn.commit()
        logger.info("Alle Datenbank-Tabellen erstellt")
    
    # =========================================================================
    # TRADES METHODS
    # =========================================================================
    
    def save_trade(self, trade: Dict) -> int:
        """Speichert einen Trade in der Datenbank."""
        cursor = self.conn.cursor()
        
        cursor.execute("""
            INSERT INTO trades (
                trade_id, symbol, action, amount, price, timestamp,
                status, strategy, confidence, reason, stop_loss, take_profit
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            trade.get('id', str(uuid.uuid4())),
            trade.get('symbol', ''),
            trade.get('action', trade.get('side', 'buy')),  # Fallback auf 'side' falls 'action' fehlt
            trade.get('amount', 0.0),
            trade.get('price', 0.0),
            trade.get('timestamp', datetime.utcnow().isoformat()),
            trade.get('status', 'open'),
            trade.get('strategy', ''),
            trade.get('confidence', 0.0),
            trade.get('reason', ''),
            trade.get('stop_loss'),
            trade.get('take_profit')
        ))
        
        self.conn.commit()
        logger.debug(f"Trade gespeichert: {trade.get('id', 'unknown')} (SL: {trade.get('stop_loss')}, TP: {trade.get('take_profit')})")
        return cursor.lastrowid
    
    def update_trade(self, trade_id: str, updates: Dict):
        """Aktualisiert einen Trade (z.B. Status, Exit-Preis, P&L)."""
        cursor = self.conn.cursor()
        
        set_clause = ", ".join([f"{key} = ?" for key in updates.keys()])
        values = list(updates.values()) + [trade_id]
        
        cursor.execute(f"""
            UPDATE trades SET {set_clause}
            WHERE trade_id = ?
        """, values)
        
        self.conn.commit()
        logger.debug(f"Trade aktualisiert: {trade_id}")
    
    def get_trade(self, trade_id: str) -> Optional[Dict]:
        """Holt einen spezifischen Trade."""
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM trades WHERE trade_id = ?", (trade_id,))
        row = cursor.fetchone()
        return dict(row) if row else None
    
    def get_trades(self, symbol: Optional[str] = None, status: Optional[str] = None,
                   limit: int = 100) -> List[Dict]:
        """Holt Trades mit optionalen Filtern."""
        cursor = self.conn.cursor()
        
        query = "SELECT * FROM trades WHERE 1=1"
        params = []
        
        if symbol:
            query += " AND symbol = ?"
            params.append(symbol)
        
        if status:
            query += " AND status = ?"
            params.append(status)
        
        query += " ORDER BY timestamp DESC LIMIT ?"
        params.append(limit)
        
        cursor.execute(query, params)
        return [dict(row) for row in cursor.fetchall()]
    
    def get_open_trades(self, symbol: Optional[str] = None) -> List[Dict]:
        """Holt alle offenen Trades."""
        return self.get_trades(symbol=symbol, status='open')
    
    def get_trade_statistics(self) -> Dict:
        """Berechnet Trade-Statistiken."""
        cursor = self.conn.cursor()
        
        cursor.execute("""
            SELECT 
                COUNT(*) as total_trades,
                SUM(CASE WHEN pnl > 0 THEN 1 ELSE 0 END) as winning_trades,
                SUM(CASE WHEN pnl < 0 THEN 1 ELSE 0 END) as losing_trades,
                SUM(pnl) as total_pnl,
                AVG(pnl) as avg_pnl,
                MAX(pnl) as max_profit,
                MIN(pnl) as max_loss
            FROM trades
            WHERE status = 'closed'
        """)
        
        row = cursor.fetchone()
        if row:
            stats = dict(row)
            # Handle None values (wenn keine Trades vorhanden)
            stats['total_trades'] = stats['total_trades'] or 0
            stats['winning_trades'] = stats['winning_trades'] or 0
            stats['losing_trades'] = stats['losing_trades'] or 0
            stats['total_pnl'] = stats['total_pnl'] or 0.0
            stats['avg_pnl'] = stats['avg_pnl'] or 0.0
            stats['max_profit'] = stats['max_profit'] or 0.0
            stats['max_loss'] = stats['max_loss'] or 0.0
            
            # Win-Rate berechnen
            if stats['total_trades'] > 0:
                stats['win_rate'] = (stats['winning_trades'] / stats['total_trades']) * 100
            else:
                stats['win_rate'] = 0.0
            
            return stats
        
        return {
            'total_trades': 0,
            'winning_trades': 0,
            'losing_trades': 0,
            'total_pnl': 0.0,
            'avg_pnl': 0.0,
            'max_profit': 0.0,
            'max_loss': 0.0,
            'win_rate': 0.0
        }
    
    # =========================================================================
    # PORTFOLIO METHODS
    # =========================================================================
    
    def save_portfolio(self, portfolio: Dict):
        """Speichert Portfolio-Status."""
        cursor = self.conn.cursor()
        
        # Lösche alten Eintrag und erstelle neuen
        cursor.execute("DELETE FROM portfolio")
        
        cursor.execute("""
            INSERT INTO portfolio (
                balance, equity, total_trades, winning_trades, losing_trades,
                total_pnl, max_drawdown, sharpe_ratio
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            portfolio['balance'],
            portfolio['equity'],
            portfolio.get('total_trades', 0),
            portfolio.get('winning_trades', 0),
            portfolio.get('losing_trades', 0),
            portfolio.get('total_pnl', 0.0),
            portfolio.get('max_drawdown', 0.0),
            portfolio.get('sharpe_ratio', 0.0)
        ))
        
        self.conn.commit()
        logger.debug("Portfolio gespeichert")
    
    def get_portfolio(self) -> Optional[Dict]:
        """Holt aktuelles Portfolio."""
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM portfolio ORDER BY id DESC LIMIT 1")
        row = cursor.fetchone()
        return dict(row) if row else None
    
    # =========================================================================
    # POSITIONS METHODS
    # =========================================================================
    
    def save_position(self, position: Dict):
        """Speichert oder aktualisiert Position."""
        cursor = self.conn.cursor()
        
        cursor.execute("""
            INSERT OR REPLACE INTO positions (
                symbol, amount, entry_price, current_price, pnl, pnl_percent, opened_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            position['symbol'],
            position['amount'],
            position['entry_price'],
            position.get('current_price', position['entry_price']),
            position.get('pnl', 0.0),
            position.get('pnl_percent', 0.0),
            position.get('opened_at', datetime.utcnow().isoformat())
        ))
        
        self.conn.commit()
    
    def get_position(self, symbol: str) -> Optional[Dict]:
        """Holt Position für Symbol."""
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM positions WHERE symbol = ?", (symbol,))
        row = cursor.fetchone()
        return dict(row) if row else None
    
    def get_all_positions(self) -> List[Dict]:
        """Holt alle offenen Positionen."""
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM positions")
        return [dict(row) for row in cursor.fetchall()]
    
    def delete_position(self, symbol: str):
        """Löscht Position."""
        cursor = self.conn.cursor()
        cursor.execute("DELETE FROM positions WHERE symbol = ?", (symbol,))
        self.conn.commit()
    
    # =========================================================================
    # TRAINING DATA METHODS
    # =========================================================================
    
    def save_training_sample(self, trade_id: str, symbol: str, features: Dict, 
                            label: Optional[int] = None, pnl: Optional[float] = None):
        """Speichert Training Sample für Continuous Learning."""
        cursor = self.conn.cursor()
        
        cursor.execute("""
            INSERT INTO training_data (trade_id, symbol, features, label, pnl, timestamp)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            trade_id,
            symbol,
            json.dumps(features),
            label,
            pnl,
            datetime.utcnow().isoformat()
        ))
        
        self.conn.commit()
        logger.debug(f"Training sample gespeichert: {trade_id}")
    
    def get_training_data(self, symbol: Optional[str] = None, limit: int = 1000) -> pd.DataFrame:
        """Holt Training Data als DataFrame."""
        cursor = self.conn.cursor()
        
        query = "SELECT * FROM training_data WHERE label IS NOT NULL"
        params = []
        
        if symbol:
            query += " AND symbol = ?"
            params.append(symbol)
        
        query += " ORDER BY timestamp DESC LIMIT ?"
        params.append(limit)
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        
        if not rows:
            return pd.DataFrame()
        
        # Konvertiere zu DataFrame
        data = []
        for row in rows:
            row_dict = dict(row)
            features = json.loads(row_dict['features'])
            features.update({
                'label': row_dict['label'],
                'pnl': row_dict['pnl'],
                'symbol': row_dict['symbol'],
                'timestamp': row_dict['timestamp']
            })
            data.append(features)
        
        return pd.DataFrame(data)
    
    def get_training_stats(self) -> Dict:
        """Holt Training Data Statistiken."""
        cursor = self.conn.cursor()
        
        cursor.execute("""
            SELECT 
                COUNT(*) as total_samples,
                SUM(CASE WHEN label = 2 THEN 1 ELSE 0 END) as buy_samples,
                SUM(CASE WHEN label = 1 THEN 1 ELSE 0 END) as hold_samples,
                SUM(CASE WHEN label = 0 THEN 1 ELSE 0 END) as sell_samples,
                COUNT(DISTINCT symbol) as symbols_count
            FROM training_data
            WHERE label IS NOT NULL
        """)
        
        row = cursor.fetchone()
        return dict(row) if row else {}
    
    # =========================================================================
    # MODEL PERFORMANCE METHODS
    # =========================================================================
    
    def save_model_performance(self, performance: Dict):
        """Speichert Model Performance Metrics."""
        cursor = self.conn.cursor()
        
        cursor.execute("""
            INSERT INTO model_performance (
                model_version, accuracy, precision_score, recall, f1_score,
                samples_count, training_duration, timestamp, notes
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            performance.get('version', 'unknown'),
            performance.get('accuracy', 0.0),
            performance.get('precision', 0.0),
            performance.get('recall', 0.0),
            performance.get('f1_score', 0.0),
            performance.get('samples_count', 0),
            performance.get('training_duration', 0.0),
            datetime.utcnow().isoformat(),
            performance.get('notes', '')
        ))
        
        self.conn.commit()
        logger.info(f"Model performance gespeichert: v{performance.get('version')}")
    
    def get_model_performance_history(self, limit: int = 50) -> List[Dict]:
        """Holt Model Performance Historie."""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT * FROM model_performance 
            ORDER BY timestamp DESC 
            LIMIT ?
        """, (limit,))
        return [dict(row) for row in cursor.fetchall()]
    
    # =========================================================================
    # NEWS METHODS
    # =========================================================================
    
    def save_news(self, news: Dict):
        """Speichert News-Artikel."""
        cursor = self.conn.cursor()
        
        cursor.execute("""
            INSERT INTO news (
                symbol, title, content, source, url,
                sentiment_score, sentiment_label, published_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            news['symbol'],
            news['title'],
            news.get('content', ''),
            news.get('source', ''),
            news.get('url', ''),
            news.get('sentiment_score', 0.0),
            news.get('sentiment_label', 'neutral'),
            news.get('published_at', datetime.utcnow().isoformat())
        ))
        
        self.conn.commit()
    
    def get_recent_news(self, symbol: str, limit: int = 50) -> List[Dict]:
        """Holt aktuelle News für Symbol."""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT * FROM news 
            WHERE symbol = ? 
            ORDER BY published_at DESC 
            LIMIT ?
        """, (symbol, limit))
        return [dict(row) for row in cursor.fetchall()]
    
    # =========================================================================
    # SIGNALS METHODS
    # =========================================================================
    
    def save_signal(self, signal: Dict):
        """Speichert Trading Signal."""
        cursor = self.conn.cursor()
        
        cursor.execute("""
            INSERT INTO signals (
                symbol, action, confidence, strategy, reason, price, timestamp
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            signal['symbol'],
            signal['action'],
            signal['confidence'],
            signal.get('strategy', ''),
            signal.get('reason', ''),
            signal.get('price', 0.0),
            datetime.utcnow().isoformat()
        ))
        
        self.conn.commit()
    
    def mark_signal_executed(self, signal_id: int):
        """Markiert Signal als ausgeführt."""
        cursor = self.conn.cursor()
        cursor.execute("UPDATE signals SET executed = 1 WHERE id = ?", (signal_id,))
        self.conn.commit()
    
    # =========================================================================
    # UTILITY METHODS
    # =========================================================================
    
    def log(self, level: str, message: str, module: str = None):
        """Speichert Log in Datenbank."""
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT INTO bot_logs (level, message, module)
            VALUES (?, ?, ?)
        """, (level, message, module))
        self.conn.commit()
    
    def cleanup_old_data(self, days: int = 90):
        """Löscht alte Daten (älter als X Tage)."""
        cursor = self.conn.cursor()
        cutoff_date = (datetime.utcnow() - timedelta(days=days)).isoformat()
        
        # Lösche alte Logs
        cursor.execute("DELETE FROM bot_logs WHERE timestamp < ?", (cutoff_date,))
        
        # Lösche alte News
        cursor.execute("DELETE FROM news WHERE fetched_at < ?", (cutoff_date,))
        
        # Lösche alte Signale
        cursor.execute("DELETE FROM signals WHERE timestamp < ? AND executed = 1", (cutoff_date,))
        
        self.conn.commit()
        logger.info(f"Alte Daten gelöscht (älter als {days} Tage)")
    
    def backup_database(self, backup_path: str):
        """Erstellt Datenbank-Backup."""
        import shutil
        shutil.copy2(self.db_path, backup_path)
        logger.info(f"Datenbank-Backup erstellt: {backup_path}")
    
    def close(self):
        """Schließt Datenbankverbindung."""
        if self.conn:
            self.conn.close()
            logger.info("Datenbankverbindung geschlossen")
    
    def __del__(self):
        """Destructor - schließt Verbindung."""
        self.close()


# Singleton Instance
_db_instance = None

def get_database(db_path: str = "trading_bot.db") -> DatabaseManager:
    """Holt Singleton Database Instance."""
    global _db_instance
    if _db_instance is None:
        _db_instance = DatabaseManager(db_path)
    return _db_instance
