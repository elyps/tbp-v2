from abc import ABC, abstractmethod
import pandas as pd
from typing import Dict, List, Optional, Tuple
import numpy as np

class BaseStrategy(ABC):    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self.name = self.__class__.__name__
        self.indicators = []
        self.model = None
        self.initialize()
    
    @abstractmethod
    def initialize(self):
        """Initialize strategy parameters and indicators"""
        pass
    
    @abstractmethod
    def generate_signals(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        Generate trading signals based on the strategy rules
        
        Args:
            data: DataFrame containing price and indicator data
            
        Returns:
            DataFrame with signal column (1 for buy, -1 for sell, 0 for hold)
        """
        pass
    
    def calculate_indicators(self, data: pd.DataFrame) -> pd.DataFrame:
        """Calculate technical indicators for the given data"""
        return data
    
    def set_parameters(self, params: Dict):
        """Update strategy parameters"""
        self.config.update(params)
        self.initialize()
    
    def get_indicators(self) -> List[str]:
        """Get list of indicators used by the strategy"""
        return self.indicators
    
    def preprocess_data(self, data: pd.DataFrame) -> pd.DataFrame:
        """Preprocess market data before analysis"""
        if not isinstance(data.index, pd.DatetimeIndex):
            data.index = pd.to_datetime(data.index)
        return data
    
    def calculate_risk(self, data: pd.DataFrame) -> Tuple[float, float, float]:
        """
        Calculate risk parameters (stop loss, take profit, position size)
        
        Returns:
            Tuple of (stop_loss, take_profit, position_size)
        """
        # Default implementation - should be overridden by specific strategies
        atr = data['atr'] if 'atr' in data.columns else data['high'] - data['low']
        stop_loss = data['close'].iloc[-1] - 2 * atr.iloc[-1]
        take_profit = data['close'].iloc[-1] + 3 * atr.iloc[-1]
        position_size = 0.1  # Default to 10% of portfolio
        
        return stop_loss, take_profit, position_size
    
    def train_model(self, X: pd.DataFrame, y: pd.Series):
        """Train machine learning model if the strategy uses one"""
        pass
    
    def predict(self, X: pd.DataFrame) -> np.ndarray:
        """Make predictions using the trained model"""
        if self.model is None:
            raise ValueError("Model has not been trained yet")
        return self.model.predict(X)
