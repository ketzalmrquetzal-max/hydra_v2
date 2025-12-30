# -*- coding: utf-8 -*-
"""
HYDRA V2 - BALAM BRAIN (El Cerebro Estratega)
Núcleo de decisiones que combina análisis técnico con contexto del Sentinela
"""

import sys
import os

sys.path.insert(
    0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", ".."))
)

from .technical_analyst import TechnicalAnalyst
from .evidence_generator import EvidenceGenerator

# Importar memoria en la nube (opcional)
try:
    from backend.app.connectors.supabase.supabase_connector import (
        SupabaseConnector,
    )

    SUPABASE_AVAILABLE = True
except ImportError:
    SUPABASE_AVAILABLE = False


class BalamBrain:
    """
    BALAM - El Cerebro Estratega de Hydra

    Filosofía: "Francotirador" - Solo dispara con >90% de probabilidad

    Proceso de Pensamiento:
    1. Analizar técnicamente (RSI, EMAs, Bollinger)
    2. Cruzar con contexto del Sentinela (sentimiento del mercado)
    3. Generar expediente forense con evidencia visual
    4. Emitir decisión con nivel de confianza
    """

    def __init__(self, enable_cloud_memory: bool = True):
        print("🧠 Inicializando BALAM - El Cerebro Estratega...")
        self.analyst = TechnicalAnalyst()
        self.artist = EvidenceGenerator()

        # Inicializar memoria en la nube
        self.memory = None
        if enable_cloud_memory and SUPABASE_AVAILABLE:
            try:
                self.memory = SupabaseConnector()
            except Exception as e:
                print(f"   ⚠️ Memoria en nube no disponible: {e}")

        print("   ✅ Componentes cargados")

    def evaluate_market(self, symbol: str, candles: list, sentinel_report: str) -> dict:
        """
        EL PROCESO DE PENSAMIENTO DE BALAM

        Args:
            symbol: Par de trading (ej: BTCUSDT)
            candles: Lista de velas OHLCV
            sentinel_report: Reporte del Sentinela con contexto de mercado

        Returns:
            dict: Expediente forense con decisión, confianza, razón y evidencia
        """

        # ═══════════════════════════════════════════════════════════
        # 🔥 MODO TEST: FORZAR DISPARO (ELIMINAR DESPUÉS DEL TEST)
        # ═══════════════════════════════════════════════════════════
        TEST_MODE = False  # 🚨 Modo normal - análisis real

        if TEST_MODE:
            print("🔥🔥🔥 MODO TEST ACTIVO - FORZANDO BUY 100% 🔥🔥🔥")
            return {
                "symbol": symbol,
                "action": "BUY",
                "confidence": 100,
                "reason": "🔥 TEST MODE: Señal forzada para probar disparo del sistema",
                "trend": "TEST",
                "is_lateral_market": False,
                "technical_data": {
                    "rsi": 100,
                    "price": 100000,
                    "ema_50": 99000,
                    "ema_200": 98000,
                    "bb_upper": 102000,
                    "bb_lower": 98000,
                    "adx": 50,
                },
                "sentinel_context": "TEST MODE ACTIVO",
            }

        # ═══════════════════════════════════════════════════════════
        # FASE 1: ANÁLISIS TÉCNICO
        # ═══════════════════════════════════════════════════════════

        try:
            data = self.analyst.analyze_candles(candles)
            full_df = self.analyst.get_full_analysis(candles)
        except Exception as e:
            return {
                "symbol": symbol,
                "action": "ERROR",
                "confidence": 0,
                "reason": f"Error en análisis técnico: {str(e)}",
                "technical_data": {},
                "sentinel_context": sentinel_report[:50] if sentinel_report else "N/A",
            }

        # Extraer indicadores clave
        rsi = data["RSI"]
        precio = data["close"]
        ema_50 = data["EMA_50"]
        ema_200 = data.get("EMA_200", ema_50)  # Fallback si no hay suficientes datos

        # Bollinger Bands
        bb_upper = data.get("BBU_20_2.0", precio * 1.02)
        bb_lower = data.get("BBL_20_2.0", precio * 0.98)
        bb_mid = data.get("BBM_20_2.0", precio)

        # MACD
        macd = data.get("MACD_12_26_9", 0)
        macd_signal = data.get("MACDs_12_26_9", 0)

        # ADX (Filtro Anti-Whipsaw)
        adx = data.get("ADX_14", 25)  # Default 25 si no existe

        # ═══════════════════════════════════════════════════════════
        # FASE 1.5: FILTRO ANTI-WHIPSAW (ADX)
        # ═══════════════════════════════════════════════════════════

        # Si ADX < 10, el mercado está lateral (zona de peligro)
        ADX_THRESHOLD = 10
        is_lateral_market = adx < ADX_THRESHOLD

        # ═══════════════════════════════════════════════════════════
        # FASE 2: DETERMINACIÓN DE TENDENCIA
        # ═══════════════════════════════════════════════════════════

        tendencia = "LATERAL"
        if precio > ema_50 > ema_200:
            tendencia = "ALCISTA"
        elif precio < ema_50 < ema_200:
            tendencia = "BAJISTA"

        # ═══════════════════════════════════════════════════════════
        # FASE 3: LÓGICA DE DECISIÓN "FRANCOTIRADOR"
        # ═══════════════════════════════════════════════════════════

        decision = "HOLD"
        confidence = 0
        razon = "Esperando alineación perfecta..."

        # --- CASO DE COMPRA (LONG) ---
        # Estrategia: Rebote en Tendencia Alcista
        # Regla 1: Tendencia Alcista (Precio arriba de EMA 50 y EMA 200)
        # Regla 2: RSI < 35 (Sobreventa temporal)
        # Regla 3: Precio cerca de banda inferior de Bollinger

        if tendencia == "ALCISTA" and rsi < 35:
            decision = "BUY"
            confidence = 80
            razon = f"Pullback en tendencia alcista + RSI sobreventa ({rsi:.1f})"

            # Bonus: Precio tocando banda inferior
            if precio <= bb_lower * 1.01:
                confidence += 10
                razon += " + Tocando Bollinger inferior"

            # Bonus: MACD cruzando hacia arriba
            if macd > macd_signal and macd < 0:
                confidence += 5
                razon += " + MACD alcista"

        # Regla alternativa: RSI extremadamente bajo en cualquier tendencia
        elif rsi < 25 and precio > ema_200:
            decision = "BUY"
            confidence = 75
            razon = f"RSI extremo ({rsi:.1f}) + Arriba de EMA200"

        # --- CASO DE VENTA (SHORT) ---
        # Regla 1: Tendencia Bajista
        # Regla 2: RSI > 65 (Sobrecompra temporal)

        elif tendencia == "BAJISTA" and rsi > 65:
            decision = "SELL"
            confidence = 80
            razon = f"Rally en tendencia bajista + RSI sobrecompra ({rsi:.1f})"

            # Bonus: Precio tocando banda superior
            if precio >= bb_upper * 0.99:
                confidence += 10
                razon += " + Tocando Bollinger superior"

            # Bonus: MACD cruzando hacia abajo
            if macd < macd_signal and macd > 0:
                confidence += 5
                razon += " + MACD bajista"

        # Regla alternativa: RSI extremadamente alto
        elif rsi > 75 and precio < ema_200:
            decision = "SELL"
            confidence = 75
            razon = f"RSI extremo ({rsi:.1f}) + Debajo de EMA200"

        # ═══════════════════════════════════════════════════════════
        # FASE 4: AJUSTE POR CONTEXTO DEL SENTINELA
        # ═══════════════════════════════════════════════════════════

        # Convertir sentinel_report a string si es dict
        if isinstance(sentinel_report, dict):
            sentinel_report = str(sentinel_report.get("summary", sentinel_report))

        sentinel_upper = sentinel_report.upper() if sentinel_report else ""

        # Detectar sentimiento del Sentinela
        sentimiento_negativo = any(
            word in sentinel_upper
            for word in [
                "PÁNICO",
                "PANICO",
                "MIEDO",
                "FEAR",
                "-0.8",
                "-0.9",
                "-1.0",
                "EXTREME FEAR",
            ]
        )
        sentimiento_positivo = any(
            word in sentinel_upper
            for word in [
                "EUFORIA",
                "CODICIA",
                "GREED",
                "0.8",
                "0.9",
                "1.0",
                "EXTREME GREED",
            ]
        )

        if decision == "BUY":
            if sentimiento_negativo:
                # Comprar cuando hay pánico (contrarian) si tendencia es alcista
                confidence += 10
                razon += " + Comprando en pánico (contrarian)"
            elif sentimiento_positivo:
                # Peligroso comprar en euforia
                confidence -= 25
                if confidence < 60:
                    decision = "HOLD"
                    razon = "Cancelado: Euforia detectada, riesgo alto"

        elif decision == "SELL":
            if sentimiento_positivo:
                # Vender en euforia (contrarian)
                confidence += 10
                razon += " + Vendiendo en euforia (contrarian)"
            elif sentimiento_negativo:
                # Peligroso vender en pánico (ya bajó)
                confidence -= 20
                if confidence < 60:
                    decision = "HOLD"
                    razon = "Cancelado: Pánico ya instalado, tarde para vender"

        # ═══════════════════════════════════════════════════════════
        # FASE 4.5: FILTRO ANTI-WHIPSAW (MERCADO LATERAL)
        # ═══════════════════════════════════════════════════════════

        if decision != "HOLD" and is_lateral_market:
            original_decision = decision
            decision = "HOLD"
            confidence = 40
            razon = f"BLOQUEADO: Mercado lateral detectado (ADX {adx:.1f} < {ADX_THRESHOLD}). Riesgo de whipsaw. Señal original: {original_decision}"

        # ═══════════════════════════════════════════════════════════
        # FASE 5: UMBRAL MÍNIMO DE CONFIANZA
        # ═══════════════════════════════════════════════════════════

        if decision != "HOLD" and confidence < 50:
            decision = "HOLD"
            razon = (
                f"Confianza insuficiente ({confidence}%), manteniendo postura neutral"
            )
            confidence = 50

        # ═══════════════════════════════════════════════════════════
        # FASE 6: GENERAR EVIDENCIA VISUAL
        # ═══════════════════════════════════════════════════════════

        expediente = {
            "symbol": symbol,
            "action": decision,
            "confidence": min(confidence, 100),  # Cap at 100
            "reason": razon,
            "trend": tendencia,
            "is_lateral_market": is_lateral_market,
            "technical_data": {
                "rsi": round(rsi, 2),
                "price": round(precio, 2),
                "ema_50": round(ema_50, 2),
                "ema_200": round(ema_200, 2),
                "bb_upper": round(bb_upper, 2),
                "bb_lower": round(bb_lower, 2),
                "adx": round(adx, 2),
            },
            "sentinel_context": (
                sentinel_report[:100] + "..."
                if len(sentinel_report) > 100
                else sentinel_report
            ),
        }

        # Generar gráfico de evidencia
        try:
            evidence_chart = self.artist.create_chart(full_df, symbol, expediente)
            expediente["evidence_chart_base64"] = evidence_chart
        except Exception as e:
            expediente["evidence_chart_base64"] = None
            expediente["evidence_error"] = str(e)

        # ═══════════════════════════════════════════════════════════
        # FASE 7: GUARDAR EN LA NUBE (SI ES BUY O SELL)
        # ═══════════════════════════════════════════════════════════

        if (decision in ["BUY", "SELL"] or confidence > 40) and self.memory is not None:
            try:
                self.memory.guardar_log(expediente)
            except Exception as e:
                print(f"   ⚠️ Error guardando en nube: {e}")

        return expediente

    def quick_evaluate(
        self, symbol: str, candles: list, sentinel_report: str = ""
    ) -> str:
        """
        Evaluación rápida que retorna solo la acción recomendada.

        Returns:
            str: "BUY", "SELL", or "HOLD"
        """
        result = self.evaluate_market(symbol, candles, sentinel_report)
        return result["action"]


# Test directo
if __name__ == "__main__":
    import random

    print("\n🧪 TEST DIRECTO DE BALAM BRAIN")
    print("=" * 50)

    balam = BalamBrain()

    # Generar velas simuladas (tendencia alcista con caída)
    candles = []
    precio = 50000
    for i in range(250):
        if i < 200:
            precio += random.uniform(-50, 150)  # Tendencia alcista
        else:
            precio -= random.uniform(100, 300)  # Caída para bajar RSI

        candles.append(
            {
                "time": i,
                "open": precio,
                "high": precio + random.uniform(10, 50),
                "low": precio - random.uniform(10, 50),
                "close": precio + random.uniform(-20, 20),
                "volume": random.uniform(100, 1000),
            }
        )

    sentinel_fake = "SENTIMIENTO: -0.8 (PÁNICO) - Miedo extremo por caída de Bitcoin"

    print("\n📊 Evaluando escenario: Pullback en tendencia alcista + Pánico")
    result = balam.evaluate_market("BTCUSDT", candles, sentinel_fake)

    print(f"\n🎯 DECISIÓN: {result['action']}")
    print(f"📈 CONFIANZA: {result['confidence']}%")
    print(f"📝 RAZÓN: {result['reason']}")
    print(f"🔄 TENDENCIA: {result['trend']}")
    print(f"📊 RSI: {result['technical_data']['rsi']}")
    print(f"💰 PRECIO: ${result['technical_data']['price']:.2f}")
