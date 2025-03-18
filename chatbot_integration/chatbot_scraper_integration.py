"""
Módulo de integración entre el sistema de scraping automático y el chatbot.
Este módulo permite que el chatbot acceda a la información obtenida por el scraper.
"""
import os
import json
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime

# Importar componentes del scraper
from scraper_integration import get_scraper
from archon_langgraph_scraper import ArchonLangGraphScraper

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler("data/chatbot_scraper.log"),
        logging.StreamHandler()
    ]
)

class ChatbotScraperConnector:
    """
    Conector entre el chatbot y el sistema de scraping.
    Proporciona métodos para acceder a la información recopilada.
    """
    
    def __init__(self):
        """Inicializa el conector."""
        self.scraper = None
        self._kb_cache = {}
        self._last_update = None
        
    def initialize(self):
        """
        Inicializa la conexión con el scraper.
        
        Returns:
            bool: True si se inicializó correctamente, False en caso contrario
        """
        try:
            # Obtener instancia existente del scraper
            self.scraper = get_scraper()
            
            if not self.scraper:
                logging.warning("No se pudo obtener la instancia del scraper. El conector funcionará con capacidades limitadas.")
                return False
                
            # Verificar acceso a la base de conocimiento
            kb_stats = self.scraper.get_knowledge_base_stats()
            logging.info(f"Conectado al scraper. Base de conocimiento: {kb_stats}")
            
            # Cargar caché inicial
            self._update_cache()
            
            return True
            
        except Exception as e:
            logging.error(f"Error al inicializar conector chatbot-scraper: {e}")
            return False
            
    def _update_cache(self):
        """Actualiza la caché de la base de conocimiento."""
        if not self.scraper:
            return
            
        try:
            # Obtener datos de la base de conocimiento
            kb_data = self.scraper.get_knowledge_base_data()
            
            if kb_data:
                self._kb_cache = kb_data
                self._last_update = datetime.now()
                logging.info(f"Caché de conocimiento actualizada. Entradas: {len(kb_data)}")
                
        except Exception as e:
            logging.error(f"Error al actualizar caché: {e}")
            
    def get_relevant_info(self, query: str, category: Optional[str] = None, max_results: int = 5) -> List[Dict[str, Any]]:
        """
        Obtiene información relevante para una consulta del chatbot.
        
        Args:
            query: Consulta del usuario
            category: Categoría para filtrar resultados (opcional)
            max_results: Número máximo de resultados
            
        Returns:
            Lista de fragmentos de información relevantes
        """
        # Verificar si es necesario actualizar la caché
        if (not self._last_update or 
            (datetime.now() - self._last_update).total_seconds() > 3600):  # 1 hora
            self._update_cache()
            
        if not self.scraper:
            # Si no hay scraper, devolver información predeterminada
            return self._fallback_info(query, category)
            
        try:
            # Realizar búsqueda semántica en la base de conocimiento
            results = self.scraper.search_knowledge_base(
                query=query,
                category=category,
                max_results=max_results
            )
            
            if not results:
                # Si no hay resultados, usar fallback
                return self._fallback_info(query, category)
                
            return results
            
        except Exception as e:
            logging.error(f"Error al buscar información: {e}")
            return self._fallback_info(query, category)
            
    def _fallback_info(self, query: str, category: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Proporciona información de respaldo cuando no hay datos del scraper.
        
        Args:
            query: Consulta del usuario
            category: Categoría para filtrar resultados (opcional)
            
        Returns:
            Lista de fragmentos de información básica
        """
        # Respuestas predefinidas para preguntas comunes
        fallbacks = {
            "eventos": [
                {
                    "content": "Ibiza ofrece numerosos eventos durante todo el año, especialmente en verano. Las discotecas más famosas incluyen Pacha, Amnesia, Ushuaïa y Hï Ibiza.",
                    "source": "información predefinida",
                    "date": datetime.now().isoformat()
                }
            ],
            "playas": [
                {
                    "content": "Las playas más populares de Ibiza incluyen Playa d'en Bossa, Cala Comte, Cala Bassa, Talamanca y Las Salinas.",
                    "source": "información predefinida",
                    "date": datetime.now().isoformat()
                }
            ],
            "general": [
                {
                    "content": "Ibiza es una isla del archipiélago balear en España, famosa por su vida nocturna y turismo. También cuenta con lugares declarados Patrimonio de la Humanidad por la UNESCO.",
                    "source": "información predefinida",
                    "date": datetime.now().isoformat()
                }
            ]
        }
        
        # Si se especifica categoría y existe en fallbacks, usar esa
        if category and category in fallbacks:
            return fallbacks[category]
            
        # En caso contrario, intentar determinar la categoría por palabras clave
        query_lower = query.lower()
        if any(word in query_lower for word in ["fiesta", "evento", "discoteca", "club", "música"]):
            return fallbacks["eventos"]
        elif any(word in query_lower for word in ["playa", "nadar", "costa", "arena", "cala"]):
            return fallbacks["playas"]
        else:
            return fallbacks["general"]
    
    def get_latest_updates(self, category: Optional[str] = None, days: int = 7) -> List[Dict[str, Any]]:
        """
        Obtiene las actualizaciones más recientes recopiladas por el scraper.
        
        Args:
            category: Categoría para filtrar resultados (opcional)
            days: Número de días hacia atrás para buscar
            
        Returns:
            Lista de actualizaciones recientes
        """
        if not self.scraper:
            return []
            
        try:
            # Obtener actualizaciones recientes
            return self.scraper.get_recent_updates(category=category, days=days)
            
        except Exception as e:
            logging.error(f"Error al obtener actualizaciones recientes: {e}")
            return []
            
    def get_categories(self) -> List[str]:
        """
        Obtiene las categorías disponibles en la base de conocimiento.
        
        Returns:
            Lista de categorías
        """
        if not self.scraper:
            # Categorías predeterminadas
            return ["general", "eventos", "restaurantes", "playas", "alojamiento"]
            
        try:
            # Obtener categorías del scraper
            return self.scraper.get_categories()
            
        except Exception as e:
            logging.error(f"Error al obtener categorías: {e}")
            # Categorías predeterminadas
            return ["general", "eventos", "restaurantes", "playas", "alojamiento"]


# Instancia global para usar en la aplicación
connector = ChatbotScraperConnector()

def init_connector():
    """
    Inicializa el conector para usar en la aplicación.
    
    Returns:
        ChatbotScraperConnector: Instancia inicializada del conector
    """
    global connector
    
    if not connector.scraper:
        connector.initialize()
        
    return connector
    
def get_connector() -> ChatbotScraperConnector:
    """
    Obtiene la instancia del conector.
    
    Returns:
        ChatbotScraperConnector: Instancia del conector
    """
    global connector
    return connector


# Funciones de utilidad para el chatbot

def enhance_chatbot_context(user_query: str) -> Dict[str, Any]:
    """
    Mejora el contexto del chatbot con información del scraper.
    Esta función se puede usar en el endpoint del chatbot.
    
    Args:
        user_query: Consulta del usuario
        
    Returns:
        Dict: Contexto enriquecido para el chatbot
    """
    # Obtener conector
    conn = get_connector()
    
    # Categorizar la consulta (implementación simple)
    category = None
    query_lower = user_query.lower()
    
    if any(word in query_lower for word in ["fiesta", "evento", "discoteca", "club", "música"]):
        category = "eventos"
    elif any(word in query_lower for word in ["playa", "nadar", "costa", "arena", "cala"]):
        category = "playas"
    elif any(word in query_lower for word in ["hotel", "alojamiento", "hostal", "apartamento"]):
        category = "alojamiento"
    elif any(word in query_lower for word in ["restaurante", "comida", "comer", "gastronomía"]):
        category = "restaurantes"
        
    # Obtener información relevante
    relevant_info = conn.get_relevant_info(user_query, category=category)
    
    # Formatear el contexto para el chatbot
    context = {
        "query": user_query,
        "category": category,
        "scraped_data": relevant_info,
        "timestamp": datetime.now().isoformat()
    }
    
    logging.info(f"Contexto enriquecido para chatbot. Consulta: '{user_query}', Categoría: {category}, Resultados: {len(relevant_info)}")
    
    return context


# Ejemplo de uso en el endpoint del chatbot:
"""
from chatbot_scraper_integration import enhance_chatbot_context

@app.route('/api/chatbot', methods=['POST'])
def chatbot_endpoint():
    data = request.json
    user_query = data.get('query', '')
    
    # Enriquecer el contexto con información del scraper
    enhanced_context = enhance_chatbot_context(user_query)
    
    # Pasar el contexto enriquecido al chatbot
    response = chatbot.get_response(user_query, context=enhanced_context)
    
    return jsonify({
        "success": True,
        "response": response
    })
"""


# Función para actualizar el endpoint del bot_chat existente:
def update_bot_chat_with_scraper_data(flask_app, original_bot_chat_func):
    """
    Actualiza la función bot_chat existente para integrar datos del scraper.
    
    Args:
        flask_app: Aplicación Flask
        original_bot_chat_func: Función bot_chat original
        
    Returns:
        function: Nueva función bot_chat que integra datos del scraper
    """
    # Inicializar el conector
    init_connector()
    
    # Definir la nueva función de bot_chat
    def enhanced_bot_chat():
        from flask import request, jsonify
        
        # Obtener datos del request
        data = request.json
        user_query = data.get('query', '')
        
        # Enriquecer el contexto con información del scraper
        enhanced_context = enhance_chatbot_context(user_query)
        
        # Guardar el contexto en la solicitud para que la función original pueda usarlo
        request.enhanced_context = enhanced_context
        
        # Llamar a la función original
        response = original_bot_chat_func()
        
        # Si la respuesta es un objeto JSON, intentar mejorarla
        if hasattr(response, 'json'):
            try:
                json_data = response.json
                
                # Añadir información de la fuente si existe
                if enhanced_context['scraped_data']:
                    sources = []
                    for item in enhanced_context['scraped_data']:
                        if 'source' in item and item['source'] not in sources:
                            sources.append(item['source'])
                    
                    if sources:
                        json_data['sources'] = sources
                        
                # Actualizar la respuesta
                response.json = json_data
                
            except Exception as e:
                logging.error(f"Error al mejorar respuesta del chatbot: {e}")
        
        return response
    
    # Reemplazar la función original en la aplicación
    enhanced_bot_chat.__name__ = original_bot_chat_func.__name__
    
    # Nota: Este enfoque es para ilustrar cómo se podría integrar
    # En una aplicación real, es mejor modificar directamente la función original
    
    return enhanced_bot_chat


# Código de prueba
if __name__ == "__main__":
    logging.info("Probando integración chatbot-scraper")
    
    # Inicializar conector
    conn = init_connector()
    
    # Probar consultas
    queries = [
        "¿Qué fiestas hay en Ibiza?",
        "¿Cuáles son las mejores playas?",
        "¿Dónde puedo comer paella en Ibiza?"
    ]
    
    for query in queries:
        logging.info(f"Consultando: '{query}'")
        context = enhance_chatbot_context(query)
        logging.info(f"Categoría detectada: {context['category']}")
        logging.info(f"Resultados: {len(context['scraped_data'])}")
        
    logging.info("Prueba completada")
