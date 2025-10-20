"""
Hilfsfunktionen für den Trading-Bot.
"""

import logging
import os
from datetime import datetime
from typing import Dict

def setup_logging(config: Dict):
    """
    Konfiguriert das Logging-System.
    
    Args:
        config: Logging-Konfiguration
    """
    log_level = config.get('level', 'INFO')
    log_format = config.get('format', '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    log_file = config.get('file', 'trading_bot.log')
    
    # Erstelle logs-Verzeichnis falls nicht vorhanden
    log_dir = os.path.dirname(log_file) if os.path.dirname(log_file) else 'logs'
    if log_dir and not os.path.exists(log_dir):
        os.makedirs(log_dir, exist_ok=True)
    
    # Konfiguriere Logging
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format=log_format,
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler()
        ]
    )
    
    logger = logging.getLogger(__name__)
    logger.info("Logging-System erfolgreich konfiguriert")

def format_currency(amount: float, currency: str = 'USD') -> str:
    """
    Formatiert einen Betrag als Währung.
    
    Args:
        amount: Betrag
        currency: Währungscode
        
    Returns:
        Formatierter String
    """
    if currency == 'USD' or currency == 'USDT':
        return f"${amount:,.2f}"
    elif currency == 'EUR':
        return f"€{amount:,.2f}"
    else:
        return f"{amount:,.2f} {currency}"

def format_percentage(value: float) -> str:
    """
    Formatiert einen Wert als Prozentsatz.
    
    Args:
        value: Wert (z.B. 0.05 für 5%)
        
    Returns:
        Formatierter String
    """
    return f"{value * 100:.2f}%"

def calculate_percentage_change(old_value: float, new_value: float) -> float:
    """
    Berechnet die prozentuale Änderung.
    
    Args:
        old_value: Alter Wert
        new_value: Neuer Wert
        
    Returns:
        Prozentuale Änderung
    """
    if old_value == 0:
        return 0.0
    return ((new_value - old_value) / old_value) * 100

def timestamp_to_datetime(timestamp: int) -> datetime:
    """
    Konvertiert einen Unix-Timestamp in ein datetime-Objekt.
    
    Args:
        timestamp: Unix-Timestamp in Millisekunden
        
    Returns:
        datetime-Objekt
    """
    return datetime.fromtimestamp(timestamp / 1000)

def validate_config(config: Dict, required_keys: list) -> bool:
    """
    Validiert eine Konfiguration.
    
    Args:
        config: Zu validierende Konfiguration
        required_keys: Liste erforderlicher Schlüssel
        
    Returns:
        True wenn gültig
    """
    for key in required_keys:
        if key not in config:
            logging.error(f"Fehlender Konfigurationsschlüssel: {key}")
            return False
    return True
