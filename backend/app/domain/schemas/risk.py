# -*- coding: utf-8 -*-
"""
HYDRA V2 - RISK MANAGEMENT SCHEMAS
Estructuras de datos para El Guardián (Risk Manager)
"""

from pydantic import BaseModel, Field, validator
from typing import Literal
from datetime import datetime
from enum import Enum


class OrderSide(str, Enum):
    """Dirección de la orden"""

    BUY = "BUY"
    SELL = "SELL"
    LONG = "LONG"
    SHORT = "SHORT"


class OrderStatus(str, Enum):
    """Estados posibles de una orden"""

    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    EXECUTED = "EXECUTED"
    FAILED = "FAILED"


class RejectionReason(str, Enum):
    """Razones de rechazo del Guardián"""

    DAILY_LOSS_LIMIT_EXCEEDED = "DAILY_LOSS_LIMIT_EXCEEDED"
    POSITION_SIZE_TOO_LARGE = "POSITION_SIZE_TOO_LARGE"
    LEVERAGE_TOO_HIGH = "LEVERAGE_TOO_HIGH"
    MAX_POSITIONS_REACHED = "MAX_POSITIONS_REACHED"
    HEARTBEAT_TIMEOUT = "HEARTBEAT_TIMEOUT"
    KILL_SWITCH_ACTIVE = "KILL_SWITCH_ACTIVE"
    INSUFFICIENT_BALANCE = "INSUFFICIENT_BALANCE"
    INVALID_STOP_LOSS = "INVALID_STOP_LOSS"


# ==================== SOLICITUD DE ORDEN (Input del Estratega) ====================


class OrderRequest(BaseModel):
    """
    Solicitud de orden desde BALAM (El Estratega).
    Esta es la estructura que Balam envía al Guardián para pedir permiso.
    """

    symbol: str = Field(..., description="Par de trading (ej: BTCUSDT)")
    side: OrderSide = Field(..., description="Dirección: BUY/SELL/LONG/SHORT")
    quantity: float = Field(..., gt=0, description="Cantidad a operar")
    leverage: int = Field(
        default=25, ge=1, le=50, description="Apalancamiento solicitado"
    )
    stop_loss_pct: float = Field(
        ..., gt=0, lt=0.5, description="Stop Loss en % (ej: 0.02 = 2%)"
    )
    take_profit_pct: float | None = Field(
        None, gt=0, description="Take Profit en % (opcional)"
    )

    # Metadatos para el Black Box Recorder
    strategy_name: str = Field(
        default="BALAM_V2", description="Nombre de la estrategia"
    )
    confidence: float = Field(..., ge=0, le=1, description="Confianza de Balam (0-1)")
    reasoning: str = Field(..., description="Justificación de Balam")

    @validator("stop_loss_pct")
    def validate_stop_loss(cls, v):
        if v > 0.2:  # Stop Loss mayor a 20% es sospechoso
            raise ValueError("Stop Loss demasiado amplio (>20%), revisa estrategia")
        return v


# ==================== RESPUESTA DEL GUARDIÁN (Output) ====================


class OrderApproval(BaseModel):
    """
    Respuesta del Guardián después de analizar la solicitud.
    Si approved=True, incluye una firma digital única.
    """

    request_id: str = Field(..., description="ID único de la solicitud")
    approved: bool = Field(..., description="¿Orden aprobada?")

    # Si fue aprobada
    adjusted_quantity: float | None = Field(
        None,
        description="Cantidad ajustada por el Guardián (puede ser menor que la solicitada)",
    )
    signature: str | None = Field(
        None, description="Firma criptográfica SHA-256 (solo si approved=True)"
    )

    # Si fue rechazada
    rejection_reason: RejectionReason | None = Field(
        None, description="Razón del rechazo"
    )
    rejection_details: str | None = Field(
        None, description="Detalles adicionales del rechazo"
    )

    # Metadatos
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    current_daily_loss_pct: float = Field(..., description="Pérdida acumulada hoy (%)")
    remaining_risk_budget: float = Field(
        ..., description="Cuánto más se puede arriesgar hoy (%)"
    )


# ==================== CONFIGURACIÓN DE RIESGO ====================


class RiskLimits(BaseModel):
    """
    Configuración de los límites de riesgo (Las 3 Leyes).
    Estos valores vienen del archivo .env pero se validan aquí.
    """

    max_daily_loss_pct: float = Field(
        default=0.03,
        ge=0.01,
        le=0.1,
        description="Ley 1: Límite de Sangre (3% default)",
    )
    max_risk_per_trade_pct: float = Field(
        default=0.01, ge=0.001, le=0.05, description="Ley 2: Regla del 1%"
    )
    heartbeat_timeout_seconds: int = Field(
        default=60, ge=10, le=300, description="Ley 3: Timeout del Heartbeat"
    )
    max_leverage: int = Field(default=25, ge=1, le=50)
    max_concurrent_positions: int = Field(default=3, ge=1, le=10)


# ==================== ESTADO DEL SISTEMA ====================


class SystemHealth(BaseModel):
    """
    Estado de salud del sistema (para la Ley 3: Heartbeat)
    """

    sentinel_last_heartbeat: datetime | None = None
    executor_last_heartbeat: datetime | None = None
    balam_last_heartbeat: datetime | None = None

    is_sentinel_alive: bool = False
    is_executor_alive: bool = False
    is_balam_alive: bool = False

    kill_switch_active: bool = False

    @property
    def is_system_blind(self) -> bool:
        """
        Si el Sentinel está muerto, estamos ciegos.
        Ley 3: "Si no puedo ver, no puedo pelear"
        """
        return not self.is_sentinel_alive


# ==================== POSICIÓN ABIERTA ====================


class Position(BaseModel):
    """
    Representa una posición abierta en el mercado
    """

    position_id: str
    symbol: str
    side: OrderSide
    entry_price: float
    quantity: float
    leverage: int
    stop_loss_price: float
    take_profit_price: float | None

    unrealized_pnl: float = 0.0
    unrealized_pnl_pct: float = 0.0

    opened_at: datetime = Field(default_factory=datetime.utcnow)
    closed_at: datetime | None = None

    status: Literal["OPEN", "CLOSED"] = "OPEN"


# ==================== LOG FORENSE ====================


class RiskDecisionLog(BaseModel):
    """
    Registro forense de cada decisión del Guardián.
    "Cada decisión queda registrada. Determinismo total."
    """

    log_id: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)

    # Input (lo que pidió Balam)
    order_request: OrderRequest

    # Output (lo que decidió el Guardián)
    order_approval: OrderApproval

    # Contexto en el momento de la decisión
    account_balance_usdt: float
    daily_loss_usdt: float
    daily_loss_pct: float
    open_positions_count: int
    system_health: SystemHealth

    class Config:
        json_encoders = {datetime: lambda v: v.isoformat()}
