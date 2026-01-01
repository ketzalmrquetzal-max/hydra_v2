# -*- coding: utf-8 -*-
"""
HYDRA V2 - SUPABASE CONNECTOR (La Caja Negra en la Nube)
Persistencia de decisiones de Balam en la nube

Configura en tu .env:
  SUPABASE_URL=https://tu-proyecto.supabase.co
  SUPABASE_KEY=tu-clave-anon-o-service-role
"""

import os
from datetime import datetime
from typing import Optional, Dict, Any
from dotenv import load_dotenv

load_dotenv()


class SupabaseConnector:
    """
    SUPABASE CONNECTOR - La Caja Negra Indestructible

    Guarda cada decisión de Balam en la nube para:
    - Auditoría completa
    - Análisis post-mortem
    - Backup automático
    - No perder datos si la PC se apaga
    """

    def __init__(self):
        print("☁️ Inicializando Supabase Connector...")

        self.url = os.getenv("SUPABASE_URL", "")
        self.key = os.getenv("SUPABASE_KEY", "")
        self.client = None
        self._connected = False

        if not self.url or not self.key:
            print("   ⚠️ Credenciales de Supabase no encontradas")
            print("   Configura SUPABASE_URL y SUPABASE_KEY en .env")
            print("   Modo: Solo memoria local (sin persistencia en nube)")
        else:
            try:
                from supabase import create_client, Client

                self.client: Client = create_client(self.url, self.key)
                self._connected = True
                print(f"   ✅ Conectado a Supabase: {self.url[:30]}...")
            except ImportError:
                print("   ⚠️ Librería 'supabase' no instalada")
                print("   Ejecuta: pip install supabase")
            except Exception as e:
                print(f"   ❌ Error conectando: {e}")

    @property
    def is_connected(self) -> bool:
        return self._connected and self.client is not None

    def guardar_log(self, expediente: dict) -> bool:
        """
        Guarda la decisión de Balam en la tabla logs_balam.

        Args:
            expediente: Diccionario con la decisión de Balam
                {symbol, action, confidence, reason, technical_data, ...}

        Returns:
            bool: True si se guardó correctamente
        """
        if not self.is_connected:
            print("   ⚠️ Supabase Offline - Guardando solo en memoria local")
            return False

        try:
            # Preparar datos para la tabla SQL
            data = {
                "symbol": expediente.get("symbol", "UNKNOWN"),
                "action": expediente.get("action", "HOLD"),
                "confidence": float(expediente.get("confidence", 0)),
                "reason": expediente.get("reason", "")[:500],  # Limitar longitud
                "technical_data": expediente.get("technical_data", {}),
            }

            # Agregar imagen de evidencia si existe
            if "evidence_chart_base64" in expediente:
                # Solo guardar si no es muy grande (max 500KB en base64)
                img = expediente["evidence_chart_base64"]
                if img and len(img) < 500000:
                    data["evidence_image"] = img

            # Insertar en tabla
            result = self.client.table("logs_balam").insert(data).execute()

            if result.data:
                print(
                    f"   💾 Expediente guardado en la Nube (ID: {result.data[0].get('id', '?')})"
                )
                return True
            else:
                print("   ⚠️ Inserción sin confirmación")
                return False

        except Exception as e:
            print(f"   ❌ Error escribiendo en Supabase: {e}")
            return False

    def obtener_historial(self, symbol: str = None, limit: int = 50) -> list:
        """
        Obtiene el historial de decisiones desde la nube.

        Args:
            symbol: Filtrar por símbolo (opcional)
            limit: Número máximo de registros

        Returns:
            list: Lista de expedientes históricos
        """
        if not self.is_connected:
            return []

        try:
            query = (
                self.client.table("logs_balam")
                .select("*")
                .limit(limit)
                .order("timestamp", desc=True)
            )

            if symbol:
                query = query.eq("symbol", symbol)

            result = query.execute()
            return result.data if result.data else []

        except Exception as e:
            print(f"   ❌ Error leyendo Supabase: {e}")
            return []

    def actualizar_pnl(self, log_id: int, pnl: float) -> bool:
        """
        Actualiza el PnL (ganancia/pérdida) de una operación.

        Args:
            log_id: ID del registro en Supabase
            pnl: Ganancia (+) o pérdida (-)

        Returns:
            bool: True si se actualizó correctamente
        """
        if not self.is_connected:
            return False

        try:
            self.client.table("logs_balam").update({"result_pnl": pnl}).eq(
                "id", log_id
            ).execute()

            print(f"   📊 PnL actualizado: ${pnl:+.2f}")
            return True

        except Exception as e:
            print(f"   ❌ Error actualizando PnL: {e}")
            return False

    def obtener_estadisticas(self, symbol: str = None) -> dict:
        """
        Calcula estadísticas de trading desde los logs.

        Returns:
            dict: {total_trades, wins, losses, win_rate, total_pnl}
        """
        if not self.is_connected:
            return {"error": "No conectado"}

        try:
            query = self.client.table("logs_balam").select(
                "action, confidence, result_pnl"
            )

            if symbol:
                query = query.eq("symbol", symbol)

            result = query.execute()
            logs = result.data if result.data else []

            # Calcular estadísticas
            trades = [l for l in logs if l["action"] in ["BUY", "SELL"]]
            total = len(trades)

            if total == 0:
                return {"total_trades": 0, "message": "Sin trades registrados"}

            pnls = [l.get("result_pnl", 0) or 0 for l in trades]
            wins = sum(1 for p in pnls if p > 0)
            losses = sum(1 for p in pnls if p < 0)

            return {
                "total_trades": total,
                "wins": wins,
                "losses": losses,
                "win_rate": (wins / total * 100) if total > 0 else 0,
                "total_pnl": sum(pnls),
                "avg_confidence": (
                    sum(l["confidence"] for l in trades) / total if total > 0 else 0
                ),
            }

    def save_state(self, state: dict) -> bool:
        """
        Guarda el estado del sistema para persistencia entre reinicios.
        """
        if not self.is_connected:
            return False
            
        try:
            data = {
                "id": "current_state",
                "data": state,
                "updated_at": datetime.utcnow().isoformat()
            }
            # Solo intentar si el cliente está listo
            self.client.table("system_state").upsert(data).execute()
            return True
        except Exception as e:
            # No detener el bot si la tabla no existe, solo avisar
            if "relation \"public.system_state\" does not exist" in str(e):
                print("   ⚠️ Tabla 'system_state' no encontrada en Supabase. Persistencia desactivada.")
            else:
                print(f"   ❌ Error guardando estado: {e}")
            return False

    def load_state(self) -> Optional[dict]:
        """
        Carga el último estado guardado del sistema.
        """
        if not self.is_connected:
            return None
            
        try:
            result = self.client.table("system_state").select("data").eq("id", "current_state").execute()
            if result.data:
                return result.data[0].get("data")
            return None
        except Exception as e:
            if "relation \"public.system_state\" does not exist" in str(e):
                print("   ⚠️ No se puede cargar estado: tabla 'system_state' no existe.")
            return None


# Test directo
if __name__ == "__main__":
    print("\n🧪 TEST SUPABASE CONNECTOR")
    print("=" * 50)

    connector = SupabaseConnector()

    if connector.is_connected:
        print("\n✅ Conexión exitosa")

        # Test de inserción
        test_expediente = {
            "symbol": "BTCUSDT",
            "action": "BUY",
            "confidence": 85.5,
            "reason": "Test desde Python - RSI bajo + Tendencia alcista",
            "technical_data": {"rsi": 28.5, "price": 95000.0, "ema_50": 94000.0},
        }

        print("\n📝 Intentando guardar log de prueba...")
        success = connector.guardar_log(test_expediente)

        if success:
            print("✅ Log guardado correctamente")

            # Leer historial
            print("\n📜 Últimos 5 logs:")
            historial = connector.obtener_historial(limit=5)
            for log in historial:
                print(
                    f"   [{log.get('timestamp', '?')}] {log.get('action')} - {log.get('confidence')}%"
                )

    else:
        print("\n⚠️ No conectado - Configura las credenciales en .env")

    print("\n" + "=" * 50)
