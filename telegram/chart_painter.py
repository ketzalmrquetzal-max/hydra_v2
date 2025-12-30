import matplotlib

matplotlib.use("Agg")  # Importante para servidores sin pantalla (Nube)
import matplotlib.pyplot as plt
import io
import pandas as pd


class ChartPainter:
    def generar_grafico(self, candles):
        """
        Recibe velas, dibuja un gráfico estilo Binance Dark Mode
        y devuelve la imagen en memoria (bytes).
        """
        # 1. Preparar Datos
        df = pd.DataFrame(
            candles, columns=["time", "open", "high", "low", "close", "volume"]
        )
        cols = ["open", "high", "low", "close", "volume"]
        df[cols] = df[cols].apply(pd.to_numeric)

        # Calcular indicadores (Pandas puro para compatibilidad)
        df["EMA_50"] = df["close"].ewm(span=50, adjust=False).mean()
        df["EMA_200"] = df["close"].ewm(span=200, adjust=False).mean()

        # Bollinger Bands (20, 2)
        df["SMA_20"] = df["close"].rolling(window=20).mean()
        df["STD_20"] = df["close"].rolling(window=20).std()
        df["BBU_20_2.0"] = df["SMA_20"] + (df["STD_20"] * 2)
        df["BBL_20_2.0"] = df["SMA_20"] - (df["STD_20"] * 2)

        # Tomar las últimas 50 velas para que se vea bien
        subset = df.tail(50).reset_index(drop=True)

        # 2. Configurar Estilo "Hacker/Binance"
        plt.style.use("dark_background")
        fig, ax = plt.subplots(figsize=(10, 6))
        ax.set_facecolor("#0b0e11")  # Fondo Binance
        fig.patch.set_facecolor("#0b0e11")

        # 3. Dibujar Velas (Truco rápido con matplotlib)
        # Verde si sube, Rojo si baja
        up = subset[subset.close >= subset.open]
        down = subset[subset.close < subset.open]

        # Mechas
        ax.vlines(up.index, up.low, up.high, color="#0ecb81", linewidth=1)
        ax.vlines(down.index, down.low, down.high, color="#f6465d", linewidth=1)
        # Cuerpos
        ax.vlines(up.index, up.open, up.close, color="#0ecb81", linewidth=6)
        ax.vlines(down.index, down.open, down.close, color="#f6465d", linewidth=6)

        # 4. Dibujar Indicadores
        ax.plot(subset["EMA_50"], color="cyan", label="EMA 50", linewidth=1.5)
        ax.plot(subset["EMA_200"], color="orange", label="EMA 200", linewidth=1.5)

        # Bandas de Bollinger (Sombreado)
        ax.fill_between(
            subset.index,
            subset["BBL_20_2.0"],
            subset["BBU_20_2.0"],
            color="gray",
            alpha=0.1,
        )

        last_price = subset.iloc[-1]["close"] if not subset.empty else 0
        ax.set_title(
            f"HYDRA V2 VISUAL FEED - BTC/USDT (${last_price:.2f})", color="white"
        )
        ax.grid(color="#2b2f36", linestyle="--", linewidth=0.5)
        ax.legend(loc="upper left", fontsize="small")

        # 5. Guardar en Memoria
        buf = io.BytesIO()
        plt.savefig(buf, format="png", bbox_inches="tight")
        buf.seek(0)
        plt.close(fig)

        return buf
