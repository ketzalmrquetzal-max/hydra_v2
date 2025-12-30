# -*- coding: utf-8 -*-
"""
HYDRA V2 - GEMINI HTTP CLIENT
Cliente HTTP directo para Gemini API (sin SDK, sin problemas de compilación)
"""

import requests
import json
from typing import Optional


class GeminiHTTPClient:
    """
    Cliente HTTP para Gemini API.
    Alternativa al SDK oficial que evita problemas de compilación de grpcio.
    
    Uso:
        client = GeminiHTTPClient(api_key="tu_api_key")
        response = client.generate_content("Analiza este texto...")
    """
    
    def __init__(self, api_key: str, model: str = "gemini-2.0-flash"):
        """
        Inicializa el cliente HTTP.
        
        Args:
            api_key: Tu API Key de Google AI Studio
            model: Modelo a usar (por defecto: gemini-2.0-flash)
        """
        self.api_key = api_key
        self.model = model
        self.base_url = "https://generativelanguage.googleapis.com/v1beta/models"
    
    def generate_content(
        self, 
        prompt: str,
        temperature: float = 1.0,
        max_output_tokens: Optional[int] = None
    ) -> str:
        """
        Genera contenido usando Gemini API vía HTTP.
        
        Args:
            prompt: El texto del prompt
            temperature: Creatividad (0.0-2.0, default 1.0)
            max_output_tokens: Máximo de tokens a generar (opcional)
            
        Returns:
            str: Texto generado por Gemini
            
        Raises:
            Exception: Si hay error en la API
        """
        # Construir URL
        url = f"{self.base_url}/{self.model}:generateContent?key={self.api_key}"
        
        # Construir payload
        payload = {
            "contents": [{
                "parts": [{
                    "text": prompt
                }]
            }],
            "generationConfig": {
                "temperature": temperature,
            }
        }
        
        if max_output_tokens:
            payload["generationConfig"]["maxOutputTokens"] = max_output_tokens
        
        # Headers
        headers = {
            "Content-Type": "application/json"
        }
        
        try:
            # Hacer request
            response = requests.post(
                url, 
                headers=headers, 
                json=payload,
                timeout=30
            )
            
            # Verificar status
            response.raise_for_status()
            
            # Parsear respuesta
            data = response.json()
            
            # Extraer texto
            if "candidates" in data and len(data["candidates"]) > 0:
                candidate = data["candidates"][0]
                if "content" in candidate and "parts" in candidate["content"]:
                    parts = candidate["content"]["parts"]
                    if len(parts) > 0 and "text" in parts[0]:
                        return parts[0]["text"]
            
            # Si no encontramos texto, retornar error
            return f"Error: Respuesta inesperada de Gemini API: {data}"
        
        except requests.exceptions.Timeout:
            raise Exception("Timeout: Gemini API no respondió en 30 segundos")
        
        except requests.exceptions.HTTPError as e:
            error_msg = f"HTTP Error {response.status_code}"
            try:
                error_data = response.json()
                if "error" in error_data:
                    error_msg += f": {error_data['error'].get('message', 'Unknown error')}"
            except:
                pass
            raise Exception(error_msg)
        
        except Exception as e:
            raise Exception(f"Error en Gemini API: {str(e)}")


# Test rápido
if __name__ == "__main__":
    import os
    from dotenv import load_dotenv
    
    load_dotenv()
    
    api_key = os.getenv("GEMINI_API_KEY")
    
    if not api_key:
        print("❌ No se encontró GEMINI_API_KEY en .env")
        exit(1)
    
    print("=" * 60)
    print("TEST: Gemini HTTP Client")
    print("=" * 60)
    
    try:
        client = GeminiHTTPClient(api_key=api_key)
        
        print("\n🧪 Enviando prompt de prueba...")
        
        response = client.generate_content(
            "Responde con una sola palabra: ¿Cuál es la capital de Francia?"
        )
        
        print(f"\n✅ Respuesta de Gemini:\n{response}")
        
        print("\n" + "=" * 60)
        print("TEST COMPLETADO - Gemini HTTP funcionando")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
