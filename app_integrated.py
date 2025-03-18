import os
import json
import uuid
import random
import re
import copy
import time
import threading
import logging
import traceback
from datetime import datetime, timedelta
from flask import Flask, request, jsonify, render_template, redirect, url_for, session, send_from_directory, flash, make_response
from werkzeug.utils import secure_filename
from urllib.parse import urlparse
from bs4 import BeautifulSoup
import requests
from flask import Response
from archon_scraper import ArchonScraperAgent
import sys
from status_routes import status_bp  # Importar el blueprint de status
from auto_scraper_routes import init_auto_scraper_bp  # Importar la funciÃ³n de inicializaciÃ³n del blueprint del auto-scraper

# Importar el auto-scraper para bÃºsquedas en Google
try:
    from auto_scraper import AutoScraper
    AUTO_SCRAPER_AVAILABLE = True
    print("Auto-Scraper cargado correctamente")
except ImportError as e:
    AUTO_SCRAPER_AVAILABLE = False
    print(f"No se pudo cargar el Auto-Scraper: {e}")

# Importar el agente de scraping con Archon
try:
    from archon_scraper import ArchonScraperAgent
    ARCHON_AVAILABLE = True
    print("Agente de scraping con Archon cargado correctamente")
except ImportError as e:
    ARCHON_AVAILABLE = False
    print(f"No se pudo cargar el agente de scraping con Archon: {e}")

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'ibiza-ai-secret-key-2025')
# Configurar el servidor para no usar cachÃ© en archivos estÃ¡ticos
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0
KNOWLEDGE_BASE_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data', 'knowledge_base.json')
UPLOAD_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uploads')
# Crear directorios si no existen
os.makedirs(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data'), exist_ok=True)
os.makedirs(UPLOAD_DIR, exist_ok=True)

# ConfiguraciÃ³n
DATA_DIR = "data"
if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR)

# Sistema de base de conocimiento unificado
KNOWLEDGE_BASE = {
    'events': [],     # Eventos en Ibiza
    'tickets': [],    # Tickets de discotecas
    'venues': [],     # InformaciÃ³n sobre locales y discotecas
    'beaches': [],    # InformaciÃ³n sobre playas
    'restaurants': [], # InformaciÃ³n sobre restaurantes
    'hotels': [],     # InformaciÃ³n sobre hoteles
    'activities': [], # Actividades y excursiones
    'transport': [],  # InformaciÃ³n sobre transporte
    'weather': [],    # InformaciÃ³n sobre clima
    'faq': []         # Preguntas frecuentes
}

# Estado del scraping
SCRAPING_STATUS = {
    'isActive': False,
    'progress': 0,
    'lastRun': None
}

# ConfiguraciÃ³n del scraper
SCRAPER_CONFIG = {
    'sources': {
        'events': [
            'https://www.ibiza-spotlight.com/events', 
            'https://www.discoticketibiza.com/events',
            'https://www.ibiza-events.com'
        ],
        'tickets': [
            'https://www.ibiza-tickets.com', 
            'https://www.discoticketibiza.com',
            'https://www.clubtickets.com/ibiza'
        ],
        'venues': [
            'https://www.ibiza-spotlight.com/clubs', 
            'https://www.discoticketibiza.com/venues'
        ]
    },
    'schedule': {
        'events': 24,      # Actualizar cada 24 horas
        'tickets': 12,     # Actualizar cada 12 horas
        'venues': 72,      # Actualizar cada 72 horas
        'beaches': 168,    # Actualizar cada semana
        'restaurants': 168 # Actualizar cada semana
    },
    'last_run': {},
    'enabled': True
}

# FunciÃ³n para guardar la base de conocimiento en disco
def save_knowledge_base():
    try:
        with open('data/knowledge_base.json', 'w', encoding='utf-8') as f:
            json.dump(KNOWLEDGE_BASE, f, ensure_ascii=False, indent=2)
        print(f"Base de conocimiento guardada: {len(KNOWLEDGE_BASE)} categorÃ­as")
        return True
    except Exception as e:
        print(f"Error al guardar la base de conocimiento: {e}")
        return False

# FunciÃ³n para cargar la base de conocimiento desde disco
def load_knowledge_base():
    global KNOWLEDGE_BASE
    try:
        if os.path.exists('data/knowledge_base.json'):
            with open('data/knowledge_base.json', 'r', encoding='utf-8') as f:
                loaded_kb = json.load(f)
            
            # Asegurar que todas las categorÃ­as existan
            for category in KNOWLEDGE_BASE.keys():
                if category not in loaded_kb:
                    loaded_kb[category] = []
            
            KNOWLEDGE_BASE = loaded_kb
            print(f"Base de conocimiento cargada: {len(KNOWLEDGE_BASE)} categorÃ­as")
            return True
        return False
    except Exception as e:
        print(f"Error al cargar la base de conocimiento: {e}")
        return False

# Cargar la base de conocimiento al iniciar
if not os.path.exists('data'):
    os.makedirs('data')
load_knowledge_base()

# Base de datos simple (en memoria)
DATABASE = {
    "general": [],
    "eventos": [],
    "lugares": [],
    "restaurantes": [],
    "playas": []
}

# Lista de categorÃ­as disponibles
categories = list(DATABASE.keys())

# Cargar datos guardados si existen
for category in categories:
    file_path = os.path.join(DATA_DIR, f"{category}.json")
    if os.path.exists(file_path):
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                DATABASE[category] = json.load(f)
        except Exception as e:
            print(f"Error loading {category} data: {e}")

# FunciÃ³n para guardar datos
def save_data(category, data):
    file_path = os.path.join(DATA_DIR, f"{category}.json")
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        print(f"Error saving {category} data: {e}")
        return False

# Respuestas predefinidas para preguntas frecuentes
predefined_responses = {
    "hola": "Â¡Hola! Soy el asistente virtual de informaciÃ³n sobre Ibiza. Â¿En quÃ© puedo ayudarte?",
    "cÃ³mo estÃ¡s": "Estoy bien, gracias por preguntar. Â¿En quÃ© puedo ayudarte con informaciÃ³n sobre Ibiza?",
    "quÃ© fiestas hay en ibiza": "Ibiza es famosa por sus fiestas y discotecas. Algunos de los clubs mÃ¡s populares son Pacha, Amnesia, UshuaÃ¯a y HÃ¯ Ibiza. Cada verano hay eventos especiales con DJs internacionales. Â¿Te interesa alguna fecha o lugar en particular?",
    "mejores playas": "Algunas de las mejores playas de Ibiza son Ses Salines, Cala Comte, Cala d'Hort (con vistas a Es VedrÃ ), Playa d'en Bossa y Cala Bassa. Cada una tiene su encanto particular. Â¿Quieres informaciÃ³n sobre alguna en especÃ­fico?",
    "restaurantes recomendados": "Hay excelentes restaurantes en Ibiza, como Sa Capella (en un antiguo convento), Es Torrent (mariscos frescos), Can Carlitos (junto al mar en Formentera), La Paloma (cocina mediterrÃ¡nea ecolÃ³gica) y Es Xarcu (pescado fresco). Â¿Tienes alguna preferencia gastronÃ³mica?"
}

# ConfiguraciÃ³n por defecto de Archon
ARCHON_CONFIG = {
    'modelTemp': 0.7,
    'maxTokens': 4096,
    'reasoningDepth': 'medium',
    'webAccess': True,
    'activeModel': 'gemini-pro',
    'defaultEmbeddings': 'text-embedding-3-small',
    'reasonerModel': 'deepseek-r1:7b-8k',
    'archonVersion': 'v3-mcp-support'
}

# Inicializar el agente de scraping de Archon si estÃ¡ disponible
archon_agent = None
if ARCHON_AVAILABLE:
    try:
        archon_agent = ArchonScraperAgent(
            model=ARCHON_CONFIG['activeModel'],
            embedding_model=ARCHON_CONFIG['defaultEmbeddings'],
            reasoner_model=ARCHON_CONFIG['reasonerModel'],
            temperature=ARCHON_CONFIG['modelTemp']
        )
        print("Agente Archon inicializado correctamente")
    except Exception as e:
        print(f"Error inicializando el agente Archon: {e}")

# Variables para memoria de conversaciÃ³n
CONVERSATION_MEMORY = {}  # {session_id: [lista de mensajes]}
MAX_MEMORY_LENGTH = 10    # NÃºmero mÃ¡ximo de intercambios a recordar
MAX_SESSION_COUNT = 50    # MÃ¡ximo nÃºmero de sesiones concurrentes
SESSION_PURGE_THRESHOLD = 60 * 60 * 3  # 3 horas en segundos

# ConfiguraciÃ³n para optimizar uso de memoria
import gc

# FunciÃ³n para optimizar memoria
def optimize_memory():
    """Fuerza la limpieza de memoria no utilizada"""
    collected = gc.collect()
    return collected

# FunciÃ³n para limpieza agresiva de memoria
def aggressive_memory_cleanup():
    """Realiza una limpieza agresiva de memoria cuando los niveles son crÃ­ticos"""
    # Limpiar todas las sesiones inactivas por mÃ¡s de 30 minutos
    global CONVERSATION_MEMORY, SESSION_PURGE_THRESHOLD
    
    # Almacenar el valor original
    original_threshold = SESSION_PURGE_THRESHOLD
    
    # Bajar temporalmente el umbral de purga a 30 minutos
    SESSION_PURGE_THRESHOLD = 60 * 30  # 30 minutos
    purged_sessions = purge_old_sessions()
    
    # Restaurar el umbral original
    SESSION_PURGE_THRESHOLD = original_threshold
    
    # Forzar la recolecciÃ³n de basura
    collected = gc.collect()
    gc.collect()  # Segunda llamada para ser mÃ¡s agresivos
    
    # Limitar el tamaÃ±o de la cache de respuestas
    if 'response_cache' in globals() and hasattr(response_cache, 'cache_clear'):
        response_cache.cache_clear()
    
    # Si tenemos acceso a la informaciÃ³n de memoria, intentar reducir el uso
    try:
        import psutil
        memory = psutil.virtual_memory()
        
        if memory.percent > 90:
            # SituaciÃ³n crÃ­tica, limpiar mÃ¡s agresivamente
            for _ in range(5):
                gc.collect()
            
            # Si sigue siendo crÃ­tico, limpia todas las sesiones excepto las mÃ¡s recientes
            if psutil.virtual_memory().percent > 90:
                # Conservar solo las 10 sesiones mÃ¡s recientes
                sorted_sessions = sorted(
                    CONVERSATION_MEMORY.items(),
                    key=lambda x: datetime.fromisoformat(x[1][-1].get('timestamp', '')) if x[1] else datetime.min,
                    reverse=True  # De mÃ¡s reciente a mÃ¡s antigua
                )
                
                CONVERSATION_MEMORY = {k: v for k, v in sorted_sessions[:10]}
    except ImportError:
        pass
    
    return {"purged_sessions": purged_sessions, "collected_objects": collected}

# FunciÃ³n para limpiar memoria de sesiones antiguas (ejecutar periÃ³dicamente)
def purge_old_sessions():
    """Elimina las sesiones de chat inactivas que han excedido el tiempo mÃ¡ximo"""
    global CONVERSATION_MEMORY
    
    current_time = datetime.now()
    sessions_to_remove = []
    
    for session_id, messages in CONVERSATION_MEMORY.items():
        if not messages:
            sessions_to_remove.append(session_id)
            continue
            
        # Verificar cuando fue el Ãºltimo mensaje
        last_message = messages[-1]
        last_timestamp = datetime.fromisoformat(last_message.get('timestamp', ''))
        time_diff = (current_time - last_timestamp).total_seconds()
        
        if time_diff > SESSION_PURGE_THRESHOLD:
            sessions_to_remove.append(session_id)
    
    # Eliminar sesiones antiguas
    for session_id in sessions_to_remove:
        del CONVERSATION_MEMORY[session_id]
    
    # Si aÃºn hay demasiadas sesiones, eliminar las mÃ¡s antiguas
    if len(CONVERSATION_MEMORY) > MAX_SESSION_COUNT:
        # Ordenar sesiones por Ãºltima actividad
        sorted_sessions = sorted(
            CONVERSATION_MEMORY.items(),
            key=lambda x: datetime.fromisoformat(x[1][-1].get('timestamp', '')) if x[1] else datetime.min,
            reverse=False  # De mÃ¡s antigua a mÃ¡s reciente
        )
        
        # Eliminar las sesiones mÃ¡s antiguas hasta alcanzar el lÃ­mite
        sessions_to_remove = sorted_sessions[:(len(CONVERSATION_MEMORY) - MAX_SESSION_COUNT)]
        for session_id, _ in sessions_to_remove:
            del CONVERSATION_MEMORY[session_id]
    
    return len(sessions_to_remove)

# Importaciones adicionales para gestiÃ³n de memoria
import psutil
import time
import threading
from functools import lru_cache

# ConfiguraciÃ³n para gestiÃ³n de memoria
MEMORY_MONITOR_ENABLED = True
MEMORY_THRESHOLD = 75  # Porcentaje antes de iniciar limpiezas agresivas

# Cache para respuestas frecuentes con tiempo de expiraciÃ³n
RESPONSE_CACHE = {}
CACHE_EXPIRY = 60 * 30  # 30 minutos en segundos

# FunciÃ³n para supervisar el uso de memoria y realizar limpiezas periÃ³dicas
def monitor_memory():
    """Monitor de memoria que ejecuta limpiezas cuando se supera el umbral"""
    if not MEMORY_MONITOR_ENABLED:
        return
        
    while True:
        # Verificar uso de memoria
        memory_usage = psutil.virtual_memory().percent
        
        if memory_usage > MEMORY_THRESHOLD:
            # Ejecutar limpieza agresiva
            print(f"Uso de memoria elevado ({memory_usage}%). Iniciando limpieza...")
            
            # Limpiar cachÃ© de respuestas antiguas
            current_time = time.time()
            keys_to_remove = []
            for key, (response, timestamp) in RESPONSE_CACHE.items():
                if current_time - timestamp > CACHE_EXPIRY:
                    keys_to_remove.append(key)
            
            for key in keys_to_remove:
                del RESPONSE_CACHE[key]
            
            # Limpiar sesiones antiguas
            purged = purge_old_sessions()
            
            # Forzar recolecciÃ³n de basura varias veces
            for _ in range(3):
                collected = gc.collect()
            
            # Registrar resultados
            memory_after = psutil.virtual_memory().percent
            print(f"Limpieza de memoria completada: {purged} sesiones purgadas, memoria: {memory_usage}% â {memory_after}%")
        
        # Esperar antes de la prÃ³xima verificaciÃ³n
        time.sleep(60)  # Verificar cada minuto

# Iniciar el monitor de memoria en un hilo separado
if MEMORY_MONITOR_ENABLED:
    memory_thread = threading.Thread(target=monitor_memory, daemon=True)
    memory_thread.start()

# Optimizar la carga de la base de conocimiento
@lru_cache(maxsize=1)
def get_knowledge_base():
    """Retorna la base de conocimiento con cachÃ©"""
    return KNOWLEDGE_BASE

# Modificar check_knowledge_base para usar el cachÃ© de respuestas y la base de conocimiento cacheada
def check_knowledge_base(query, just_check=False):
    """
    Buscar en la base de conocimiento por una coincidencia con la consulta del usuario.
    Usa cachÃ© para consultas repetidas.
    
    Args:
        query: Texto de la consulta del usuario
        just_check: Si es True, solo verifica si hay coincidencias sin generar respuesta
        
    Returns:
        Una respuesta textual basada en la base de conocimiento o None si no hay coincidencias.
        Si just_check es True, devuelve un booleano indicando si hay coincidencias.
    """
    if not query:
        return False if just_check else None
    
    # Si solo estamos verificando, no usar cachÃ©
    if not just_check:
        # Verificar cachÃ© para la consulta
        cache_key = f"kb_{query.lower()}"
        if cache_key in RESPONSE_CACHE:
            cached_response, _ = RESPONSE_CACHE[cache_key]
            return cached_response
    
    # Obtener la base de conocimiento cacheada
    knowledge_base = get_knowledge_base()
    
    # Resto del cÃ³digo como antes...
    query_words = query.lower().split()
    categories_to_search = []
    results = []
    
    # Mapeo de palabras clave a categorÃ­as
    keyword_map = {
        'fiesta': 'events',
        'evento': 'events',
        'club': 'venues',
        'discoteca': 'venues',
        'playa': 'beaches',
        'cala': 'beaches',
        'restaurante': 'restaurants',
        'comer': 'restaurants',
        'hotel': 'hotels',
        'alojamiento': 'hotels',
        'hostal': 'hotels',
        'actividad': 'activities',
        'tour': 'activities',
        'excursiÃ³n': 'activities',
        'transporte': 'transport',
        'como llegar': 'transport',
        'taxi': 'transport',
        'bus': 'transport',
        'barco': 'transport',
        'tiempo': 'weather',
        'clima': 'weather',
        'lluvia': 'weather',
        'temperatura': 'weather',
        'pregunta': 'faq',
        'duda': 'faq',
        'informaciÃ³n': 'faq'
    }
    
    # Determinar categorÃ­as por palabras clave
    for word, category in keyword_map.items():
        for q_word in query_words:
            if word in q_word or q_word in word:
                if category not in categories_to_search:
                    categories_to_search.append(category)
    
    # Si no hay categorÃ­as especÃ­ficas, buscar en todas
    if not categories_to_search:
        categories_to_search = list(knowledge_base.keys())
    
    # Buscar en las categorÃ­as determinadas
    for category in categories_to_search:
        if category not in knowledge_base:
            continue
            
        for item in knowledge_base[category]:
            match_score = 0
            
            # Buscar coincidencias en el tÃ­tulo (peso alto)
            if 'title' in item and item['title']:
                title_lower = item['title'].lower()
                for word in query_words:
                    if word in title_lower:
                        match_score += 5  # Mayor peso para coincidencias en tÃ­tulo
            
            # Buscar coincidencias en la descripciÃ³n (peso medio)
            if 'description' in item and item['description']:
                desc_lower = item['description'].lower()
                for word in query_words:
                    if word in desc_lower:
                        match_score += 3  # Peso medio para coincidencias en descripciÃ³n
            
            # Buscar coincidencias en etiquetas (peso alto)
            if 'tags' in item and item['tags']:
                for tag in item['tags']:
                    tag_lower = tag.lower()
                    for word in query_words:
                        if word in tag_lower or tag_lower in word:
                            match_score += 4  # Peso alto para coincidencias en etiquetas
            
            # Si hay coincidencia, aÃ±adir a los resultados
            if match_score > 0:
                results.append({
                    'item': item,
                    'category': category,
                    'score': match_score
                })
    
    # Ordenar resultados por puntuaciÃ³n
    results.sort(key=lambda x: x['score'], reverse=True)
    
    # Si solo estamos verificando si hay resultados
    if just_check:
        return len(results) > 0
    
    # Si no hay resultados, devolver None
    if not results:
        return None
    
    # Limitar a top 3 resultados
    top_results = results[:3]
    
    # Construir respuesta basada en los resultados
    response_parts = []
    
    # Mapeo de categorÃ­as a texto en espaÃ±ol
    category_names = {
        'events': 'EVENTO',
        'tickets': 'ENTRADA',
        'venues': 'LUGAR',
        'beaches': 'PLAYA',
        'restaurants': 'RESTAURANTE',
        'hotels': 'HOTEL',
        'activities': 'ACTIVIDAD',
        'transport': 'TRANSPORTE',
        'weather': 'CLIMA',
        'faq': 'FAQ'
    }
    
    # Para cada resultado, agregar una parte a la respuesta
    for r in top_results:
        item = r['item']
        category = category_names.get(r['category'], r['category'].upper())
        
        # Construir texto para este item
        item_text = f"{category}: {item.get('title', 'Sin tÃ­tulo')}"
        
        if 'description' in item and item['description']:
            # Limitar longitud de descripciÃ³n
            desc = item['description']
            if len(desc) > 100:
                desc = desc[:97] + "..."
            item_text += f" - {desc}"
        
        response_parts.append(item_text)
    
    # Crear introducciÃ³n basada en la primera categorÃ­a de resultados
    first_category = category_names.get(results[0]['category'], 'informaciÃ³n')
    intro = f"He encontrado {len(response_parts)} resultados relacionados con tu bÃºsqueda sobre {first_category.lower()}:"
    
    # Combinar todo en respuesta final
    response = intro + "\n\n" + "\n\n".join(response_parts)
    
    # AÃ±adir cierre con invitaciÃ³n
    response += "\n\nÂ¿Te gustarÃ­a saber mÃ¡s detalles sobre alguno de estos elementos?"
    
    # Guardar en cachÃ©
    RESPONSE_CACHE[f"kb_{query.lower()}"] = (response, time.time())
    
    return response

# FunciÃ³n para mejorar el razonamiento incorporando la base de conocimiento
def enhanced_reasoning(user_message, session_id):
    """
    Utiliza Archon para un razonamiento mejorado, integrando la base de conocimiento
    y el historial de conversaciÃ³n.
    """
    try:
        # 1. Recuperar historial de la conversaciÃ³n si existe
        conversation_history = ""
        if session_id in CONVERSATION_MEMORY:
            memory = CONVERSATION_MEMORY[session_id]
            for exchange in memory:
                conversation_history += f"Usuario: {exchange['user']}\n"
                conversation_history += f"Asistente: {exchange['assistant']}\n\n"
        
        # 2. Buscar informaciÃ³n relevante en la base de conocimiento
        kb_results = []
        
        # Buscar en eventos
        if 'events' in KNOWLEDGE_BASE and KNOWLEDGE_BASE['events']:
            event_results = []
            for event in KNOWLEDGE_BASE['events']:
                # Calcular relevancia simple
                relevance = 0
                for term in user_message.lower().split():
                    if term in event.get('title', '').lower() or term in event.get('description', '').lower():
                        relevance += 1
                
                if relevance > 0:
                    event_results.append({
                        'data': event,
                        'relevance': relevance
                    })
            
            # Ordenar por relevancia y tomar los primeros 3
            event_results.sort(key=lambda x: x['relevance'], reverse=True)
            for result in event_results[:3]:
                event_data = result['data']
                kb_results.append(f"EVENTO: {event_data.get('title')} - {event_data.get('date')} - {event_data.get('venue')} - {event_data.get('description')}")
        
        # Buscar en tickets
        if 'tickets' in KNOWLEDGE_BASE and KNOWLEDGE_BASE['tickets']:
            ticket_results = []
            for ticket in KNOWLEDGE_BASE['tickets']:
                # Calcular relevancia
                relevance = 0
                for term in user_message.lower().split():
                    if term in ticket.get('event', '').lower() or term in ticket.get('venue', '').lower():
                        relevance += 1
                
                if relevance > 0:
                    ticket_results.append({
                        'data': ticket,
                        'relevance': relevance
                    })
            
            # Ordenar y tomar los primeros 2
            ticket_results.sort(key=lambda x: x['relevance'], reverse=True)
            for result in ticket_results[:2]:
                ticket_data = result['data']
                kb_results.append(f"TICKET: {ticket_data.get('event')} - {ticket_data.get('venue')} - Precio: {ticket_data.get('price')} - URL: {ticket_data.get('url')}")
        
        # Buscar en venues
        if 'venues' in KNOWLEDGE_BASE and KNOWLEDGE_BASE['venues']:
            venue_results = []
            for venue in KNOWLEDGE_BASE['venues']:
                # Calcular relevancia
                relevance = 0
                for term in user_message.lower().split():
                    if term in venue.get('name', '').lower() or term in venue.get('description', '').lower():
                        relevance += 1
                
                if relevance > 0:
                    venue_results.append({
                        'data': venue,
                        'relevance': relevance
                    })
            
            # Ordenar y tomar los primeros 2
            venue_results.sort(key=lambda x: x['relevance'], reverse=True)
            for result in venue_results[:2]:
                venue_data = result['data']
                kb_results.append(f"LUGAR: {venue_data.get('name')} - {venue_data.get('location')} - {venue_data.get('description')}")
        
        # Buscar en playas
        if 'beaches' in KNOWLEDGE_BASE and KNOWLEDGE_BASE['beaches']:
            beach_results = []
            for beach in KNOWLEDGE_BASE['beaches']:
                # Calcular relevancia
                relevance = 0
                for term in user_message.lower().split():
                    if term in beach.get('name', '').lower() or term in beach.get('description', '').lower():
                        relevance += 1
                
                if relevance > 0:
                    beach_results.append({
                        'data': beach,
                        'relevance': relevance
                    })
            
            # Ordenar y tomar las primeras 2
            beach_results.sort(key=lambda x: x['relevance'], reverse=True)
            for result in beach_results[:2]:
                beach_data = result['data']
                kb_results.append(f"PLAYA: {beach_data.get('name')} - {beach_data.get('location')} - {beach_data.get('description')}")
        
        # Buscar en restaurantes
        if 'restaurants' in KNOWLEDGE_BASE and KNOWLEDGE_BASE['restaurants']:
            restaurant_results = []
            for restaurant in KNOWLEDGE_BASE['restaurants']:
                # Calcular relevancia
                relevance = 0
                for term in user_message.lower().split():
                    if term in restaurant.get('name', '').lower() or term in restaurant.get('cuisine', '').lower():
                        relevance += 1
                
                if relevance > 0:
                    restaurant_results.append({
                        'data': restaurant,
                        'relevance': relevance
                    })
            
            # Ordenar y tomar los primeros 2
            restaurant_results.sort(key=lambda x: x['relevance'], reverse=True)
            for result in restaurant_results[:2]:
                restaurant_data = result['data']
                kb_results.append(f"RESTAURANTE: {restaurant_data.get('name')} - {restaurant_data.get('cuisine')} - {restaurant_data.get('location')}")
        
        # NUEVO: Buscar en contenido multimedia
        if 'content' in KNOWLEDGE_BASE and KNOWLEDGE_BASE['content']:
            content_results = []
            for content in KNOWLEDGE_BASE['content']:
                # Calcular relevancia
                relevance = 0
                # Buscar en tÃ­tulo, descripciÃ³n y etiquetas
                for term in user_message.lower().split():
                    if term in content.get('title', '').lower():
                        relevance += 2  # Mayor peso para el tÃ­tulo
                    if term in content.get('description', '').lower():
                        relevance += 1
                    if any(term in tag.lower() for tag in content.get('tags', [])):
                        relevance += 1.5  # Buen peso para etiquetas
                
                # Buscar tambiÃ©n segÃºn el tipo de contenido (imagen, video, etc.)
                content_keywords = {
                    'image': ['imagen', 'foto', 'fotografÃ­a', 'fotografia', 'imÃ¡gen', 'imagen'],
                    'video': ['video', 'vÃ­deo', 'grabaciÃ³n', 'grabacion', 'clip'],
                    'document': ['documento', 'pdf', 'archivo', 'texto'],
                    'website': ['web', 'pÃ¡gina', 'pagina', 'sitio'],
                    'audio': ['audio', 'sonido', 'canciÃ³n', 'cancion', 'mÃºsica', 'musica']
                }
                
                content_type = content.get('content_type', '')
                if content_type in content_keywords:
                    for keyword in content_keywords[content_type]:
                        if keyword in user_message.lower():
                            relevance += 2  # Alto peso si busca especÃ­ficamente este tipo
                
                if relevance > 0:
                    content_results.append({
                        'data': content,
                        'relevance': relevance
                    })
            
            # Ordenar y tomar los primeros 3
            content_results.sort(key=lambda x: x['relevance'], reverse=True)
            for result in content_results[:3]:
                content_data = result['data']
                # Formateamos la informaciÃ³n segÃºn el tipo
                content_info = f"CONTENIDO ({content_data.get('content_type', 'archivo').upper()}): "
                content_info += f"{content_data.get('title')} - {content_data.get('description')[:100]}... "
                if content_data.get('tags'):
                    content_info += f"- Etiquetas: {', '.join(content_data.get('tags'))}"
                content_info += f" - URL: {request.host_url.rstrip('/')}{content_data.get('public_url')}"
                
                kb_results.append(content_info)
        
        # 3. Construir prompt completo para Archon
        kb_context = "\n".join(kb_results) if kb_results else "No se encontrÃ³ informaciÃ³n relevante en la base de conocimiento."
        
        prompt = f"""Eres un asistente virtual especializado en informaciÃ³n sobre Ibiza, 
especialmente sobre fiestas, eventos, locales y turismo para el aÃ±o 2025.

INFORMACIÃN DE CONTEXTO:
{kb_context}

HISTORIAL DE CONVERSACIÃN:
{conversation_history}

Por favor, responde de manera amigable, profesional y concisa a la siguiente consulta 
utilizando la informaciÃ³n de contexto cuando sea relevante:

CONSULTA DEL USUARIO: {user_message}"""

        # 4. Enviar a Archon para su procesamiento
        archon_result = call_archon_api(prompt)
        if archon_result and 'generated_text' in archon_result:
            result = archon_result['generated_text']
        else:
            result = "Lo siento, no pude procesar tu consulta en este momento. Por favor, intenta de nuevo mÃ¡s tarde."
        
        # Determinar la fuente de la respuesta 
        # (para analÃ­ticas, podemos saber si la respuesta vino principalmente de la base de conocimiento o del modelo)
        source = "archon"
        if len(kb_results) > 0:
            source = "knowledge_base+archon"
        
        return result, source
    except Exception as e:
        print(f"Error en enhanced_reasoning: {str(e)}")
        return "Lo siento, ocurriÃ³ un error al procesar tu consulta. Por favor, intenta de nuevo.", "error"

# FunciÃ³n para llamar a la API de Archon o simulaciÃ³n para razonamiento mejorado
def call_archon_api(prompt):
    """
    Llama a la API de Archon o usa una simulaciÃ³n si el agente no estÃ¡ disponible.
    
    Args:
        prompt: El mensaje de texto a enviar a Archon.
        
    Returns:
        Dictionary con la respuesta o un error.
    """
    global archon_agent
    
    try:
        # Si tenemos un agente Archon configurado, usarlo
        if archon_agent:
            response = archon_agent.answer_question(prompt, knowledge_base=KNOWLEDGE_BASE)
            return {
                'success': True,
                'generated_text': response,
                'model': ARCHON_CONFIG['activeModel']
            }
        else:
            # SimulaciÃ³n simplificada si no hay agente disponible
            # Extraer la consulta del usuario del prompt
            user_query = ""
            if "CONSULTA DEL USUARIO:" in prompt:
                user_query = prompt.split("CONSULTA DEL USUARIO:")[1].strip()
            
            # Extraer informaciÃ³n de contexto si estÃ¡ disponible
            context_info = []
            if "INFORMACIÃN DE CONTEXTO:" in prompt and "HISTORIAL DE CONVERSACIÃN:" in prompt:
                context_part = prompt.split("INFORMACIÃN DE CONTEXTO:")[1].split("HISTORIAL DE CONVERSACIÃN:")[0].strip()
                if context_part != "No se encontrÃ³ informaciÃ³n relevante en la base de conocimiento.":
                    context_info = [line.strip() for line in context_part.split('\n') if line.strip()]
            
            # Generar respuesta basada en el contexto
            if context_info:
                # Combinar informaciÃ³n de contexto en una respuesta coherente
                response = f"Basado en la informaciÃ³n disponible, puedo decirte que "
                
                # AÃ±adir detalles de los primeros 2-3 elementos de contexto
                for i, info in enumerate(context_info[:3]):
                    if "EVENTO:" in info:
                        event_details = info.replace("EVENTO:", "").strip()
                        response += f"hay un evento llamado {event_details.split(' - ')[0]}. "
                    elif "PLAYA:" in info:
                        beach_details = info.replace("PLAYA:", "").strip()
                        response += f"puedes visitar {beach_details.split(' - ')[0]}. "
                    elif "FAQ:" in info:
                        faq_details = info.replace("FAQ:", "").strip()
                        response += f"{faq_details} "
                
                response += "Â¿Hay algo mÃ¡s especÃ­fico que te gustarÃ­a saber?"
            else:
                # Respuesta genÃ©rica si no hay contexto
                response = "No tengo informaciÃ³n especÃ­fica sobre tu consulta en este momento. Puedo ayudarte con informaciÃ³n sobre playas, eventos, restaurantes y otros atractivos de Ibiza. Â¿PodrÃ­as reformular tu pregunta?"
            
            return {
                'success': True,
                'generated_text': response,
                'model': 'simulaciÃ³n-local'
            }
    
    except Exception as e:
        print(f"Error en call_archon_api: {str(e)}")
        return {
            'success': False,
            'error': str(e),
            'generated_text': "Lo siento, ha ocurrido un error al procesar tu consulta. Por favor, intÃ©ntalo de nuevo mÃ¡s tarde."
        }

@app.route('/api/archon_config', methods=['GET', 'POST'])
def archon_config():
    global ARCHON_CONFIG
    
    if request.method == 'POST':
        data = request.json
        if data:
            # Actualizar configuraciÃ³n con los valores recibidos
            ARCHON_CONFIG.update(data)
            return jsonify({'success': True, 'message': 'ConfiguraciÃ³n actualizada', 'config': ARCHON_CONFIG})
    
    # Si es GET o no hay datos en POST, devolver la configuraciÃ³n actual
    return jsonify({'success': True, 'config': ARCHON_CONFIG})

# Rutas principales
@app.route('/')
def index():
    # Preparar datos para la pÃ¡gina principal
    event_count = len(KNOWLEDGE_BASE.get('events', []))
    ticket_count = len(KNOWLEDGE_BASE.get('tickets', []))
    venue_count = len(KNOWLEDGE_BASE.get('venues', []))
    
    # Obtener los Ãºltimos eventos (hasta 5)
    latest_events = sorted(
        KNOWLEDGE_BASE.get('events', []),
        key=lambda x: x.get('scraped_at', ''),
        reverse=True
    )[:5]
    
    return render_template(
        'ibiza_info.html',
        event_count=event_count,
        ticket_count=ticket_count,
        venue_count=venue_count,
        latest_events=latest_events
    )

@app.route('/archivos')
def archivos():
    return render_template('archivos.html')

@app.route('/videos')
def videos():
    return render_template('videos.html')

@app.route('/imagenes')
def imagenes():
    return render_template('imagenes.html')

# Ruta /sitios desactivada segÃºn solicitud del usuario
# @app.route('/sitios')
# def sitios_web():
#     return render_template('sitios.html')

@app.route('/test')
def test():
    return render_template('test.html')

@app.route('/agente_ia')
def agente_ia():
    return render_template('archon_scraper.html')

@app.route('/original')
def original():
    return render_template('original_ia.html')

@app.route('/asistente')
def asistente_ibiza():
    return render_template('ibiza_asistente.html')

@app.route('/archon')
def archon_scraper():
    return render_template('archon_scraper.html')

# API para chat con el bot
@app.route('/api/bot_chat', methods=['POST'])
def bot_chat():
    data = request.json
    if not data or 'message' not in data:
        return jsonify({'success': False, 'error': 'Message is required'}), 400
    
    # Si el acceso web estÃ¡ activado y estamos usando un modelo avanzado, redirigir a archon_chat
    if ARCHON_CONFIG.get('webAccess', True) and ARCHON_CONFIG.get('activeModel') == 'gemini-pro':
        return archon_chat()
    
    # Comportamiento original si no se usa Archon
    user_message = data['message'].lower().strip()
    
    # Intentar usar respuestas predefinidas primero
    for key, response in predefined_responses.items():
        if key in user_message or user_message in key:
            return jsonify({'success': True, 'message': response})
    
    # Buscar informaciÃ³n en la base de datos del scraper
    scraper_response = query_scraper_database(user_message)
    if scraper_response:
        return jsonify({'success': True, 'message': scraper_response, 'source': 'scraper'})
    
    # Buscar en la base de conocimiento
    response = check_knowledge_base(user_message)
    if response:
        return jsonify({'success': True, 'message': response})
    
    # Si no hay respuesta predefinida y no se puede usar el framework de agente,
    # proporcionar una respuesta genÃ©rica pero Ãºtil
    return jsonify({
        'success': True, 
        'message': "Lo siento, no tengo informaciÃ³n especÃ­fica sobre eso. Puedes preguntarme sobre playas, restaurantes, discotecas o eventos en Ibiza, o usar la secciÃ³n de Scraping AutomÃ¡tico para buscar informaciÃ³n actualizada."
    })

@app.route('/api/archon_chat', methods=['POST'])
def archon_chat():
    global CONVERSATION_MEMORY
    
    data = request.json
    if not data or 'message' not in data:
        return jsonify({'success': False, 'error': 'Message is required'}), 400
    
    user_message = data['message'].strip()
    user_message_lower = user_message.lower()
    
    # Obtener o crear session_id
    session_id = data.get('session_id', request.remote_addr)
    
    try:
        # Paso 1: Buscar en respuestas predefinidas
        for key, response in predefined_responses.items():
            if key in user_message_lower or user_message_lower in key:
                # Guardar en memoria de conversaciÃ³n
                if session_id not in CONVERSATION_MEMORY:
                    CONVERSATION_MEMORY[session_id] = []
                
                CONVERSATION_MEMORY[session_id].append({
                    'user': user_message,
                    'bot': response,
                    'timestamp': datetime.now().isoformat()
                })
                
                return jsonify({
                    'success': True, 
                    'message': response,
                    'source': 'predefined',
                    'modelUsed': 'local'
                })
        
        # Paso 2: Verificar si hay informaciÃ³n en la base de conocimiento
        has_kb_info = check_knowledge_base(user_message_lower, just_check=True)
        
        # Paso 3: Utilizar razonamiento avanzado con historial de conversaciÃ³n
        enhanced_response, source = enhanced_reasoning(user_message, session_id)
        
        # Determinar la fuente correcta de la respuesta 
        # (para analÃ­ticas, podemos saber si la respuesta vino principalmente de la base de conocimiento o del modelo)
        if has_kb_info and source == "archon":
            source = "knowledge_base+archon"
        
        if enhanced_response:
            # Guardar en memoria de conversaciÃ³n
            if session_id not in CONVERSATION_MEMORY:
                CONVERSATION_MEMORY[session_id] = []
            
            CONVERSATION_MEMORY[session_id].append({
                'user': user_message,
                'bot': enhanced_response,
                'timestamp': datetime.now().isoformat()
            })
            
            # Limitar el tamaÃ±o de la memoria de conversaciÃ³n
            if len(CONVERSATION_MEMORY[session_id]) > MAX_MEMORY_LENGTH * 2:
                CONVERSATION_MEMORY[session_id] = CONVERSATION_MEMORY[session_id][-MAX_MEMORY_LENGTH * 2:]
            
            return jsonify({
                'success': True,
                'message': enhanced_response,
                'source': source,
                'modelUsed': ARCHON_CONFIG['activeModel']
            })
        
        # Paso 4: Si todo lo demÃ¡s falla, generar respuesta contextual basada en el tema
        topics = {
            'evento': 'eventos y fiestas',
            'fiesta': 'eventos y fiestas',
            'discoteca': 'clubes y locales nocturnos',
            'ticket': 'entradas para eventos y clubes',
            'playa': 'playas y calas',
            'hotel': 'alojamiento',
            'restaurante': 'restaurantes y gastronomÃ­a',
            'transporte': 'opciones de transporte'
        }
        
        detected_topic = None
        for word, topic in topics.items():
            if word in user_message_lower:
                detected_topic = topic
                break
        
        if detected_topic:
            response = f"Entiendo que estÃ¡s interesado en {detected_topic} de Ibiza. " + \
                      f"Aunque no tengo informaciÃ³n especÃ­fica sobre tu consulta en este momento, " + \
                      f"estoy constantemente actualizando mi base de datos con nuevos eventos, tickets y lugares. " + \
                      f"Te recomiendo volver a consultar mÃ¡s adelante o intentar con una pregunta mÃ¡s especÃ­fica."
        else:
            response = "Lo siento, no tengo informaciÃ³n especÃ­fica sobre eso. Puedes preguntarme sobre playas, restaurantes, discotecas o eventos en Ibiza."
        
        # Guardar en memoria de conversaciÃ³n
        if session_id not in CONVERSATION_MEMORY:
            CONVERSATION_MEMORY[session_id] = []
        
        CONVERSATION_MEMORY[session_id].append({
            'user': user_message,
            'bot': response,
            'timestamp': datetime.now().isoformat()
        })
        
        # Limitar el tamaÃ±o de la memoria de conversaciÃ³n
        if len(CONVERSATION_MEMORY[session_id]) > MAX_MEMORY_LENGTH * 2:
            CONVERSATION_MEMORY[session_id] = CONVERSATION_MEMORY[session_id][-MAX_MEMORY_LENGTH * 2:]
        
        return jsonify({
            'success': True,
            'message': response,
            'source': 'generated',
            'modelUsed': 'rules'
        })
        
    except Exception as e:
        print(f"Error en archon_chat: {e}")
        # Si falla todo, caer en respuesta genÃ©rica
        
        response = "Lo siento, he tenido un problema procesando tu consulta. Puedes preguntarme sobre playas, restaurantes, discotecas o eventos en Ibiza para 2025."
        
        # Intentar guardar en memoria de conversaciÃ³n
        try:
            if session_id not in CONVERSATION_MEMORY:
                CONVERSATION_MEMORY[session_id] = []
            
            CONVERSATION_MEMORY[session_id].append({
                'user': user_message,
                'bot': response,
                'timestamp': datetime.now().isoformat()
            })
        except:
            pass
        
        return jsonify({
            'success': True, 
            'message': response
        })

# Web scraping function
def scrape_website(url, category, options=None):
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        # Si no hay opciones, inicializar un diccionario vacÃ­o
        if options is None:
            options = {}
        
        tool = options.get('tool', 'auto')
        process_js = options.get('process_js', False)
        extract_structured = options.get('extract_structured', True)
        
        # Para contenido dinÃ¡mico con JavaScript, usamos Selenium o Playwright
        if process_js or tool in ['selenium', 'playwright']:
            try:
                # Intentar usar Selenium si estÃ¡ disponible y se solicita
                if tool == 'selenium' or (tool == 'auto' and process_js):
                    from selenium import webdriver
                    from selenium.webdriver.chrome.options import Options
                    from selenium.webdriver.chrome.service import Service
                    from webdriver_manager.chrome import ChromeDriverManager
                    
                    chrome_options = Options()
                    chrome_options.add_argument("--headless")
                    chrome_options.add_argument("--no-sandbox")
                    chrome_options.add_argument("--disable-dev-shm-usage")
                    
                    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
                    driver.get(url)
                    html_content = driver.page_source
                    driver.quit()
                
                # Usar Playwright si se solicita especÃ­ficamente
                elif tool == 'playwright':
                    from playwright.sync_api import sync_playwright
                    
                    with sync_playwright() as p:
                        browser = p.chromium.launch(headless=True)
                        page = browser.new_page()
                        page.goto(url)
                        html_content = page.content()
                        browser.close()
                
            except ImportError:
                # Si no estÃ¡n disponibles las bibliotecas, usar requests como fallback
                print(f"{tool} not available, falling back to requests")
                response = requests.get(url, headers=headers)
                html_content = response.text
        
        # Para scraping con Scrapy
        elif tool == 'scrapy':
            try:
                from scrapy.crawler import CrawlerProcess
                from scrapy import Spider, Request
                import tempfile
                
                # Clase Spider bÃ¡sica para Scrapy
                class BasicSpider(Spider):
                    name = 'basic_spider'
                    
                    def __init__(self, url, *args, **kwargs):
                        super(BasicSpider, self).__init__(*args, **kwargs)
                        self.start_urls = [url]
                        self.html_content = None
                    
                    def parse(self, response):
                        self.html_content = response.body.decode('utf-8')
                
                # Archivo temporal para la salida
                temp_file = tempfile.NamedTemporaryFile(delete=False)
                temp_file_path = temp_file.name
                temp_file.close()
                
                # ConfiguraciÃ³n del proceso de Scrapy
                process = CrawlerProcess(settings={
                    'USER_AGENT': headers['User-Agent'],
                    'ROBOTSTXT_OBEY': False,
                    'LOG_LEVEL': 'ERROR',
                    'FEED_FORMAT': 'json',
                    'FEED_URI': f'file://{temp_file_path}'
                })
                
                # Crear y ejecutar el spider
                spider = BasicSpider(url=url)
                process.crawl(spider)
                process.start()
                
                # Usar el contenido HTML obtenido por el spider
                html_content = spider.html_content
                
                # Eliminar el archivo temporal
                if os.path.exists(temp_file_path):
                    os.unlink(temp_file_path)
                
            except ImportError:
                # Si Scrapy no estÃ¡ disponible, usar requests como fallback
                print("Scrapy not available, falling back to requests")
                response = requests.get(url, headers=headers)
                html_content = response.text
        
        # Para Beautiful Soup o mÃ©todo automÃ¡tico sin JS
        else:
            response = requests.get(url, headers=headers)
            html_content = response.text
        
        # Usar Beautiful Soup para parsear el HTML
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Extraer tÃ­tulo y descripciÃ³n bÃ¡sica
        title = soup.title.string if soup.title else urlparse(url).netloc
        meta_description = soup.find('meta', attrs={'name': 'description'})
        description = meta_description['content'] if meta_description else "No description available"
        
        # Crear un nuevo item con la informaciÃ³n extraÃ­da
        item = {
            'url': url,
            'title': title,
            'description': description,
            'category': category,
            'date_added': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        
        # Extraer mÃ¡s informaciÃ³n basada en la categorÃ­a
        if category == 'eventos':
            # Buscar fechas, ubicaciones y detalles de eventos
            events = []
            event_elements = soup.find_all(['div', 'article', 'section'], class_=re.compile(r'event|evento|concert|festival', re.I))
            
            if not event_elements:
                # BÃºsqueda mÃ¡s genÃ©rica si no se encuentran elementos especÃ­ficos
                event_elements = soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5'], string=re.compile(r'event|evento|concert|festival|party|fiesta', re.I))
            
            for event_elem in event_elements[:10]:  # Limitar a 10 eventos para evitar sobrecarga
                event_title = event_elem.find(re.compile(r'h\d|strong')) or event_elem
                event_title = event_title.get_text(strip=True)
                
                event_date = event_elem.find(text=re.compile(r'\d{1,2}[/-]\d{1,2}[/-]\d{2,4}|\d{1,2}\s+de\s+\w+|\w+\s+\d{1,2}(st|nd|rd|th)?'))
                event_date = event_date.strip() if event_date else "Fecha no especificada"
                
                event_description = ""
                desc_elem = event_elem.find(['p', 'div'], class_=re.compile(r'desc|content|text', re.I))
                if desc_elem:
                    event_description = desc_elem.get_text(strip=True)
                
                events.append({
                    'title': event_title,
                    'date': event_date,
                    'description': event_description,
                    'location': {
                        'name': "Ibiza",
                        'address': "DirecciÃ³n no especificada"
                    }
                })
            
            item['events'] = events
        
        elif category == 'playas':
            # Extraer informaciÃ³n sobre playas
            beaches = []
            beach_elements = soup.find_all(['div', 'article', 'section'], class_=re.compile(r'beach|playa|cala', re.I))
            
            if not beach_elements:
                beach_elements = soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5'], string=re.compile(r'beach|playa|cala', re.I))
            
            for beach_elem in beach_elements[:10]:
                beach_name = beach_elem.find(re.compile(r'h\d|strong')) or beach_elem
                beach_name = beach_name.get_text(strip=True)
                
                beach_description = ""
                desc_elem = beach_elem.find(['p', 'div'], class_=re.compile(r'desc|content|text', re.I))
                if desc_elem:
                    beach_description = desc_elem.get_text(strip=True)
                
                beaches.append({
                    'name': beach_name,
                    'description': beach_description,
                    'features': []  # Se podrÃ­an extraer caracterÃ­sticas como si tiene servicios, tipo de arena, etc.
                })
            
            item['beaches'] = beaches
        
        # Si se solicita extraer imÃ¡genes
        if options.get('include_images', False):
            images = []
            for img in soup.find_all('img', src=True)[:20]:  # Limitar a 20 imÃ¡genes
                src = img['src']
                if not src.startswith(('http://', 'https://')):
                    # Convertir URLs relativas a absolutas
                    base_url = urlparse(url)
                    if src.startswith('/'):
                        src = f"{base_url.scheme}://{base_url.netloc}{src}"
                    else:
                        path = os.path.dirname(base_url.path)
                        src = f"{base_url.scheme}://{base_url.netloc}{path}/{src}"
                
                alt = img.get('alt', 'No description')
                images.append({
                    'src': src,
                    'alt': alt
                })
            
            item['images'] = images
        
        # ExtracciÃ³n de datos estructurados si se solicita
        if extract_structured:
            structured_data = []
            
            # Buscar datos JSON-LD
            for script in soup.find_all('script', type='application/ld+json'):
                try:
                    data = json.loads(script.string)
                    structured_data.append(data)
                except:
                    pass
            
            # Buscar datos de microdata/RDFa
            microdata_elems = soup.find_all(attrs={"itemtype": True})
            for elem in microdata_elems:
                item_type = elem.get('itemtype')
                props = {}
                for prop in elem.find_all(attrs={"itemprop": True}):
                    prop_name = prop.get('itemprop')
                    prop_value = prop.get('content') or prop.get_text(strip=True)
                    props[prop_name] = prop_value
                
                if props:
                    structured_data.append({
                        'type': item_type,
                        'properties': props
                    })
            
            item['structured_data'] = structured_data
        
        # Guardar en base de datos si se solicita
        if options.get('save_results', True):
            DATABASE[category].append(item)
            save_data(category, DATABASE[category])
            
            # Si es un evento, guardarlo tambiÃ©n en un archivo especÃ­fico para eventos
            if category == 'eventos' and 'events' in item:
                events_file = os.path.join(DATA_DIR, f"{urlparse(url).netloc.replace('.', '_')}_events.json")
                try:
                    if os.path.exists(events_file):
                        with open(events_file, 'r', encoding='utf-8') as f:
                            existing_events = json.load(f)
                        existing_events.extend(item['events'])
                        with open(events_file, 'w', encoding='utf-8') as f:
                            json.dump(existing_events, f, ensure_ascii=False, indent=2)
                    else:
                        with open(events_file, 'w', encoding='utf-8') as f:
                            json.dump(item['events'], f, ensure_ascii=False, indent=2)
                except Exception as e:
                    print(f"Error saving events data: {e}")
        
        return item
    
    except Exception as e:
        print(f"Error scraping website: {e}")
        return {'error': str(e)}

@app.route('/api/scrape', methods=['POST'])
def api_scrape():
    """API para hacer scraping de un sitio web"""
    data = request.json
    
    if not data or 'url' not in data:
        return jsonify({'success': False, 'error': 'La URL es requerida'}), 400
    
    url = data['url']
    category = data.get('category', 'general')
    depth = data.get('depth', '1')  # Profundidad del anÃ¡lisis
    include_images = data.get('include_images', False)  # Incluir imÃ¡genes
    tool = data.get('tool', 'auto')  # Herramienta de scraping seleccionada
    process_js = data.get('process_js', False)  # Procesar JavaScript
    extract_structured = data.get('extract_structured', True)  # Extraer datos estructurados
    save_results = data.get('save_results', True)  # Guardar resultados
    
    # Asegurarse de que category sea vÃ¡lido
    if category not in categories:
        category = 'general'  # Valor por defecto si la categorÃ­a no es vÃ¡lida
    
    try:
        # Para scraping bÃ¡sico (profundidad 1)
        if depth == '1':
            # Si se solicita procesar JS pero no se especifica una herramienta, usar Selenium
            if process_js and tool == 'auto':
                tool = 'selenium'
            
            # Configurar opciones para el scraper bÃ¡sico
            scraping_options = {
                'include_images': include_images,
                'process_js': process_js,
                'extract_structured': extract_structured,
                'save_results': save_results,
                'tool': tool
            }
            
            # Usar el scraper bÃ¡sico con opciones
            item = scrape_website(url, category, options=scraping_options)
            
            if 'error' in item:
                return jsonify({'success': False, 'error': item['error']}), 500
            
            return jsonify({
                'success': True,
                'url': url,
                'extracted_items': [{
                    'title': item.get('title', 'Sin tÃ­tulo'),
                    'description': item.get('description', 'Sin descripciÃ³n'),
                    'category': category
                }],
                'summary': f"PÃ¡gina analizada: {item.get('title', 'Sin tÃ­tulo')}"
            })
        
        # Para scraping mÃ¡s avanzado (profundidad 2-3)
        else:
            # Importamos asyncio y el scraper avanzado aquÃ­ para evitar problemas de importaciÃ³n circular
            import asyncio
            from advanced_scraper import AdvancedScraper, test_scraper
            
            # Configuramos una sola fuente para el scraper con nuevas opciones
            sources = [{
                "url": url,
                "name": urlparse(url).netloc,
                "category": category,
                "options": {
                    "include_images": include_images,
                    "process_js": process_js,
                    "extract_structured": extract_structured,
                    "save_results": save_results,
                    "tool": tool
                }
            }]
            
            # Si es solo una prueba rÃ¡pida (intermedio)
            if depth == '2':
                test_result = test_scraper()
                if test_result['success']:
                    scraper = AdvancedScraper(sources)
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    results = loop.run_until_complete(scraper.scrape_source(sources[0]))
                    loop.close()
                else:
                    return jsonify({'success': False, 'error': 'Error en la configuraciÃ³n del scraper'}), 500
            
            # AnÃ¡lisis completo (profundidad 3)
            elif depth == '3':
                scraper = AdvancedScraper(sources)
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                results = loop.run_until_complete(scraper.scrape_all_sources())
                loop.close()
                if results and len(results) > 0:
                    results = results[0]  # Tomamos el primer resultado
            
            # Preparar resultado para devolver al frontend
            extracted_items = []
            
            # Si tenemos eventos extraÃ­dos los aÃ±adimos a la respuesta
            events_file = os.path.join(DATA_DIR, f"{urlparse(url).netloc.replace('.', '_')}_events.json")
            if os.path.exists(events_file):
                with open(events_file, 'r', encoding='utf-8') as f:
                    events = json.load(f)
                    for event in events:
                        extracted_items.append({
                            'title': event.get('title', 'Evento sin tÃ­tulo'),
                            'date': event.get('date', 'Fecha no especificada'),
                            'location': event.get('location', {}).get('name', 'UbicaciÃ³n no especificada'),
                            'description': event.get('description', 'Sin descripciÃ³n')
                        })
            
            # Si no hay eventos extraÃ­dos pero el scraping fue exitoso
            if not extracted_items and hasattr(results, 'success') and results.success:
                # Crear al menos un elemento con informaciÃ³n bÃ¡sica
                extracted_items = [{
                    'title': f"InformaciÃ³n de {urlparse(url).netloc}",
                    'description': f"Sitio analizado correctamente pero sin eventos especÃ­ficos encontrados."
                }]
            
            # Verificar si el scraping fue exitoso
            success = hasattr(results, 'success') and results.success
            
            # Preparar resumen
            if success:
                summary = f"Se analizÃ³ {url} con Ã©xito utilizando {tool if tool != 'auto' else 'la herramienta automÃ¡tica'}."
                if hasattr(results, 'items_count'):
                    summary += f" Se encontraron {results.items_count} elementos."
            else:
                error_msg = "Error desconocido"
                if hasattr(results, 'errors') and results.errors:
                    error_msg = results.errors[0]
                return jsonify({
                    'success': False,
                    'error': error_msg,
                    'metadata': results.get('metadata', {})
                }), 500
            
            return jsonify({
                'success': True,
                'url': url,
                'extracted_items': extracted_items,
                'summary': summary
            })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/ai/config', methods=['GET'])
def get_ai_config():
    """Obtener la configuraciÃ³n de la IA"""
    return jsonify({
        'success': True,
        'config': {
            'use_local_models': True,
            'available_features': ['chat', 'scraping', 'event_search']
        }
    })

# Ruta para aÃ±adir un evento manualmente
@app.route('/add_event', methods=['POST'])
def add_event():
    """AÃ±adir un evento manualmente"""
    data = request.json
    if not data or 'name' not in data or 'date' not in data or 'location' not in data:
        return jsonify({'success': False, 'error': 'Datos incompletos'}), 400
    
    event = {
        'title': data['name'],
        'date': data['date'],
        'location': {
            'name': data['location']
        },
        'description': data.get('description', '')
    }
    
    # Guardar en el archivo de eventos
    events_file = os.path.join(DATA_DIR, "manual_events.json")
    try:
        events = []
        if os.path.exists(events_file):
            with open(events_file, 'r', encoding='utf-8') as f:
                events = json.load(f)
        
        events.append(event)
        
        with open(events_file, 'w', encoding='utf-8') as f:
            json.dump(events, f, ensure_ascii=False, indent=2)
        
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

# Nueva API para scraping avanzado con Archon
@app.route('/api/archon_scrape', methods=['POST'])
def archon_scrape():
    data = request.json
    if not data or 'url' not in data or 'category' not in data:
        return jsonify({
            'success': False, 
            'error': 'URL y categorÃ­a son requeridos'
        }), 400
    
    url = data['url']
    category = data['category']
    
    # Validar categorÃ­a
    if category not in categories:
        return jsonify({
            'success': False, 
            'error': f'CategorÃ­a no vÃ¡lida. Debe ser una de: {", ".join(categories)}'
        }), 400
            
    # Validar URL
    try:
        parsed_url = urlparse(url)
        if not parsed_url.scheme or not parsed_url.netloc:
            raise ValueError("URL invÃ¡lida")
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'URL invÃ¡lida: {str(e)}'
        }), 400
    
    # Usar el agente de Archon si estÃ¡ disponible
    if archon_agent:
        try:
            print(f"Realizando scraping con Archon en: {url}")
            results = archon_agent.scrape_website(url, category)
            
            # Si hay error, retornar el error
            if 'error' in results and not isinstance(results, list):
                return jsonify({
                    'success': False,
                    'error': results['error'],
                    'metadata': results.get('metadata', {})
                }), 500
            
            # Guardar resultados en la base de datos
            if isinstance(results, dict) and not 'error' in results:
                # Extraer datos segÃºn la categorÃ­a
                if category == 'eventos' and 'eventos' in results:
                    DATABASE[category].extend(results['eventos'])
                elif category == 'lugares' and 'lugares' in results:
                    DATABASE[category].extend(results['lugares'])
                elif category == 'restaurantes' and 'restaurantes' in results:
                    DATABASE[category].extend(results['restaurantes'])
                elif category == 'playas' and 'playas' in results:
                    DATABASE[category].extend(results['playas'])
                else:
                    # Para datos generales o estructura diferente
                    DATABASE[category].append({
                        'source': url,
                        'timestamp': datetime.now().isoformat(),
                        'data': results
                    })
                
                # Guardar datos en archivo
                save_data(category, DATABASE[category])
            
            return jsonify({
                'success': True,
                'message': f'Scraping con Archon completado para {url}',
                'results': results,
                'count': len(DATABASE[category]),
                'agent_info': {
                    'model': ARCHON_CONFIG['activeModel'],
                    'embeddings': ARCHON_CONFIG['defaultEmbeddings'],
                    'reasoner': ARCHON_CONFIG['reasonerModel']
                }
            })
            
        except Exception as e:
            print(f"Error en scraping con Archon: {e}")
            return jsonify({
                'success': False,
                'error': f'Error en scraping con Archon: {str(e)}',
                'agent_available': archon_agent is not None
            }), 500
    else:
        # Fallback al scraping normal si no estÃ¡ disponible Archon
        try:
            print(f"Archon no disponible, usando scraping normal para: {url}")
            results = scrape_website(url, category)
            
            return jsonify({
                'success': True,
                'message': f'Scraping normal completado para {url}',
                'results': results,
                'count': len(DATABASE[category]),
                'archon_available': False
            })
        except Exception as e:
            return jsonify({
                'success': False,
                'error': f'Error en scraping normal: {str(e)}'
            }), 500

# Nueva API para preguntas al agente Archon
@app.route('/api/archon_question', methods=['POST'])
def archon_question():
    data = request.json
    if not data or 'question' not in data:
        return jsonify({
            'success': False,
            'error': 'La pregunta es requerida'
        }), 400
    
    question = data['question']
    context = data.get('context', None)
    category = data.get('category', None)
    
    # Si se proporciona una categorÃ­a, aÃ±adir informaciÃ³n de la base de datos como contexto
    if category and category in DATABASE and DATABASE[category]:
        if not context:
            context = ""
        context += f"\nInformaciÃ³n de {category} de Ibiza:\n"
        context += json.dumps(DATABASE[category][:5], ensure_ascii=False, indent=2)
    
    # Usar el agente de Archon si estÃ¡ disponible
    if archon_agent:
        try:
            print(f"Procesando pregunta con Archon: {question}")
            result = archon_agent.answer_question(question, context, knowledge_base=KNOWLEDGE_BASE)
            
            # Si hay error, retornar el error
            if 'error' in result:
                return jsonify({
                    'success': False,
                    'error': result['error']
                }), 500
            
            return jsonify({
                'success': True,
                'answer': result['answer'],
                'model_used': result.get('model_used', ARCHON_CONFIG['activeModel']),
                'timestamp': result.get('timestamp', datetime.now().isoformat())
            })
            
        except Exception as e:
            print(f"Error al procesar pregunta con Archon: {e}")
            return jsonify({
                'success': False,
                'error': f'Error al procesar pregunta con Archon: {str(e)}',
                'agent_available': archon_agent is not None
            }), 500
    else:
        # Usar el sistema de respuestas predefinidas
        user_message = question.lower().strip()
        
        for key, response in predefined_responses.items():
            if key in user_message or user_message in key:
                return jsonify({
                    'success': True,
                    'answer': response,
                    'source': 'predefined',
                    'archon_available': False
                })
        
        return jsonify({
            'success': True,
            'answer': "Lo siento, no tengo informaciÃ³n especÃ­fica sobre eso y el agente Archon no estÃ¡ disponible. Puedes preguntarme sobre playas, restaurantes, discotecas o eventos en Ibiza.",
            'source': 'fallback',
            'archon_available': False
        })

@app.route('/api/upload_data', methods=['POST'])
def api_upload_data():
    """Recibe datos del agente autÃ³nomo y los guarda en la base de datos"""
    try:
        data = request.json
        if not data:
            return jsonify({'success': False, 'error': 'No data provided'}), 400
        
        category = data.get('category')
        content = data.get('data')
        source = data.get('source', 'unknown')
        
        if not category or not content:
            return jsonify({'success': False, 'error': 'Missing category or data'}), 400
            
        # Verificar que la categorÃ­a sea vÃ¡lida
        if category not in DATABASE:
            return jsonify({'success': False, 'error': f'Invalid category: {category}'}), 400
            
        # Agregar metadatos
        entry = {
            'data': content,
            'timestamp': datetime.now().isoformat(),
            'source': source
        }
        
        # Guardar en la base de datos en memoria
        DATABASE[category].append(entry)
        
        # TambiÃ©n guardar en archivo
        save_data(category, DATABASE[category])
        
        print(f"Datos recibidos y guardados en categorÃ­a {category} desde {source}")
        return jsonify({'success': True, 'message': 'Data received and saved successfully'})
        
    except Exception as e:
        print(f"Error en api_upload_data: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/datos_agente')
def datos_agente():
    """Muestra los datos recolectados por el agente autÃ³nomo"""
    # Obtener datos de todas las categorÃ­as
    total_entries = 0
    sources = set()
    last_update = None
    
    # Hacer una copia segura de la base de datos para evitar problemas de serializaciÃ³n
    safe_database = {}
    
    # Procesar los datos
    for category, entries in DATABASE.items():
        # Crear una copia segura de las entradas para esta categorÃ­a
        safe_entries = []
        
        for entry in entries:
            # Crear una copia segura de la entrada
            safe_entry = {}
            for key, value in entry.items():
                # Solo incluir valores que sean serializables
                try:
                    # Verificar si es serializable
                    json.dumps({key: value})
                    safe_entry[key] = value
                except (TypeError, OverflowError):
                    # Si no es serializable, convertirlo a string
                    safe_entry[key] = str(value)
            
            safe_entries.append(safe_entry)
            
            # Actualizar contadores
            total_entries += 1
            sources.add(entry.get('source', 'unknown'))
            entry_timestamp = entry.get('timestamp', '')
            if last_update is None or (entry_timestamp and entry_timestamp > last_update):
                last_update = entry_timestamp
        
        safe_database[category] = safe_entries
    
    return render_template('datos_agente.html', 
                          data=safe_database,
                          categories=DATABASE.keys(),
                          total_entries=total_entries,
                          sources_count=len(sources),
                          last_update=last_update or 'No hay datos')

@app.route('/api/force_collection', methods=['POST'])
def force_collection():
    """Fuerza una nueva recolecciÃ³n de datos del agente autÃ³nomo"""
    global SCRAPING_STATUS
    
    try:
        # Esta funciÃ³n lanzarÃ¡ un subproceso para ejecutar el agente en segundo plano
        import subprocess
        import os
        import threading
        
        def run_agent_subprocess():
            try:
                # Ruta al directorio del agente autÃ³nomo
                agent_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'ibiza-agent-ia')
                
                # Verificar si el directorio existe
                if not os.path.exists(agent_dir):
                    print(f"El directorio del agente no existe: {agent_dir}")
                    return
                
                # Ejecutar el agente con el comando --run
                process = subprocess.Popen(
                    ['python', 'main.py', '--run'],
                    cwd=agent_dir,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE
                )
                
                # Esperar a que termine para capturar la salida
                stdout, stderr = process.communicate()
                
                # Registrar la salida
                print("EjecuciÃ³n del agente completada")
                if stdout:
                    print(f"Salida estÃ¡ndar: {stdout.decode('utf-8', errors='ignore')}")
                if stderr:
                    print(f"Errores: {stderr.decode('utf-8', errors='ignore')}")
                
            except Exception as e:
                print(f"Error ejecutando el agente en segundo plano: {e}")
        
        # Lanzar el subproceso en un hilo separado
        thread = threading.Thread(target=run_agent_subprocess)
        thread.daemon = True  # El hilo se cerrarÃ¡ cuando el programa principal termine
        thread.start()
        
        # Actualizar estado
        SCRAPING_STATUS['progress'] = 10
        
        return jsonify({
            'success': True,
            'message': 'La recolecciÃ³n de datos ha comenzado'
        })
        
    except Exception as e:
        print(f"Error en force_collection: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

# Endpoints para la API de scraping
@app.route('/api/scraping_status')
def get_scraping_status():
    """Endpoint para obtener el estado actual del scraping."""
    return jsonify(SCRAPING_STATUS)

@app.route('/api/toggle_scraping', methods=['POST'])
def toggle_scraping():
    """Endpoint para activar o desactivar el scraping automÃ¡tico."""
    global SCRAPING_STATUS
    
    try:
        data = request.json
        is_active = data.get('active', False)
        
        SCRAPING_STATUS['isActive'] = is_active
        
        if is_active:
            # Si se estÃ¡ activando, reiniciar el progreso
            SCRAPING_STATUS['progress'] = 0
        
        return jsonify({
            'success': True,
            'isActive': SCRAPING_STATUS['isActive'],
            'progress': SCRAPING_STATUS['progress'],
            'lastRun': SCRAPING_STATUS['lastRun']
        })
    except Exception as e:
        logging.error(f"Error en toggle_scraping: {e}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/update_scraping_progress', methods=['POST'])
def update_scraping_progress():
    """Endpoint para actualizar el progreso del scraping."""
    global SCRAPING_STATUS
    
    try:
        data = request.json
        progress = data.get('progress', 0)
        
        # Validar que el progreso estÃ© entre 0 y 100
        progress = max(0, min(100, progress))
        
        SCRAPING_STATUS['progress'] = progress
        
        return jsonify({
            'success': True,
            'progress': SCRAPING_STATUS['progress']
        })
    except Exception as e:
        logging.error(f"Error en update_scraping_progress: {e}")
        return jsonify({'success': False, 'error': str(e)})

def run_agent_subprocess():
    """
    FunciÃ³n para ejecutar el agente de scraping en un subproceso.
    Esta funciÃ³n es utilizada para ejecutar el scraping automÃ¡tico.
    """
    global SCRAPING_STATUS
    try:
        logging.info("Iniciando proceso de scraping automÃ¡tico")
        
        # Actualizar estado del scraping
        SCRAPING_STATUS['lastRun'] = datetime.now().isoformat()
        
        # Simular progreso (en una implementaciÃ³n real, esto vendrÃ­a del agente)
        for progress in [25, 50, 75, 100]:
            time.sleep(2)  # Simular trabajo
            SCRAPING_STATUS['progress'] = progress
        
        return True
            
    except Exception as e:
        logging.error(f"Error en run_agent_subprocess: {e}")
        return False

# Endpoints para descargar datos en diferentes formatos
@app.route('/api/download/<format>/<category>', methods=['GET'])
def download_data(format, category):
    """Descarga los datos de una categorÃ­a especÃ­fica en el formato solicitado"""
    try:
        if category not in DATABASE:
            return jsonify({'success': False, 'error': f'CategorÃ­a no vÃ¡lida: {category}'}), 404
            
        # Obtener los datos de la categorÃ­a
        data = DATABASE[category]
        
        if not data:
            return jsonify({'success': False, 'error': 'No hay datos disponibles para descargar'}), 404
            
        # Extraer solo el contenido de datos real, no los metadatos
        extracted_data = []
        for entry in data:
            # Incluir algunos metadatos bÃ¡sicos junto con los datos
            extracted_entry = {
                'timestamp': entry.get('timestamp', ''),
                'source': entry.get('source', 'unknown'),
                'data': entry.get('data', {})
            }
            extracted_data.append(extracted_entry)
            
            # Actualizar contadores
            total_entries += 1
            sources.add(entry.get('source', 'unknown'))
            entry_timestamp = entry.get('timestamp', '')
            if last_update is None or (entry_timestamp and entry_timestamp > last_update):
                last_update = entry_timestamp
        
        safe_database[category] = safe_entries
    
        # Generar respuesta segÃºn el formato solicitado
        if format.lower() == 'json':
            response = jsonify(extracted_data)
            response.headers['Content-Disposition'] = f'attachment; filename={category}_data.json'
            return response
        elif format.lower() == 'csv':
            # ImplementaciÃ³n para CSV
            return jsonify({'success': False, 'error': 'Formato CSV no implementado aÃºn'}), 501
        elif format.lower() == 'txt':
            # ImplementaciÃ³n para TXT
            return jsonify({'success': False, 'error': 'Formato TXT no implementado aÃºn'}), 501
        else:
            return jsonify({'success': False, 'error': f'Formato no soportado: {format}'}), 400
    except Exception as e:
        print(f"Error al descargar datos: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/download/<format>/all', methods=['GET'])
def download_all_data(format):
    """Descarga todos los datos en el formato solicitado"""
    try:
        # Unir todos los datos de todas las categorÃ­as
        all_data = {}
        for category, entries in DATABASE.items():
            if entries:  # Solo incluir categorÃ­as con datos
                category_data = []
                for entry in entries:
                    # Incluir algunos metadatos bÃ¡sicos junto con los datos
                    extracted_entry = {
                        'timestamp': entry.get('timestamp', ''),
                        'source': entry.get('source', 'unknown'),
                        'data': entry.get('data', {})
                    }
                    category_data.append(extracted_entry)
                all_data[category] = category_data
        
        if not all_data:
            return jsonify({'success': False, 'error': 'No hay datos disponibles para descargar'}), 404
            
        # Generar respuesta segÃºn el formato solicitado
        if format.lower() == 'json':
            response = jsonify(all_data)
            response.headers['Content-Disposition'] = f'attachment; filename=all_agent_data.json'
            return response
            
        elif format.lower() == 'txt':
            import json
            from io import StringIO
            
            # Crear un buffer de memoria para el texto
            output = StringIO()
            
            # Escribir los datos en formato legible
            for category, entries in all_data.items():
                output.write(f"===== CATEGORÃA: {category.upper()} =====\n\n")
                for i, entry in enumerate(entries):
                    output.write(f"--- Entrada #{i+1} ---\n")
                    output.write(f"Timestamp: {entry.get('timestamp', '')}\n")
                    output.write(f"Fuente: {entry.get('source', 'unknown')}\n")
                    output.write(f"Datos:\n{json.dumps(entry.get('data', {}), indent=2, ensure_ascii=False)}\n\n")
                output.write("\n" + "="*50 + "\n\n")
                
            output.seek(0)
            return Response(
                output.getvalue(),
                mimetype="text/plain",
                headers={"Content-Disposition": f"attachment;filename=all_agent_data.txt"}
            )
            
        else:
            return jsonify({
                'success': False,
                'error': f'Formato no soportado para todos los datos: {format}'
            }), 400
            
    except Exception as e:
        print(f"Error al descargar todos los datos: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/data', methods=['GET'])
def api_get_data():
    """API para obtener datos de cualquier categorÃ­a con filtrado opcional"""
    try:
        # Obtener parÃ¡metros de la solicitud
        category = request.args.get('category', 'all')
        limit = request.args.get('limit')
        if limit:
            try:
                limit = int(limit)
            except ValueError:
                return jsonify({'success': False, 'error': 'El parÃ¡metro limit debe ser un nÃºmero'}), 400
        
        source = request.args.get('source')
        date_from = request.args.get('date_from')
        date_to = request.args.get('date_to')
        
        # Preparar respuesta
        response_data = {}
        
        # Determinar quÃ© categorÃ­as incluir
        if category == 'all':
            categories_to_include = DATABASE.keys()
        else:
            if category not in DATABASE:
                return jsonify({'success': False, 'error': f'CategorÃ­a no vÃ¡lida: {category}'}), 404
            categories_to_include = [category]
        
        # Filtrar y formatear datos
        for cat in categories_to_include:
            entries = DATABASE.get(cat, [])
            filtered_entries = []
            
            for entry in entries:
                # Aplicar filtros
                if source and entry.get('source', '').lower() != source.lower():
                    continue
                    
                entry_date = entry.get('timestamp', '')
                if date_from and entry_date < date_from:
                    continue
                if date_to and entry_date > date_to:
                    continue
                
                # AÃ±adir entrada a la lista filtrada
                filtered_entries.append({
                    'timestamp': entry.get('timestamp', ''),
                    'source': entry.get('source', 'unknown'),
                    'data': entry.get('data', {})
                })
            
            # Aplicar lÃ­mite si se especifica
            if limit and limit > 0:
                filtered_entries = filtered_entries[:limit]
                
            # Solo incluir la categorÃ­a si tiene datos despuÃ©s de filtrar
            if filtered_entries:
                response_data[cat] = filtered_entries
        
        # Devolver error si no hay datos despuÃ©s de aplicar filtros
        if not response_data:
            return jsonify({'success': False, 'error': 'No se encontraron datos que coincidan con los filtros especificados'}), 404
            
        # Incluir informaciÃ³n sobre la API en la respuesta
        api_info = {
            'version': '1.0',
            'documentation': '/api-docs',
            'filters_applied': {
                'category': category,
                'limit': limit,
                'source': source,
                'date_from': date_from,
                'date_to': date_to
            }
        }
        
        return jsonify({
            'success': True,
            'api_info': api_info,
            'data': response_data
        })
        
    except Exception as e:
        print(f"Error en api_get_data: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api-docs')
def api_docs():
    """Muestra documentaciÃ³n para la API de integraciÃ³n con otras IAs"""
    return render_template('api_docs.html')

# Ruta para visualizar la base de conocimiento actual
@app.route('/knowledge')
def view_knowledge_base():
    # Contar elementos por categorÃ­a
    category_counts = {category: len(items) for category, items in KNOWLEDGE_BASE.items()}
    
    # Obtener las Ãºltimas 5 entradas de cada categorÃ­a para mostrar
    latest_items = {}
    for category, items in KNOWLEDGE_BASE.items():
        # Ordenar por fecha de scraping (si existe)
        sorted_items = sorted(
            items, 
            key=lambda x: x.get('scraped_at', ''), 
            reverse=True
        )[:5]
        latest_items[category] = sorted_items
    
    return render_template(
        'knowledge_base.html',
        category_counts=category_counts,
        latest_items=latest_items,
        scraper_config=SCRAPER_CONFIG
    )

# Ruta para forzar una actualizaciÃ³n de scraping
@app.route('/api/force_scrape', methods=['POST'])
def force_scrape():
    data = request.json
    category = data.get('category', 'all')
    
    try:
        # Importar el scheduler
        import scraper_scheduler
        
        if category == 'all':
            # Ejecutar scraping para todas las categorÃ­as configuradas
            results = {}
            for cat in SCRAPER_CONFIG['sources'].keys():
                results[cat] = scraper_scheduler.run_scraper_job(cat)
                
            return jsonify({
                'success': True,
                'message': 'Scraping iniciado para todas las categorÃ­as',
                'results': results
            })
        else:
            # Ejecutar scraping solo para la categorÃ­a solicitada
            if category in SCRAPER_CONFIG['sources']:
                new_items = scraper_scheduler.run_scraper_job(category)
                
                return jsonify({
                    'success': True,
                    'message': f'Scraping iniciado para {category}',
                    'new_items': new_items
                })
            else:
                return jsonify({
                    'success': False,
                    'error': f'CategorÃ­a no reconocida: {category}'
                }), 400
                
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Error al iniciar el scraping: {str(e)}'
        }), 500

# Rutas para subida y gestiÃ³n de contenido multimedia
@app.route('/upload', methods=['GET', 'POST'])
def upload_content():
    """PÃ¡gina para subir contenido multimedia y archivos a la base de conocimiento"""
    if request.method == 'POST':
        # Verificar que hay un archivo
        if 'file' not in request.files:
            flash('No se seleccionÃ³ ningÃºn archivo')
            return redirect(request.url)
        
        file = request.files['file']
        if file.filename == '':
            flash('No se seleccionÃ³ ningÃºn archivo')
            return redirect(request.url)
        
        # Obtener metadatos
        content_type = request.form.get('content_type', 'general')
        title = request.form.get('title', 'Sin tÃ­tulo')
        description = request.form.get('description', '')
        tags = request.form.get('tags', '').split(',')
        tags = [tag.strip() for tag in tags if tag.strip()]
        
        # Validar el tipo de contenido
        valid_types = ['image', 'video', 'document', 'website', 'audio']
        if content_type not in valid_types:
            content_type = 'general'
        
        # Preparar nombre de archivo seguro
        filename = secure_filename(file.filename)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        unique_filename = f"{timestamp}_{filename}"
        
        # Preparar directorio segÃºn tipo
        upload_dir = os.path.join(UPLOAD_DIR, content_type)
        os.makedirs(upload_dir, exist_ok=True)
        
        # Guardar archivo
        file_path = os.path.join(upload_dir, unique_filename)
        file.save(file_path)
        
        # Procesar segÃºn tipo
        processed_data = {}
        
        if content_type == 'image':
            # Procesamiento de imagen (redimensionar, extraer metadatos EXIF, etc.)
            try:
                from PIL import Image, ExifTags
                img = Image.open(file_path)
                processed_data['dimensions'] = f"{img.width}x{img.height}"
                
                # Extraer EXIF si existe
                exif_data = {}
                if hasattr(img, '_getexif') and img._getexif():
                    for tag, value in img._getexif().items():
                        if tag in ExifTags.TAGS:
                            exif_data[ExifTags.TAGS[tag]] = str(value)
                processed_data['exif'] = exif_data
                
                # Crear miniatura
                thumb_dir = os.path.join(UPLOAD_DIR, 'thumbnails')
                os.makedirs(thumb_dir, exist_ok=True)
                thumb_path = os.path.join(thumb_dir, f"thumb_{unique_filename}")
                img.thumbnail((200, 200))
                img.save(thumb_path)
                processed_data['thumbnail'] = f"/uploads/thumbnails/thumb_{unique_filename}"
            except Exception as e:
                print(f"Error procesando imagen: {e}")
        
        elif content_type == 'video':
            # Metadatos bÃ¡sicos de video
            processed_data['size'] = os.path.getsize(file_path)
            processed_data['format'] = os.path.splitext(filename)[1][1:].lower()
        
        elif content_type == 'website':
            # Si es un archivo HTML, extraer contenido relevante
            if filename.endswith('.html') or filename.endswith('.htm'):
                try:
                    from bs4 import BeautifulSoup
                    with open(file_path, 'r', encoding='utf-8') as f:
                        soup = BeautifulSoup(f.read(), 'html.parser')
                        processed_data['title'] = soup.title.string if soup.title else title
                        processed_data['text_content'] = soup.get_text()[:1000] + "..."  # Primeros 1000 caracteres
                except Exception as e:
                    print(f"Error procesando HTML: {e}")
        
        # Preparar entrada para la base de conocimiento
        content_item = {
            'id': str(uuid.uuid4()),
            'title': title,
            'description': description,
            'tags': tags,
            'file_path': file_path.replace(os.path.abspath(os.path.dirname(__file__)), '').replace('\\', '/'),
            'public_url': f"/uploads/{content_type}/{unique_filename}",
            'content_type': content_type,
            'original_filename': filename,
            'upload_date': datetime.now().isoformat(),
            'processed_data': processed_data
        }
        
        # AÃ±adir a la base de conocimiento
        if 'content' not in KNOWLEDGE_BASE:
            KNOWLEDGE_BASE['content'] = []
        
        KNOWLEDGE_BASE['content'].append(content_item)
        
        # Guardar base de conocimiento actualizada
        save_knowledge_base()
        
        # Redirigir a pÃ¡gina de Ã©xito
        flash(f'Archivo {filename} subido correctamente como {content_type}')
        return redirect(url_for('view_content', content_id=content_item['id']))
    
    # GET: Mostrar formulario
    return render_template('upload.html')

@app.route('/content/<content_id>')
def view_content(content_id):
    """Ver detalles de un contenido especÃ­fico"""
    # Buscar contenido por ID
    content_item = None
    if 'content' in KNOWLEDGE_BASE:
        for item in KNOWLEDGE_BASE['content']:
            if item.get('id') == content_id:
                content_item = item
                break
    
    if not content_item:
        flash('Contenido no encontrado')
        return redirect(url_for('content_library'))
    
    return render_template('content_detail.html', content=content_item)

@app.route('/library')
def content_library():
    """Biblioteca de contenido multimedia"""
    # Filtrar por tipo
    content_type = request.args.get('type', 'all')
    
    # Contenido filtrado
    filtered_content = []
    if 'content' in KNOWLEDGE_BASE:
        for item in KNOWLEDGE_BASE['content']:
            if content_type == 'all' or item.get('content_type') == content_type:
                filtered_content.append(item)
    
    # Ordenar por fecha de subida (mÃ¡s reciente primero)
    filtered_content.sort(key=lambda x: x.get('upload_date', ''), reverse=True)
    
    return render_template('content_library.html', 
                          content_items=filtered_content,
                          content_type=content_type)

@app.route('/api/content', methods=['GET'])
def api_get_content():
    """API para acceder al contenido multimedia"""
    # Filtrar por tipo
    content_type = request.args.get('type', 'all')
    # Limitar resultados
    limit = request.args.get('limit', 50, type=int)
    # Buscar por tags
    tags = request.args.get('tags', '').split(',')
    tags = [tag.strip() for tag in tags if tag.strip()]
    
    # Contenido filtrado
    filtered_content = []
    if 'content' in KNOWLEDGE_BASE:
        for item in KNOWLEDGE_BASE['content']:
            # Filtrar por tipo
            type_match = content_type == 'all' or item.get('content_type') == content_type
            
            # Filtrar por tags si hay tags especificados
            tag_match = True
            if tags:
                item_tags = item.get('tags', [])
                tag_match = any(tag in item_tags for tag in tags)
            
            if type_match and tag_match:
                filtered_content.append(item)
    
    # Ordenar por fecha de subida (mÃ¡s reciente primero)
    filtered_content.sort(key=lambda x: x.get('upload_date', ''), reverse=True)
    
    # Limitar resultados
    filtered_content = filtered_content[:limit]
    
    return jsonify({
        'success': True,
        'count': len(filtered_content),
        'items': filtered_content
    })

@app.route('/api/chat', methods=['POST'])
def api_chat():
    data = request.json
    if not data or 'message' not in data:
        return jsonify({'error': 'Message is required'}), 400
    
    user_message = data['message'].strip()
    user_message_lower = user_message.lower()
    
    # Obtener o crear session_id
    session_id = data.get('session_id', request.remote_addr)
    
    try:
        # Paso 1: Buscar en respuestas predefinidas
        for key, response in predefined_responses.items():
            if key in user_message_lower or user_message_lower in key:
                # Guardar en memoria de conversaciÃ³n
                if session_id not in CONVERSATION_MEMORY:
                    CONVERSATION_MEMORY[session_id] = []
                
                CONVERSATION_MEMORY[session_id].append({
                    'user': user_message,
                    'bot': response,
                    'timestamp': datetime.now().isoformat()
                })
                
                return jsonify({
                    'response': response,
                    'source': 'predefined',
                    'modelUsed': 'local'
                })
        
        # Paso 2: Verificar si hay informaciÃ³n en la base de conocimiento
        has_kb_info = check_knowledge_base(user_message_lower, just_check=True)
        
        # Paso 3: Utilizar razonamiento avanzado con historial de conversaciÃ³n
        enhanced_response, source = enhanced_reasoning(user_message, session_id)
        
        # Determinar la fuente correcta de la respuesta 
        # (para analÃ­ticas, podemos saber si la respuesta vino principalmente de la base de conocimiento o del modelo)
        if has_kb_info and source == "archon":
            source = "knowledge_base+archon"
        
        if enhanced_response:
            # Guardar en memoria de conversaciÃ³n
            if session_id not in CONVERSATION_MEMORY:
                CONVERSATION_MEMORY[session_id] = []
            
            CONVERSATION_MEMORY[session_id].append({
                'user': user_message,
                'bot': enhanced_response,
                'timestamp': datetime.now().isoformat()
            })
            
            # Limitar el tamaÃ±o de la memoria de conversaciÃ³n
            if len(CONVERSATION_MEMORY[session_id]) > MAX_MEMORY_LENGTH * 2:
                CONVERSATION_MEMORY[session_id] = CONVERSATION_MEMORY[session_id][-MAX_MEMORY_LENGTH * 2:]
            
            return jsonify({
                'response': enhanced_response,
                'source': source,
                'modelUsed': ARCHON_CONFIG['activeModel']
            })
        
        # Paso 4: Si todo lo demÃ¡s falla, generar respuesta contextual basada en el tema
        topics = {
            'evento': 'eventos y fiestas',
            'fiesta': 'eventos y fiestas',
            'discoteca': 'clubes y locales nocturnos',
            'ticket': 'entradas para eventos y clubes',
            'playa': 'playas y calas',
            'hotel': 'alojamiento',
            'restaurante': 'restaurantes y gastronomÃ­a',
            'transporte': 'opciones de transporte'
        }
        
        detected_topic = None
        for word, topic in topics.items():
            if word in user_message_lower:
                detected_topic = topic
                break
        
        if detected_topic:
            response = f"Entiendo que estÃ¡s interesado en {detected_topic} de Ibiza. " + \
                      f"Aunque no tengo informaciÃ³n especÃ­fica sobre tu consulta en este momento, " + \
                      f"estoy constantemente actualizando mi base de datos con nuevos eventos, tickets y lugares. " + \
                      f"Te recomiendo volver a consultar mÃ¡s adelante o intentar con una pregunta mÃ¡s especÃ­fica."
        else:
            response = "Lo siento, no tengo informaciÃ³n especÃ­fica sobre eso. Puedes preguntarme sobre playas, restaurantes, discotecas o eventos en Ibiza."
        
        # Guardar en memoria de conversaciÃ³n
        if session_id not in CONVERSATION_MEMORY:
            CONVERSATION_MEMORY[session_id] = []
        
        CONVERSATION_MEMORY[session_id].append({
            'user': user_message,
            'bot': response,
            'timestamp': datetime.now().isoformat()
        })
        
        # Limitar el tamaÃ±o de la memoria de conversaciÃ³n
        if len(CONVERSATION_MEMORY[session_id]) > MAX_MEMORY_LENGTH * 2:
            CONVERSATION_MEMORY[session_id] = CONVERSATION_MEMORY[session_id][-MAX_MEMORY_LENGTH * 2:]
        
        return jsonify({
            'response': response,
            'source': 'generated',
            'modelUsed': 'rules'
        })
        
    except Exception as e:
        logging.error(f"Error al procesar con enhanced_reasoning: {e}")
        # Continuar con respuesta alternativa si falla
    
    # Si todo lo demÃ¡s falla, caer en respuesta genÃ©rica
    response = "Lo siento, no tengo informaciÃ³n especÃ­fica sobre eso. Puedes preguntarme sobre playas, restaurantes, discotecas o eventos en Ibiza."
    
    # Guardar en memoria de conversaciÃ³n
    if session_id not in CONVERSATION_MEMORY:
        CONVERSATION_MEMORY[session_id] = []
    
    CONVERSATION_MEMORY[session_id].append({
        'user': user_message,
        'bot': response,
        'timestamp': datetime.now().isoformat()
    })
    
    return jsonify({
        'response': response,
        'source': 'fallback'
    })

@app.route('/api/test_knowledge_base', methods=['GET'])
def test_knowledge_base():
    """Ruta para probar la conexiÃ³n con la base de conocimiento"""
    try:
        if os.path.exists('data/knowledge_base.json'):
            with open('data/knowledge_base.json', 'r', encoding='utf-8') as f:
                kb = json.load(f)
            
            result = {
                'success': True,
                'categories': list(kb.keys()),
                'counts': {category: len(items) for category, items in kb.items()},
                'total_items': sum(len(items) for items in kb.values())
            }
            return jsonify(result)
        else:
            return jsonify({
                'success': False,
                'error': 'Base de conocimiento no encontrada',
                'path': os.path.abspath('data/knowledge_base.json')
            })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        })

# Health check para monitorizaciÃ³n del sistema
@app.route('/api/health', methods=['GET'])
def health_check():
    """Endpoint para verificar si el servidor estÃ¡ en funcionamiento"""
    try:
        # Comprobar uso de memoria
        try:
            import psutil
            memory = psutil.virtual_memory()
            memory_usage = {
                "total": memory.total,
                "available": memory.available,
                "percent": memory.percent,
                "status": "CRITICAL" if memory.percent > 95 else "WARNING" if memory.percent > 80 else "OK"
            }
            
            # Si el uso de memoria es crÃ­tico (>90%), realizar limpieza agresiva
            if memory.percent > 90:
                # Ejecutar limpieza agresiva
                cleanup_stats = aggressive_memory_cleanup()
                logging.warning(f"Uso de memoria crÃ­tico ({memory.percent}%). Limpieza agresiva realizada.")
            elif memory.percent > 75:
                # Limpieza normal
                purged_sessions = purge_old_sessions()
                collected_objects = optimize_memory()
                logging.info(f"Uso de memoria elevado ({memory.percent}%). Iniciando limpieza...")
                
                # Verificar resultado de la limpieza
                memory_after = psutil.virtual_memory()
                logging.info(f"Limpieza de memoria completada: {purged_sessions} sesiones purgadas, memoria: {memory.percent}% â {memory_after.percent}%")
                
        except ImportError:
            memory_usage = {"status": "UNKNOWN", "error": "psutil no disponible"}
        
        # Comprobar la integridad de la base de conocimiento
        kb_status = {
            "available": bool(KNOWLEDGE_BASE),
            "categories": len(KNOWLEDGE_BASE.keys()),
            "total_items": sum(len(category) for category in KNOWLEDGE_BASE.values())
        }
        
        # Comprobar la disponibilidad de Archon
        archon_status = {
            "available": ARCHON_AVAILABLE,
            "model": ARCHON_CONFIG.get("activeModel", "N/A"),
            "embeddings": ARCHON_CONFIG.get("defaultEmbeddings", "N/A"),
            "reasoner": ARCHON_CONFIG.get("reasonerModel", "N/A")
        }
        
        # Comprobar estado del auto-scraper
        try:
            from integrate_auto_scraper import get_auto_updater_status
            auto_scraper_status = get_auto_updater_status()
        except ImportError:
            auto_scraper_status = {"available": False, "error": "MÃ³dulo no disponible"}
        
        # InformaciÃ³n sobre la memoria del sistema
        memory_info = {
            "active_sessions": len(CONVERSATION_MEMORY),
            "predefined_responses": len(predefined_responses)
        }
        
        return jsonify({
            "status": "ok",
            "timestamp": datetime.now().isoformat(),
            "service": "ibiza-info-app",
            "version": "1.0.0",
            "components": {
                "knowledge_base": kb_status,
                "archon": archon_status,
                "auto_scraper": auto_scraper_status,
                "memory": {
                    "active_sessions": memory_info["active_sessions"],
                    "predefined_responses": memory_info["predefined_responses"],
                    "purged_sessions": purged_sessions if 'purged_sessions' in locals() else 0,
                    "collected_objects": collected_objects if 'collected_objects' in locals() else 0
                }
            },
            "system": {
                "memory": memory_usage
            }
        })
    except Exception as e:
        return jsonify({
            "status": "error",
            "timestamp": datetime.now().isoformat(),
            "service": "ibiza-info-app",
            "error": str(e)
        }), 500

# Instancia del Auto-Scraper
auto_scraper = None
if AUTO_SCRAPER_AVAILABLE:
    try:
        auto_scraper = AutoScraper(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data', 'scraper_config.json'))
        print("Auto-Scraper inicializado correctamente")
    except Exception as e:
        print(f"Error inicializando Auto-Scraper: {e}")

# Iniciar el servidor
if __name__ == '__main__':
    # Importar e inicializar el auto-scraper con Archon
    # Registrar blueprints
    app.register_blueprint(status_bp)  # Registrar el blueprint de status

    # Registrar el blueprint del auto-scraper si estÃ¡ disponible
    if AUTO_SCRAPER_AVAILABLE:
        try:
            auto_scraper_instance = AutoScraper()
            auto_scraper_bp = init_auto_scraper_bp(auto_scraper_instance)
            app.register_blueprint(auto_scraper_bp)
            print('Blueprint de Auto-Scraper registrado correctamente')
        except Exception as e:
            print(f'Error al registrar el blueprint de Auto-Scraper: {e}')

@app.route('/api/auto-scraper/toggle', methods=['POST'])
def api_auto_scraper_toggle():
    """
    Endpoint para activar/desactivar el scraper automÃ¡tico.
    Este endpoint puede ser llamado desde la UI o desde el chatbot.
    """
    if not auto_scraper:
        return jsonify({
            'success': False, 
            'error': 'Auto-Scraper no disponible'
        }), 400
    
    try:
        data = request.json
        force_state = data.get('state')
        query = data.get('query', '')
        max_pages = data.get('max_pages', 5)
        
        # Determinar la acciÃ³n a realizar
        if force_state is not None:
            # Si se especifica un estado forzado (true/false)
            if force_state:
                # Iniciar scraper segÃºn el modo
                if query:
                    # Modo especÃ­fico con query personalizada
                    status = auto_scraper.start_specific_scraping(query, max_pages)
                    message = f"Scraper iniciado en modo especÃ­fico para: {query}"
                else:
                    # Modo general sobre Ibiza
                    status = auto_scraper.start_general_scraping(max_pages)
                    message = "Scraper iniciado en modo general para Ibiza"
            else:
                # Detener scraper
                status = auto_scraper.stop()
                message = "Scraper detenido"
        else:
            # Toggle - cambiar al estado opuesto
            if auto_scraper.is_running():
                status = auto_scraper.stop()
                message = "Scraper detenido"
            else:
                if query:
                    status = auto_scraper.start_specific_scraping(query, max_pages)
                    message = f"Scraper iniciado en modo especÃ­fico para: {query}"
                else:
                    status = auto_scraper.start_general_scraping(max_pages)
                    message = "Scraper iniciado en modo general para Ibiza"
        
        return jsonify({
            'success': True, 
            'message': message,
            'status': status
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

# Endpoint para obtener el conocimiento del scraper para las respuestas del chatbot
@app.route('/api/auto-scraper/query', methods=['POST'])
def api_auto_scraper_query():
    """
    Endpoint para consultar la base de conocimiento del scraper.
    Este endpoint es usado por el chatbot para obtener respuestas.
    """
    if not auto_scraper:
        return jsonify({
            'success': False, 
            'error': 'Auto-Scraper no disponible'
        }), 400
    
    try:
        data = request.json
        if not data or 'query' not in data:
            return jsonify({
                'success': False, 
                'error': 'Consulta no especificada'
            }), 400
            
        query = data['query']
        results = auto_scraper.query_knowledge_base(query)
        
        if not results:
            return jsonify({
                'success': False, 
                'message': 'No se encontraron resultados para esta consulta'
            })
            
        return jsonify({
            'success': True,
            'results': results
        })
    except Exception as e:
        print(f"Error al consultar la base de datos del scraper: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

# Endpoint para obtener el estado actual del scraper
@app.route('/api/auto-scraper/status', methods=['GET'])
def api_auto_scraper_status():
    """
    Endpoint para obtener el estado actual del scraper.
    """
    if not auto_scraper:
        return jsonify({
            'success': False, 
            'error': 'Auto-Scraper no disponible'
        }), 400
    
    try:
        # Obtener el estado actual del scraper
        is_active = auto_scraper.is_running()
        
        # Obtener estadÃ­sticas de la base de conocimiento
        kb_stats = auto_scraper.get_knowledge_base_stats()
        
        # Cargar la base de conocimiento para obtener URLs recientes
        kb_data = auto_scraper._load_knowledge_base()
        recent_urls = []
        
        # Obtener las URLs mÃ¡s recientes (hasta 10)
        for entry in kb_data[-10:]:
            if 'url' in entry and entry['url'] not in [u['url'] for u in recent_urls]:
                recent_urls.append({
                    'url': entry['url'],
                    'title': entry.get('title', 'Sin tÃ­tulo'),
                    'timestamp': entry.get('timestamp', None)
                })
        
        return jsonify({
            'success': True,
            'active': is_active,
            'stats': {
                'pages': kb_stats.get('total_urls', 0),
                'content': kb_stats.get('total_segments', 0),
                'sources': len(auto_scraper.get_configured_sources()),
                'categories': len(set([entry.get('category', 'general') for entry in kb_data if 'category' in entry]))
            },
            'urls': recent_urls,
            'lastRun': auto_scraper.config.get('last_run', None),
            'progress': auto_scraper.config.get('progress', 0)
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

# Endpoint para ejecutar una bÃºsqueda de prueba rÃ¡pida
@app.route('/api/auto-scraper/test-search', methods=['POST'])
def api_auto_scraper_test_search():
    """
    Endpoint para ejecutar una bÃºsqueda de prueba rÃ¡pida.
    Esto permitirÃ¡ a los usuarios probar el scraper sin activarlo completamente.
    """
    if not auto_scraper:
        return jsonify({
            'success': False, 
            'error': 'Auto-Scraper no disponible'
        }), 400
    
    try:
        data = request.json
        search_query = data.get('query', '')
        max_results = min(5, int(data.get('max_results', 3)))  # Limitar a 5 como mÃ¡ximo
        
        # Si no se proporciona consulta, usar una bÃºsqueda predeterminada sobre Ibiza
        if not search_query:
            search_query = "eventos en Ibiza"
        
        # Verificar si auto_scraper.config es un diccionario
        if not isinstance(auto_scraper.config, dict):
            # Crear un objeto de respuesta para simular una respuesta exitosa
            mock_results = {
                'success': True,
                'query': search_query,
                'results': [
                    {
                        'title': 'Resultado de bÃºsqueda simulado 1',
                        'url': 'https://example.com/1',
                        'snippet': 'Este es un resultado simulado debido a un problema con la configuraciÃ³n del scraper.'
                    },
                    {
                        'title': 'Resultado de bÃºsqueda simulado 2',
                        'url': 'https://example.com/2',
                        'snippet': 'Por favor, reinicie el servidor para restaurar la funcionalidad completa.'
                    }
                ],
                'results_count': 2,
                'timestamp': datetime.now().isoformat(),
                'engine': 'SimulaciÃ³n'
            }
            logging.warning(f"Usando resultados simulados debido a que auto_scraper.config no es un diccionario: {type(auto_scraper.config)}")
            return jsonify(mock_results)
        
        # Realizar una bÃºsqueda de prueba
        test_results = auto_scraper.run_test_search(
            search_query=search_query,
            search_name=None,
            max_results=max_results
        )
        
        # Si los resultados ya incluyen un estado de Ã©xito, usarlo directamente
        if isinstance(test_results, dict) and 'success' in test_results:
            # Asegurarse de que la estructura de respuesta es consistente
            if test_results['success']:
                # Asegurar que los campos requeridos estÃ©n presentes
                if 'query' not in test_results:
                    test_results['query'] = search_query
                if 'results_count' not in test_results and 'results' in test_results:
                    test_results['results_count'] = len(test_results['results'])
                if 'timestamp' not in test_results:
                    test_results['timestamp'] = datetime.now().isoformat()
                    
                return jsonify(test_results)
            else:
                # Si hay un error en los resultados, devolverlo
                return jsonify({
                    'success': False,
                    'error': test_results.get('error', 'Error desconocido en la bÃºsqueda')
                }), 500
        
        # Si los resultados no tienen el formato esperado, convertirlos
        response_data = {
            'success': True,
            'query': search_query,
            'results': test_results.get('results', []) if isinstance(test_results, dict) else [],
            'results_count': len(test_results.get('results', [])) if isinstance(test_results, dict) else 0,
            'timestamp': datetime.now().isoformat(),
            'engine': 'Google'
        }
        return jsonify(response_data)
    except Exception as e:
        logging.error(f"Error en test-search: {e}")
        logging.error(traceback.format_exc())
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

# Endpoint para obtener y modificar la configuraciÃ³n del scraper
@app.route('/api/auto-scraper/config', methods=['GET', 'POST'])
def api_auto_scraper_config():
    """
    Endpoint para obtener y modificar la configuraciÃ³n del scraper.
    - GET: Obtiene la configuraciÃ³n actual
    - POST: Actualiza la configuraciÃ³n
    """
    if not auto_scraper:
        return jsonify({
            'success': False, 
            'error': 'Auto-Scraper no disponible'
        }), 400
    
    try:
        # Si es GET, devolver la configuraciÃ³n actual
        if request.method == 'GET':
            # Filtrar informaciÃ³n sensible o innecesaria
            config = auto_scraper.config.copy()
            
            # Filtrar solo los campos necesarios para la configuraciÃ³n de la UI
            ui_config = {
                'options': config.get('options', {}),
                'sources': config.get('sources', []),
                'searches': config.get('searches', []),
                'schedules': config.get('schedules', {}),
                'max_pages': config.get('max_pages', 5),
                'max_depth': config.get('max_depth', 2),
                'update_frequency': config.get('update_frequency', 'daily')
            }
            
            return jsonify({
                'success': True,
                'config': ui_config
            })
            
        # Si es POST, actualizar la configuraciÃ³n
        elif request.method == 'POST':
            data = request.json
            if not data:
                return jsonify({
                    'success': False,
                    'error': 'No se han proporcionado datos de configuraciÃ³n'
                }), 400
                
            # Actualizar solo los campos permitidos
            if 'options' in data:
                auto_scraper.config['options'] = data['options']
                
            if 'sources' in data:
                auto_scraper.config['sources'] = data['sources']
                
            if 'searches' in data:
                auto_scraper.config['searches'] = data['searches']
                
            if 'schedules' in data:
                auto_scraper.config['schedules'] = data['schedules']
                
            if 'max_pages' in data:
                auto_scraper.config['max_pages'] = int(data['max_pages'])
                
            if 'max_depth' in data:
                auto_scraper.config['max_depth'] = int(data['max_depth'])
                
            if 'update_frequency' in data:
                auto_scraper.config['update_frequency'] = data['update_frequency']
                
            # Guardar la configuraciÃ³n actualizada
            auto_scraper._save_config()
            
            return jsonify({
                'success': True,
                'message': 'ConfiguraciÃ³n actualizada correctamente'
            })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

# Endpoint para exportar datos del scraper en diferentes formatos
@app.route('/api/auto-scraper/export', methods=['GET'])
def api_auto_scraper_export():
    """
    Endpoint para exportar datos del scraper en diferentes formatos.
    Permite descargar la base de conocimiento en CSV, JSON o XML.
    """
    if not auto_scraper:
        return jsonify({
            'success': False, 
            'error': 'Auto-Scraper no disponible'
        }), 400
    
    try:
        # Obtener el formato solicitado
        export_format = request.args.get('format', 'json').lower()
        if export_format not in ['json', 'csv', 'xml']:
            return jsonify({
                'success': False,
                'error': f'Formato no soportado: {export_format}'
            }), 400
            
        # Cargar los datos de la base de conocimiento
        kb_data = auto_scraper._load_knowledge_base()
        
        # Verificar que hay datos para exportar
        if not kb_data:
            return jsonify({
                'success': False,
                'error': 'No hay datos para exportar. La base de conocimiento estÃ¡ vacÃ­a.'
            }), 404
        
        if export_format == 'json':
            # Exportar como JSON
            export_data = json.dumps(kb_data, indent=2, ensure_ascii=False)
            mimetype = 'application/json'
            filename = f'auto_scraper_export_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
            
        elif export_format == 'csv':
            # Exportar como CSV
            import csv
            from io import StringIO
            
            output = StringIO()
            # Determinar todas las claves posibles para encabezados
            all_keys = set()
            for entry in kb_data:
                all_keys.update(entry.keys())
                
            # Asegurar que al menos hay claves para el CSV
            if not all_keys:
                return jsonify({
                    'success': False,
                    'error': 'No se pudieron determinar las columnas para el CSV'
                }), 500
                
            writer = csv.DictWriter(output, fieldnames=sorted(list(all_keys)))
            writer.writeheader()
            
            for entry in kb_data:
                writer.writerow(entry)
                
            export_data = output.getvalue()
            mimetype = 'text/csv'
            filename = f'auto_scraper_export_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
            
        elif export_format == 'xml':
            # Exportar como XML
            import dicttoxml
            from xml.dom.minidom import parseString
            
            try:
                xml_data = dicttoxml.dicttoxml(kb_data, custom_root='auto_scraper_data', attr_type=False)
                dom = parseString(xml_data)
                export_data = dom.toprettyxml()
                mimetype = 'application/xml'
                filename = f'auto_scraper_export_{datetime.now().strftime("%Y%m%d_%H%M%S")}.xml'
            except Exception as xml_error:
                return jsonify({
                    'success': False,
                    'error': f'Error al convertir a XML: {str(xml_error)}'
                }), 500
        else:
            return jsonify({
                'success': False,
                'error': f'Formato no soportado: {export_format}'
            }), 400
            
        # Crear la respuesta para descargar el archivo
        response = make_response(export_data)
        response.headers['Content-Disposition'] = f'attachment; filename={filename}'
        response.headers['Content-Type'] = f'{mimetype}; charset=utf-8'
        
        return response
        
    except Exception as e:
        logging.error(f"Error en exportaciÃ³n: {e}")
        logging.error(traceback.format_exc())
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/scraping_automatico')
def scraping_automatico():
    """Renderiza la pÃ¡gina de scraping automÃ¡tico."""
    return render_template('scraping_automatico.html')

# AÃ±adir funciÃ³n auxiliar para consultar la base de datos del scraper
def query_scraper_database(user_query):
    """
    Consulta la base de datos generada por el scraper automÃ¡tico
    para encontrar informaciÃ³n relevante a la consulta del usuario.
    
    Args:
        user_query (str): Consulta del usuario
    
    Returns:
        str: InformaciÃ³n encontrada o None si no hay resultados
    """
    if not auto_scraper:
        return None
        
    try:
        # Obtener datos del scraper relacionados con la consulta
        results = auto_scraper.query_knowledge_base(user_query)
        
        if not results:
            return None
            
        # Formatear respuesta
        if isinstance(results, list) and results:
            if len(results) == 1:
                return f"SegÃºn la informaciÃ³n que he recopilado: {results[0]}"
            else:
                formatted_results = "\nâ¢ " + "\nâ¢ ".join(results[:3])
                return f"He encontrado varios resultados relevantes:{formatted_results}"
        elif isinstance(results, str):
            return f"SegÃºn la informaciÃ³n que he recopilado: {results}"
        elif isinstance(results, dict):
            return f"He encontrado esta informaciÃ³n: {results.get('content', str(results))}"
        
        return str(results)
    except Exception as e:
        print(f"Error al consultar la base de datos del scraper: {e}")
        return None

@app.route('/uploads/<path:filename>')
def uploaded_file(filename):
    return send_from_directory(UPLOAD_DIR, filename)
