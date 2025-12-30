# -*- coding: utf-8 -*-
"""
HYDRA V2 - BALAM: Evidence Generator (El Artista Forense)
Genera gráficos como evidencia visual de las decisiones de Balam
"""

import matplotlib

matplotlib.use("Agg")  # Backend sin GUI para servidores
import matplotlib.pyplot as plt
import io
import base64
from datetime import datetime


class EvidenceGenerator:
    """
    EL GENERADOR DE EVIDENCIA - El artista forense de Balam

    Crea gráficos visuales que documentan:
    - Por qué se tomó una decisión
    - Estado del mercado en ese momento
    - Niveles técnicos relevantes
    """

    def __init__(self):
        # Configurar estilo oscuro
        plt.style.use("dark_background")
        print("🎨 Evidence Generator inicializado")

    def create_chart(self, df, symbol: str, decision: dict) -> str:
        """
        Genera una imagen PNG del gráfico actual y la convierte a Base64.

        Args:
            df: DataFrame con precios e indicadores
            symbol: Par de trading (ej: BTCUSDT)
            decision: Diccionario con la decisión de Balam

        Returns:
            str: Imagen en formato Base64 para embed en HTML/Dashboard
        """
        fig, axes = plt.subplots(
            2, 1, figsize=(12, 8), gridspec_kw={"height_ratios": [3, 1]}
        )

        # === GRÁFICO PRINCIPAL (Precio + EMAs) ===
        ax1 = axes[0]

        # Últimas 50 velas para claridad
        tail = min(50, len(df))
        plot_data = df.tail(tail)
        x_range = range(len(plot_data))

        # Dibujar Precio
        ax1.plot(
            x_range,
            plot_data["close"].values,
            label="Precio",
            color="white",
            linewidth=2,
        )

        # Dibujar EMAs
        if "EMA_50" in plot_data.columns:
            ax1.plot(
                x_range,
                plot_data["EMA_50"].values,
                label="EMA 50",
                color="cyan",
                linestyle="--",
                alpha=0.7,
            )
        if "EMA_200" in plot_data.columns:
            ax1.plot(
                x_range,
                plot_data["EMA_200"].values,
                label="EMA 200",
                color="orange",
                linestyle="--",
                alpha=0.7,
            )

        # Bollinger Bands
        if "BBU_20_2.0" in plot_data.columns and "BBL_20_2.0" in plot_data.columns:
            ax1.fill_between(
                x_range,
                plot_data["BBL_20_2.0"].values,
                plot_data["BBU_20_2.0"].values,
                alpha=0.1,
                color="purple",
                label="Bollinger Bands",
            )

        # Marcar la decisión
        action = decision.get("action", "HOLD")
        confidence = decision.get("confidence", 0)

        color_map = {"BUY": "#00ff00", "SELL": "#ff0000", "HOLD": "#ffff00"}
        marker_color = color_map.get(action, "#ffffff")

        # Flecha en la última vela
        last_price = plot_data["close"].iloc[-1]
        ax1.annotate(
            f"{action}\n{confidence}%",
            xy=(len(x_range) - 1, last_price),
            xytext=(len(x_range) - 5, last_price * (1.02 if action == "BUY" else 0.98)),
            fontsize=12,
            fontweight="bold",
            color=marker_color,
            arrowprops=dict(arrowstyle="->", color=marker_color, lw=2),
        )

        ax1.set_title(
            f"EVIDENCIA BALAM: {symbol} - {action} ({confidence}%)",
            fontsize=14,
            fontweight="bold",
            color="white",
        )
        ax1.legend(loc="upper left")
        ax1.grid(True, alpha=0.2)
        ax1.set_ylabel("Precio (USDT)")

        # === GRÁFICO RSI ===
        ax2 = axes[1]

        if "RSI" in plot_data.columns:
            ax2.plot(
                x_range,
                plot_data["RSI"].values,
                label="RSI",
                color="magenta",
                linewidth=1.5,
            )
            ax2.axhline(
                y=70, color="red", linestyle="--", alpha=0.5, label="Sobrecompra (70)"
            )
            ax2.axhline(
                y=30, color="green", linestyle="--", alpha=0.5, label="Sobreventa (30)"
            )
            ax2.fill_between(x_range, 70, 100, alpha=0.1, color="red")
            ax2.fill_between(x_range, 0, 30, alpha=0.1, color="green")
            ax2.set_ylim(0, 100)

        ax2.set_ylabel("RSI")
        ax2.set_xlabel("Velas")
        ax2.legend(loc="upper left")
        ax2.grid(True, alpha=0.2)

        # Timestamp
        fig.text(
            0.99,
            0.01,
            f'Generado: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}',
            ha="right",
            fontsize=8,
            color="gray",
        )

        plt.tight_layout()

        # Guardar en memoria (no en disco)
        buf = io.BytesIO()
        plt.savefig(buf, format="png", facecolor="#0d1117", dpi=100)
        buf.seek(0)

        # Convertir a Base64
        image_base64 = base64.b64encode(buf.read()).decode("utf-8")
        plt.close(fig)

        return image_base64

    def save_to_file(self, base64_image: str, filename: str) -> str:
        """
        Guarda la imagen Base64 como archivo PNG.

        Args:
            base64_image: Imagen en Base64
            filename: Nombre del archivo (sin extensión)

        Returns:
            str: Path del archivo guardado
        """
        import os

        # Crear directorio si no existe
        evidence_dir = "docs/logs/evidence"
        os.makedirs(evidence_dir, exist_ok=True)

        filepath = (
            f"{evidence_dir}/{filename}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
        )

        # Decodificar y guardar
        image_data = base64.b64decode(base64_image)
        with open(filepath, "wb") as f:
            f.write(image_data)

        return filepath


# Test directo
if __name__ == "__main__":
    import pandas as pd
    import random

    print("🧪 Test del Evidence Generator...")

    # Generar datos fake
    data = {
        "close": [50000 + random.uniform(-500, 500) for _ in range(50)],
        "EMA_50": [50000 + random.uniform(-200, 200) for _ in range(50)],
        "EMA_200": [49500 + random.uniform(-100, 100) for _ in range(50)],
        "RSI": [50 + random.uniform(-20, 20) for _ in range(50)],
    }
    df = pd.DataFrame(data)

    decision = {
        "action": "BUY",
        "confidence": 92,
        "reason": "Test de generación de evidencia",
    }

    generator = EvidenceGenerator()
    base64_img = generator.create_chart(df, "BTCUSDT", decision)

    print(f"📸 Imagen generada: {len(base64_img)} caracteres Base64")

    # Guardar como archivo
    filepath = generator.save_to_file(base64_img, "test_evidence")
    print(f"💾 Guardado en: {filepath}")
    print("\n✅ Evidence Generator funcionando!")
