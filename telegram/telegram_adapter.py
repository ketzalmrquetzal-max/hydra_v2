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
                    saldo = self.verdugo.obtener_saldo()
                    mode_str = (
                        "🔓 Modo Simulado"
                        if hasattr(self.verdugo, "mode")
                        and self.verdugo.mode != "PRODUCTION"
                        else "🔐 Modo REAL"
                    )
                    msg = (
                        f"💰 **BÓVEDA DE HYDRA**\n"
                        f"Saldo Disponible: `${saldo:.2f} USDT`\n"
                        f"Estado: {mode_str}"
                    )
                else:
                    msg = "⚠️ Verdugo no disponible."
            except Exception as e:
                msg = f"❌ Error consultando banco: {e}"
            self.bot.reply_to(message, msg, parse_mode="Markdown")

        @self.bot.message_handler(commands=["info"])
        def system_info(message):
            state = os.getenv("ENV_STATE", "UNKNOWN")
            msg = (
                "🛡️ **ESTADO DEL SISTEMA**\n"
                "✅ Sentinela: ACTIVO\n"
                "✅ Balam V2: ONLINE\n"
                "✅ Verdugo: LISTO\n"
                "✅ Base de Datos: CONECTADA\n"
                f"🚀 Servidor: {state}"
            )
            self.bot.reply_to(message, msg)

        @self.bot.message_handler(commands=["visual"])
        def send_chart(message):
            self.bot.send_chat_action(message.chat.id, "upload_photo")
            try:
                if self.verdugo and self.verdugo.connector:
                    if hasattr(self.verdugo.connector, "get_latest_candles"):
                        candles = self.verdugo.connector.get_latest_candles()
                        foto = self.painter.generar_grafico(candles)
                        self.bot.send_photo(
                            message.chat.id,
                            foto,
                            caption="📊 **VISTA ACTUAL DE BALAM**",
                        )
                    else:
                        self.bot.reply_to(
                            message, "⚠️ El conector actual no soporta gráficos."
                        )
                else:
                    self.bot.reply_to(message, "⚠️ Verdugo desconectado.")
            except Exception as e:
                self.bot.reply_to(message, f"❌ No pude generar la foto: {e}")

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
