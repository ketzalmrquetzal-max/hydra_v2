# -*- coding: utf-8 -*-
"""
HYDRA V2 - BINANCE TESTNET CONNECTOR
Conecta con el Futures Testnet de Binance (dinero ficticio, API real)

Para obtener API Keys de Testnet:
1. Ve a: https://testnet.binancefuture.com/
2. Haz login con GitHub
3. Generate API Key
4. Añadelas a tu .env:
   BINANCE_TESTNET_API_KEY=xxx
   BINANCE_TESTNET_SECRET=xxx
"""

import os
import time
import hmac
import hashlib
import requests
from datetime import datetime
from urllib.parse import urlencode
from dotenv import load_dotenv

load_dotenv()


class BinanceTestnetConnector:
    """
    BINANCE FUTURES TESTNET CONNECTOR

    Permite operar en el testnet de Binance con dinero ficticio.
    API idéntica a producción, pero sin riesgo real.
    """

    # URLs del Testnet
    BASE_URL = "https://testnet.binancefuture.com"
    WS_URL = "wss://stream.binancefuture.com"

    def __init__(self):
        print("🔌 Inicializando Binance Testnet Connector...")

        # Usar keys específicas de testnet o fallback a las normales
        self.api_key = os.getenv(
            "BINANCE_TESTNET_API_KEY", os.getenv("BINANCE_API_KEY", "")
        )
        self.api_secret = os.getenv(
            "BINANCE_TESTNET_SECRET", os.getenv("BINANCE_SECRET_KEY", "")
        )

        if not self.api_key or not self.api_secret:
            print("   ⚠️ WARNING: No se encontraron API Keys de Testnet")
            print(
                "   Configura BINANCE_TESTNET_API_KEY y BINANCE_TESTNET_SECRET en .env"
            )
            self._connected = False
        else:
            print(f"   ✅ API Key encontrada: {self.api_key[:8]}...")
            self._connected = True

        self.session = requests.Session()
        self.session.headers.update({"X-MBX-APIKEY": self.api_key})

    def _generate_signature(self, params: dict) -> str:
        """Genera firma HMAC SHA256 para la petición"""
        query_string = urlencode(params)
        signature = hmac.new(
            self.api_secret.encode("utf-8"),
            query_string.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()
        return signature

    def _request(
        self, method: str, endpoint: str, params: dict = None, signed: bool = False
    ) -> dict:
        """
        Ejecuta una petición a la API.

        Args:
            method: GET, POST, DELETE
            endpoint: /fapi/v1/...
            params: Parámetros de la petición
            signed: Si requiere firma (endpoints privados)
        """
        url = f"{self.BASE_URL}{endpoint}"
        params = params or {}

        if signed:
            params["timestamp"] = int(time.time() * 1000)
            params["signature"] = self._generate_signature(params)

        try:
            if method == "GET":
                response = self.session.get(url, params=params, timeout=10)
            elif method == "POST":
                response = self.session.post(url, params=params, timeout=10)
            elif method == "DELETE":
                response = self.session.delete(url, params=params, timeout=10)
            else:
                raise ValueError(f"Método no soportado: {method}")

            data = response.json()

            if response.status_code != 200:
                error_msg = data.get("msg", "Error desconocido")
                raise Exception(f"API Error {response.status_code}: {error_msg}")

            return data

        except requests.exceptions.RequestException as e:
            raise Exception(f"Error de conexión: {str(e)}")

    def ping(self) -> bool:
        """Verifica conexión con el servidor"""
        try:
            self._request("GET", "/fapi/v1/ping")
            return True
        except:
            return False

    def get_server_time(self) -> datetime:
        """Obtiene hora del servidor"""
        data = self._request("GET", "/fapi/v1/time")
        return datetime.fromtimestamp(data["serverTime"] / 1000)

    def get_account_balance(self) -> dict:
        """
        Obtiene el saldo de la cuenta.

        Returns:
            dict: {totalWalletBalance, availableBalance, positions}
        """
        data = self._request("GET", "/fapi/v2/account", signed=True)

        # Buscar balance USDT
        usdt_balance = 0
        for asset in data.get("assets", []):
            if asset["asset"] == "USDT":
                usdt_balance = float(asset["availableBalance"])
                break

        return {
            "totalWalletBalance": str(data.get("totalWalletBalance", 0)),
            "availableBalance": str(usdt_balance),
            "positions": data.get("positions", []),
        }

    def get_position(self, symbol: str) -> dict:
        """Obtiene información de una posición específica"""
        data = self._request(
            "GET", "/fapi/v2/positionRisk", params={"symbol": symbol}, signed=True
        )

        if data:
            return data[0]
        return {}

    def get_klines(self, symbol: str, interval: str = "1m", limit: int = 250) -> list:
        """
        Obtiene velas históricas.

        Args:
            symbol: Par de trading (BTCUSDT)
            interval: 1m, 5m, 15m, 1h, 4h, 1d
            limit: Número de velas (max 1500)
        """
        params = {"symbol": symbol, "interval": interval, "limit": limit}

        data = self._request("GET", "/fapi/v1/klines", params=params)

        # Convertir a formato estándar
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

    def get_ticker_price(self, symbol: str) -> float:
        """Obtiene precio actual"""
        data = self._request("GET", "/fapi/v1/ticker/price", params={"symbol": symbol})
        return float(data["price"])

    def place_order(
        self,
        symbol: str,
        side: str,
        quantity: float,
        order_type: str = "MARKET",
        price: float = None,
    ) -> dict:
        """
        Coloca una orden.

        Args:
            symbol: Par (BTCUSDT)
            side: BUY o SELL
            quantity: Cantidad
            order_type: MARKET o LIMIT
            price: Precio límite (solo para LIMIT)
        """
        params = {
            "symbol": symbol,
            "side": side.upper(),
            "type": order_type,
            "quantity": quantity,
        }

        if order_type == "LIMIT" and price:
            params["price"] = price
            params["timeInForce"] = "GTC"

        print(f"📡 [TESTNET] Enviando orden: {side} {quantity} {symbol}...")

        data = self._request("POST", "/fapi/v1/order", params=params, signed=True)

        print(f"✅ [TESTNET] Orden ejecutada: ID {data.get('orderId')}")

        return {
            "orderId": str(data.get("orderId")),
            "symbol": data.get("symbol"),
            "status": data.get("status"),
            "price": data.get("avgPrice", data.get("price", "0")),
            "origQty": data.get("origQty"),
            "executedQty": data.get("executedQty"),
            "side": data.get("side"),
            "type": data.get("type"),
        }

    def cancel_order(self, symbol: str, order_id: str) -> dict:
        """Cancela una orden"""
        params = {"symbol": symbol, "orderId": order_id}
        return self._request("DELETE", "/fapi/v1/order", params=params, signed=True)

    def cancel_all_orders(self, symbol: str) -> dict:
        """Cancela todas las órdenes de un símbolo"""
        return self._request(
            "DELETE", "/fapi/v1/allOpenOrders", params={"symbol": symbol}, signed=True
        )

    def set_leverage(self, symbol: str, leverage: int) -> dict:
        """Configura el apalancamiento"""
        params = {"symbol": symbol, "leverage": leverage}
        return self._request("POST", "/fapi/v1/leverage", params=params, signed=True)

    def set_margin_type(self, symbol: str, margin_type: str = "ISOLATED") -> dict:
        """Configura el tipo de margen (ISOLATED o CROSSED)"""
        params = {"symbol": symbol, "marginType": margin_type}
        return self._request("POST", "/fapi/v1/marginType", params=params, signed=True)


# Test directo
if __name__ == "__main__":
    print("\n🧪 TEST BINANCE TESTNET CONNECTOR")
    print("=" * 50)

    connector = BinanceTestnetConnector()

    # Test ping
    print("\n1. Ping al servidor...")
    if connector.ping():
        print("   ✅ Servidor responde")
    else:
        print("   ❌ Sin conexión")

    # Test tiempo
    print("\n2. Hora del servidor...")
    try:
        server_time = connector.get_server_time()
        print(f"   ✅ {server_time}")
    except Exception as e:
        print(f"   ⚠️ {e}")

    # Test precio
    print("\n3. Precio BTC/USDT...")
    try:
        price = connector.get_ticker_price("BTCUSDT")
        print(f"   ✅ ${price:.2f}")
    except Exception as e:
        print(f"   ⚠️ {e}")

    # Test balance (requiere API key válida)
    print("\n4. Balance de cuenta...")
    try:
        balance = connector.get_account_balance()
        print(f"   ✅ Saldo: ${float(balance['availableBalance']):.2f} USDT")
    except Exception as e:
        print(f"   ⚠️ {e}")

    print("\n" + "=" * 50)
    print("Test completado")
