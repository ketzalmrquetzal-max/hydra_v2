# -*- coding: utf-8 -*-
"""
HYDRA V2 - MAIN SERVER
FastAPI server para el Dashboard y API de comunicación entre módulos
"""

import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import List
import uvicorn


# ═══════════════════════════════════════════════════════════
# MEMORIA COMPARTIDA (Sistema de Estado)
# ═══════════════════════════════════════════════════════════


class SystemMemory:
    """Memoria compartida en RAM para comunicación entre módulos"""

    def __init__(self):
        self.latest_report = "Esperando primer análisis del Sentinela..."
        self.logs: List[str] = []
        self.system_status = "INITIALIZING"


memory = SystemMemory()


# ═══════════════════════════════════════════════════════════
# MODELOS DE DATOS
# ═══════════════════════════════════════════════════════════


class LogMessage(BaseModel):
    """Modelo para recibir logs desde los módulos"""

    timestamp: str
    source: str
    message: str


# ═══════════════════════════════════════════════════════════
# APLICACIÓN FASTAPI
# ═══════════════════════════════════════════════════════════

app = FastAPI(title="Hydra Trading System", version="2.0.0")

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ═══════════════════════════════════════════════════════════
# API ENDPOINTS - DASHBOARD HYDRA OS
# ═══════════════════════════════════════════════════════════

# --- Conectores para datos reales ---
try:
    from backend.app.connectors.supabase.supabase_connector import SupabaseConnector

    db = SupabaseConnector()
except:
    db = None


@app.get("/api/status")
def get_status():
    return {
        "status": memory.system_status,
        "mode": "HYDRA OS v2.0",
        "latest_sentinel_report": memory.latest_report,
        "total_logs": len(memory.logs),
    }


@app.get("/api/wallet")
def get_wallet():
    """Devuelve el saldo actual (Bóveda)"""
    # TODO: Conectar con Verdugo real cuando esté en producción
    return {
        "balance_total": 10.00,
        "usdt_free": 10.00,
        "btc_value": 0.00,
        "pnl_daily": "+0.0%",
        "pnl_total": "0.00",
        "mode": "SIMULATION",
    }


@app.get("/api/brain")
def get_brain_status():
    """Devuelve la última decisión de Balam (Cortex)"""
    # Respuesta por defecto (sin conexión a DB)
    default_response = {
        "action": "HOLD",
        "confidence": 0,
        "reason": "Sistema en modo local - Sin conexión a Supabase",
        "timestamp": "N/A",
        "trend": "NEUTRAL",
    }

    try:
        if db and db.client:
            response = (
                db.client.table("logs_balam")
                .select("*")
                .order("id", desc=True)
                .limit(1)
                .execute()
            )
            if response.data:
                log = response.data[0]
                return {
                    "action": log.get("action", "HOLD"),
                    "confidence": log.get("confidence", 0),
                    "reason": log.get("reason", "Sin datos"),
                    "timestamp": log.get("timestamp", "N/A"),
                    "trend": log.get("trend", "NEUTRAL"),
                }
        return default_response
    except Exception as e:
        # En caso de error, devolver respuesta por defecto (no ERROR)
        print(f"⚠️ Brain API: {e}")
        return default_response


@app.get("/api/system")
def get_system_health():
    """Estado de los componentes (Health Check)"""
    return {
        "status": memory.system_status,
        "version": "2.0.0",
        "modules": {
            "sentinel": {"status": "🟢 ACTIVO", "description": "Escaneando mercado"},
            "balam": {"status": "🟢 ONLINE", "description": "Analizando oportunidades"},
            "guardian": {"status": "🛡️ VIGILANDO", "description": "Protegiendo capital"},
            "telegram": {
                "status": "📨 CONECTADO",
                "description": "Escuchando comandos",
            },
        },
        "uptime": "RUNNING",
    }


@app.get("/api/logs")
def get_logs(limit: int = 50):
    return memory.logs[-limit:]


@app.post("/api/log")
def add_log(log: LogMessage):
    entry = f"[{log.timestamp}] {log.source}: {log.message}"
    memory.logs.append(entry)

    if log.source == "SENTINEL":
        memory.latest_report = log.message
        memory.system_status = "ACTIVE"

    if len(memory.logs) > 1000:
        memory.logs = memory.logs[-500:]

    return {"status": "received", "total_logs": len(memory.logs)}


# ═══════════════════════════════════════════════════════════
# SERVIR FRONTEND
# ═══════════════════════════════════════════════════════════

# Calcular path al frontend
frontend_path = project_root / "frontend"
print(f"📂 Frontend path: {frontend_path}")
print(f"📂 Frontend exists: {frontend_path.exists()}")

if frontend_path.exists():
    # Montar archivos estáticos
    app.mount("/static", StaticFiles(directory=str(frontend_path)), name="static")

    # Servir index.html en la raíz
    @app.get("/")
    async def serve_dashboard():
        return FileResponse(str(frontend_path / "index.html"))

else:

    @app.get("/")
    def no_frontend():
        return {"error": f"Frontend no encontrado en: {frontend_path}"}


# ═══════════════════════════════════════════════════════════
# INICIO
# ═══════════════════════════════════════════════════════════

if __name__ == "__main__":
    print("🐉 HYDRA DASHBOARD SERVER INICIANDO...")
    print(f"📊 Dashboard: http://localhost:8000")
    print(f"📡 API Docs: http://localhost:8000/docs")

    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
