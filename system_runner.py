# -*- coding: utf-8 -*-
"""
HYDRA V2 - SYSTEM RUNNER (El Director de Orquesta)
Script principal para ejecución 24/7 en la nube (Railway/Render)

Este archivo une todos los módulos y corre el loop infinito de trading.
"""

import time
import sys
import os
from datetime import datetime

# Agregar el directorio raíz al path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from dotenv import load_dotenv

load_dotenv()

# Importar módulos de Hydra
from backend.app.services.sentinel.sentinel_service import SentinelService
from backend.app.services.balam.balam_brain import BalamBrain
from backend.app.services.execution_service import Executioner
from telegram import TelegramAdapter
from backend.app.services.risk_manager import RiskManager
from backend.app.core.config import is_kill_switch_active, get_settings
from backend.app.domain.schemas.risk import OrderRequest, OrderSide


def main():
    """
    HYDRA V2 - LOOP PRINCIPAL DE TRADING

    Flujo cada ciclo:
    1. Sentinel escanea mercado (cada hora)
    2. Obtener velas actuales
    3. Balam evalúa oportunidad
    4. Guardian valida riesgo
    5. Verdugo ejecuta (si hay señal)
    6. Telegram notifica
    7. Repetir
    """

    print("\n" + "🐉" * 25)
    print("   HYDRA V2 - CLOUD DEPLOYMENT")
    print("   Sistema de Trading Automatizado")
    print("🐉" * 25)

    # ═══════════════════════════════════════════════════════════
    # FASE 1: INICIALIZACIÓN DE MÓDULOS
    # ═══════════════════════════════════════════════════════════

    try:
        print("\n📦 Inicializando módulos...")

        sentinel = SentinelService()
        print("   ✅ Sentinel (El Centinela)")

        balam = BalamBrain(enable_cloud_memory=True)
        print("   ✅ Balam (El Estratega)")

        guardian = RiskManager()
        print("   ✅ Guardian (El Protector)")

        verdugo = Executioner()
        print("   ✅ Executioner (El Verdugo)")

        telegram = TelegramAdapter(verdugo_ref=verdugo, supabase_ref=balam.memory)
        telegram.iniciar_escucha()
        print("   ✅ Telegram (Centro de Comando Interactivo)")

        # Notificar inicio
        telegram.enviar_mensaje(
            f"""
🚀 HYDRA V2 DESPLEGADO - INICIO PRUEBA 48H

Modulos activos:
- Sentinel (Analisis cada hora)
- Balam (Umbral: 50 puntos - Optimizado)
- Guardian
- Verdugo
- Telegram: COMANDOS ACTIVOS (/balam, /visual, /balance)

Capital inicial: $10 USDT
Objetivo: +$2 netos

Inicio: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Modo: {'PRODUCCION' if os.getenv('ENV_STATE') == 'PRODUCTION' else 'LIVE TEST'}
"""
        )

    except Exception as e:
        print(f"❌ Error fatal al iniciar: {e}")
        sys.exit(1)

    # ═══════════════════════════════════════════════════════════
    # FASE 2: CONFIGURACIÓN DE TIEMPOS
    # ═══════════════════════════════════════════════════════════

    CICLO_MINUTOS = 5  # Cada cuántos minutos evaluar
    SENTINEL_CADA_CICLOS = 12  # Sentinel cada hora (12 ciclos de 5 min)

    ciclo_actual = 0
    ultimo_reporte_sentinel = "Esperando primer escaneo..."
    total_trades = 0

    print(f"\n⏰ Configuración:")
    print(f"   Ciclo de evaluación: cada {CICLO_MINUTOS} minutos")
    print(f"   Sentinel: cada {SENTINEL_CADA_CICLOS * CICLO_MINUTOS} minutos")

    # ═══════════════════════════════════════════════════════════
    # FASE 3: LOOP INFINITO (CORAZÓN DEL SISTEMA)
    # ═══════════════════════════════════════════════════════════

    print("\n" + "=" * 50)
    print("   INICIANDO LOOP DE TRADING")
    print("=" * 50)

    while True:
        try:
            ciclo_actual += 1
            inicio_ciclo = time.time()

            print(f"\n{'='*50}")
            print(f"   CICLO #{ciclo_actual}")
            print(f"   {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"{'='*50}")

            # --- A. SENTINEL (Cada hora) ---
            if ciclo_actual % SENTINEL_CADA_CICLOS == 1 or ciclo_actual == 1:
                print("\n👁️ SENTINEL: Escaneando mercado...")
                try:
                    reporte = sentinel.generate_market_report()
                    ultimo_reporte_sentinel = reporte.get("analysis", "Sin análisis")
                    print(f"   ✅ Reporte generado")

                    # Notificar cada hora
                    telegram.enviar_mensaje(
                        f"""
REPORTE HORARIO - Sentinel

Sentiment: {reporte.get('sentiment_score', 0):.2f}
Fear/Greed: {reporte.get('fear_greed', 'N/A')}

{ultimo_reporte_sentinel[:400]}...
"""
                    )
                except Exception as e:
                    print(f"   ⚠️ Error en Sentinel: {e}")

            # --- B. OBTENER VELAS (Simuladas por ahora) ---
            print("\n📊 Obteniendo datos de mercado...")
            candles = _generar_velas_simuladas()
            precio_actual = candles[-1]["close"]
            print(f"   ✅ {len(candles)} velas | Precio: ${precio_actual:.2f}")

            # --- C. BALAM EVALÚA ---
            print("\n🧠 BALAM: Evaluando oportunidad...")
            expediente = balam.evaluate_market(
                "BTCUSDT", candles, ultimo_reporte_sentinel
            )

            accion = expediente.get("action", "HOLD")
            confianza = expediente.get("confidence", 0)
            razon = expediente.get("reason", "")
            adx = expediente.get("technical_data", {}).get("adx", 0)

            print(f"   📋 Decisión: {accion}")
            print(f"   🎯 Confianza: {confianza}%")
            print(f"   📈 ADX: {adx:.1f}")

            # --- D. GUARDIAN VALIDA ---
            print("\n🛡️ GUARDIAN: Validando...")
            guardian.receive_heartbeat("SYSTEM_RUNNER")

            if is_kill_switch_active():
                print("   ⛔ KILL SWITCH ACTIVO")
                telegram.enviar_mensaje("⛔ KILL SWITCH ACTIVO - Trading pausado")
                time.sleep(60)
                continue

            # --- E. VERDUGO EJECUTA (si hay señal) ---
            if accion in ["BUY", "SELL"] and confianza >= 50:
                print(f"\n🛡️ GUARDIÁN: Validando orden de {accion}...")

                # Construir solicitud formal para el Guardián
                settings = get_settings()
                saldo = verdugo.obtener_saldo()
                cantidad_estimada = (
                    saldo * settings.max_risk_per_trade_pct
                ) / precio_actual

                order_request = OrderRequest(
                    symbol="BTCUSDT",
                    side=OrderSide.BUY if accion == "BUY" else OrderSide.SELL,
                    quantity=round(cantidad_estimada, 6),
                    leverage=1,
                    stop_loss_pct=settings.stop_loss_pct,
                    take_profit_pct=settings.stop_loss_pct * 1.5,
                    confidence=confianza / 100,
                    reasoning=razon,
                )

                # Guardián evalúa y decide
                aprobacion = guardian.validate_order(order_request)

                if aprobacion.approved:
                    print(
                        f"✅ APROBADO por Guardián | Cantidad: {aprobacion.adjusted_quantity}"
                    )

                    expediente["quantity"] = aprobacion.adjusted_quantity
                    expediente["guardian_signature"] = aprobacion.signature

                    recibo = verdugo.ejecutar_orden_balam(expediente)

                    if recibo:
                        total_trades += 1
                        print(f"   ✅ TRADE #{total_trades} EJECUTADO")
                        telegram.enviar_mensaje(
                            f"🎯 TRADE EJECUTADO\n"
                            f"Acción: {accion}\n"
                            f"Cantidad: {aprobacion.adjusted_quantity}\n"
                            f"Confianza: {confianza}%"
                        )
                else:
                    print(f"⛔ RECHAZADO por Guardián: {aprobacion.rejection_reason}")
                    print(f"   Detalle: {aprobacion.rejection_details}")
            else:
                print(f"   ⏸️ Sin señal de trading")

            # --- F. ESTADÍSTICAS ---
            duracion = time.time() - inicio_ciclo
            print(f"\n⏱️ Ciclo completado en {duracion:.2f}s")
            print(f"📊 Trades totales: {total_trades}")

            # --- G. ESPERAR SIGUIENTE CICLO ---
            print(f"\n💤 Esperando {CICLO_MINUTOS} minutos...")
            time.sleep(CICLO_MINUTOS * 60)

        except KeyboardInterrupt:
            print("\n\n🛑 Detenido por usuario")
            telegram.enviar_mensaje("🛑 HYDRA detenido manualmente")
            break

        except Exception as e:
            print(f"\n⚠️ Error en ciclo: {e}")
            telegram.enviar_mensaje(f"⚠️ Error en Hydra: {str(e)[:100]}")
            time.sleep(60)  # Esperar 1 min antes de reintentar

    # Resumen final
    print("\n" + "=" * 50)
    print("   SESIÓN FINALIZADA")
    print(f"   Ciclos: {ciclo_actual}")
    print(f"   Trades: {total_trades}")
    print("=" * 50)


def _generar_velas_simuladas(count: int = 280) -> list:
    """
    Genera velas simuladas para testing.
    En producción real, usar API de Binance.
    """
    import random

    candles = []
    precio = 95000 + random.uniform(-2000, 2000)

    for i in range(count):
        cambio = random.uniform(-300, 350)
        precio = max(precio + cambio, 50000)

        candles.append(
            {
                "time": int(time.time()) - (count - i) * 60,
                "open": precio - random.uniform(0, 100),
                "high": precio + random.uniform(50, 200),
                "low": precio - random.uniform(50, 200),
                "close": precio,
                "volume": random.uniform(100, 1000),
            }
        )

    return candles


if __name__ == "__main__":
    main()
