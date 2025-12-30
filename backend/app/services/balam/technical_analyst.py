# -*- coding: utf-8 -*-
"""
HYDRA V2 - BALAM: Technical Analyst (Los Ojos Matemáticos)
Convierte velas crudas de Binance en indicadores técnicos
VERSIÓN PURA: Sin dependencias de pandas_ta (calcula todo manualmente)
"""

import pandas as pd
import numpy as np


class TechnicalAnalyst:
    """
    EL ANALISTA TÉCNICO - Los ojos matemáticos de Balam

    Calcula indicadores manualmente sin dependencias externas:
    - RSI (Fuerza Relativa)
    - EMAs (Tendencias)
    - Bollinger Bands (Volatilidad)
    """

    def __init__(self):
        print("📈 Technical Analyst inicializado (Pure Python)")

    def _calculate_rsi(self, prices: pd.Series, period: int = 14) -> pd.Series:
        """Calcula el Relative Strength Index (RSI) usando Wilder smoothing"""
        delta = prices.diff()

        # Separar ganancias y pérdidas
        gain = delta.copy()
        loss = delta.copy()

        gain[gain < 0] = 0
        loss[loss > 0] = 0
        loss = abs(loss)

        # Usar EMA en lugar de SMA para Wilder smoothing
        alpha = 1.0 / period
        avg_gain = gain.ewm(alpha=alpha, adjust=False).mean()
        avg_loss = loss.ewm(alpha=alpha, adjust=False).mean()

        # Evitar división por cero
        avg_loss = avg_loss.replace(0, 0.0001)

        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))

        # Reemplazar NaN con 50 (neutral)
        rsi = rsi.fillna(50)

        return rsi

    def _calculate_ema(self, prices: pd.Series, period: int) -> pd.Series:
        """Calcula Exponential Moving Average"""
        return prices.ewm(span=period, adjust=False).mean()

    def _calculate_sma(self, prices: pd.Series, period: int) -> pd.Series:
        """Calcula Simple Moving Average"""
        return prices.rolling(window=period).mean()

    def _calculate_bollinger(
        self, prices: pd.Series, period: int = 20, std_dev: int = 2
    ) -> tuple:
        """Calcula Bollinger Bands"""
        sma = self._calculate_sma(prices, period)
        std = prices.rolling(window=period).std()

        upper = sma + (std * std_dev)
        lower = sma - (std * std_dev)

        return upper, sma, lower

    def _calculate_macd(
        self, prices: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9
    ) -> tuple:
        """Calcula MACD"""
        ema_fast = self._calculate_ema(prices, fast)
        ema_slow = self._calculate_ema(prices, slow)

        macd_line = ema_fast - ema_slow
        signal_line = self._calculate_ema(macd_line, signal)
        histogram = macd_line - signal_line

        return macd_line, signal_line, histogram

    def _calculate_adx(self, df: pd.DataFrame, period: int = 14) -> pd.Series:
        """
        Calcula el Average Directional Index (ADX)

        ADX < 25: Mercado lateral (NO OPERAR - riesgo de whipsaw)
        ADX > 25: Tendencia fuerte (seguro operar)
        ADX > 40: Tendencia muy fuerte
        """
        high = df["high"]
        low = df["low"]
        close = df["close"]

        # True Range
        tr1 = high - low
        tr2 = abs(high - close.shift(1))
        tr3 = abs(low - close.shift(1))
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)

        # +DM y -DM (Directional Movement)
        up_move = high - high.shift(1)
        down_move = low.shift(1) - low

        plus_dm = pd.Series(0.0, index=df.index)
        minus_dm = pd.Series(0.0, index=df.index)

        plus_dm[(up_move > down_move) & (up_move > 0)] = up_move
        minus_dm[(down_move > up_move) & (down_move > 0)] = down_move

        # Suavizado con Wilder (EMA)
        alpha = 1.0 / period
        atr = tr.ewm(alpha=alpha, adjust=False).mean()
        plus_di = 100 * (plus_dm.ewm(alpha=alpha, adjust=False).mean() / atr)
        minus_di = 100 * (minus_dm.ewm(alpha=alpha, adjust=False).mean() / atr)

        # DX y ADX
        dx = 100 * abs(plus_di - minus_di) / (plus_di + minus_di + 0.0001)
        adx = dx.ewm(alpha=alpha, adjust=False).mean()

        # Reemplazar NaN con 20 (neutral pero bajo)
        adx = adx.fillna(20)

        return adx, plus_di, minus_di

    def analyze_candles(self, candles: list) -> pd.Series:
        """
        Recibe velas crudas de Binance y devuelve la última vela con indicadores.

        Args:
            candles: Lista de diccionarios con datos OHLCV

        Returns:
            pd.Series: Última vela con todos los indicadores
        """
        # Convertir a DataFrame
        if isinstance(candles[0], dict):
            df = pd.DataFrame(candles)
        else:
            df = pd.DataFrame(
                candles, columns=["time", "open", "high", "low", "close", "volume"]
            )

        # Asegurar columnas numéricas
        for col in ["open", "high", "low", "close", "volume"]:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors="coerce")

        # Calcular indicadores
        df["RSI"] = self._calculate_rsi(df["close"], 14)
        df["EMA_50"] = self._calculate_ema(df["close"], 50)
        df["EMA_200"] = self._calculate_ema(df["close"], 200)

        # Bollinger Bands
        bb_upper, bb_mid, bb_lower = self._calculate_bollinger(df["close"], 20, 2)
        df["BBU_20_2.0"] = bb_upper
        df["BBM_20_2.0"] = bb_mid
        df["BBL_20_2.0"] = bb_lower

        # MACD
        macd, macd_signal, macd_hist = self._calculate_macd(df["close"])
        df["MACD_12_26_9"] = macd
        df["MACDs_12_26_9"] = macd_signal
        df["MACDh_12_26_9"] = macd_hist

        # ADX (Filtro Anti-Whipsaw)
        adx, plus_di, minus_di = self._calculate_adx(df, 14)
        df["ADX_14"] = adx
        df["DI_plus_14"] = plus_di
        df["DI_minus_14"] = minus_di

        # Limpiar NaN
        df.dropna(inplace=True)

        if len(df) == 0:
            raise ValueError("No hay suficientes datos para calcular indicadores")

        return df.iloc[-1]

    def get_full_analysis(self, candles: list) -> pd.DataFrame:
        """
        Devuelve el DataFrame completo con todos los indicadores.
        """
        if isinstance(candles[0], dict):
            df = pd.DataFrame(candles)
        else:
            df = pd.DataFrame(
                candles, columns=["time", "open", "high", "low", "close", "volume"]
            )

        for col in ["open", "high", "low", "close", "volume"]:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors="coerce")

        df["RSI"] = self._calculate_rsi(df["close"], 14)
        df["EMA_50"] = self._calculate_ema(df["close"], 50)
        df["EMA_200"] = self._calculate_ema(df["close"], 200)

        bb_upper, bb_mid, bb_lower = self._calculate_bollinger(df["close"], 20, 2)
        df["BBU_20_2.0"] = bb_upper
        df["BBM_20_2.0"] = bb_mid
        df["BBL_20_2.0"] = bb_lower

        macd, macd_signal, macd_hist = self._calculate_macd(df["close"])
        df["MACD_12_26_9"] = macd
        df["MACDs_12_26_9"] = macd_signal
        df["MACDh_12_26_9"] = macd_hist

        # ADX (Filtro Anti-Whipsaw)
        adx, plus_di, minus_di = self._calculate_adx(df, 14)
        df["ADX_14"] = adx
        df["DI_plus_14"] = plus_di
        df["DI_minus_14"] = minus_di

        df.dropna(inplace=True)

        return df


if __name__ == "__main__":
    import random

    print("Test del Technical Analyst (Pure Python)...")

    candles = []
    precio = 50000
    for i in range(250):
        precio += random.uniform(-100, 150)
        candles.append(
            {
                "time": i,
                "open": precio,
                "high": precio + random.uniform(0, 50),
                "low": precio - random.uniform(0, 50),
                "close": precio + random.uniform(-20, 20),
                "volume": random.uniform(100, 1000),
            }
        )

    analyst = TechnicalAnalyst()
    result = analyst.analyze_candles(candles)

    print(f"\nUltima vela analizada:")
    print(f"   Precio: ${result['close']:.2f}")
    print(f"   RSI: {result['RSI']:.2f}")
    print(f"   EMA 50: ${result['EMA_50']:.2f}")
    print(f"   EMA 200: ${result['EMA_200']:.2f}")
    print("\nTechnical Analyst OK!")
