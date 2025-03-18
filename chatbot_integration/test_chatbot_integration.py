"""
Script para probar la integración del chatbot con el sistema de scraping.
Permite simular consultas y ver cómo se integrarían los datos del scraper.
"""
import os
import sys
import json
import argparse
import logging
from datetime import datetime

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler("test_chatbot_integration.log"),
        logging.StreamHandler()
    ]
)

try:
    # Importar integración del chatbot
    from chatbot_scraper_integration import enhance_chatbot_context, init_connector
    from bot_chat_integration import enhance_bot_response
except ImportError as e:
    logging.error(f"Error al importar módulos: {e}")
    logging.error("Asegúrate de estar en el directorio correcto y que los archivos existen")
    sys.exit(1)

def test_query(query, use_color=True):
    """
    Prueba una consulta al chatbot con la integración del scraper.
    
    Args:
        query: Consulta a probar
        use_color: Si True, usa colores en la salida
    """
    # Inicializar conector
    try:
        init_connector()
        logging.info("Conector inicializado correctamente")
    except Exception as e:
        logging.error(f"Error al inicializar conector: {e}")
        return
    
    # Colores ANSI para terminal
    RESET = "\033[0m"
    BOLD = "\033[1m"
    BLUE = "\033[34m" 
    GREEN = "\033[32m"
    YELLOW = "\033[33m"
    
    if not use_color:
        RESET = BOLD = BLUE = GREEN = YELLOW = ""
    
    print(f"\n{BOLD}{'='*70}{RESET}")
    print(f"{BOLD}Consulta:{RESET} {query}")
    print(f"{BOLD}{'='*70}{RESET}\n")
    
    # 1. Obtener contexto enriquecido
    try:
        print(f"{BOLD}{BLUE}1. Obteniendo contexto del scraper...{RESET}")
        context = enhance_chatbot_context(query)
        
        print(f"\n{BOLD}Categoría detectada:{RESET} {context.get('category', 'ninguna')}")
        print(f"{BOLD}Resultados encontrados:{RESET} {len(context.get('scraped_data', []))}")
        
        if context.get('scraped_data'):
            print(f"\n{BOLD}Datos encontrados:{RESET}")
            for i, item in enumerate(context.get('scraped_data', [])[:3]):
                print(f"\n{BOLD}[Resultado {i+1}]{RESET}")
                print(f"- {BOLD}Contenido:{RESET} {item.get('content', '')[:100]}...")
                print(f"- {BOLD}Fuente:{RESET} {item.get('source', 'desconocida')}")
                print(f"- {BOLD}Relevancia:{RESET} {item.get('relevance', 0)}")
        else:
            print("\nNo se encontraron datos relevantes en el scraper")
            
    except Exception as e:
        logging.error(f"Error al obtener contexto: {e}")
        print(f"\n{BOLD}Error al obtener contexto del scraper:{RESET} {str(e)}")
    
    # 2. Obtener respuesta mejorada
    try:
        print(f"\n{BOLD}{GREEN}2. Generando respuesta mejorada...{RESET}")
        
        # Crear una respuesta original simulada
        original_response = f"Esta es una respuesta original simulada para la consulta: {query}"
        
        # Generar respuesta mejorada
        enhanced = enhance_bot_response(query, original_response)
        
        print(f"\n{BOLD}Fuente de la respuesta:{RESET} {enhanced.get('source', 'desconocida')}")
        print(f"\n{BOLD}{YELLOW}Respuesta final:{RESET}\n")
        print(enhanced.get('response', 'No se pudo generar una respuesta'))
        
    except Exception as e:
        logging.error(f"Error al generar respuesta: {e}")
        print(f"\n{BOLD}Error al generar respuesta:{RESET} {str(e)}")
    
    print(f"\n{BOLD}{'='*70}{RESET}\n")

def main():
    parser = argparse.ArgumentParser(description="Prueba la integración del chatbot con el scraper")
    parser.add_argument("--query", "-q", type=str, help="Consulta a probar")
    parser.add_argument("--no-color", action="store_true", help="Desactivar colores en la salida")
    parser.add_argument("--interactive", "-i", action="store_true", help="Modo interactivo")
    
    args = parser.parse_args()
    
    if args.interactive:
        print("Modo interactivo. Escribe 'salir' para terminar.")
        
        while True:
            try:
                query = input("\nConsulta > ")
                if query.lower() in ["salir", "exit", "quit", "q"]:
                    break
                    
                if query.strip():
                    test_query(query, not args.no_color)
                    
            except KeyboardInterrupt:
                print("\nSaliendo...")
                break
            except Exception as e:
                logging.error(f"Error en modo interactivo: {e}")
                print(f"Error: {e}")
    
    elif args.query:
        test_query(args.query, not args.no_color)
    
    else:
        # Consultas de ejemplo
        example_queries = [
            "¿Qué puedo hacer en Ibiza?",
            "¿Cuáles son las mejores playas de Ibiza?",
            "¿Qué fiestas hay en Ibiza este verano?",
            "¿Dónde puedo comer comida típica ibicenca?",
            "¿Cómo llego a Es Vedrà?",
        ]
        
        print("Usando consultas de ejemplo:")
        for query in example_queries:
            test_query(query, not args.no_color)

if __name__ == "__main__":
    main()
