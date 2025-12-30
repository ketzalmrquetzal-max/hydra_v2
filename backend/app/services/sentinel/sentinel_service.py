# -*- coding: utf-8 -*-
"""
HYDRA V2 - SENTINEL SERVICE (El Centinela Completo)
Orquesta la recolección de inteligencia y el análisis de sentimiento
"""

import time
import requests
from datetime import datetime
from .news_fetcher import NewsFetcher
from .sentiment_brain import SentimentBrain
from backend.app.core.forensic_logger import sentinel_logger


class SentinelService:
    """
    EL CENTINELA - Sistema de Inteligencia de Mercado

    Componentes:
    - Los Ojos (NewsFetcher): RSS Feeds + Fear & Greed Index
    - El Cerebro (SentimentBrain): Gemini AI para análisis

    Función:
    Generar informes de situación para que Balam tome mejores decisiones.
    """

    def __init__(self):
        print("👁️ Inicializando Sistemas del Centinela...")

        try:
            self.eyes = NewsFetcher()
            print("   ✅ Ojos activados (News Fetcher)")

            self.brain = SentimentBrain()
            print("   ✅ Cerebro activado (Gemini AI)")

            sentinel_logger.logger.info("Centinela completamente operacional")

        except Exception as e:
            sentinel_logger.logger.error(f"Error inicializando Centinela: {e}")
            raise

    def generate_market_report(self) -> dict:
        """
        Ejecuta el ciclo completo de inteligencia.

        Proceso:
        1. MIRAR: Recolectar datos (RSS + Fear & Greed)
        2. PENSAR: Analizar con Gemini AI
        3. REPORTAR: Devolver informe estructurado

        Returns:
            dict: {
                "timestamp": datetime,
                "fear_greed": str,
                "headlines": str,
                "analysis": str,
                "sentiment_score": float,
                "elapsed_seconds": float
            }
        """
        sentinel_logger.logger.info("🔍 Iniciando generación de informe de mercado")
        print("\n" + "=" * 60)
        print("📡 CENTINELA: Escaneando el horizonte...")
        print("=" * 60)

        start_time = time.time()

        # ═══════════════════════════════════════════════════════
        # FASE 1: RECOLECCIÓN (Los Ojos)
        # ═══════════════════════════════════════════════════════

        print("\n[1/3] 👁️ Recolectando inteligencia (RSS Feeds & F&G Index)...")

        # Obtener datos en paralelo conceptual (en V2 usaremos asyncio)
        fear_data = self.eyes.get_fear_and_greed()
        print(f"      ├─ {fear_data}")

        news_data = self.eyes.get_latest_headlines(limit=6)
        headline_count = len([h for h in news_data.split("\n") if h.strip()])
        print(f"      └─ Titulares capturados: {headline_count}")

        # ═══════════════════════════════════════════════════════
        # FASE 2: ANÁLISIS (El Cerebro)
        # ═══════════════════════════════════════════════════════

        print("\n[2/3] 🧠 Procesando datos con Gemini 1.5 Flash...")

        analysis_report = self.brain.analyze_context(news_data, fear_data)
        sentiment_score = self.brain.parse_sentiment_score(analysis_report)

        print(
            f"      └─ Sentiment Score: {sentiment_score:+.2f} ({self._describe_sentiment(sentiment_score)})"
        )

        # ═══════════════════════════════════════════════════════
        # FASE 3: COMPILACIÓN DEL REPORTE
        # ═══════════════════════════════════════════════════════

        elapsed = time.time() - start_time

        report = {
            "timestamp": datetime.utcnow(),
            "fear_greed": fear_data,
            "headlines": news_data,
            "analysis": analysis_report,
            "sentiment_score": sentiment_score,
            "elapsed_seconds": elapsed,
        }

        print(f"\n[3/3] ✅ Informe generado en {elapsed:.2f} segundos.")

        # Log forense
        sentinel_logger.log_decision(
            "MARKET_REPORT_GENERATED",
            {
                "sentiment_score": sentiment_score,
                "elapsed_seconds": elapsed,
                "headline_count": headline_count,
            },
        )

        # Enviar al Dashboard
        self._enviar_a_dashboard(analysis_report)

        return report

    def _enviar_a_dashboard(self, mensaje: str):
        """
        Envía logs al Dashboard para visualización en tiempo real.

        Args:
            mensaje: Texto del reporte o log a enviar
        """
        try:
            payload = {
                "timestamp": datetime.now().strftime("%H:%M:%S"),
                "source": "SENTINEL",
                "message": mensaje,
            }
            # Enviar al servidor FastAPI local
            requests.post("http://localhost:8000/api/log", json=payload, timeout=1)
        except requests.exceptions.ConnectionError:
            # Dashboard no está corriendo, ignorar silenciosamente
            pass
        except Exception as e:
            print(f"⚠️ No se pudo enviar al dashboard: {e}")

    def _describe_sentiment(self, score: float) -> str:
        """Convierte el score numérico a descripción legible"""
        if score <= -0.7:
            return "Pánico Extremo"
        elif score <= -0.3:
            return "Miedo"
        elif score <= 0.3:
            return "Neutral"
        elif score <= 0.7:
            return "Optimismo"
        else:
            return "Euforia"

    def print_formatted_report(self, report: dict) -> None:
        """
        Imprime el reporte en formato legible para humanos.

        Args:
            report: Diccionario retornado por generate_market_report()
        """
        print("\n" + "=" * 60)
        print("📊 INFORME DE SITUACIÓN DEL CENTINELA")
        print("=" * 60)
        print(f"⏰ Timestamp: {report['timestamp'].strftime('%Y-%m-%d %H:%M:%S UTC')}")
        print(f"⚡ Tiempo de generación: {report['elapsed_seconds']:.2f}s")
        print("\n" + "-" * 60)
        print("ANÁLISIS DE IA:")
        print("-" * 60)
        print(report["analysis"])
        print("-" * 60)
        print(f"\n📈 Sentiment Score: {report['sentiment_score']:+.2f}")
        headlines_list = report["headlines"].split("\n")
        count = len([h for h in headlines_list if h.strip()])
        print(f"📰 Headlines analizados: {count}")
        print("=" * 60 + "\n")


# ═══════════════════════════════════════════════════════════════
# BLOQUE DE EJECUCIÓN DIRECTA PARA PRUEBAS
# ═══════════════════════════════════════════════════════════════

if __name__ == "__main__":
    try:
        # Inicializar el Centinela
        sentinel = SentinelService()

        # Generar informe
        informe = sentinel.generate_market_report()

        # Mostrar en formato bonito
        sentinel.print_formatted_report(informe)

        print("✅ Test del Centinela completado exitosamente\n")

    except Exception as e:
        print(f"\n❌ Error en el test del Centinela: {e}\n")
        import traceback

        traceback.print_exc()
