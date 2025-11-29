# =======================
# OPENAI LLM - CONFIGURADO ✅
# =======================
import os
from openai import OpenAI
from typing import List, Dict, Any

# =======================
# CONFIGURACIÓN DE OPENAI
# =======================
# Cliente OpenAI - inicialización diferida para evitar errores al importar
client = None

def get_openai_client():
    """Obtiene o crea el cliente de OpenAI."""
    global client
    if client is None:
        api_key = os.getenv("OPENAI_API_KEY")
        if api_key and api_key != "tu_api_key_aqui":
            try:
                client = OpenAI(api_key=api_key)
            except Exception as e:
                print(f"⚠️ Error inicializando cliente OpenAI: {e}")
                client = None
    return client

MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
MAX_TOKENS = int(os.getenv("OPENAI_MAX_TOKENS", "2000"))
TEMPERATURE = float(os.getenv("OPENAI_TEMPERATURE", "0.7"))

def generate_reply(user: str, message: str, history: List[Dict[str, Any]]) -> str:
    '''
    Genera una respuesta usando OpenAI GPT basada en el mensaje del usuario y el historial.
    
    Args:
        user: Nombre del usuario
        message: Mensaje actual del usuario
        history: Lista de mensajes anteriores para contexto
        
    Returns:
        str: Respuesta generada por el modelo
    '''
    try:
        # Verificar que la API key esté configurada
        if not os.getenv("OPENAI_API_KEY"):
            return "❌ Error: API Key de OpenAI no configurada. Por favor, configura OPENAI_API_KEY en el archivo .env"
        
        # Construir el contexto del historial
        context_messages = []
        
        # Agregar mensajes del historial (últimos 5 para mantener contexto)
        for msg in history[-5:]:
            if msg.get("user_message"):
                context_messages.append({"role": "user", "content": msg["user_message"]})
            if msg.get("bot_response"):
                context_messages.append({"role": "assistant", "content": msg["bot_response"]})
        
        # Agregar el mensaje actual
        context_messages.append({"role": "user", "content": message})
        
        # Llamar a la API de OpenAI
        openai_client = get_openai_client()
        if not openai_client:
            return "❌ Error: Cliente de OpenAI no inicializado. Verifica la configuración de OPENAI_API_KEY."
        
        response = openai_client.chat.completions.create(
            model=MODEL,
            messages=context_messages,
            max_tokens=MAX_TOKENS,
            temperature=TEMPERATURE,
            user=user
        )
        
        return response.choices[0].message.content.strip()
        
    except Exception as e:
        return f"❌ Error con OpenAI: {str(e)}"

def test_openai_connection() -> Dict[str, Any]:
    '''
    Prueba la conexión con OpenAI para verificar que la API Key funciona.
    
    Returns:
        Dict con el resultado de la prueba
    '''
    try:
        if not os.getenv("OPENAI_API_KEY"):
            return {
                "success": False,
                "error": "API Key no configurada",
                "message": "Configura OPENAI_API_KEY en el archivo .env"
            }
        
        # Hacer una llamada simple para probar la conexión
        openai_client = get_openai_client()
        if not openai_client:
            return {
                "success": False,
                "error": "Cliente no inicializado",
                "message": "Verifica la configuración de OPENAI_API_KEY"
            }
        
        response = openai_client.chat.completions.create(
            model=MODEL,
            messages=[{"role": "user", "content": "Hola, ¿funcionas?"}],
            max_tokens=10
        )
        
        return {
            "success": True,
            "message": "Conexión con OpenAI exitosa",
            "model": MODEL,
            "response": response.choices[0].message.content
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "message": "Error al conectar con OpenAI"
        }
