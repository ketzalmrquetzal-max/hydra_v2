# -*- coding: utf-8 -*-
"""
HYDRA V2 - CORE CONFIGURATION
Seguridad de Grado Bancario: API Keys NUNCA en el código fuente
"""

import os
from pathlib import Path
from pydantic_settings import BaseSettings
from pydantic import Field, validator
from typing import Literal


class Settings(BaseSettings):
    """
    Configuración centralizada del sistema Hydra.
    Carga variables desde .env (NUNCA hardcodeadas)
    """

    # ==================== BINANCE API ====================
    binance_api_key: str = Field(..., env="BINANCE_API_KEY")
    binance_secret_key: str = Field(..., env="BINANCE_SECRET_KEY")
    binance_testnet: bool = Field(default=True, env="BINANCE_TESTNET")

    # ==================== GEMINI AI BRAIN ====================
    gemini_api_key: str = Field(..., env="GEMINI_API_KEY")

    # ==================== TELEGRAM COMMAND CENTER ====================
    telegram_token: str = Field(..., env="TELEGRAM_TOKEN")
    telegram_chat_id: str = Field(..., env="TELEGRAM_CHAT_ID")

    # ==================== DATABASE (SUPABASE) ====================
    supabase_url: str | None = Field(default=None, env="SUPABASE_URL")
    supabase_key: str | None = Field(default=None, env="SUPABASE_KEY")

    # ==================== SYSTEM SETTINGS ====================
    env_state: Literal["DEVELOPMENT", "PRODUCTION"] = Field(
        default="DEVELOPMENT", env="ENV_STATE"
    )

    # ==================== RISK MANAGEMENT (Las 3 Leyes) ====================
    # Ley 1: Daily Loss Limit
    max_daily_loss_pct: float = Field(
        default=0.05,
        env="MAX_DAILY_LOSS",
        description="5% pérdida máxima diaria antes de activar Kill Switch",
    )

    # Ley 2: Position Sizing
    max_risk_per_trade_pct: float = Field(
        default=0.02,
        env="RISK_PER_TRADE",
        description="2% máximo de riesgo por operación",
    )

    # Ley 2.5: Stop Loss Distance
    stop_loss_pct: float = Field(
        default=0.02,
        env="STOP_LOSS_PCT",
        description="2% distancia del stop loss desde precio de entrada",
    )

    # Ley 3: Heartbeat Monitor
    heartbeat_timeout_seconds: int = Field(
        default=60, description="Segundos sin heartbeat antes de asumir ceguera"
    )

    # Límites adicionales
    max_leverage: int = Field(
        default=5,
        le=50,
        description="Apalancamiento máximo permitido (5x - conservador)",
    )

    max_concurrent_positions: int = Field(
        default=3, description="Máximo de posiciones abiertas simultáneamente"
    )

    # ==================== PATHS ====================
    @property
    def project_root(self) -> Path:
        """Raíz del proyecto"""
        return Path(__file__).parent.parent.parent

    @property
    def logs_dir(self) -> Path:
        """Directorio de logs"""
        # Navigate from backend/ to project root, then to docs/logs
        path = self.project_root.parent / "docs" / "logs"
        path.mkdir(parents=True, exist_ok=True)
        return path

    @property
    def kill_switch_path(self) -> Path:
        """Archivo de Kill Switch mecánico"""
        return self.project_root / "EMERGENCY_STOP"

    # ==================== VALIDATORS ====================
    @validator("max_daily_loss_pct")
    def validate_daily_loss(cls, v):
        if not 0 < v <= 0.1:  # Entre 0% y 10%
            raise ValueError("Daily loss debe estar entre 0% y 10%")
        return v

    @validator("max_risk_per_trade_pct")
    def validate_risk_per_trade(cls, v):
        if not 0 < v <= 0.05:  # Entre 0% y 5%
            raise ValueError("Risk per trade debe estar entre 0% y 5%")
        return v

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
        extra = "allow"  # Permitir campos extra del .env


# Singleton global
_settings: Settings | None = None


def get_settings() -> Settings:
    """
    Obtiene la configuración global (patrón singleton)
    """
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings


def is_kill_switch_active() -> bool:
    """
    Verifica si el Kill Switch mecánico está activado.
    Si existe el archivo EMERGENCY_STOP, el sistema NO debe operar.
    """
    settings = get_settings()
    return settings.kill_switch_path.exists()


def activate_kill_switch() -> None:
    """
    Activa el Kill Switch creando el archivo de emergencia.
    """
    settings = get_settings()
    settings.kill_switch_path.touch()


def deactivate_kill_switch() -> None:
    """
    Desactiva el Kill Switch eliminando el archivo de emergencia.
    Solo debe hacerse manualmente por el operador humano.
    """
    settings = get_settings()
    if settings.kill_switch_path.exists():
        settings.kill_switch_path.unlink()
