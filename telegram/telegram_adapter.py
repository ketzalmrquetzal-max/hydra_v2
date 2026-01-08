import os
import telebot
import threading
from dotenv import load_dotenv
from .chart_painter import ChartPainter

load_dotenv()


class TelegramAdapter:
    def __init__(self, verdugo_ref=None, supabase_ref=None):
        self.token = os.getenv("TELEGRAM_TOKEN")
        self.chat_id = os.getenv("TELEGRAM_CHAT_ID")
        if not self.token:
            print("⚠️ TELEGRAM_TOKEN no encontrado. El bot no funcionará.")
            self.bot = None
            return

        self.bot = telebot.TeleBot(self.token)

        # Referencias a otros módulos para consultar datos
        self.verdugo = verdugo_ref
        self.supabase = supabase_ref
        self.painter = ChartPainter()

        # Configurar los comandos
        self._setup_commands()

    def _setup_commands(self):
        """Define qué hace el bot cuando escribes /comando"""
        if not self.bot:
            return

        @self.bot.message_handler(commands=["start", "help"])
        def send_welcome(message):
            ayuda = (
                "🐉 **HYDRA COMMAND CENTER** 🐉\n\n"
                "/balam - Estado mental y última acción\n"
                "/balance - Saldo y PnL de la cartera\n"
                "/info - Estado de salud del sistema\n"
                "/visual - Gráfico en tiempo real (Binance view)"
            )
            self.bot.reply_to(message, ayuda, parse_mode="Markdown")

        @self.bot.message_handler(commands=["balam"])
        def check_balam(message):
            self.bot.send_chat_action(message.chat.id, "typing")
            try:
                if self.supabase:
                    data = (
                        self.supabase.client.table("logs_balam")
                        .select("*")
                        .order("id", desc=True)
                        .limit(1)
                        .execute()
                    )
                    if data.data:
                        log = data.data[0]
                        msg = (
                            f"🧠 **ESTADO DE BALAM**\n"
                            f"Última Decisión: `{log.get('action', 'UNKNOWN')}`\n"
                            f"Confianza: {log.get('confidence', 0)} pts\n"
                            f"Razón: _{log.get('reason', 'N/A')}_\n"
                            f"Hora: {log.get('timestamp', 'N/A')}"
                        )
                    else:
                        msg = "🧠 Balam está despierto, pero aún no ha escrito en su diario."
                else:
                    msg = "⚠️ No hay conexión a Memoria (Supabase)."
            except Exception as e:
                msg = f"❌ Error leyendo memoria: {e}"

            self.bot.reply_to(message, msg, parse_mode="Markdown")

        @self.bot.message_handler(commands=["balance"])
        def check_balance(message):
            self.bot.send_chat_action(message.chat.id, "typing")
            try:
                if self.verdugo:
                    # Usar nueva función para detalles completos
                    info = self.verdugo.obtener_info_cuenta()

                    # Soporte para estructura Mock y Real (Binance suele dar 'balances')
                    saldo_total = 0.0
                    saldo_usdt = 0.0

                    # Normalizar datos (Mock usa keys específicas, Binance usa otras)
                    if "totalWalletBalance" in info:  # MockExchange
                        saldo_total = float(info.get("totalWalletBalance", 0))
                        saldo_usdt = float(info.get("availableBalance", 0))
                        positions = info.get("positions", {})
                    else:  # Fallback genérico o Binance Real
                        saldo_usdt = self.verdugo.obtener_saldo()
                        saldo_total = saldo_usdt
                        positions = {}

                    mode_str = (
                        "🔓 Modo Simulado"
                        if hasattr(self.verdugo, "mode")
                        and self.verdugo.mode != "PRODUCTION"
                        else "🔐 Modo REAL"
                    )

                    msg = (
                        f"💰 **BÓVEDA DE HYDRA**\n"
                        f"💵 Saldo USDT: `${saldo_usdt:,.2f}`\n"
                        f"🏦 Patrimonio Total: `${saldo_total:,.2f}`\n"
                        f"Estado: {mode_str}\n\n"
                        f"🪙 **PORTAFOLIO:**\n"
                    )

                    activos_encontrados = False
                    for symbol, data in positions.items():
                        qty = float(data.get("qty", 0))
                        if qty > 0:
                            entry = float(data.get("entry_price", 0))
                            msg += f"• **{symbol}**: `{qty:.5f}` (Avg: ${entry:,.2f})\n"
                            activos_encontrados = True

                    if not activos_encontrados:
                        msg += "_Sin activos en cartera_"

                else:
                    msg = "⚠️ Verdugo no disponible."
            except Exception as e:
                print(f"Error en /balance: {e}")
                msg = f"❌ Error consultando banco: {e}"
            self.bot.reply_to(message, msg, parse_mode="Markdown")

        @self.bot.message_handler(commands=["visual"])
        def send_chart(message):
            """Genera y envía gráfico de velas actual"""
            self.bot.send_chat_action(message.chat.id, "upload_photo")
            try:
                if self.verdugo and self.verdugo.connector:
                    candles = []
                    # Detectar método correcto según conector (Mock o Real)
                    if hasattr(self.verdugo.connector, "get_latest_candles"):
                        # Intentar con argumentos (Binance) o sin ellos (Mock)
                        try:
                            candles = self.verdugo.connector.get_latest_candles(
                                symbol="BTCUSDT", interval="5m", limit=50
                            )
                        except TypeError:
                            candles = self.verdugo.connector.get_latest_candles(
                                symbol="BTCUSDT"
                            )

                    if candles:
                        foto = self.painter.generar_grafico(candles)
                        self.bot.send_photo(
                            message.chat.id,
                            foto,
                            caption="📊 **VISTA DE MERCADO (BTC/USDT)**",
                        )
                    else:
                        self.bot.reply_to(message, "⚠️ No pude obtener datos de velas.")
                else:
                    self.bot.reply_to(message, "⚠️ Verdugo desconectado.")
            except Exception as e:
                print(f"Error generando visual: {e}")
                self.bot.reply_to(message, f"❌ Error generando gráfico: {e}")

    def iniciar_escucha(self):
        """Inicia el bot en un hilo separado para no bloquear el trading"""
        if not self.bot:
            return

        hilo = threading.Thread(target=self.bot.infinity_polling)
        hilo.daemon = True
        hilo.start()
        print("📨 Telegram Listener activado en segundo plano.")

    def enviar_mensaje(self, mensaje):
        """Método clásico para enviar reportes"""
        if not self.bot:
            print(f"⚠️ Telegram no configurado. Mensaje no enviado: {mensaje}")
            return

        try:
            self.bot.send_message(self.chat_id, mensaje)
        except Exception as e:
            print(f"Error Telegram: {e}")
