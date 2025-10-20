"""
Risikomanagement-Modul für den Trading-Bot.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional
import logging

logger = logging.getLogger(__name__)

class RiskManager:
    """
    Verwaltet Risikomanagement und Positionsgrößenberechnung.
    """
    
    def __init__(self, config: Dict, initial_balance: float):
        """
        Initialisiert den Risk-Manager.
        
        Args:
            config: Risikomanagement-Konfiguration
            initial_balance: Anfangskapital
        """
        self.config = config
        self.initial_balance = initial_balance
        self.current_balance = initial_balance
        
        # Risikomanagement-Parameter
        self.max_risk_per_trade = config.get('max_risk_per_trade', 0.01)  # 1% pro Trade
        self.max_portfolio_risk = config.get('max_portfolio_risk', 0.05)  # 5% gesamt
        self.max_open_positions = config.get('max_open_positions', 3)
        self.risk_reward_ratio = config.get('min_risk_reward_ratio', 2.0)
        
        logger.info("RiskManager erfolgreich initialisiert")
    
    def evaluate_risk(
        self, 
        signals: List[Dict], 
        portfolio: Dict, 
        current_price: float
    ) -> List[Dict]:
        """
        Bewertet Risiko und erstellt Handelsentscheidungen.
        
        Args:
            signals: Liste von Handelssignalen
            portfolio: Aktuelles Portfolio
            current_price: Aktueller Marktpreis
            
        Returns:
            Liste von ausführbaren Handelsentscheidungen
        """
        decisions = []
        
        # Aktualisiere Balance
        self.current_balance = portfolio.get('balance', self.initial_balance)
        
        # Hole offene Positionen
        open_positions = portfolio.get('positions', {})
        num_open_positions = len(open_positions)
        
        for signal in signals:
            try:
                action = signal.get('action')
                symbol = signal.get('symbol')
                
                # Verkaufssignale: Nur wenn Position existiert
                if action == 'sell':
                    if symbol not in open_positions:
                        logger.debug(f"Verkaufssignal für {symbol} ignoriert: Keine offene Position")
                        continue
                
                # Kaufsignale: Nur wenn nicht max. Positionen erreicht
                if action == 'buy':
                    if num_open_positions >= self.max_open_positions:
                        logger.info(f"Kaufsignal ignoriert: Maximale Anzahl offener Positionen erreicht ({num_open_positions})")
                        continue
                
                decision = self._evaluate_signal(signal, current_price)
                if decision:
                    decisions.append(decision)
            except Exception as e:
                logger.error(f"Fehler bei der Risikobewertung: {str(e)}")
        
        return decisions
    
    def _evaluate_signal(self, signal: Dict, current_price: float) -> Optional[Dict]:
        """
        Bewertet ein einzelnes Signal und erstellt eine Handelsentscheidung.
        
        Args:
            signal: Handelssignal
            current_price: Aktueller Preis
            
        Returns:
            Handelsentscheidung oder None
        """
        action = signal.get('action')
        confidence = signal.get('confidence', 0.5)
        
        # Mindest-Konfidenz prüfen
        min_confidence = self.config.get('min_confidence', 0.6)
        if confidence < min_confidence:
            logger.debug(f"Signal ignoriert: Konfidenz zu niedrig ({confidence:.2%})")
            return None
        
        # Stop-Loss und Take-Profit berechnen
        stop_loss, take_profit = self._calculate_risk_levels(current_price, action)
        
        # Positionsgröße berechnen
        position_size = self._calculate_position_size(
            current_price, 
            stop_loss, 
            confidence
        )
        
        if position_size <= 0:
            logger.debug("Positionsgröße zu klein, Signal ignoriert")
            return None
        
        # Handelsentscheidung erstellen
        decision = {
            'action': action,
            'amount': position_size,
            'price': current_price,
            'stop_loss': stop_loss,
            'take_profit': take_profit,
            'confidence': confidence,
            'strategy': signal.get('strategy', 'unknown'),
            'reason': signal.get('reason', ''),
            'risk_reward_ratio': self._calculate_risk_reward(
                current_price, stop_loss, take_profit, action
            )
        }
        
        logger.info(f"Handelsentscheidung: {decision['action']} {decision['amount']:.4f} @ {current_price:.2f}")
        
        return decision
    
    def _calculate_risk_levels(
        self, 
        entry_price: float, 
        action: str
    ) -> tuple:
        """
        Berechnet Stop-Loss und Take-Profit Levels.
        
        Args:
            entry_price: Einstiegspreis
            action: 'buy' oder 'sell'
            
        Returns:
            Tuple von (stop_loss, take_profit)
        """
        # Standard-Stop-Loss: 2% vom Einstiegspreis
        stop_loss_pct = self.config.get('stop_loss_pct', 0.02)
        
        if action == 'buy':
            stop_loss = entry_price * (1 - stop_loss_pct)
            take_profit = entry_price * (1 + stop_loss_pct * self.risk_reward_ratio)
        else:  # sell
            stop_loss = entry_price * (1 + stop_loss_pct)
            take_profit = entry_price * (1 - stop_loss_pct * self.risk_reward_ratio)
        
        return stop_loss, take_profit
    
    def _calculate_position_size(
        self, 
        entry_price: float, 
        stop_loss: float,
        confidence: float
    ) -> float:
        """
        Berechnet die optimale Positionsgröße basierend auf Risiko.
        
        Args:
            entry_price: Einstiegspreis
            stop_loss: Stop-Loss Level
            confidence: Signal-Konfidenz
            
        Returns:
            Positionsgröße
        """
        # Risikobetrag basierend auf aktuellem Kontostand
        risk_amount = self.current_balance * self.max_risk_per_trade
        
        # Risiko pro Einheit
        risk_per_unit = abs(entry_price - stop_loss)
        
        if risk_per_unit == 0:
            return 0
        
        # Positionsgröße berechnen
        position_size = risk_amount / risk_per_unit
        
        # Anpassung basierend auf Konfidenz
        position_size *= confidence
        
        # Maximale Positionsgröße basierend auf verfügbarem Kapital
        max_position_value = self.current_balance * 0.3  # Maximal 30% des Kapitals
        max_position_size = max_position_value / entry_price
        
        position_size = min(position_size, max_position_size)
        
        return position_size
    
    def _calculate_risk_reward(
        self, 
        entry_price: float, 
        stop_loss: float, 
        take_profit: float,
        action: str
    ) -> float:
        """
        Berechnet das Risk-Reward-Verhältnis.
        
        Args:
            entry_price: Einstiegspreis
            stop_loss: Stop-Loss Level
            take_profit: Take-Profit Level
            action: 'buy' oder 'sell'
            
        Returns:
            Risk-Reward-Verhältnis
        """
        risk = abs(entry_price - stop_loss)
        reward = abs(take_profit - entry_price)
        
        if risk == 0:
            return 0
        
        return reward / risk
    
    def update_balance(self, new_balance: float):
        """
        Aktualisiert den aktuellen Kontostand.
        
        Args:
            new_balance: Neuer Kontostand
        """
        self.current_balance = new_balance
    
    def get_risk_metrics(self) -> Dict:
        """
        Gibt aktuelle Risikometriken zurück.
        
        Returns:
            Dictionary mit Risikometriken
        """
        return {
            'current_balance': self.current_balance,
            'initial_balance': self.initial_balance,
            'total_return': ((self.current_balance / self.initial_balance) - 1) * 100,
            'max_risk_per_trade': self.max_risk_per_trade * 100,
            'max_portfolio_risk': self.max_portfolio_risk * 100,
            'max_open_positions': self.max_open_positions
        }
