import os
import pandas as pd
import numpy as np
import yfinance as yf
import ccxt
from datetime import datetime, timedelta
from typing import Optional, Dict, List, Union
import pytz

class DataLoader:
    """
    Class for loading and preprocessing financial market data from various sources.
    Supports both historical and real-time data.
    """
    
    def __init__(self, data_dir: str = "data", cache_data: bool = True):
        self.data_dir = data_dir
        self.cache_data = cache_data
        self.exchange = ccxt.binance()  # Default exchange, can be changed
        
        # Create necessary directories
        os.makedirs(os.path.join(data_dir, "historical"), exist_ok=True)
        os.makedirs(os.path.join(data_dir, "processed"), exist_ok=True)
    
    def load_historical_data(
        self, 
        symbol: str, 
        start_date: str = "2010-01-01", 
        end_date: Optional[str] = None,
        interval: str = "1d",
        source: str = "yfinance"
    ) -> pd.DataFrame:
        """
        Load historical price data from specified source.
        
        Args:
            symbol: Trading pair symbol (e.g., 'BTC-USD' or 'AAPL')
            start_date: Start date in 'YYYY-MM-DD' format
            end_date: End date in 'YYYY-MM-DD' format (default: today)
            interval: Data interval ('1m', '5m', '15m', '1h', '1d', etc.)
            source: Data source ('yfinance' or 'ccxt')
            
        Returns:
            DataFrame with OHLCV data and datetime index
        """
        if end_date is None:
            end_date = datetime.now().strftime("%Y-%m-%d")
            
        cache_file = os.path.join(
            self.data_dir, 
            "historical", 
            f"{symbol.replace('-', '')}_{start_date}_{end_date}_{interval}.parquet"
        )
        
        # Try to load from cache first
        if os.path.exists(cache_file) and self.cache_data:
            try:
                df = pd.read_parquet(cache_file)
                if not df.empty:
                    return df
            except:
                pass
        
        # Fetch fresh data if not in cache
        if source.lower() == 'yfinance':
            df = self._fetch_yfinance_data(symbol, start_date, end_date, interval)
        elif source.lower() == 'ccxt':
            df = self._fetch_ccxt_data(symbol, start_date, end_date, interval)
        else:
            raise ValueError(f"Unsupported data source: {source}")
        
        # Cache the data
        if self.cache_data and not df.empty:
            df.to_parquet(cache_file)
            
        return df
    
    def _fetch_yfinance_data(
        self, 
        symbol: str, 
        start_date: str, 
        end_date: str, 
        interval: str
    ) -> pd.DataFrame:
        """Fetch historical data from Yahoo Finance"""
        try:
            ticker = yf.Ticker(symbol)
            df = ticker.history(start=start_date, end=end_date, interval=interval, auto_adjust=True)
            
            # Standardize column names
            df = df.rename(columns={
                'Open': 'open',
                'High': 'high',
                'Low': 'low',
                'Close': 'close',
                'Volume': 'volume'
            })
            
            # Ensure datetime index
            if not isinstance(df.index, pd.DatetimeIndex):
                df.index = pd.to_datetime(df.index)
                
            return df
        except Exception as e:
            print(f"Error fetching data from Yahoo Finance: {e}")
            return pd.DataFrame()
    
    def _fetch_ccxt_data(
        self, 
        symbol: str, 
        start_date: str, 
        end_date: str, 
        interval: str
    ) -> pd.DataFrame:
        """Fetch historical data from CCXT exchange"""
        try:
            # Convert timeframes between yfinance and CCXT
            timeframe_map = {
                '1m': '1m', '5m': '5m', '15m': '15m', 
                '1h': '1h', '1d': '1d', '1w': '1w'
            }
            
            if interval not in timeframe_map:
                raise ValueError(f"Unsupported interval: {interval}")
                
            since = int(datetime.strptime(start_date, '%Y-%m-%d').timestamp() * 1000)
            end_timestamp = int(datetime.strptime(end_date, '%Y-%m-%d').timestamp() * 1000)
            
            all_ohlcv = []
            
            while since < end_timestamp:
                ohlcv = self.exchange.fetch_ohlcv(
                    symbol, 
                    timeframe_map[interval], 
                    since=since,
                    limit=1000
                )
                
                if not ohlcv:
                    break
                    
                all_ohlcv.extend(ohlcv)
                since = ohlcv[-1][0] + 1
                
                # Respect rate limits
                time.sleep(self.exchange.rateLimit / 1000)
            
            # Convert to DataFrame
            df = pd.DataFrame(
                all_ohlcv, 
                columns=['timestamp', 'open', 'high', 'low', 'close', 'volume']
            )
            
            # Convert timestamp to datetime
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            df = df.set_index('timestamp')
            
            # Filter by date range
            df = df.loc[start_date:end_date]
            
            # Convert data types
            for col in ['open', 'high', 'low', 'close', 'volume']:
                df[col] = pd.to_numeric(df[col])
                
            return df
            
        except Exception as e:
            print(f"Error fetching data from CCXT: {e}")
            return pd.DataFrame()
    
    def get_live_data(
        self, 
        symbol: str, 
        lookback: int = 100,
        interval: str = "1h"
    ) -> pd.DataFrame:
        """
        Get the most recent market data
        
        Args:
            symbol: Trading pair symbol
            lookback: Number of candles to fetch
            interval: Time interval for candles
            
        Returns:
            DataFrame with recent OHLCV data
        """
        try:
            ohlcv = self.exchange.fetch_ohlcv(symbol, interval, limit=lookback)
            df = pd.DataFrame(
                ohlcv, 
                columns=['timestamp', 'open', 'high', 'low', 'close', 'volume']
            )
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            df = df.set_index('timestamp')
            return df
        except Exception as e:
            print(f"Error fetching live data: {e}")
            return pd.DataFrame()
    
    def preprocess_data(
        self, 
        df: pd.DataFrame, 
        fill_method: str = 'ffill',
        normalize: bool = True
    ) -> pd.DataFrame:
        """
        Preprocess the data by handling missing values and optionally normalizing
        
        Args:
            df: Input DataFrame with OHLCV data
            fill_method: Method for filling missing values ('ffill', 'bfill', 'linear')
            normalize: Whether to normalize the data
            
        Returns:
            Preprocessed DataFrame
        """
        # Make a copy to avoid modifying the original
        df = df.copy()
        
        # Handle missing values
        if df.isnull().any().any():
            if fill_method == 'ffill':
                df = df.ffill().bfill()
            elif fill_method == 'bfill':
                df = df.bfill().ffill()
            elif fill_method == 'linear':
                df = df.interpolate(method='linear')
            else:
                df = df.dropna()
        
        # Normalize the data (except volume)
        if normalize:
            price_cols = ['open', 'high', 'low', 'close']
            if all(col in df.columns for col in price_cols):
                # Calculate returns instead of direct normalization
                for col in price_cols:
                    df[f'{col}_returns'] = df[col].pct_change()
                
                # Handle volume separately
                if 'volume' in df.columns:
                    df['volume_pct_change'] = df['volume'].pct_change()
        
        return df
    
    def resample_data(
        self, 
        df: pd.DataFrame, 
        interval: str
    ) -> pd.DataFrame:
        """
        Resample time series data to a different interval
        
        Args:
            df: Input DataFrame with datetime index
            interval: Target interval (e.g., '1h', '4h', '1d')
            
        Returns:
            Resampled DataFrame
        """
        if not isinstance(df.index, pd.DatetimeIndex):
            raise ValueError("DataFrame must have a DatetimeIndex")
        
        # Convert interval to pandas frequency string
        freq_map = {
            '1m': '1T', '5m': '5T', '15m': '15T', '30m': '30T',
            '1h': '1H', '4h': '4H', '1d': '1D', '1w': '1W', '1M': '1M'
        }
        
        if interval not in freq_map:
            raise ValueError(f"Unsupported interval: {interval}")
        
        # Resample OHLCV data
        ohlc_dict = {
            'open': 'first',
            'high': 'max',
            'low': 'min',
            'close': 'last',
            'volume': 'sum'
        }
        
        # Only include columns that exist in the DataFrame
        columns = [col for col in ohlc_dict.keys() if col in df.columns]
        resampled_ohlc = {}
        
        for col in columns:
            if col in ['open', 'high', 'low', 'close']:
                resampled_ohlc[col] = ohlc_dict[col]
            elif col == 'volume':
                resampled_ohlc[col] = ohlc_dict[col]
        
        return df.resample(freq_map[interval]).apply(resampled_ohlc).dropna()
