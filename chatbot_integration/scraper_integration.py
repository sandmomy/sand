"""
Módulo de integración del sistema de scraping automático con Archon y LangGraph.
Este archivo proporciona funciones para inicializar y configurar el sistema en la aplicación web.
"""
import os
import logging
import traceback
from typing import Dict, Any, Optional
from flask import current_app, g, Flask

# Importar componentes del sistema
from scraper_api import init_app as init_api
from archon_langgraph_scraper import ArchonLangGraphScraper, start_scraper_service

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler("data/scraper_integration.log"),
        logging.StreamHandler()
    ]
)

# Variable global para la instancia del scraper
_scraper_instance = None

def get_scraper() -> Optional[ArchonLangGraphScraper]:
    """
    Obtiene la instancia global del scraper.
    
    Returns:
        ArchonLangGraphScraper: Instancia del scraper o None si no se ha iniciado
    """
    global _scraper_instance
    
    # Si no existe, intentar obtenerla de la aplicación
    if _scraper_instance is None and 'app' in globals():
        if hasattr(current_app, 'scraper'):
            _scraper_instance = current_app.scraper
    
    return _scraper_instance

def init_scraper(auto_start=True) -> Optional[ArchonLangGraphScraper]:
    """
    Inicializa el sistema de scraping.
    
    Args:
        auto_start: Si es True, inicia automáticamente el scraper
        
    Returns:
        ArchonLangGraphScraper: Instancia del scraper o None si hubo un error
    """
    global _scraper_instance
    
    try:
        logging.info("Inicializando sistema de scraping automático")
        
        # Crear instancia del scraper si no existe
        if _scraper_instance is None:
            _scraper_instance = ArchonLangGraphScraper()
            
            # Iniciar el scraper si se solicita
            if auto_start:
                _scraper_instance.start()
                logging.info("Scraper iniciado automáticamente")
                
        # Registrar evento de cierre para detener el scraper al cerrar la aplicación
        if 'app' in globals() and hasattr(current_app, '_got_first_request'):
            current_app.teardown_appcontext(teardown_scraper)
            
        return _scraper_instance
            
    except Exception as e:
        logging.error(f"Error al inicializar el sistema de scraping: {e}")
        traceback.print_exc()
        return None

def teardown_scraper(exception=None):
    """
    Detiene el scraper al cerrar la aplicación.
    
    Args:
        exception: Excepción que causó el cierre (si existe)
    """
    global _scraper_instance
    
    if _scraper_instance is not None and _scraper_instance.is_running:
        try:
            logging.info("Deteniendo scraper al cerrar la aplicación")
            _scraper_instance.stop()
        except Exception as e:
            logging.error(f"Error al detener el scraper: {e}")
            traceback.print_exc()

def init_app(app: Flask, auto_start=True):
    """
    Inicializa el sistema de scraping en la aplicación Flask.
    
    Args:
        app: Aplicación Flask
        auto_start: Si es True, inicia automáticamente el scraper
    """
    try:
        # Inicializar API de scraping
        init_api(app)
        
        # Inicializar scraper
        scraper = init_scraper(auto_start)
        
        # Almacenar instancia en la aplicación
        app.scraper = scraper
        
        logging.info("Sistema de scraping integrado correctamente en la aplicación")
        
    except Exception as e:
        logging.error(f"Error al integrar el sistema de scraping: {e}")
        traceback.print_exc()

def run_scheduled_tasks():
    """
    Ejecuta tareas programadas manualmente.
    Útil para pruebas o para ejecutar tareas fuera del programador.
    """
    scraper = get_scraper()
    
    if scraper is None:
        logging.error("No se pudo obtener la instancia del scraper")
        return False
        
    try:
        # Ejecutar tareas diarias
        scraper._run_daily_tasks()
        return True
    except Exception as e:
        logging.error(f"Error al ejecutar tareas programadas: {e}")
        traceback.print_exc()
        return False

def check_archon_setup() -> Dict[str, Any]:
    """
    Verifica la configuración de Archon.
    
    Returns:
        Dict: Estado de la configuración de Archon
    """
    try:
        result = {
            "available": False,
            "openrouter": False,
            "openai": False,
            "deepseek": False,
            "ready": False,
            "message": ""
        }
        
        # Verificar variables de entorno
        if os.environ.get("OPENROUTER_API_KEY"):
            result["openrouter"] = True
        
        if os.environ.get("OPENAI_API_KEY"):
            result["openai"] = True
        
        # Verificar disponibilidad de Archon
        try:
            # Intentar importar Archon
            from archon import Archon
            result["available"] = True
            
            # Verificar acceso a los modelos
            try:
                archon = Archon()
                llm_check = archon.llm.check() if hasattr(archon.llm, "check") else True
                embedding_check = archon.embedding.check() if hasattr(archon.embedding, "check") else True
                
                if llm_check and embedding_check:
                    result["ready"] = True
                    result["message"] = "Archon está configurado y listo para usar"
                else:
                    result["message"] = "Archon está disponible pero no todos los servicios están listos"
                    
            except Exception as e:
                result["message"] = f"Error al inicializar Archon: {str(e)}"
                
        except ImportError:
            result["message"] = "Archon no está instalado o disponible"
            
        # Verificar modelo de razonamiento
        if result["available"] and result["openrouter"]:
            result["deepseek"] = True
        
        return result
        
    except Exception as e:
        logging.error(f"Error al verificar configuración de Archon: {e}")
        traceback.print_exc()
        return {
            "available": False,
            "ready": False,
            "message": f"Error al verificar configuración: {str(e)}"
        }


# Código para pruebas manuales
if __name__ == "__main__":
    logging.info("Ejecutando programa de prueba del módulo de integración")
    
    # Verificar configuración de Archon
    archon_status = check_archon_setup()
    logging.info(f"Estado de Archon: {archon_status}")
    
    # Inicializar scraper
    scraper = init_scraper(auto_start=False)
    
    if scraper:
        logging.info("Scraper inicializado correctamente")
        
        # Mostrar configuración
        sources_count = len(scraper.config.sources)
        searches_count = len(scraper.config.searches)
        logging.info(f"Configuración: {sources_count} fuentes, {searches_count} búsquedas")
        
        # Ejecutar prueba
        logging.info("Ejecutando prueba de tarea...")
        if sources_count > 0:
            source = scraper.config.sources[0]
            task_id = scraper.run_source_now(source.id)
            logging.info(f"Tarea iniciada con ID: {task_id}")
        
        logging.info("Prueba completada")
    else:
        logging.error("No se pudo inicializar el scraper")
