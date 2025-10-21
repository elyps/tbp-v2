"""
KI-Modell für Marktprognosen und Handelsentscheidungen.
Implementiert Machine Learning Modelle für den Trading-Bot.
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple
import logging
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.preprocessing import StandardScaler
import joblib
import os

# XGBoost und LightGBM Importe
try:
    import xgboost as xgb
    XGBOOST_AVAILABLE = True
except ImportError:
    XGBOOST_AVAILABLE = False
    
try:
    import lightgbm as lgb
    LIGHTGBM_AVAILABLE = True
except ImportError:
    LIGHTGBM_AVAILABLE = False

logger = logging.getLogger(__name__)

class MLModel:
    """
    Klasse für Machine Learning Modelle zur Vorhersage von Marktbewegungen.
    """
    
    def __init__(self, settings: Dict):
        """
        Initialisiert das ML-Modell.
        
        Args:
            settings: Dictionary mit ML-Einstellungen
        """
        self.settings = settings
        self.model = None
        self.scaler = StandardScaler()
        self.is_trained = False
        self.model_path = settings.get('model_path', 'models/')
        
        # Erstelle Modell-Verzeichnis
        os.makedirs(self.model_path, exist_ok=True)
        
        # Lade gespeichertes Modell falls vorhanden
        self._load_model()
        
        logger.info("MLModel erfolgreich initialisiert")
    
    def _load_model(self):
        """Lädt ein gespeichertes Modell, falls vorhanden."""
        model_file = os.path.join(self.model_path, 'trading_model.pkl')
        scaler_file = os.path.join(self.model_path, 'scaler.pkl')
        
        try:
            if os.path.exists(model_file) and os.path.exists(scaler_file):
                self.model = joblib.load(model_file)
                self.scaler = joblib.load(scaler_file)
                self.is_trained = True
                logger.info("Gespeichertes Modell erfolgreich geladen")
        except Exception as e:
            logger.warning(f"Fehler beim Laden des Modells: {str(e)}")
    
    def train(self, X: pd.DataFrame, y: pd.Series):
        """
        Trainiert das ML-Modell mit den gegebenen Daten.
        
        Args:
            X: Feature-DataFrame
            y: Target-Series (1 für Kauf, -1 für Verkauf, 0 für Halten)
        """
        try:
            logger.info(f"Starte Training mit {len(X)} Samples...")
            
            # Daten skalieren
            X_scaled = self.scaler.fit_transform(X)
            
            # Modell initialisieren basierend auf Typ
            model_type = self.settings.get('model_type', 'xgboost')
            
            if model_type == 'xgboost' and XGBOOST_AVAILABLE:
                self.model = xgb.XGBClassifier(
                    n_estimators=self.settings.get('n_estimators', 200),
                    max_depth=self.settings.get('max_depth', 7),
                    learning_rate=self.settings.get('learning_rate', 0.05),
                    subsample=self.settings.get('subsample', 0.8),
                    colsample_bytree=self.settings.get('colsample_bytree', 0.8),
                    random_state=42,
                    n_jobs=-1,
                    use_label_encoder=False,
                    eval_metric='logloss'
                )
                logger.info("XGBoost Modell initialisiert")
            elif model_type == 'lightgbm' and LIGHTGBM_AVAILABLE:
                self.model = lgb.LGBMClassifier(
                    n_estimators=self.settings.get('n_estimators', 200),
                    max_depth=self.settings.get('max_depth', 7),
                    learning_rate=self.settings.get('learning_rate', 0.05),
                    subsample=self.settings.get('subsample', 0.8),
                    colsample_bytree=self.settings.get('colsample_bytree', 0.8),
                    random_state=42,
                    n_jobs=-1,
                    verbose=-1
                )
                logger.info("LightGBM Modell initialisiert")
            elif model_type == 'random_forest':
                self.model = RandomForestClassifier(
                    n_estimators=self.settings.get('n_estimators', 100),
                    max_depth=self.settings.get('max_depth', 10),
                    random_state=42,
                    n_jobs=-1
                )
                logger.info("Random Forest Modell initialisiert")
            elif model_type == 'gradient_boosting':
                self.model = GradientBoostingClassifier(
                    n_estimators=self.settings.get('n_estimators', 100),
                    max_depth=self.settings.get('max_depth', 5),
                    learning_rate=self.settings.get('learning_rate', 0.1),
                    random_state=42
                )
                logger.info("Gradient Boosting Modell initialisiert")
            else:
                if model_type == 'xgboost' and not XGBOOST_AVAILABLE:
                    logger.warning("XGBoost nicht verfügbar. Verwende Random Forest als Fallback.")
                    model_type = 'random_forest'
                elif model_type == 'lightgbm' and not LIGHTGBM_AVAILABLE:
                    logger.warning("LightGBM nicht verfügbar. Verwende Random Forest als Fallback.")
                    model_type = 'random_forest'
                
                if model_type == 'random_forest':
                    self.model = RandomForestClassifier(
                        n_estimators=self.settings.get('n_estimators', 100),
                        max_depth=self.settings.get('max_depth', 10),
                        random_state=42,
                        n_jobs=-1
                    )
                else:
                    raise ValueError(f"Unbekannter Modelltyp: {model_type}")
            
            # Trainieren
            self.model.fit(X_scaled, y)
            self.is_trained = True
            
            # Modell speichern
            self._save_model()
            
            # Genauigkeit berechnen
            accuracy = self.model.score(X_scaled, y)
            logger.info(f"Training abgeschlossen. Genauigkeit: {accuracy:.2%}")
            
        except Exception as e:
            logger.error(f"Fehler beim Training: {str(e)}", exc_info=True)
    
    def _save_model(self):
        """Speichert das trainierte Modell."""
        try:
            model_file = os.path.join(self.model_path, 'trading_model.pkl')
            scaler_file = os.path.join(self.model_path, 'scaler.pkl')
            
            joblib.dump(self.model, model_file)
            joblib.dump(self.scaler, scaler_file)
            
            logger.info("Modell erfolgreich gespeichert")
        except Exception as e:
            logger.error(f"Fehler beim Speichern des Modells: {str(e)}")
    
    def predict(self, df: pd.DataFrame) -> Dict:
        """
        Macht Vorhersagen basierend auf den gegebenen Features.
        
        Args:
            df: DataFrame mit Marktdaten und berechneten Indikatoren
            
        Returns:
            Dictionary mit Vorhersagen und Wahrscheinlichkeiten
        """
        if not self.is_trained:
            logger.warning("Modell ist noch nicht trainiert. Gebe Standardwerte zurück.")
            return {
                'signal': 0,
                'confidence': 0.0,
                'probability_buy': 0.33,
                'probability_sell': 0.33,
                'probability_hold': 0.34
            }
        
        try:
            # Features vorbereiten
            features = self._prepare_features(df)
            
            if features is None or features.empty:
                return {
                    'signal': 0,
                    'confidence': 0.0,
                    'probability_buy': 0.33,
                    'probability_sell': 0.33,
                    'probability_hold': 0.34
                }
            
            # Skalieren
            X_scaled = self.scaler.transform(features)
            
            # Vorhersage
            prediction = self.model.predict(X_scaled)[0]
            probabilities = self.model.predict_proba(X_scaled)[0]
            
            # Label-Mapping zurück: 0,1,2 -> -1,1,0
            # 0 (XGBoost-Label) -> -1 (Verkaufssignal)
            # 1 (XGBoost-Label) ->  0 (Haltensignal)
            # 2 (XGBoost-Label) ->  1 (Kaufsignal)
            signal_map = {0: -1, 1: 0, 2: 1}
            signal_mapped = signal_map.get(int(prediction), 0)
            
            if int(prediction) not in signal_map:
                logger.warning(f"Unerwartetes Prediction-Label '{prediction}' erhalten. Wird als 'Halten' behandelt.")
            
            # Ergebnis formatieren
            result = {
                'signal': signal_mapped,
                'confidence': float(max(probabilities)),
                'probabilities': probabilities.tolist()
            }
            
            # Wahrscheinlichkeiten nach Klassen (XGBoost gibt [0, 1, 2] zurück)
            classes = self.model.classes_
            for i, cls in enumerate(classes):
                if cls == 2:  # XGBoost Klasse 2 = Kauf (1)
                    result['probability_buy'] = float(probabilities[i])
                elif cls == 0:  # XGBoost Klasse 0 = Verkauf (-1)
                    result['probability_sell'] = float(probabilities[i])
                else:  # XGBoost Klasse 1 = Halten (0)
                    result['probability_hold'] = float(probabilities[i])
            
            logger.debug(f"Vorhersage: {result}")
            return result
            
        except Exception as e:
            logger.error(f"Fehler bei der Vorhersage: {str(e)}", exc_info=True)
            return {
                'signal': 0,
                'confidence': 0.0,
                'probability_buy': 0.33,
                'probability_sell': 0.33,
                'probability_hold': 0.34
            }
            
    def _get_feature_names(self) -> List[str]:
        """Gibt eine Liste aller Feature-Namen zurück, die vom Modell verwendet werden."""
        return [
            # Basis-Indikatoren
            'sma_20', 'sma_50', 'ema_9', 'ema_21', 'rsi_14', 'macd_line', 
            'macd_signal', 'macd_hist', 'momentum', 'stoch_k', 'stoch_d', 
            'bb_upper', 'bb_middle', 'bb_lower', 'atr', 'adx', 'plus_di', 'minus_di', 
            'volume', 'obv', 'cmf', 'vortex_pos', 'vortex_neg',
            # Abgeleitete Features
            'price_sma20_ratio', 'price_distance_sma20', 'price_sma50_ratio',
            'bb_position', 'bb_width', 'sma20_sma50_ratio', 'trend_alignment',
            'rsi_normalized', 'rsi_oversold', 'rsi_overbought', 'volume_ratio',
            'volume_trend', 'obv_trend', 'trend_strong', 'trend_weak',
            'stoch_signal', 'macd_positive', 'macd_momentum', 'vortex_diff',
            # Lag Features (NEU)
            'rsi_lag_1', 'rsi_lag_3', 'rsi_lag_5',
            'macd_hist_lag_1', 'macd_hist_lag_3',
            'adx_lag_3', 'volume_ratio_lag_3',
            # On-Chain & Futures Features (NEU)
            'active_addresses', 'transaction_count', 'transaction_volume',
            'exchange_inflow', 'exchange_outflow', 'exchange_netflow',
            'whale_inflow', 'whale_outflow',
            'futures_open_interest', 'futures_funding_rate', 'futures_long_liquidations',
            'futures_short_liquidations', 'nvt_signal', 'sopr', 'mvrv_z_score'
        ]

    def _create_features_from_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Erstellt alle abgeleiteten Features aus dem Indikatoren-DataFrame.
        Diese Methode ist für die Batch-Verarbeitung (Training) optimiert.
        """
        features_df = df.copy()
        
        # Preis-Ratios
        features_df['price_sma20_ratio'] = features_df['close'] / features_df['sma_20']
        features_df['price_distance_sma20'] = (features_df['close'] - features_df['sma_20']) / features_df['sma_20']
        features_df['price_sma50_ratio'] = features_df['close'] / features_df['sma_50']
        
        # Bollinger Band Position & Width
        bb_range = features_df['bb_upper'] - features_df['bb_lower']
        features_df['bb_position'] = (features_df['close'] - features_df['bb_lower']) / bb_range
        features_df['bb_width'] = bb_range / features_df['bb_middle']
        
        # Trend-Features
        features_df['sma20_sma50_ratio'] = features_df['sma_20'] / features_df['sma_50']
        features_df['trend_alignment'] = np.where(features_df['sma_20'] > features_df['sma_50'], 1, -1)
        
        # Momentum-Features
        features_df['rsi_normalized'] = (features_df['rsi_14'] - 50) / 50
        features_df['rsi_oversold'] = np.where(features_df['rsi_14'] < 30, 1, 0)
        features_df['rsi_overbought'] = np.where(features_df['rsi_14'] > 70, 1, 0)
        
        # Volumen-Features
        avg_vol = features_df['volume'].rolling(window=20).mean()
        features_df['volume_ratio'] = features_df['volume'] / avg_vol
        features_df['volume_trend'] = features_df['volume'].pct_change(5)
        features_df['obv_trend'] = features_df['obv'].pct_change(5)
        
        # ADX Trend-Stärke
        features_df['trend_strong'] = np.where(features_df['adx'] > 25, 1, 0)
        features_df['trend_weak'] = np.where(features_df['adx'] < 20, 1, 0)
        
        # Stochastic Momentum
        features_df['stoch_signal'] = np.where(features_df['stoch_k'] > features_df['stoch_d'], 1, -1)
        
        # MACD Signal
        features_df['macd_positive'] = np.where(features_df['macd_hist'] > 0, 1, 0)
        features_df['macd_momentum'] = features_df['macd_hist'].rolling(window=3).mean()

        # Vortex Difference
        features_df['vortex_diff'] = features_df['vortex_pos'] - features_df['vortex_neg']

        # Lag Features (NEU) - geben dem Modell historischen Kontext
        lags = [1, 3, 5]
        for lag in lags:
            features_df[f'rsi_lag_{lag}'] = features_df['rsi_14'].shift(lag)
        features_df['macd_hist_lag_1'] = features_df['macd_hist'].shift(1)
        features_df['macd_hist_lag_3'] = features_df['macd_hist'].shift(3)
        features_df['adx_lag_3'] = features_df['adx'].shift(3)
        features_df['volume_ratio_lag_3'] = features_df['volume_ratio'].shift(3)
        
        # Ersetze unendliche Werte und fülle NaNs, die durch Berechnungen entstanden sind
        features_df.replace([np.inf, -np.inf], np.nan, inplace=True)
        features_df.fillna(0, inplace=True)
        
        return features_df

    def _select_features_from_df(self, df: pd.DataFrame) -> pd.DataFrame:
        """Wählt die für das Modell definierten Feature-Spalten aus einem DataFrame aus."""
        feature_names = self._get_feature_names()
        
        # Stelle sicher, dass alle Feature-Spalten im DataFrame existieren
        available_features = [f for f in feature_names if f in df.columns]
        missing_features = [f for f in feature_names if f not in df.columns]
        
        if missing_features:
            logger.warning(f"Fehlende Feature-Spalten: {missing_features}. Werden mit 0 gefüllt.")
            for f in missing_features:
                df[f] = 0
        
        return df[feature_names].copy()
    
    def _prepare_features(self, df: pd.DataFrame) -> Optional[pd.DataFrame]:
        """
        Bereitet Features für das Modell vor.
        Diese Methode ist für eine einzelne Vorhersage (letzte Zeile des df) optimiert.
        
        Args:
            df: DataFrame mit Marktdaten und Indikatoren
            
        Returns:
            DataFrame mit einer Zeile der ausgewählten Features
        """
        try:
            # Erstelle alle Features für den gesamten DataFrame
            all_features = self._create_features_from_indicators(df)
            
            # Wähle die relevanten Feature-Spalten aus
            selected_features = self._select_features_from_df(all_features)
            
            # Gib nur die letzte Zeile zurück, da diese für die Live-Vorhersage ist
            last_row = selected_features.iloc[[-1]]
            
            logger.debug(f"Features für Vorhersage vorbereitet: {len(last_row.columns)} Features")
            
            return last_row
            
        except Exception as e:
            logger.error(f"Fehler bei der Feature-Vorbereitung: {str(e)}")
            return None
    
    def incremental_train(self, X: pd.DataFrame, y: pd.Series):
        """
        Führt inkrementelles Training mit neuen Daten durch.
        Behält das bestehende Modell und trainiert es mit zusätzlichen Daten weiter.
        
        Args:
            X: Neue Feature-DataFrame
            y: Neue Target-Series
        """
        try:
            logger.info(f"Starte inkrementelles Training mit {len(X)} neuen Samples...")
            
            # Wenn kein Modell existiert, normales Training
            if not self.is_trained:
                logger.info("Kein trainiertes Modell vorhanden - führe vollständiges Training durch")
                self.train(X, y)
                return
            
            # Skaliere neue Daten mit bestehendem Scaler
            X_scaled = self.scaler.transform(X)
            
            # Für Tree-basierte Modelle (XGBoost, LightGBM) mit warm_start
            model_type = self.settings.get('model_type', 'xgboost')
            
            if model_type in ['xgboost', 'lightgbm'] and hasattr(self.model, 'n_estimators'):
                # Erhöhe Anzahl der Bäume für zusätzliches Lernen
                current_n_estimators = self.model.n_estimators
                additional_trees = self.settings.get('incremental_trees', 50)
                
                self.model.n_estimators = current_n_estimators + additional_trees
                
                # XGBoost unterstützt xgb_model Parameter für warm start
                if model_type == 'xgboost' and XGBOOST_AVAILABLE:
                    self.model.fit(X_scaled, y, xgb_model=self.model.get_booster())
                else:
                    # Für andere Modelle: Kombiniere mit alten Daten falls verfügbar
                    self.model.fit(X_scaled, y)
                
                logger.info(f"Inkrementelles Training abgeschlossen: {current_n_estimators} -> {self.model.n_estimators} Bäume")
            else:
                # Fallback: Vollständiges Re-Training
                logger.warning(f"Inkrementelles Training nicht unterstützt für {model_type}, führe Re-Training durch")
                self.train(X, y)
                return
            
            # Speichere aktualisiertes Modell
            self._save_model()
            
            # Berechne neue Genauigkeit
            accuracy = self.model.score(X_scaled, y)
            logger.info(f"Inkrementelles Training abgeschlossen. Neue Genauigkeit auf Sample: {accuracy:.2%}")
            
        except Exception as e:
            logger.error(f"Fehler beim inkrementellen Training: {str(e)}", exc_info=True)
    
    def evaluate_on_new_data(self, X: pd.DataFrame, y: pd.Series) -> Dict:
        """
        Evaluiert das Modell auf neuen Daten ohne zu trainieren.
        
        Args:
            X: Feature-DataFrame
            y: Target-Series
            
        Returns:
            Dictionary mit Evaluationsmetriken
        """
        try:
            if not self.is_trained:
                logger.warning("Modell ist nicht trainiert")
                return {}
            
            X_scaled = self.scaler.transform(X)
            
            # Predictions
            y_pred = self.model.predict(X_scaled)
            
            # Accuracy
            accuracy = self.model.score(X_scaled, y)
            
            # Confusion Matrix
            from sklearn.metrics import confusion_matrix, classification_report
            cm = confusion_matrix(y, y_pred)
            
            # Classification Report
            report = classification_report(y, y_pred, output_dict=True, zero_division=0)
            
            result = {
                'accuracy': accuracy,
                'confusion_matrix': cm.tolist(),
                'classification_report': report,
                'sample_count': len(X)
            }
            
            logger.info(f"Evaluation abgeschlossen: Accuracy={accuracy:.2%} auf {len(X)} Samples")
            return result
            
        except Exception as e:
            logger.error(f"Fehler bei der Evaluation: {str(e)}", exc_info=True)
            return {}
    
    def get_feature_importance(self) -> Dict:
        """
        Gibt die Feature-Wichtigkeit zurück.
        
        Returns:
            Dictionary mit Feature-Namen und ihrer Wichtigkeit
        """
        if not self.is_trained or not hasattr(self.model, 'feature_importances_'):
            return {}
        
        try:
            importances = self.model.feature_importances_
            feature_names = self.model.feature_names_in_
            
            importance_dict = dict(zip(feature_names, importances))
            
            # Sortiert nach Wichtigkeit
            importance_dict = dict(
                sorted(importance_dict.items(), key=lambda x: x[1], reverse=True)
            )
            
            return importance_dict
            
        except Exception as e:
            logger.error(f"Fehler beim Abrufen der Feature-Wichtigkeit: {str(e)}")
            return {}
