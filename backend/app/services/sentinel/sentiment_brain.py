# -*- coding: utf-8 -*-
"""
HYDRA V2 - SENTIMENT BRAIN (El Cerebro del Centinela)
Análisis de sentimiento usando Gemini 1.5 Flash vía HTTP
"""

import os
from backend.app.core.config import get_settings
from .gemini_http_client import GeminiHTTPClient


class SentimentBrain:
    """
    El Cerebro del Centinela.
    Procesa inteligencia cruda y genera análisis estratégico usando Gemini AI.
    
    Características:
    - Ultrarrápido (Gemini 1.5 Flash < 1 segundo)
    - Análisis contextual profundo
    - Detección de cisnes negros
    - Recomendaciones accionables
    
    Implementación:
    - Usa HTTP REST API directamente (sin SDK, sin problemas de compilación)
    """
    
    def __init__(self):
        settings = get_settings()
        
        # Validar que existe la API Key
        if not settings.gemini_api_key:
            raise ValueError(
                "❌ ERROR: No encontré la GEMINI_API_KEY en el archivo .env. "
                "Por favor, añádela antes de usar el Centinela."
            )
        
        # Inicializar cliente HTTP de Gemini (sin SDK, sin problemas de compilación)
        self.client = GeminiHTTPClient(
            api_key=settings.gemini_api_key,
            model='gemini-2.0-flash'
        )
        
        print("🧠 Sentiment Brain inicializado (Gemini HTTP Client)")
    
    def analyze_context(self, headlines: str, fear_index: str) -> str:
        """
        Le pide a Gemini que actúe como un Analista de Riesgos Paranoico.
        
        Args:
            headlines: Titulares de noticias (formato bullet points)
            fear_index: Dato del Fear & Greed Index
            
        Returns:
            str: Informe estructurado con sentimiento, alerta y recomendación
        """
        
        prompt = f"""
ACTÚA COMO: 'EL CENTINELA', un sistema de inteligencia artificial para trading de alta frecuencia.
TU MISIÓN: Analizar el sentimiento del mercado cripto para proteger el capital.

════════════════════════════════════════════════════════════

DATOS ACTUALES:
1. {fear_index}
2. TITULARES RECIENTES:
{headlines}

════════════════════════════════════════════════════════════

INSTRUCCIONES DE ANÁLISIS:
- Analiza si hay PÁNICO, EUFORIA o CALMA en el mercado
- Detecta "Cisnes Negros" (Regulaciones, Hacks, Guerras, Bancarrotas)
- Identifica FOMO (miedo a perderse algo) o FUD (miedo, incertidumbre, duda)
- Sé BREVE y DIRECTO. Estilo militar/técnico.

════════════════════════════════════════════════════════════

FORMATO DE SALIDA OBLIGATORIO (copia exactamente esta estructura):

🌡️ SENTIMIENTO: [Número del -1.0 (Pánico Total) al +1.0 (Euforia Total)]
📋 RESUMEN: [Una frase describiendo qué está pasando]
⚠️ ALERTA: [NULA / BAJA / MEDIA / ALTA / CRÍTICA]
🎯 RECOMENDACIÓN: [HOLD / COMPRA CAUTELOSA / VENTA DEFENSIVA / CERRAR TODO]
💡 JUSTIFICACIÓN: [Una línea explicando por qué]

════════════════════════════════════════════════════════════

EJEMPLO DE RESPUESTA CORRECTA:

🌡️ SENTIMIENTO: -0.7
📋 RESUMEN: Mercado en pánico por noticias de regulación en EEUU
⚠️ ALERTA: ALTA
🎯 RECOMENDACIÓN: VENTA DEFENSIVA
💡 JUSTIFICACIÓN: Correlación negativa con regulaciones históricas

════════════════════════════════════════════════════════════

AHORA, ANALIZA LOS DATOS PROPORCIONADOS Y RESPONDE EN EL FORMATO EXACTO.
"""
        
        try:
            # Generar respuesta con Gemini HTTP Client
            response_text = self.client.generate_content(
                prompt=prompt,
                temperature=0.7  # Más determinista para análisis
            )
            
            return response_text
        
        except Exception as e:
            error_msg = f"""
❌ ERROR CEREBRAL EN GEMINI:
Tipo: {type(e).__name__}
Detalle: {str(e)}

⚠️ MODO DEGRADADO ACTIVADO
🌡️ SENTIMIENTO: 0.0
📋 RESUMEN: Sistema de análisis AI temporalmente fuera de línea
⚠️ ALERTA: MEDIA
🎯 RECOMENDACIÓN: HOLD
💡 JUSTIFICACIÓN: Sin datos de sentimiento, mantener postura neutral
"""
            return error_msg
    
    def parse_sentiment_score(self, report: str) -> float:
        """
        Extrae el score numérico del sentimiento del reporte.
        
        Args:
            report: Texto del reporte generado por analyze_context
            
        Returns:
            float: Score entre -1.0 y 1.0, o 0.0 si no se puede parsear
        """
        try:
            # Buscar la línea que empieza con 🌡️ SENTIMIENTO:
            for line in report.split('\n'):
                if 'SENTIMIENTO:' in line or '🌡️' in line:
                    # Extraer el número (puede estar como -0.7, 0.5, etc.)
                    parts = line.split(':')
                    if len(parts) >= 2:
                        # Limpiar y convertir a float
                        score_str = parts[1].strip().split()[0]  # Toma solo el primer número
                        score = float(score_str)
                        # Clampear entre -1 y 1
                        return max(-1.0, min(1.0, score))
            
            return 0.0  # Si no encuentra, retorna neutral
        
        except (ValueError, IndexError):
            return 0.0


# PRUEBA RÁPIDA (Solo si ejecutas este archivo directo)
if __name__ == "__main__":
    print("=" * 60)
    print("TEST: Sentiment Brain (El Cerebro del Centinela)")
    print("=" * 60)
    
    try:
        brain = SentimentBrain()
        
        # Datos de prueba (simulados)
        test_headlines = """- Bitcoin cae 10% en las últimas 24 horas
- SEC anuncia nueva regulación para exchanges
- Pánico en redes sociales tras caída abrupta
- Analistas predicen soporte en $90k"""
        
        test_fear = "Índice Miedo/Codicia: 22 (Extreme Fear)"
        
        print("\n🧪 Analizando datos de prueba...")
        report = brain.analyze_context(test_headlines, test_fear)
        
        print("\n" + "=" * 60)
        print("INFORME DEL CEREBRO:")
        print("=" * 60)
        print(report)
        print("=" * 60)
        
        # Extraer score
        score = brain.parse_sentiment_score(report)
        print(f"\nSentiment Score extraído: {score}")
        
    except Exception as e:
        print(f"\n❌ Error en el test: {e}")
        import traceback
        traceback.print_exc()
