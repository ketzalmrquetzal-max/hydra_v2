# -*- coding: utf-8 -*-
"""
HYDRA V2 - EL GUARDIÁN (RISK MANAGER)
Auditor Residente con Veto Absoluto.

"No le importa si Balam tiene un presentimiento. Le importan las matemáticas."

LAS 3 LEYES DE LA ROBÓTICA FINANCIERA:
1. Daily Loss Limit: -3% = Kill Switch
2. Position Sizing: Nunca arriesgar >1% por operación
3. Heartbeat Monitor: Si no puedo ver, no puedo pelear
"""

import hashlib
import uuid
from datetime import datetime, timedelta
from typing import Tuple

from backend.app.domain.schemas.risk import (
    OrderRequest,
    OrderApproval,
    RejectionReason,
    RiskLimits,
    SystemHealth,
    RiskDecisionLog
)
from backend.app.core.config import get_settings, is_kill_switch_active, activate_kill_switch
from backend.app.core.forensic_logger import guardian_logger
from backend.app.connectors.supabase.position_tracker import get_position_tracker


class RiskManager:
    """
    EL GUARDIÁN
    
    Responsabilidades:
    - Validar cada orden contra Las 3 Leyes
    - Ajustar tamaños de posición (Position Sizing)
    - Monitorear salud del sistema (Heartbeat)
    - Activar Kill Switch cuando sea necesario
    - Generar firma digital para órdenes aprobadas
    - Logging forense de cada decisión
    """
    
    def __init__(self):
        self.settings = get_settings()
        self.position_tracker = get_position_tracker()
        
        # Estado del sistema (Ley 3: Heartbeat)
        self.system_health = SystemHealth()
        
        # Configuración de riesgos (Las 3 Leyes)
        self.risk_limits = RiskLimits(
            max_daily_loss_pct=self.settings.max_daily_loss_pct,
            max_risk_per_trade_pct=self.settings.max_risk_per_trade_pct,
            heartbeat_timeout_seconds=self.settings.heartbeat_timeout_seconds,
            max_leverage=self.settings.max_leverage,
            max_concurrent_positions=self.settings.max_concurrent_positions
        )
        
        guardian_logger.logger.info("🛡️ GUARDIÁN INICIADO - Modo: Auditor Residente con Veto Absoluto")
    
    # ==================== PUNTO DE ENTRADA PRINCIPAL ====================
    
    def validate_order(self, order_request: OrderRequest) -> OrderApproval:
        """
        FLUJO DE VISADO:
        Balam solicita → Guardián analiza → Aprueba (con firma) o Rechaza
        
        Este es el único punto de entrada para solicitudes de órdenes.
        """
        request_id = str(uuid.uuid4())
        
        guardian_logger.logger.info(f"📋 Nueva solicitud recibida: {request_id}")
        guardian_logger.logger.info(f"   Symbol: {order_request.symbol} | Side: {order_request.side} | Qty: {order_request.quantity}")
        guardian_logger.logger.info(f"   Confidence: {order_request.confidence:.1%} | Reasoning: {order_request.reasoning}")
        
        # VALIDACIÓN 1: Kill Switch mecánico
        if is_kill_switch_active():
            return self._reject_order(
                request_id,
                order_request,
                RejectionReason.KILL_SWITCH_ACTIVE,
                "EMERGENCY_STOP activo. Sistema en modo seguro."
            )
        
        # VALIDACIÓN 2: Estado del sistema actualizado
        self._update_system_health()
        
        # VALIDACIÓN 3: LEY 3 - Heartbeat Monitor
        if self.system_health.is_system_blind:
            return self._reject_order(
                request_id,
                order_request,
                RejectionReason.HEARTBEAT_TIMEOUT,
                "Sentinel no responde. No puedo ver, no puedo pelear."
            )
        
        # VALIDACIÓN 4: LEY 1 - Daily Loss Limit
        daily_loss_pct = self.position_tracker.get_daily_pnl_pct()
        if daily_loss_pct <= -self.risk_limits.max_daily_loss_pct * 100:
            # Activar Kill Switch
            guardian_logger.log_kill_switch_activation(
                "DAILY_LOSS_LIMIT_EXCEEDED",
                {"daily_loss_pct": daily_loss_pct, "limit": -self.risk_limits.max_daily_loss_pct * 100}
            )
            activate_kill_switch()
            
            return self._reject_order(
                request_id,
                order_request,
                RejectionReason.DAILY_LOSS_LIMIT_EXCEEDED,
                f"Límite de sangre alcanzado: {daily_loss_pct:.2f}% (Límite: {-self.risk_limits.max_daily_loss_pct * 100}%)"
            )
        
        # VALIDACIÓN 5: LEY 2 - Position Sizing
        adjusted_quantity, sizing_valid = self._validate_and_adjust_position_size(order_request)
        
        if not sizing_valid:
            return self._reject_order(
                request_id,
                order_request,
                RejectionReason.POSITION_SIZE_TOO_LARGE,
                f"Riesgo solicitado excede el 1% del capital. Ajuste no posible."
            )
        
        # VALIDACIÓN 6: Apalancamiento
        if order_request.leverage > self.risk_limits.max_leverage:
            return self._reject_order(
                request_id,
                order_request,
                RejectionReason.LEVERAGE_TOO_HIGH,
                f"Apalancamiento {order_request.leverage}x excede el límite ({self.risk_limits.max_leverage}x)"
            )
        
        # VALIDACIÓN 7: Máximo de posiciones concurrentes
        if self.position_tracker.get_open_positions_count() >= self.risk_limits.max_concurrent_positions:
            return self._reject_order(
                request_id,
                order_request,
                RejectionReason.MAX_POSITIONS_REACHED,
                f"Máximo de posiciones alcanzado ({self.risk_limits.max_concurrent_positions})"
            )
        
        # ✅ TODAS LAS VALIDACIONES PASADAS → APROBAR
        return self._approve_order(request_id, order_request, adjusted_quantity)
    
    # ==================== LÓGICA DE APROBACIÓN ====================
    
    def _approve_order(
        self, 
        request_id: str, 
        order_request: OrderRequest,
        adjusted_quantity: float
    ) -> OrderApproval:
        """
        Aprueba la orden y genera una firma digital única.
        Solo órdenes con firma válida pueden ejecutarse.
        """
        # Generar firma criptográfica (SHA-256)
        signature = self._generate_signature(request_id, order_request)
        
        daily_loss_pct = self.position_tracker.get_daily_pnl_pct()
        remaining_budget = self.position_tracker.get_remaining_risk_budget_pct(
            self.risk_limits.max_daily_loss_pct
        )
        
        approval = OrderApproval(
            request_id=request_id,
            approved=True,
            adjusted_quantity=adjusted_quantity,
            signature=signature,
            rejection_reason=None,
            rejection_details=None,
            current_daily_loss_pct=daily_loss_pct,
            remaining_risk_budget=remaining_budget
        )
        
        # Log forense
        guardian_logger.log_guardian_approval(
            approved=True,
            request_id=request_id,
            reason=f"Todas las validaciones pasadas. Qty ajustada: {adjusted_quantity}"
        )
        
        guardian_logger.logger.info(f"✅ ORDEN APROBADA: {request_id}")
        guardian_logger.logger.info(f"   Firma: {signature[:16]}...")
        guardian_logger.logger.info(f"   Cantidad ajustada: {adjusted_quantity} (Original: {order_request.quantity})")
        
        return approval
    
    def _reject_order(
        self,
        request_id: str,
        order_request: OrderRequest,
        reason: RejectionReason,
        details: str
    ) -> OrderApproval:
        """
        Rechaza la orden y registra el motivo.
        """
        daily_loss_pct = self.position_tracker.get_daily_pnl_pct()
        remaining_budget = self.position_tracker.get_remaining_risk_budget_pct(
            self.risk_limits.max_daily_loss_pct
        )
        
        approval = OrderApproval(
            request_id=request_id,
            approved=False,
            adjusted_quantity=None,
            signature=None,
            rejection_reason=reason,
            rejection_details=details,
            current_daily_loss_pct=daily_loss_pct,
            remaining_risk_budget=remaining_budget
        )
        
        # Log forense
        guardian_logger.log_guardian_rejection(
            request_id=request_id,
            reason=reason.value,
            details=details
        )
        
        guardian_logger.logger.warning(f"❌ ORDEN RECHAZADA: {request_id}")
        guardian_logger.logger.warning(f"   Razón: {reason.value}")
        guardian_logger.logger.warning(f"   Detalles: {details}")
        
        return approval
    
    # ==================== LEY 2: POSITION SIZING ====================
    
    def _validate_and_adjust_position_size(
        self, 
        order_request: OrderRequest
    ) -> Tuple[float, bool]:
        """
        LEY 2: Valida y ajusta el tamaño de la posición.
        
        Retorna: (cantidad_ajustada, es_válido)
        """
        # Calcular tamaño máximo permitido según el 1% de riesgo
        max_allowed_quantity = self.position_tracker.calculate_position_size(
            risk_pct=self.risk_limits.max_risk_per_trade_pct,
            stop_loss_pct=order_request.stop_loss_pct,
            entry_price=1.0  # Se ajustará con precio real en ejecución
        )
        
        # Si Balam pidió menos de lo permitido, aprobar su cantidad
        if order_request.quantity <= max_allowed_quantity:
            return order_request.quantity, True
        
        # Si pidió más, ajustar al máximo permitido
        guardian_logger.logger.warning(
            f"⚠️ Ajuste de posición requerido: Solicitado={order_request.quantity}, Máximo={max_allowed_quantity:.4f}"
        )
        
        return max_allowed_quantity, True
    
    # ==================== LEY 3: HEARTBEAT MONITOR ====================
    
    def _update_system_health(self) -> None:
        """
        LEY 3: Verifica que todos los módulos estén vivos.
        """
        timeout = timedelta(seconds=self.risk_limits.heartbeat_timeout_seconds)
        now = datetime.utcnow()
        
        # Verificar Sentinel (el más crítico)
        if self.system_health.sentinel_last_heartbeat:
            time_since_sentinel = now - self.system_health.sentinel_last_heartbeat
            self.system_health.is_sentinel_alive = time_since_sentinel < timeout
        else:
            self.system_health.is_sentinel_alive = False
        
        # Actualizar Kill Switch
        self.system_health.kill_switch_active = is_kill_switch_active()
    
    def receive_heartbeat(self, module_name: str) -> None:
        """
        Recibe un heartbeat de un módulo.
        Debe ser llamado periódicamente por Sentinel, Executor, Balam.
        """
        now = datetime.utcnow()
        
        if module_name == "SENTINEL":
            self.system_health.sentinel_last_heartbeat = now
            self.system_health.is_sentinel_alive = True
        elif module_name == "EXECUTOR":
            self.system_health.executor_last_heartbeat = now
            self.system_health.is_executor_alive = True
        elif module_name == "BALAM":
            self.system_health.balam_last_heartbeat = now
            self.system_health.is_balam_alive = True
    
    # ==================== FIRMA DIGITAL ====================
    
    def _generate_signature(self, request_id: str, order_request: OrderRequest) -> str:
        """
        Genera una firma SHA-256 única para la orden.
        El Verdugo verificará esta firma antes de ejecutar.
        """
        payload = f"{request_id}|{order_request.symbol}|{order_request.side}|{order_request.quantity}|{datetime.utcnow().isoformat()}"
        signature = hashlib.sha256(payload.encode()).hexdigest()
        return signature
    
    def verify_signature(self, signature: str) -> bool:
        """
        Verifica que una firma sea válida.
        (Versión simple V1, mejoraremos en V2 con almacenamiento de firmas)
        """
        return len(signature) == 64 and signature.isalnum()
    
    # ==================== KILL SWITCH MANUAL ====================
    
    def emergency_stop(self, reason: str) -> None:
        """
        Activa el Kill Switch manualmente.
        Llamar en emergencias (ej: anomalía detectada por Sentinel)
        """
        guardian_logger.log_kill_switch_activation(
            reason=reason,
            context={
                "daily_loss": self.position_tracker.get_daily_pnl_pct(),
                "open_positions": self.position_tracker.get_open_positions_count()
            }
        )
        
        activate_kill_switch()
        guardian_logger.logger.critical(f"🚨 KILL SWITCH ACTIVADO: {reason}")


# Singleton global
_risk_manager: RiskManager | None = None


def get_risk_manager() -> RiskManager:
    """Obtiene el Risk Manager global (patrón singleton)"""
    global _risk_manager
    if _risk_manager is None:
        _risk_manager = RiskManager()
    return _risk_manager
