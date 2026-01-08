# -*- coding: utf-8 -*-
"""
HYDRA V2 - MOCK EXCHANGE (El Simulador Fantasma)
Simula Binance sin usar dinero real - Para pruebas seguras
"""

import time
import random
import uuid
import requests
from datetime import datetime


class MockExchange:
    """
    EL SIMULADOR FANTASMA

    Finge ser Binance para permitir pruebas seguras:
    - Acepta órdenes de compra/venta
    - Mantiene un saldo ficticio
    - Retorna recibos idénticos a los reales
    - Tu dinero real permanece intacto
    """

    def __init__(self, initial_balance: float = 40.0):
        """
        Inicializa el simulador con dinero de Monopoly.

        Args:
            initial_balance: Saldo inicial en USDT (default: $40 - capital real del usuario)
        """
        print("💰 EXCHANGE CONECTADO (Modo Simulación)")
        print(f"   💵 Saldo disponible: ${initial_balance:.2f} USDT")

        self.usdt_balance = initial_balance
        self.initial_balance = initial_balance
        self.positions = {}  # {symbol: quantity}
        self.order_history = []
        self.trade_count = 0

        # Precios simulados (cercanos al real)
        self.simulated_prices = {
            "BTCUSDT": 95000.0,
            "ETHUSDT": 3500.0,
            "SOLUSDT": 180.0,
            "BNBUSDT": 700.0,
        }

    def _get_simulated_price(self, symbol: str) -> float:
        """Obtiene el PRECIO REAL de Binance (o simulado si falla)"""
        try:
            url = f"https://api.binance.com/api/v3/ticker/price?symbol={symbol}"
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                price = float(response.json()["price"])
                self.simulated_prices[symbol] = price  # Cache para fallback
                return price
        except Exception as e:
            print(f"⚠️ Error fetching price: {e}")

        # Fallback a simulación con ruido
        base_price = self.simulated_prices.get(symbol, 95000.0)
        noise = base_price * random.uniform(-0.005, 0.005)
        return base_price + noise

    def get_account_balance(self) -> dict:
        """
        Simula pedir el saldo a Binance.

        Returns:
            dict: Estructura idéntica a la respuesta de Binance
        """
        time.sleep(0.05)  # Simular latencia de red

        # Calcular valor de posiciones
        total_position_value = 0
        for symbol, data in self.positions.items():
            qty = data["qty"]
            price = self._get_simulated_price(symbol)
            total_position_value += qty * price

        total_balance = self.usdt_balance + total_position_value

        return {
            "totalWalletBalance": str(total_balance),
            "availableBalance": str(self.usdt_balance),
            "positions": self.positions.copy(),
            "unrealizedProfit": str(
                total_position_value - (self.initial_balance - self.usdt_balance)
            ),
        }

    def place_order(
        self, symbol: str, side: str, quantity: float, price: float = None
    ) -> dict:
        """
        Simula la ejecución de una orden.

        Args:
            symbol: Par de trading (ej: BTCUSDT)
            side: "BUY" o "SELL"
            quantity: Cantidad a operar
            price: Precio límite (opcional, si None es orden de mercado)

        Returns:
            dict: Recibo de orden idéntico al formato de Binance

        Raises:
            Exception: Si no hay fondos suficientes
        """
        print(f"📡 [MOCK] Recibiendo orden: {side} {quantity} {symbol}...")
        time.sleep(0.1)  # Simular latencia

        # Si no hay precio (Market Order), usar precio simulado
        if price is None:
            price = self._get_simulated_price(symbol)

        costo = quantity * price
        self.trade_count += 1
        order_id = str(uuid.uuid4())[:8]

        # === VALIDACIÓN Y EJECUCIÓN ===

        if side.upper() == "BUY":
            # Verificar fondos
            if costo > self.usdt_balance:
                raise Exception(
                    f"❌ [MOCK] Saldo insuficiente. Necesitas ${costo:.2f}, tienes ${self.usdt_balance:.2f}"
                )

            # Ejecutar compra
            self.usdt_balance -= costo

            # Actualizar posición y precio promedio de entrada
            current_pos = self.positions.get(symbol, {"qty": 0.0, "entry_price": 0.0})
            total_qty = current_pos["qty"] + quantity

            # Nuevo precio promedio ponderado (con validación para evitar división por cero)
            if total_qty > 0:
                avg_price = (
                    (current_pos["qty"] * current_pos["entry_price"])
                    + (quantity * price)
                ) / total_qty
            else:
                avg_price = (
                    price  # Si no hay cantidad previa, el precio promedio es el actual
                )

            self.positions[symbol] = {"qty": total_qty, "entry_price": avg_price}

            print(f"✅ [MOCK] COMPRA EXITOSA")
            print(f"   Cantidad: {quantity} {symbol.replace('USDT', '')}")
            print(f"   Precio: ${price:.2f}")
            print(f"   Costo Total: ${costo:.2f}")
            print(f"   Saldo restante: ${self.usdt_balance:.2f} USDT")

        elif side.upper() == "SELL":
            # Verificar posición
            current_pos = self.positions.get(symbol, {"qty": 0.0, "entry_price": 0.0})
            current_qty = current_pos["qty"]

            if quantity > current_qty:
                raise Exception(
                    f"❌ [MOCK] Posición insuficiente. Tienes {current_qty}, intentas vender {quantity}"
                )

            # --- CÁLCULO DE PNL REAL (1x) ---
            entry_price = current_pos["entry_price"]
            raw_pnl = (price - entry_price) * quantity

            # Retorno del capital original + ganancia/pérdida
            capital_original_retornado = entry_price * quantity
            retorno_total = capital_original_retornado + raw_pnl

            self.usdt_balance += retorno_total

            # Actualizar cantidad restante
            self.positions[symbol]["qty"] -= quantity

            # Limpiar posiciones vacías
            if self.positions[symbol]["qty"] <= 0:
                del self.positions[symbol]

            print(f"✅ [MOCK] VENTA EXITOSA")
            print(f"   Cantidad: {quantity} {symbol.replace('USDT', '')}")
            print(f"   Precio Entrada: ${entry_price:.2f}")
            print(f"   Precio Salida: ${price:.2f}")
            print(f"   PnL Real: ${raw_pnl:.2f}")
            print(f"   Saldo actual: ${self.usdt_balance:.2f} USDT")

        else:
            raise Exception(f"❌ [MOCK] Lado de orden inválido: {side}")

        # Crear recibo (formato idéntico a Binance)
        recibo = {
            "orderId": order_id,
            "symbol": symbol,
            "status": "FILLED",
            "price": str(price),
            "origQty": str(quantity),
            "executedQty": str(quantity),
            "side": side.upper(),
            "type": "MARKET" if price is None else "LIMIT",
            "time": int(datetime.now().timestamp() * 1000),
            "updateTime": int(datetime.now().timestamp() * 1000),
        }

        # Guardar en historial
        self.order_history.append(recibo)

        return recibo

    def get_position(self, symbol: str) -> dict:
        """Obtiene información de una posición específica"""
        pos_data = self.positions.get(symbol, {"qty": 0.0, "entry_price": 0.0})
        qty = pos_data["qty"]
        entry_price = pos_data["entry_price"]

        current_price = self._get_simulated_price(symbol)

        # Calcular PnL no realizado (1x)
        if entry_price > 0:
            unrealized_pnl = (current_price - entry_price) * qty
        else:
            unrealized_pnl = 0.0

        return {
            "symbol": symbol,
            "positionAmt": str(qty),
            "entryPrice": str(entry_price),
            "markPrice": str(current_price),
            "unRealizedProfit": str(unrealized_pnl),
            "leverage": "1",
        }

    def get_order_history(self) -> list:
        """Retorna el historial de órdenes"""
        return self.order_history

    def get_latest_candles(self, symbol="BTCUSDT"):
        """Devuelve VELAS REALES de Binance para el gráfico"""
        try:
            # Klines: [time, open, high, low, close, vol, ...]
            url = f"https://api.binance.com/api/v3/klines?symbol={symbol}&interval=1h&limit=50"
            response = requests.get(url, timeout=5)

            if response.status_code == 200:
                raw_candles = response.json()
                candles = []
                for c in raw_candles:
                    candles.append(
                        {
                            "time": c[0],
                            "open": float(c[1]),
                            "high": float(c[2]),
                            "low": float(c[3]),
                            "close": float(c[4]),
                            "volume": float(c[5]),
                        }
                    )
                return candles
        except Exception as e:
            print(f"⚠️ Error fetching klines: {e}")

        # Fallback: Velas de emergencia
        import random

        candles = []
        precio = self.simulated_prices.get(symbol, 95000.0)
        for i in range(50):
            precio += random.uniform(-100, 100)
            candles.append(
                {
                    "time": i,
                    "open": precio,
                    "high": precio + 50,
                    "low": precio - 50,
                    "close": precio + 20,
                    "volume": 1000,
                }
            )
        return candles

    def reset(self):
        """Reinicia el simulador a su estado inicial"""
        self.usdt_balance = self.initial_balance
        self.positions = {}
        self.order_history = []
        self.trade_count = 0
        print("🔄 [MOCK] Simulador reiniciado")


# Test directo
if __name__ == "__main__":
    print("\n🧪 TEST DEL MOCK EXCHANGE")
    print("=" * 50)

    exchange = MockExchange(initial_balance=1000.0)

    # Ver saldo inicial
    balance = exchange.get_account_balance()
    print(f"\n💰 Saldo disponible: ${float(balance['availableBalance']):.2f}")

    # Comprar BTC
    print("\n--- Comprando 0.005 BTC ---")
    recibo = exchange.place_order("BTCUSDT", "BUY", 0.005)
    print(f"📝 Orden ID: {recibo['orderId']}")

    # Ver saldo después
    balance = exchange.get_account_balance()
    print(f"\n💰 Saldo después de compra: ${float(balance['availableBalance']):.2f}")
    print(f"📊 Posiciones: {balance['positions']}")

    # Vender BTC
    print("\n--- Vendiendo 0.005 BTC ---")
    recibo2 = exchange.place_order("BTCUSDT", "SELL", 0.005)

    # Ver saldo final
    balance = exchange.get_account_balance()
    print(f"\n💰 Saldo final: ${float(balance['availableBalance']):.2f}")

    print("\n✅ Mock Exchange funcionando correctamente!")
