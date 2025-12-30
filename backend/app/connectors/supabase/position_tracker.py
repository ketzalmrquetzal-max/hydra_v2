# -*- coding: utf-8 -*-
"""
HYDRA V2 - POSITION TRACKER
Rastreo persistente de posiciones, pérdidas diarias y estado de la cuenta.
Componente crítico para Las 3 Leyes del Guardián.
"""

from datetime import datetime, date
from typing import List
from backend.app.domain.schemas.risk import Position, OrderSide


class PositionTracker:
    """
    Mantiene el estado de todas las posiciones abiertas y el historial diario.
    En V1 usaremos memoria (dict). En V2 migraremos a Supabase.
    """
    
    def __init__(self):
        # Base de datos en memoria (temporal)
        self._open_positions: dict[str, Position] = {}
        self._daily_pnl: dict[date, float] = {}  # {fecha: PnL en USDT}
        self._account_balance: float = 0.0
        self._initial_balance: float = 0.0
        
    def set_initial_balance(self, balance: float) -> None:
        """Establece el balance inicial de la cuenta"""
        self._account_balance = balance
        self._initial_balance = balance
    
    def get_account_balance(self) -> float:
        """Retorna el balance actual"""
        return self._account_balance
    
    def add_position(self, position: Position) -> None:
        """Registra una nueva posición abierta"""
        self._open_positions[position.position_id] = position
    
    def remove_position(self, position_id: str) -> Position | None:
        """Cierra una posición y la retorna"""
        return self._open_positions.pop(position_id, None)
    
    def get_open_positions(self) -> List[Position]:
        """Retorna todas las posiciones abiertas"""
        return list(self._open_positions.values())
    
    def get_open_positions_count(self) -> int:
        """Cuenta de posiciones abiertas (para Ley 2)"""
        return len(self._open_positions)
    
    def update_position_pnl(self, position_id: str, current_price: float) -> None:
        """
        Actualiza el PnL no realizado de una posición basado en el precio actual
        """
        if position_id not in self._open_positions:
            return
        
        position = self._open_positions[position_id]
        
        # Calcular PnL según la dirección
        if position.side in [OrderSide.BUY, OrderSide.LONG]:
            pnl = (current_price - position.entry_price) * position.quantity
        else:  # SELL o SHORT
            pnl = (position.entry_price - current_price) * position.quantity
        
        # Aplicar apalancamiento
        pnl *= position.leverage
        
        position.unrealized_pnl = pnl
        position.unrealized_pnl_pct = (pnl / (position.entry_price * position.quantity)) * 100
    
    def record_realized_pnl(self, pnl_usdt: float) -> None:
        """
        Registra un PnL realizado (cuando se cierra una posición)
        y actualiza el balance.
        """
        today = date.today()
        
        # Acumular PnL del día
        if today not in self._daily_pnl:
            self._daily_pnl[today] = 0.0
        
        self._daily_pnl[today] += pnl_usdt
        self._account_balance += pnl_usdt
    
    def get_daily_pnl_usdt(self) -> float:
        """
        Retorna el PnL acumulado del día actual en USDT.
        LEY 1: Esto se compara contra el límite de sangre.
        """
        today = date.today()
        return self._daily_pnl.get(today, 0.0)
    
    def get_daily_pnl_pct(self) -> float:
        """
        Retorna el PnL del día como porcentaje del balance inicial del día.
        LEY 1: Si esto <= -3%, Kill Switch.
        """
        today = date.today()
        daily_pnl = self._daily_pnl.get(today, 0.0)
        
        if self._initial_balance == 0:
            return 0.0
        
        return (daily_pnl / self._initial_balance) * 100
    
    def get_total_unrealized_pnl(self) -> float:
        """
        Suma el PnL no realizado de todas las posiciones abiertas.
        """
        return sum(pos.unrealized_pnl for pos in self._open_positions.values())
    
    def reset_daily_tracking(self) -> None:
        """
        Resetea el tracking diario (llamar a las 00:00 UTC).
        El balance se mantiene, solo se resetea el contador de pérdidas diarias.
        """
        today = date.today()
        self._daily_pnl[today] = 0.0
        self._initial_balance = self._account_balance
    
    def calculate_position_size(
        self, 
        risk_pct: float,
        stop_loss_pct: float,
        entry_price: float
    ) -> float:
        """
        LEY 2: Calcula el tamaño de posición basado en el riesgo permitido.
        
        Fórmula:
        Riesgo_USD = Balance * risk_pct
        Cantidad = Riesgo_USD / (entry_price * stop_loss_pct)
        
        Ejemplo:
        - Balance: $1000
        - Risk: 1% = $10
        - Entry: $100
        - Stop Loss: 5%
        - Cantidad = $10 / ($100 * 0.05) = $10 / $5 = 2 unidades
        """
        risk_amount_usdt = self._account_balance * risk_pct
        position_size = risk_amount_usdt / (entry_price * stop_loss_pct)
        return position_size
    
    def get_remaining_risk_budget_pct(self, max_daily_loss_pct: float) -> float:
        """
        Retorna cuánto % de riesgo queda disponible hoy.
        Si ya perdiste -2% y el límite es -3%, retorna 1%.
        """
        current_loss_pct = self.get_daily_pnl_pct()
        
        if current_loss_pct >= 0:
            # Si vamos ganando, el presupuesto completo está disponible
            return abs(max_daily_loss_pct)
        
        remaining = abs(max_daily_loss_pct) - abs(current_loss_pct)
        return max(0, remaining)


# Singleton global
_tracker: PositionTracker | None = None


def get_position_tracker() -> PositionTracker:
    """Obtiene el tracker global (patrón singleton)"""
    global _tracker
    if _tracker is None:
        _tracker = PositionTracker()
    return _tracker
