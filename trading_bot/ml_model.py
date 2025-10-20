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
            
            # Label-Mapping zurück: 0,1,2 -> -1,0,1
            # 0 (XGBoost) -> -1 (Verkauf)
            # 1 (XGBoost) ->  0 (Halten)
            # 2 (XGBoost) ->  1 (Kauf)
            signal_mapped = int(prediction) - 1
            
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
    
    def _prepare_features(self, df: pd.DataFrame) -> Optional[pd.DataFrame]:
        """
        Bereitet Features für das Modell vor.
        MUSS EXAKT die gleichen 38 Features wie beim Premium-Training erstellen!
        
        Args:
            df: DataFrame mit Marktdaten und Indikatoren
            
        Returns:
            DataFrame mit ausgewählten Features
        """
        try:
            # Basis-Features (ALLE 20 wie im Premium-Training)
            base_features = [
                # Moving Averages
                'sma_20', 'sma_50', 'ema_9', 'ema_21',
                # Momentum
                'rsi_14', 'macd_line', 'macd_signal', 'macd_hist', 'momentum',
                'stoch_k', 'stoch_d',
                # Volatilität
                'bb_upper', 'bb_middle', 'bb_lower', 'atr',
                # Trend
                'adx', 'plus_di', 'minus_di',
                # Volumen
                'volume', 'obv'
            ]
            
            # Erstelle DataFrame mit letzter Zeile
            features_df = pd.DataFrame(index=[0])
            
            # Füge verfügbare Basis-Features hinzu
            for col in base_features:
                if col in df.columns:
                    features_df[col] = df[col].tail(1).values[0]
            
            # Abgeleitete Features (EXAKT wie im Training!)
            if 'close' in df.columns:
                close_val = df['close'].tail(1).values[0]
                
                # Preis-Ratios
                if 'sma_20' in df.columns:
                    sma20 = df['sma_20'].tail(1).values[0]
                    features_df['price_sma20_ratio'] = close_val / sma20 if sma20 > 0 else 1.0
                    features_df['price_distance_sma20'] = (close_val - sma20) / sma20 if sma20 > 0 else 0.0
                
                if 'sma_50' in df.columns:
                    sma50 = df['sma_50'].tail(1).values[0]
                    features_df['price_sma50_ratio'] = close_val / sma50 if sma50 > 0 else 1.0
                
                # Bollinger Band Position & Width
                if all(col in df.columns for col in ['bb_lower', 'bb_upper', 'bb_middle']):
                    bb_lower = df['bb_lower'].tail(1).values[0]
                    bb_upper = df['bb_upper'].tail(1).values[0]
                    bb_middle = df['bb_middle'].tail(1).values[0]
                    bb_range = bb_upper - bb_lower
                    if bb_range > 0:
                        features_df['bb_position'] = (close_val - bb_lower) / bb_range
                        features_df['bb_width'] = bb_range / bb_middle if bb_middle > 0 else 0.0
                    else:
                        features_df['bb_position'] = 0.5
                        features_df['bb_width'] = 0.0
            
            # Trend-Features
            if 'sma_20' in df.columns and 'sma_50' in df.columns:
                sma20 = df['sma_20'].tail(1).values[0]
                sma50 = df['sma_50'].tail(1).values[0]
                features_df['sma20_sma50_ratio'] = sma20 / sma50 if sma50 > 0 else 1.0
                features_df['trend_alignment'] = 1 if sma20 > sma50 else -1
            
            # Momentum-Features
            if 'rsi_14' in df.columns:
                rsi = df['rsi_14'].tail(1).values[0]
                features_df['rsi_normalized'] = (rsi - 50) / 50
                features_df['rsi_oversold'] = 1 if rsi < 30 else 0
                features_df['rsi_overbought'] = 1 if rsi > 70 else 0
            
            # Volumen-Features
            if 'volume' in df.columns:
                vol = df['volume'].tail(1).values[0]
                avg_vol = df['volume'].tail(20).mean()
                features_df['volume_ratio'] = vol / avg_vol if avg_vol > 0 else 1.0
                features_df['volume_trend'] = df['volume'].pct_change(5, fill_method=None).tail(1).values[0] if len(df) >= 6 else 0.0
            
            if 'obv' in df.columns:
                features_df['obv_trend'] = df['obv'].pct_change(5, fill_method=None).tail(1).values[0] if len(df) >= 6 else 0.0
            
            # ADX Trend-Stärke
            if 'adx' in df.columns:
                adx_val = df['adx'].tail(1).values[0]
                features_df['trend_strong'] = 1 if adx_val > 25 else 0
                features_df['trend_weak'] = 1 if adx_val < 20 else 0
            
            # Stochastic Momentum
            if 'stoch_k' in df.columns and 'stoch_d' in df.columns:
                stoch_k = df['stoch_k'].tail(1).values[0]
                stoch_d = df['stoch_d'].tail(1).values[0]
                features_df['stoch_signal'] = 1 if stoch_k > stoch_d else -1
            
            # MACD Signal
            if 'macd_hist' in df.columns:
                macd_hist = df['macd_hist'].tail(1).values[0]
                features_df['macd_positive'] = 1 if macd_hist > 0 else 0
                features_df['macd_momentum'] = df['macd_hist'].tail(3).mean() if len(df) >= 3 else 0.0
            
            # NaN-Werte mit 0 füllen
            features_df = features_df.fillna(0).infer_objects(copy=False)
            
            logger.debug(f"Features vorbereitet: {len(features_df.columns)} Features")
            
            return features_df
            
        except Exception as e:
            logger.error(f"Fehler bei der Feature-Vorbereitung: {str(e)}")
            return None
    
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
