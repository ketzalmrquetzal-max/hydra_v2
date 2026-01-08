# -*- coding: utf-8 -*-
"""
HYDRA V2 - EXECUTION SERVICE (El Verdugo)
Ejecuta las órdenes de Balam - Decide si usar Mock o Real
"""

import sys
import os

sys.path.insert(
    0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
)

from dotenv import load_dotenv
from backend.app.connectors.binance.mock_exchange import MockExchange
from backend.app.core.forensic_logger import ForensicLogger

# Importar conector real (opcional)
try:
    from backend.app.connectors.binance.binance_connector import BinanceConnector

    REAL_BINANCE_AVAILABLE = True
except ImportError:
    REAL_BINANCE_AVAILABLE = False

load_dotenv()


class Executioner:
    """
    EL VERDUGO - Ejecutor de Órdenes de Hydra

    Responsabilidades:
    - Recibir decisiones de Balam
    - Validar con el Guardian (pendiente)
    - Ejecutar en Mock o Real según ENV_STATE
    - Registrar cada disparo en logs forenses
    """

    def __init__(self):
        print("\n⚔️ INICIANDO EL VERDUGO...")

        self.mode = os.getenv("ENV_STATE", "DEVELOPMENT")
        self.logger = ForensicLogger("EXECUTIONER")

        # Determinar si usar conector real o mock
        use_real = os.getenv("USE_REAL_BINANCE", "false").lower() == "true"

        if use_real and REAL_BINANCE_AVAILABLE:
            print("💰 MODO REAL: Conectado a Binance con dinero real")
            print("⚠️ ¡CUIDADO! Las órdenes se ejecutarán en el mercado real")
            self.connector = BinanceConnector()
            self._is_mock = False
        elif self.mode == "PRODUCTION":
            print("⚠️ MODO PRODUCCIÓN pero sin USE_REAL_BINANCE=true")
            print("🛡️ Usando Mock por seguridad...")
            self.connector = MockExchange()
            self._is_mock = True
        else:
            print("💰 MODO DESARROLLO: Usando MockExchange")
            self.connector = MockExchange()
            self._is_mock = True

        self.logger.log_decision(
            "EXECUTIONER_INITIALIZED", {"mode": self.mode, "is_mock": self._is_mock}
        )

        print(f"   {'🧪 Mock' if self._is_mock else '💰 REAL'} Exchange conectado")
        print("   ✅ Verdugo armado y listo")

    def obtener_saldo(self) -> float:
        """
        Obtiene el saldo disponible para operar.

        Returns:
            float: Saldo en USDT
        """
        try:
            data = self.connector.get_account_balance()
            saldo = float(data["availableBalance"])
            return saldo
        except Exception as e:
            self.logger.log_decision("BALANCE_READ_ERROR", {"error": str(e)})
            print(f"❌ Error leyendo saldo: {e}")
            return 0.0

    def obtener_info_cuenta(self) -> dict:
        """Obtiene detalles completos de la cuenta (saldo + posiciones)"""
        try:
            return self.connector.get_account_info()
        except Exception as e:
            print(f"❌ Error leyendo info cuenta: {e}")
            return {}

    def ejecutar_disparo(self, orden: dict) -> dict:
        """
        Recibe la orden de Balam y aprieta el gatillo.

        Args:
            orden: Diccionario con la decisión de Balam
                   {symbol, action, confidence, quantity (opcional)}

        Returns:
            dict: Recibo de la orden o None si falló
        """
        try:
            action = orden.get("action", "HOLD").upper()
            symbol = orden.get("symbol", "BTCUSDT")
            confidence = orden.get("confidence", 0)
            quantity = orden.get("quantity", 0.001)

            # Validar que sea una acción ejecutable
            if action not in ["BUY", "SELL"]:
                print(f"⏸️ VERDUGO: Acción '{action}' no requiere ejecución")
                return None

            # Validar confianza mínima (el Guardian debería hacer esto)
            if confidence < 50:
                print(f"🛡️ VERDUGO: Rechazado - Confianza muy baja ({confidence}%)")
                self.logger.log_decision(
                    "ORDER_REJECTED_LOW_CONFIDENCE",
                    {"action": action, "confidence": confidence, "required": 50},
                )
                return None

            print(f"\n⚔️ VERDUGO: Procesando orden de {action}...")
            print(f"   📊 Symbol: {symbol}")
            print(f"   📈 Cantidad: {quantity}")
            print(f"   🎯 Confianza: {confidence}%")

            # Log pre-ejecución
            self.logger.log_decision(
                "ORDER_EXECUTING",
                {
                    "symbol": symbol,
                    "side": action,
                    "quantity": quantity,
                    "confidence": confidence,
                    "is_mock": self._is_mock,
                },
            )

            # ¡DISPARO!
            recibo = self.connector.place_order(
                symbol=symbol, side=action, quantity=quantity
            )

            # Log post-ejecución
            self.logger.log_decision(
                "ORDER_EXECUTED",
                {
                    "order_id": recibo["orderId"],
                    "symbol": symbol,
                    "side": action,
                    "price": recibo["price"],
                    "quantity": recibo["executedQty"],
                    "status": recibo["status"],
                },
            )

            print(f"\n🧾 RECIBO FISCAL:")
            print(f"   ID: {recibo['orderId']}")
            print(f"   Status: {recibo['status']}")
            print(f"   Precio: ${float(recibo['price']):.2f}")

            return recibo

        except Exception as e:
            self.logger.log_decision("EXECUTION_FAILED", {"error": str(e)})
            print(f"💀 FALLO DE EJECUCIÓN: {e}")
            return None

    def ejecutar_orden_balam(self, expediente: dict) -> dict:
        """
        Wrapper específico para expedientes de Balam.
        Extrae la información necesaria del expediente forense.

        Args:
            expediente: Expediente completo de Balam

        Returns:
            dict: Recibo de la orden
        """
        orden = {
            "symbol": expediente.get("symbol", "BTCUSDT"),
            "action": expediente.get("action", "HOLD"),
            "confidence": expediente.get("confidence", 0),
            "quantity": expediente.get("quantity", 0.001),
        }

        return self.ejecutar_disparo(orden)

    def get_positions(self) -> dict:
        """Obtiene las posiciones actuales"""
        return self.connector.get_account_balance().get("positions", {})


# Test directo
if __name__ == "__main__":
    print("\n🧪 TEST DEL EXECUTIONER")
    print("=" * 50)

    verdugo = Executioner()

    # Ver saldo
    saldo = verdugo.obtener_saldo()
    print(f"\n💰 Saldo disponible: ${saldo:.2f} USDT")

    # Simular orden de Balam
    orden_test = {
        "symbol": "BTCUSDT",
        "action": "BUY",
        "confidence": 85,
        "quantity": 0.005,
    }

    print("\n📝 Orden de prueba:", orden_test)
    recibo = verdugo.ejecutar_disparo(orden_test)

    if recibo:
        print("\n✅ Orden ejecutada exitosamente")

    # Ver saldo final
    saldo_final = verdugo.obtener_saldo()
    print(f"\n💰 Saldo final: ${saldo_final:.2f} USDT")
