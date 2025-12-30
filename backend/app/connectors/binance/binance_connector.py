# -*- coding: utf-8 -*-
"""
HYDRA V2 - REAL BINANCE CONNECTOR
Conexión real a Binance Spot API para trading en vivo.

⚠️ ADVERTENCIA: Este módulo ejecuta trades con DINERO REAL.
"""

import os
import time
import hmac
import hashlib
from urllib.parse import urlencode
import requests
from dotenv import load_dotenv

load_dotenv()


class BinanceConnector:
    """
    Conector Real para Binance Spot API.

    Usa autenticación HMAC-SHA256 para órdenes firmadas.

    Variables de entorno requeridas:
    - BINANCE_API_KEY
    - BINANCE_SECRET_KEY
    - BINANCE_TESTNET (opcional, "true" para usar testnet)
    """

    def __init__(self):
        self.api_key = os.getenv("BINANCE_API_KEY")
        self.secret_key = os.getenv("BINANCE_SECRET_KEY")

        # Detectar si usar testnet
        use_testnet = os.getenv("BINANCE_TESTNET", "false").lower() == "true"

        if use_testnet:
            self.base_url = "https://testnet.binance.vision"
            print("🧪 Binance TESTNET conectado")
        else:
            self.base_url = "https://api.binance.com"
            print("💰 Binance REAL conectado")

        if not self.api_key or not self.secret_key:
            raise ValueError("❌ BINANCE_API_KEY y BINANCE_SECRET_KEY son requeridas")

        # Verificar conexión
        self._verify_connection()

    def _verify_connection(self):
        """Verifica que las credenciales sean válidas"""
        try:
            balance = self.get_account_balance()
            usdt = float(balance.get("availableBalance", 0))
            print(f"   💵 Saldo disponible: ${usdt:.2f} USDT")
        except Exception as e:
            print(f"   ⚠️ Error verificando conexión: {e}")

    def _generate_signature(self, params: dict) -> str:
        """Genera firma HMAC-SHA256 para requests autenticados"""
        query_string = urlencode(params)
        signature = hmac.new(
            self.secret_key.encode("utf-8"),
            query_string.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()
        return signature

    def _signed_request(self, method: str, endpoint: str, params: dict = None) -> dict:
        """Hace un request firmado a la API"""
        if params is None:
            params = {}

        # Agregar timestamp
        params["timestamp"] = int(time.time() * 1000)

        # Generar firma
        params["signature"] = self._generate_signature(params)

        # Headers
        headers = {"X-MBX-APIKEY": self.api_key}

        url = f"{self.base_url}{endpoint}"

        if method == "GET":
            response = requests.get(url, params=params, headers=headers, timeout=10)
        elif method == "POST":
            response = requests.post(url, params=params, headers=headers, timeout=10)
        elif method == "DELETE":
            response = requests.delete(url, params=params, headers=headers, timeout=10)
        else:
            raise ValueError(f"Método no soportado: {method}")

        # Manejar errores
        if response.status_code != 200:
            error_msg = response.json().get("msg", response.text)
            raise Exception(f"Binance Error {response.status_code}: {error_msg}")

        return response.json()

    def _public_request(self, endpoint: str, params: dict = None) -> dict:
        """Request público (sin firma)"""
        url = f"{self.base_url}{endpoint}"
        response = requests.get(url, params=params, timeout=10)
        return response.json()

    def get_account_balance(self) -> dict:
        """Obtiene el balance de la cuenta Spot"""
        try:
            account = self._signed_request("GET", "/api/v3/account")

            # Buscar USDT
            usdt_balance = 0.0
            btc_balance = 0.0

            for asset in account.get("balances", []):
                if asset["asset"] == "USDT":
                    usdt_balance = float(asset["free"])
                elif asset["asset"] == "BTC":
                    btc_balance = float(asset["free"])

            return {
                "availableBalance": usdt_balance,
                "usdt": usdt_balance,
                "btc": btc_balance,
                "positions": {},
            }
        except Exception as e:
            print(f"❌ Error obteniendo balance: {e}")
            return {"availableBalance": 0, "usdt": 0, "btc": 0}

    def get_current_price(self, symbol: str = "BTCUSDT") -> float:
        """Obtiene el precio actual de un símbolo"""
        try:
            data = self._public_request("/api/v3/ticker/price", {"symbol": symbol})
            return float(data["price"])
        except Exception as e:
            print(f"❌ Error obteniendo precio: {e}")
            return 0.0

    def place_order(self, symbol: str, side: str, quantity: float) -> dict:
        """
        Coloca una orden de mercado.

        Args:
            symbol: Par de trading (ej: BTCUSDT)
            side: "BUY" o "SELL"
            quantity: Cantidad a comprar/vender

        Returns:
            dict: Recibo de la orden
        """
        print(f"\n💥 EJECUTANDO ORDEN REAL: {side} {quantity} {symbol}")

        params = {
            "symbol": symbol,
            "side": side.upper(),
            "type": "MARKET",
            "quantity": quantity,
        }

        try:
            result = self._signed_request("POST", "/api/v3/order", params)

            # Formatear respuesta
            executed_qty = float(result.get("executedQty", 0))
            cummulative_quote = float(result.get("cummulativeQuoteQty", 0))
            avg_price = cummulative_quote / executed_qty if executed_qty > 0 else 0

            order_receipt = {
                "orderId": result["orderId"],
                "symbol": result["symbol"],
                "side": result["side"],
                "status": result["status"],
                "executedQty": executed_qty,
                "price": avg_price,
                "transactTime": result.get("transactTime"),
            }

            print(f"   ✅ Orden ejecutada: ID {order_receipt['orderId']}")
            print(f"   💰 Precio promedio: ${avg_price:.2f}")

            return order_receipt

        except Exception as e:
            print(f"   ❌ Error ejecutando orden: {e}")
            raise

    def get_latest_candles(
        self, symbol: str = "BTCUSDT", interval: str = "1h", limit: int = 50
    ) -> list:
        """Obtiene velas históricas"""
        try:
            data = self._public_request(
                "/api/v3/klines",
                {"symbol": symbol, "interval": interval, "limit": limit},
            )

            candles = []
            for k in data:
                candles.append(
                    {
                        "time": k[0],
                        "open": float(k[1]),
                        "high": float(k[2]),
                        "low": float(k[3]),
                        "close": float(k[4]),
                        "volume": float(k[5]),
                    }
                )

            return candles
        except Exception as e:
            print(f"❌ Error obteniendo velas: {e}")
            return []

    def get_position(self, symbol: str = "BTCUSDT") -> dict:
        """Obtiene información de posición (para Spot, es el balance del asset)"""
        balance = self.get_account_balance()
        return {
            "symbol": symbol,
            "qty": balance.get("btc", 0),
            "entry_price": 0,  # Spot no tiene entry price nativo
            "leverage": 1,
        }


# Test directo
if __name__ == "__main__":
    print("\n🧪 TEST BINANCE REAL CONNECTOR")
    print("=" * 50)

    try:
        connector = BinanceConnector()

        print("\n📊 Balance:")
        balance = connector.get_account_balance()
        print(f"   USDT: ${balance['usdt']:.2f}")
        print(f"   BTC: {balance['btc']:.8f}")

        print("\n📈 Precio BTC:")
        price = connector.get_current_price()
        print(f"   ${price:.2f}")

        print("\n✅ Conexión verificada correctamente")

    except Exception as e:
        print(f"\n❌ Error: {e}")
