"""
Script para iniciar el servidor web con la integración de chatbot-scraper.
"""
import os
import sys
import logging
from datetime import datetime

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler(f"logs/server_logs_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("server")

# Asegurar que existe el directorio de logs
os.makedirs("logs", exist_ok=True)

# Importar la aplicación principal
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from app_integrated import app

def main():
    """Función principal para iniciar el servidor con integración chatbot-scraper"""
    try:
        # Importar módulos de integración
        from chatbot_scraper_integration import enhance_chatbot_context, init_connector
        
        # Configurar la integración
        logger.info("Configurando integración chatbot-scraper...")
        
        # Inicializar conector entre chatbot y scraper
        init_status = init_connector(app)
        
        if init_status:
            logger.info("Integración chatbot-scraper configurada correctamente")
            
            # Cargar información del scraper
            context = enhance_chatbot_context("información")
            if context:
                logger.info(f"Contexto inicial del chatbot enriquecido con {len(context)} items")
            else:
                logger.warning("No se pudo enriquecer el contexto inicial del chatbot")
        else:
            logger.warning("Integración chatbot-scraper no pudo ser configurada completamente")
    
    except Exception as e:
        logger.error(f"Error al inicializar la integración chatbot-scraper: {e}")
        logger.info("Continuando sin la integración del chatbot con el scraper...")
    
    # Configuración del servidor
    host = os.environ.get('HOST', '0.0.0.0')
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('DEBUG', 'False').lower() == 'true'
    
    # Arrancar el servidor
    logger.info(f"Iniciando servidor en {host}:{port} (debug={debug})")
    app.run(host=host, port=port, debug=debug)

if __name__ == "__main__":
    main()
