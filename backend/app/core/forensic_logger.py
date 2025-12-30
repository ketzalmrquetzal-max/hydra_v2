# -*- coding: utf-8 -*-
"""
HYDRA V2 - FORENSIC LOGGER
Sistema de logging forense para auditabilidad total.
"Cada decisión queda registrada. Sabremos exactamente por qué se compró o vendió cada centavo."
"""

import logging
import json
from pathlib import Path
from datetime import datetime
from typing import Any
from backend.app.core.config import get_settings


class ForensicLogger:
    """
    Logger especializado para decisiones críticas del sistema.
    Todos los logs incluyen timestamp, contexto completo y son inmutables.
    """
    
    def __init__(self, module_name: str):
        self.module_name = module_name
        settings = get_settings()
        
        # Crear logger específico
        self.logger = logging.getLogger(f"HYDRA.{module_name}")
        self.logger.setLevel(logging.DEBUG)
        
        # Handler para archivo (logs rotativos)
        log_file = settings.logs_dir / f"{module_name.lower()}_{datetime.now().strftime('%Y%m%d')}.log"
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(logging.DEBUG)
        
        # Handler para consola
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        
        # Formato detallado
        formatter = logging.Formatter(
            '[%(asctime)s] [%(name)s] [%(levelname)s] %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)
        
        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)
    
    def log_decision(self, decision_type: str, data: dict[str, Any]) -> None:
        """
        Registra una decisión crítica con contexto completo.
        """
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "decision_type": decision_type,
            "module": self.module_name,
            **data
        }
        self.logger.info(f"DECISION: {json.dumps(log_entry, ensure_ascii=False)}")
    
    def log_guardian_approval(self, approved: bool, request_id: str, reason: str = None) -> None:
        """Log específico para decisiones del Guardián"""
        self.log_decision("GUARDIAN_APPROVAL", {
            "request_id": request_id,
            "approved": approved,
            "reason": reason
        })
    
    def log_guardian_rejection(self, request_id: str, reason: str, details: str) -> None:
        """Log específico para rechazos del Guardián"""
        self.logger.warning(f"REJECTION: {request_id} | Reason: {reason} | Details: {details}")
    
    def log_kill_switch_activation(self, reason: str, context: dict) -> None:
        """Log CRÍTICO: Kill Switch activado"""
        self.logger.critical(f"KILL_SWITCH_ACTIVATED | Reason: {reason} | Context: {json.dumps(context)}")
    
    def log_execution(self, order_id: str, status: str, details: dict) -> None:
        """Log de ejecución de órdenes"""
        self.log_decision("ORDER_EXECUTION", {
            "order_id": order_id,
            "status": status,
            **details
        })


# Crear instancias globales para cada módulo
guardian_logger = ForensicLogger("GUARDIAN")
executor_logger = ForensicLogger("EXECUTOR")
balam_logger = ForensicLogger("BALAM")
sentinel_logger = ForensicLogger("SENTINEL")
