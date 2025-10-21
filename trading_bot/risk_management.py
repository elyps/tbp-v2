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
        current_price: float,
        market_data: Optional[pd.DataFrame] = None
    ) -> List[Dict]:
        """
        Bewertet Risiko und erstellt Handelsentscheidungen.
        
        Args:
            signals: Liste von Handelssignalen
            portfolio: Aktuelles Portfolio
            current_price: Aktueller Marktpreis
            market_data: DataFrame mit aktuellen Marktdaten (für Volumen-Check)
            
        Returns:
            Liste von ausführbaren Handelsentscheidungen
        """
        decisions = []
        
        # Aktualisiere Balance
        self.current_balance = portfolio.get('balance', self.initial_balance)
        
        # Hole offene Positionen
        open_positions = portfolio.get('positions', {})
        num_open_positions = len(open_positions)
        
        logger.debug(
            "RiskManager.evaluate_risk -> balance=%.2f open_positions=%s current_price=%.2f",
            self.current_balance,
            {sym: pos.get('amount') for sym, pos in open_positions.items()},
            current_price,
        )
        for signal in signals:
            try:
                action = signal.get('action')
                symbol = signal.get('symbol')
                logger.debug(
                    "RiskManager Signal -> action=%s symbol=%s confidence=%.2f reason=%s", 
                    action,
                    symbol,
                    signal.get('confidence', 0.0),
                    signal.get('reason', ''),
                )
                
                # Verkaufssignale: Nur wenn Position existiert
                if action == 'sell':
                    if symbol not in open_positions:
                        logger.debug("RiskManager: SELL verworfen, keine Position für %s", symbol)
                        continue
                
                # Kaufsignale: Prüfe Limitierungen
                if action == 'buy':
                    # Prüfe ob bereits eine Position für dieses Symbol existiert
                    if symbol in open_positions:
                        logger.info("RiskManager: BUY verworfen, %s bereits offen", symbol)
                        continue
                    
                    # Prüfe ob max. Anzahl Positionen erreicht
                    if num_open_positions >= self.max_open_positions:
                        logger.info(
                            "RiskManager: BUY verworfen, max offene Positionen erreicht (%d)",
                            num_open_positions,
                        )
                        continue

                    # Live-Liquiditäts-Check (NEU)
                    if market_data is not None and not market_data.empty:
                        recent_volume = market_data['volume'].tail(24).mean() # Durchschnitt der letzten 24h
                        min_volume_threshold = self.config.get('min_live_volume', 10) # Mindestvolumen (z.B. 10 BTC/ETH pro Stunde)
                        if recent_volume < min_volume_threshold:
                            logger.info(
                                "RiskManager: BUY für %s verworfen, zu geringes Live-Volumen (%.2f < %.2f)",
                                symbol,
                                recent_volume,
                                min_volume_threshold
                            )
                            continue
                    else:
                        logger.warning("Keine Marktdaten für Live-Liquiditäts-Check verfügbar.")
                
                decision = self._evaluate_signal(signal, current_price)
                if decision:
                    decisions.append(decision)
                else:
                    logger.debug("RiskManager: Signal ergab keine Entscheidung")
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
        logger.debug(
            "RiskManager._evaluate_signal -> action=%s price=%.4f confidence=%.2f min_conf=%.2f",
            action,
            current_price,
            confidence,
            min_confidence,
        )
        if confidence < min_confidence:
            logger.debug(
                "RiskManager: Signal verworfen (Konfidenz %.2f < Mindest %.2f)",
                confidence,
                min_confidence,
            )
            return None
        
        # Stop-Loss und Take-Profit berechnen
        stop_loss, take_profit = self._calculate_risk_levels(current_price, action)
        logger.debug(
            "RiskManager: Levels berechnet -> stop_loss=%.4f take_profit=%.4f",
            stop_loss,
            take_profit,
        )
        
        # Positionsgröße berechnen
        position_size = self._calculate_position_size(
            current_price, 
            stop_loss, 
            confidence
        )
        logger.debug(
            "RiskManager: PositionSize berechnet -> size=%.6f balance=%.2f", 
            position_size,
            self.current_balance,
        )
        
        # Erzwinge Mindestgewinn in EUR, sofern konfiguriert
        min_profit_eur = self.config.get('min_profit_target_eur')
        if position_size > 0 and min_profit_eur and action == 'buy':
            min_tp_price = current_price + (min_profit_eur / position_size)
            if min_tp_price > take_profit:
                take_profit = min_tp_price
                logger.debug(
                    "RiskManager: TakeProfit angehoben auf %.4f für Mindestgewinn %.2f€ (size=%.6f)",
                    take_profit,
                    min_profit_eur,
                    position_size,
                )
        
        if position_size <= 0:
            logger.debug(
                "RiskManager: Signal verworfen (Positionsgröße %.6f <= 0)",
                position_size,
            )
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
        
        logger.info(
            "RiskManager: Entscheidung -> action=%s amount=%.6f price=%.4f SL=%.4f TP=%.4f RR=%.2f",
            decision['action'],
            decision['amount'],
            current_price,
            stop_loss,
            take_profit,
            decision['risk_reward_ratio'],
        )
        
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
