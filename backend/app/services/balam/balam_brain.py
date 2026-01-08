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
from backend.app.services.sentinel.gemini_http_client import GeminiHTTPClient
from backend.app.core.config import get_settings

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

        # Inicializar cliente AI
        settings = get_settings()
        self.ai_client = GeminiHTTPClient(api_key=settings.gemini_api_key)

        # Inicializar memoria
        self.memory = None
        if enable_cloud_memory and SUPABASE_AVAILABLE:
            try:
                self.memory = SupabaseConnector()
            except Exception as e:
                print(f"   ⚠️ Memoria en nube no disponible: {e}")

        print("   ✅ Componentes cargados")

    def _analyze_with_gemini(
        self, symbol: str, technical_data: dict, sentinel_report: str, trend: str
    ) -> dict:
        """
        Consulta a Gemini para obtener una decisión de trading basada en datos.
        """
        prompt = f"""
ACTÚA COMO: Un Trader Institucional de Elite (Balam).
TAREA: Analizar datos técnicos y de sentimiento para decidir una operación en {symbol}.

DATOS TÉCNICOS:
- Precio: ${technical_data.get('price')}
- Tendencia: {trend}
- RSI: {technical_data.get('rsi')} (Sobreventa < 30, Sobrecompra > 70)
- Bandas Bollinger: {technical_data.get('bb_lower')} (Inf) - {technical_data.get('bb_upper')} (Sup)
- ADX: {technical_data.get('adx')} (Fuerza de la tendencia)

SENTIMIENTO DE MERCADO (Del Centinela):
"{sentinel_report}"

TU MISIÓN:
Decidir si COMPRAR (BUY), VENDER (SELL) o ESPERAR (HOLD).
- Sé agresivo si la tendencia acompaña.
- Sé cauteloso si hay contradicciones.
- Tu confianza debe ser precisa (0-100%).

RESPONDE ÚNICAMENTE CON ESTE JSON (SIN MARKDOWN):
{{
    "action": "BUY/SELL/HOLD",
    "confidence": 85,
    "reason": "Explicación breve y técnica de por qué tomaste esta decisión."
}}
"""
        try:
            response = self.ai_client.generate_content(prompt, temperature=0.2)
            # Limpiar respuesta para obtener JSON puro
            json_str = response.replace("```json", "").replace("```", "").strip()
            import json

            return json.loads(json_str)
        except Exception as e:
            print(f"   ⚠️ Error en cerebro AI: {e}")
            return {
                "action": "HOLD",
                "confidence": 0,
                "reason": "Fallo en IA, manteniendo posición.",
            }

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
        # FASE 3: CONSULTA A LA INTELIGENCIA ARTIFICIAL (NUEVO CEREBRO)
        # ═══════════════════════════════════════════════════════════

        technical_summary = {
            "price": precio,
            "rsi": rsi,
            "adx": adx,
            "ema_50": ema_50,
            "bb_upper": bb_upper,
            "bb_lower": bb_lower,
            "is_lateral": is_lateral_market,
        }

        print("   🤖 Consultando a Gemini (Balam AI)...")
        # Aseguramos que sentinel_report sea string
        report_str = (
            str(sentinel_report) if sentinel_report else "Sin reporte disponible"
        )

        ai_decision = self._analyze_with_gemini(
            symbol, technical_summary, report_str, tendencia
        )

        decision = ai_decision.get("action", "HOLD").upper()
        confidence = ai_decision.get("confidence", 0)
        razon = ai_decision.get("reason", "Decisión calculada por AI")

        # ═══════════════════════════════════════════════════════════
        # FASE 4: FILTRO DE SEGURIDAD (RESPALDO HUMANO)
        # ═══════════════════════════════════════════════════════════

        # Umbral mínimo duro (Hard Floor)
        # Incluso si la AI dice "Compra segura", si la confianza es < 40%, no disparamos.
        if decision != "HOLD" and confidence < 40:
            decision = "HOLD"
            razon += " (Cancelado por confianza < 40%)"
            confidence = 40

        # ═══════════════════════════════════════════════════════════
        # FASE 5: GENERAR EVIDENCIA VISUAL
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
        # FASE 6: GUARDAR EN LA NUBE (SI ES BUY O SELL)
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
