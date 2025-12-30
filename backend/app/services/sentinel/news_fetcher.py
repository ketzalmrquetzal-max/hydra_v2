# -*- coding: utf-8 -*-
"""
HYDRA V2 - NEWS FETCHER (Los Ojos del Centinela)
Recolecta inteligencia de mercado usando RSS Feeds y Fear & Greed Index
"""

import feedparser
import requests
import time
from typing import List, Dict


class NewsFetcher:
    """
    Los Ojos del Centinela.
    Recolecta información del mundo exterior para alimentar el análisis.
    
    Fuentes:
    - RSS Feeds de noticias cripto (rápido, gratis, sin límites de API)
    - Fear & Greed Index (sentimiento cuantificado del mercado)
    """
    
    def __init__(self):
        # Fuentes de Inteligencia (RSS Feeds son rápidos y ligeros)
        self.sources = [
            "https://cointelegraph.com/rss",
            "https://www.coindesk.com/arc/outboundfeeds/rss/",
            "https://cryptopotato.com/feed/"
        ]
    
    def get_fear_and_greed(self) -> str:
        """
        Obtiene el índice de Miedo y Codicia (0-100).
        
        Escala:
        - 0-24: Extreme Fear (Miedo Extremo)
        - 25-44: Fear (Miedo)
        - 45-55: Neutral
        - 56-75: Greed (Codicia)
        - 76-100: Extreme Greed (Codicia Extrema)
        
        Returns:
            str: Descripción del índice con valor y clasificación
        """
        try:
            url = "https://api.alternative.me/fng/?limit=1"
            response = requests.get(url, timeout=5)
            data = response.json()
            
            value = int(data['data'][0]['value'])
            classification = data['data'][0]['value_classification']
            
            return f"Índice Miedo/Codicia: {value} ({classification})"
        
        except requests.exceptions.Timeout:
            return "Error: Timeout obteniendo F&G Index (API no responde)"
        except requests.exceptions.RequestException as e:
            return f"Error obteniendo F&G Index: {str(e)}"
        except (KeyError, ValueError) as e:
            return f"Error parseando F&G Index: {str(e)}"
    
    def get_latest_headlines(self, limit: int = 6) -> str:
        """
        Recolecta los titulares más recientes del mundo cripto.
        
        Args:
            limit: Número máximo de titulares a recolectar
            
        Returns:
            str: Titulares formateados (uno por línea con bullet points)
        """
        headlines = []
        
        try:
            for url in self.sources:
                try:
                    # Parsear RSS feed (feedparser maneja timeouts automáticamente)
                    feed = feedparser.parse(url)
                    
                    # Verificar si el feed es válido
                    if not feed.entries:
                        continue
                    
                    # Tomamos solo los 2 primeros de cada fuente para variedad
                    for entry in feed.entries[:2]:
                        # Limpiamos el título
                        clean_title = entry.title.replace("\n", " ").strip()
                        headlines.append(f"- {clean_title}")
                        
                    if len(headlines) >= limit:
                        break
                
                except Exception as e:
                    # Si una fuente falla, continuar con las demás
                    print(f"⚠️ Advertencia: Error leyendo {url}: {e}")
                    continue
            
            if not headlines:
                return "- (Sin titulares disponibles - Todas las fuentes fallaron)"
            
            return "\n".join(headlines[:limit])
        
        except Exception as e:
            return f"Error crítico leyendo noticias: {e}"
    
    def get_raw_intelligence(self, limit: int = 6) -> Dict[str, str]:
        """
        Obtiene todos los datos de inteligencia en formato estructurado.
        
        Returns:
            dict: {"fear_greed": str, "headlines": str}
        """
        return {
            "fear_greed": self.get_fear_and_greed(),
            "headlines": self.get_latest_headlines(limit=limit)
        }


# PRUEBA RÁPIDA (Solo si ejecutas este archivo directo)
if __name__ == "__main__":
    print("=" * 60)
    print("TEST: News Fetcher (Los Ojos del Centinela)")
    print("=" * 60)
    
    fetcher = NewsFetcher()
    
    print("\n[1/2] Obteniendo Fear & Greed Index...")
    print(fetcher.get_fear_and_greed())
    
    print("\n[2/2] Obteniendo titulares recientes...")
    headlines = fetcher.get_latest_headlines(limit=5)
    print(headlines)
    
    print("\n" + "=" * 60)
    print("TEST COMPLETADO")
    print("=" * 60)
