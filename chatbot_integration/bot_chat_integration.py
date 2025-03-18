"""
Integración del sistema de scraping con el endpoint de bot_chat existente.
Este módulo proporciona las funciones necesarias para integrar datos del scraper
con el chatbot sin modificar el código existente.
"""
import os
import json
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime

# Importar conector de chatbot-scraper
from chatbot_scraper_integration import enhance_chatbot_context, init_connector

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler("data/bot_chat_integration.log"),
        logging.StreamHandler()
    ]
)

# Respuestas predefinidas para preguntas frecuentes
PREDEFINED_RESPONSES = {
    "¿cómo estás?": "¡Estoy muy bien! Soy el asistente virtual de información turística de Ibiza, listo para ayudarte a planificar tu viaje y descubrir todo lo que la isla tiene para ofrecer.",
    
    "¿qué fiestas hay en ibiza?": "Ibiza es conocida mundialmente por sus fiestas y vida nocturna. Las principales discotecas como Pacha, Amnesia, Ushuaïa y Hï Ibiza ofrecen eventos de música electrónica con DJs internacionales. Te puedo ayudar a encontrar información actualizada sobre eventos específicos si me dices qué fechas te interesan.",
    
    "¿qué tiempo hace en ibiza?": "Ibiza tiene un clima mediterráneo con veranos cálidos y secos e inviernos suaves. La temporada alta (junio-septiembre) tiene temperaturas entre 25-30°C. Si necesitas información climática actual, te recomiendo consultar un servicio meteorológico en tiempo real.",
    
    "¿cuáles son las mejores playas?": "Ibiza cuenta con más de 80 playas y calas. Entre las más populares están Ses Salines, Cala Comte, Cala d'Hort (con vistas a Es Vedrà), Playa d'en Bossa y Talamanca. Si buscas playas más tranquilas, te recomendaría Cala Xarraca o Cala Llenya.",
    
    "¿dónde comer en ibiza?": "Ibiza ofrece una excelente gastronomía mediterránea. Puedes encontrar desde restaurantes gourmet hasta chiringuitos de playa. Algunos lugares populares son Sa Punta en Talamanca, Es Torrent en San José, y El Chiringuito en Es Cavallet. La cocina local destaca por el pescado fresco, el arroz y platos tradicionales como el 'bullit de peix'."
}

def enhance_bot_response(user_query: str, original_response: Optional[str] = None) -> Dict[str, Any]:
    """
    Mejora la respuesta del bot combinando datos del scraper con la respuesta original.
    
    Args:
        user_query: Consulta del usuario
        original_response: Respuesta original del bot (si existe)
        
    Returns:
        Dict: Respuesta mejorada con datos del scraper
    """
    # Normalizar consulta
    query_normalized = user_query.lower().strip()
    
    # Verificar si hay una respuesta predefinida
    predefined = None
    for key, response in PREDEFINED_RESPONSES.items():
        if query_normalized == key or query_normalized in key or key in query_normalized:
            predefined = response
            break
    
    # Si no hay respuesta original ni predefinida, obtener datos del scraper
    if not original_response and not predefined:
        # Obtener datos del scraper
        context = enhance_chatbot_context(user_query)
        scraped_data = context.get('scraped_data', [])
        
        if scraped_data:
            # Crear respuesta basada en los datos del scraper
            response_text = "Basado en la información que he encontrado: "
            for i, item in enumerate(scraped_data[:3]):  # Usar solo los 3 primeros resultados
                content = item.get('content', '')
                if content:
                    # Limitar longitud del contenido
                    if len(content) > 200:
                        content = content[:197] + "..."
                    response_text += f"\n\n{content}"
                    
                    # Añadir fuente si existe
                    source = item.get('source', '')
                    if source and not source.startswith("información predefinida"):
                        response_text += f"\n(Fuente: {source})"
            
            # Crear respuesta formateada
            return {
                "success": True,
                "response": response_text,
                "source": "scraper",
                "scraped_data_used": True
            }
    
    # Si hay una respuesta predefinida, usarla
    if predefined:
        return {
            "success": True,
            "response": predefined,
            "source": "predefined"
        }
    
    # Si hay respuesta original, devolverla
    if original_response:
        return {
            "success": True,
            "response": original_response,
            "source": "original"
        }
    
    # Respuesta por defecto
    return {
        "success": True,
        "response": "Lo siento, no tengo información específica sobre eso. ¿Puedo ayudarte con algo más sobre Ibiza?",
        "source": "default"
    }

def patch_bot_chat_handler(app):
    """
    Modifica el manejador de bot_chat existente para integrar datos del scraper.
    Esta función debe llamarse después de registrar las rutas originales.
    
    Args:
        app: Aplicación Flask
    """
    try:
        # Inicializar conector
        init_connector()
        
        # Obtener la vista original
        original_view_func = app.view_functions.get('bot_chat')
        
        if not original_view_func:
            logging.warning("No se encontró el endpoint bot_chat para modificar")
            return False
        
        # Definir la nueva función
        def enhanced_bot_chat_handler(*args, **kwargs):
            from flask import request, jsonify
            
            try:
                # Obtener datos del request
                data = request.json
                user_query = data.get('query', '')
                
                # Intentar ejecutar el manejador original
                try:
                    original_response = original_view_func(*args, **kwargs)
                    
                    # Si la respuesta original es un objeto JSON
                    if hasattr(original_response, 'json'):
                        original_data = original_response.json
                        original_text = original_data.get('response', '')
                    else:
                        # Intentar convertir a diccionario
                        try:
                            original_data = json.loads(original_response)
                            original_text = original_data.get('response', '')
                        except:
                            original_text = str(original_response)
                except Exception as e:
                    logging.error(f"Error al llamar al manejador original: {e}")
                    original_text = None
                
                # Mejorar la respuesta
                enhanced = enhance_bot_response(user_query, original_text)
                
                # Devolver respuesta mejorada
                return jsonify(enhanced)
                
            except Exception as e:
                logging.error(f"Error en enhanced_bot_chat_handler: {e}")
                return jsonify({
                    "success": False,
                    "error": "Error interno del servidor",
                    "details": str(e)
                }), 500
        
        # Reemplazar la vista original
        enhanced_bot_chat_handler.__name__ = original_view_func.__name__
        app.view_functions['bot_chat'] = enhanced_bot_chat_handler
        
        logging.info("Endpoint bot_chat modificado correctamente para integrar datos del scraper")
        return True
        
    except Exception as e:
        logging.error(f"Error al modificar endpoint bot_chat: {e}")
        return False

def setup_bot_integration(app):
    """
    Configura la integración del bot con el sistema de scraping.
    
    Args:
        app: Aplicación Flask
    """
    try:
        # Modificar endpoint existente
        success = patch_bot_chat_handler(app)
        
        if success:
            logging.info("Integración del bot con scraper configurada correctamente")
        else:
            logging.warning("No se pudo configurar la integración del bot con scraper")
            
        return success
        
    except Exception as e:
        logging.error(f"Error al configurar integración del bot: {e}")
        return False

# Código para usar en app.py:
"""
# Agregar después de registrar todas las rutas de la aplicación:

# Integrar bot con sistema de scraping
try:
    from bot_chat_integration import setup_bot_integration
    setup_bot_integration(app)
    app.logger.info("Bot integrado con sistema de scraping")
except ImportError:
    app.logger.warning("Módulo de integración de bot no disponible")
except Exception as e:
    app.logger.error(f"Error al integrar bot con scraper: {e}")
"""
