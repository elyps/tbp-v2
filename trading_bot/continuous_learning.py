"""
Kontinuierliches Lernsystem für die Trading-Bot-KI.
Sammelt automatisch Daten und trainiert das Modell kontinuierlich nach.
"""

import os
import json
import logging
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import joblib
from pathlib import Path

logger = logging.getLogger(__name__)


class TrainingDataCollector:
    """
    Sammelt automatisch Trainingsdaten aus ausgeführten Trades und Marktdaten.
    """
    
    def __init__(self, data_dir: str = 'training_data'):
        """
        Initialisiert den Datensammler.
        
        Args:
            data_dir: Verzeichnis zum Speichern der Trainingsdaten
        """
        self.data_dir = data_dir
        os.makedirs(data_dir, exist_ok=True)
        
        self.trades_file = os.path.join(data_dir, 'trades_history.json')
        self.features_file = os.path.join(data_dir, 'features_history.csv')
        self.labels_file = os.path.join(data_dir, 'labels_history.csv')
        
        logger.info(f"TrainingDataCollector initialisiert: {data_dir}")
    
    def collect_trade_outcome(self, trade: Dict, features: pd.DataFrame, outcome: Dict):
        """
        Sammelt Daten von einem abgeschlossenen Trade.
        
        Args:
            trade: Trade-Informationen (Entry)
            features: Features zum Zeitpunkt des Trade-Einstiegs
            outcome: Trade-Ergebnis (P&L, Exit-Zeitpunkt, etc.)
        """
        try:
            # Trade-Historie speichern
            self._save_trade_history(trade, outcome)
            
            # Label erstellen basierend auf Trade-Erfolg
            label = self._create_label(outcome)
            
            # Features und Label speichern
            self._save_training_sample(features, label, trade['timestamp'])
            
            logger.info(f"Trade-Outcome gesammelt: P&L={outcome.get('pnl', 0):.2f}, Label={label}")
            
        except Exception as e:
            logger.error(f"Fehler beim Sammeln von Trade-Outcome: {e}")
    
    def _create_label(self, outcome: Dict) -> int:
        """
        Erstellt ein Label basierend auf dem Trade-Ergebnis.
        
        Returns:
            -1 (Verkauf), 0 (Halten), 1 (Kauf)
        """
        pnl = outcome.get('pnl', 0)
        pnl_percent = outcome.get('pnl_percent', 0)
        
        # Erfolgsschwelle: >0.5% Gewinn = gut (Kauf), <-0.3% = schlecht (Verkauf)
        if pnl_percent > 0.5:
            return 2  # Kauf war richtig (XGBoost Klasse 2)
        elif pnl_percent < -0.3:
            return 0  # Verkauf wäre besser gewesen (XGBoost Klasse 0)
        else:
            return 1  # Halten (XGBoost Klasse 1)
    
    def _save_trade_history(self, trade: Dict, outcome: Dict):
        """Speichert die Trade-Historie."""
        history_entry = {
            **trade,
            'outcome': outcome,
            'saved_at': datetime.utcnow().isoformat()
        }
        
        # Lade bestehende Historie
        if os.path.exists(self.trades_file):
            with open(self.trades_file, 'r') as f:
                history = json.load(f)
        else:
            history = []
        
        history.append(history_entry)
        
        # Speichere aktualisierte Historie
        with open(self.trades_file, 'w') as f:
            json.dump(history, f, indent=2)
    
    def _save_training_sample(self, features: pd.DataFrame, label: int, timestamp: str):
        """Speichert ein Training-Sample (Features + Label)."""
        # Features speichern
        features_with_timestamp = features.copy()
        features_with_timestamp['timestamp'] = timestamp
        
        if os.path.exists(self.features_file):
            existing_features = pd.read_csv(self.features_file)
            features_combined = pd.concat([existing_features, features_with_timestamp], ignore_index=True)
        else:
            features_combined = features_with_timestamp
        
        features_combined.to_csv(self.features_file, index=False)
        
        # Labels speichern
        label_df = pd.DataFrame({'label': [label], 'timestamp': [timestamp]})
        
        if os.path.exists(self.labels_file):
            existing_labels = pd.read_csv(self.labels_file)
            labels_combined = pd.concat([existing_labels, label_df], ignore_index=True)
        else:
            labels_combined = label_df
        
        labels_combined.to_csv(self.labels_file, index=False)
    
    def get_training_data(self, min_samples: int = 50) -> Optional[Tuple[pd.DataFrame, pd.Series]]:
        """
        Lädt gesammelte Trainingsdaten.
        
        Args:
            min_samples: Minimale Anzahl von Samples zum Laden
            
        Returns:
            Tuple von (Features, Labels) oder None
        """
        try:
            if not os.path.exists(self.features_file) or not os.path.exists(self.labels_file):
                logger.warning("Keine Trainingsdaten verfügbar")
                return None
            
            features = pd.read_csv(self.features_file)
            labels = pd.read_csv(self.labels_file)
            
            # Entferne timestamp Spalte aus Features
            if 'timestamp' in features.columns:
                features = features.drop('timestamp', axis=1)
            
            if len(features) < min_samples:
                logger.warning(f"Nicht genug Trainingsdaten: {len(features)} < {min_samples}")
                return None
            
            logger.info(f"Trainingsdaten geladen: {len(features)} Samples")
            return features, labels['label']
            
        except Exception as e:
            logger.error(f"Fehler beim Laden der Trainingsdaten: {e}")
            return None
    
    def get_statistics(self) -> Dict:
        """Gibt Statistiken über gesammelte Daten zurück."""
        stats = {
            'total_samples': 0,
            'total_trades': 0,
            'successful_trades': 0,
            'failed_trades': 0,
            'oldest_sample': None,
            'newest_sample': None
        }
        
        try:
            if os.path.exists(self.features_file):
                features = pd.read_csv(self.features_file)
                stats['total_samples'] = len(features)
                if 'timestamp' in features.columns and len(features) > 0:
                    stats['oldest_sample'] = features['timestamp'].iloc[0]
                    stats['newest_sample'] = features['timestamp'].iloc[-1]
            
            if os.path.exists(self.trades_file):
                with open(self.trades_file, 'r') as f:
                    trades = json.load(f)
                    stats['total_trades'] = len(trades)
                    
                    for trade in trades:
                        pnl = trade.get('outcome', {}).get('pnl', 0)
                        if pnl > 0:
                            stats['successful_trades'] += 1
                        else:
                            stats['failed_trades'] += 1
        
        except Exception as e:
            logger.error(f"Fehler beim Abrufen der Statistiken: {e}")
        
        return stats


class ContinuousLearner:
    """
    Verwaltet das kontinuierliche Lernen des Modells.
    """
    
    def __init__(self, ml_model, data_collector: TrainingDataCollector, config: Dict):
        """
        Initialisiert den Continuous Learner.
        
        Args:
            ml_model: MLModel-Instanz
            data_collector: TrainingDataCollector-Instanz
            config: Konfiguration für kontinuierliches Lernen
        """
        self.ml_model = ml_model
        self.data_collector = data_collector
        self.config = config
        
        self.min_samples_for_retrain = config.get('min_samples_for_retrain', 100)
        self.retrain_frequency = config.get('retrain_frequency_hours', 24)
        self.last_retrain_time = datetime.utcnow()
        
        self.model_versions_dir = config.get('model_versions_dir', 'models/versions')
        os.makedirs(self.model_versions_dir, exist_ok=True)
        
        self.performance_file = os.path.join(self.model_versions_dir, 'performance_history.json')
        
        logger.info(f"ContinuousLearner initialisiert - Retrain alle {self.retrain_frequency}h mit min. {self.min_samples_for_retrain} Samples")
    
    def should_retrain(self) -> bool:
        """
        Prüft, ob das Modell neu trainiert werden sollte.
        
        Returns:
            True wenn Retraining empfohlen wird
        """
        # Zeitbasierte Prüfung
        time_since_last_retrain = datetime.utcnow() - self.last_retrain_time
        hours_since_retrain = time_since_last_retrain.total_seconds() / 3600
        
        if hours_since_retrain < self.retrain_frequency:
            return False
        
        # Datenbasierte Prüfung
        stats = self.data_collector.get_statistics()
        if stats['total_samples'] < self.min_samples_for_retrain:
            logger.info(f"Nicht genug Samples für Retrain: {stats['total_samples']} < {self.min_samples_for_retrain}")
            return False
        
        logger.info(f"Retrain empfohlen: {hours_since_retrain:.1f}h vergangen, {stats['total_samples']} Samples verfügbar")
        return True
    
    def retrain_model(self) -> bool:
        """
        Trainiert das Modell mit allen gesammelten Daten neu.
        
        Returns:
            True wenn erfolgreich
        """
        try:
            logger.info("Starte Model-Retraining...")
            
            # Lade Trainingsdaten
            training_data = self.data_collector.get_training_data(
                min_samples=self.min_samples_for_retrain
            )
            
            if training_data is None:
                logger.warning("Kein Retraining möglich - nicht genug Daten")
                return False
            
            X, y = training_data
            
            # Sichere aktuelles Modell als Backup
            self._backup_current_model()
            
            # Trainiere neues Modell
            logger.info(f"Trainiere Modell mit {len(X)} Samples...")
            self.ml_model.train(X, y)
            
            # Validiere neues Modell
            accuracy = self.ml_model.model.score(
                self.ml_model.scaler.transform(X), y
            )
            
            # Speichere Performance
            self._save_performance_metric(accuracy, len(X))
            
            # Update Retrain-Zeitstempel
            self.last_retrain_time = datetime.utcnow()
            
            logger.info(f"✓ Retraining erfolgreich - Genauigkeit: {accuracy:.2%}")
            return True
            
        except Exception as e:
            logger.error(f"Fehler beim Retraining: {e}", exc_info=True)
            return False
    
    def _backup_current_model(self):
        """Erstellt ein Backup des aktuellen Modells."""
        try:
            timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
            backup_dir = os.path.join(self.model_versions_dir, f'backup_{timestamp}')
            os.makedirs(backup_dir, exist_ok=True)
            
            # Kopiere aktuelle Modelle
            import shutil
            model_path = self.ml_model.model_path
            
            if os.path.exists(os.path.join(model_path, 'trading_model.pkl')):
                shutil.copy2(
                    os.path.join(model_path, 'trading_model.pkl'),
                    os.path.join(backup_dir, 'trading_model.pkl')
                )
            
            if os.path.exists(os.path.join(model_path, 'scaler.pkl')):
                shutil.copy2(
                    os.path.join(model_path, 'scaler.pkl'),
                    os.path.join(backup_dir, 'scaler.pkl')
                )
            
            logger.info(f"Modell-Backup erstellt: {backup_dir}")
            
        except Exception as e:
            logger.warning(f"Fehler beim Erstellen des Backups: {e}")
    
    def _save_performance_metric(self, accuracy: float, sample_count: int):
        """Speichert Performance-Metriken."""
        try:
            metric = {
                'timestamp': datetime.utcnow().isoformat(),
                'accuracy': accuracy,
                'sample_count': sample_count
            }
            
            # Lade bestehende Metriken
            if os.path.exists(self.performance_file):
                with open(self.performance_file, 'r') as f:
                    history = json.load(f)
            else:
                history = []
            
            history.append(metric)
            
            # Speichere aktualisierte Metriken
            with open(self.performance_file, 'w') as f:
                json.dump(history, f, indent=2)
            
            logger.info(f"Performance-Metrik gespeichert: {accuracy:.2%}")
            
        except Exception as e:
            logger.error(f"Fehler beim Speichern der Performance-Metrik: {e}")
    
    def get_performance_history(self) -> List[Dict]:
        """Gibt die Performance-Historie zurück."""
        try:
            if os.path.exists(self.performance_file):
                with open(self.performance_file, 'r') as f:
                    return json.load(f)
        except Exception as e:
            logger.error(f"Fehler beim Laden der Performance-Historie: {e}")
        
        return []
    
    def get_improvement_stats(self) -> Dict:
        """Berechnet Verbesserungsstatistiken."""
        history = self.get_performance_history()
        
        if len(history) < 2:
            return {
                'total_retrains': len(history),
                'improvement': None,
                'current_accuracy': history[-1]['accuracy'] if history else None
            }
        
        first_accuracy = history[0]['accuracy']
        current_accuracy = history[-1]['accuracy']
        improvement = current_accuracy - first_accuracy
        
        return {
            'total_retrains': len(history),
            'first_accuracy': first_accuracy,
            'current_accuracy': current_accuracy,
            'improvement': improvement,
            'improvement_percent': (improvement / first_accuracy * 100) if first_accuracy > 0 else 0
        }
