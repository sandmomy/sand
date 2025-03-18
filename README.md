# Ibiza AI - Asistente Virtual para Ibiza 2025

Un sistema de chatbot avanzado con base de conocimiento integrada y scraping automático para proporcionar información actualizada sobre eventos, tickets, venues y más en Ibiza para 2025.

## Características Principales

- **Chatbot Inteligente**: Asistente virtual especializado en información turística de Ibiza.
- **Base de Conocimiento**: Estructura unificada para almacenar y clasificar información.
- **Scraping Automático**: Recolección programada de datos de múltiples fuentes web.
- **Razonamiento Avanzado**: Integración con Archon para respuestas más contextuales.
- **Memoria de Conversación**: Sistema para mantener el contexto en conversaciones.
- **API REST**: Endpoints para interactuar con todos los componentes del sistema.
- **Panel de Administración**: Visualización y gestión de la base de conocimiento.
- **Optimizado para Producción**: Configuración para entornos de alto rendimiento.

## Estructura del Proyecto

```
tienda-web/
│
├── app.py                    # Aplicación principal (Flask)
├── production.py             # Servidor de producción (Waitress)
├── enhanced_scraper.py       # Scraper avanzado con navegación automática
├── archon_integration.py     # Integración con Archon y actualización de conocimiento
├── autonomous_agent.py       # Agente autónomo para navegación web
├── agent_browser.py          # Componente browser para el agente autónomo
├── scheduler.py              # Programador de tareas y actualización automática
├── system_check.py           # Herramienta de diagnóstico del sistema
├── test_enhanced_scraper.py  # Tests para el scraper avanzado
├── test_chatbot.py           # Tests para el chatbot y base de conocimiento
├── fix_system_issues.py      # Herramienta de reparación del sistema
├── requirements.txt          # Dependencias del proyecto
│
├── data/                     # Almacenamiento de datos
│   ├── knowledge_base.json   # Base de conocimiento principal
│   ├── scraper_config.json   # Configuración del scraper
│   ├── archon_integration_config.json # Configuración de integración con Archon
│   └── backups/              # Copias de seguridad
│
├── templates/                # Plantillas HTML
├── static/                   # Archivos estáticos
└── logs/                     # Registros y logs
```

## Componentes Clave del Sistema

### Enhanced Scraper
El Enhanced Scraper es un sistema avanzado de recopilación de datos que permite:
- Navegación automática de sitios web
- Extracción de datos estructurados
- Manejo de contenido dinámico mediante Selenium
- Actualización automática de la base de conocimiento
- Procesamiento por categorías (eventos, tickets, venues, playas, restaurantes)

Para utilizar el Enhanced Scraper:
```bash
# Actualizar una categoría específica
python enhanced_scraper.py --category events

# Actualizar todas las categorías
python enhanced_scraper.py --update-all

# Ver el estado actual del scraper
python enhanced_scraper.py --status
```

### Integración con Archon
La integración con Archon proporciona capacidades avanzadas de procesamiento de lenguaje natural:
- Uso de modelos de lenguaje OpenRouter (gemini-pro)
- Generación de embeddings con OpenAI (text-embedding-3-small) 
- Razonamiento con deepseek-r1:7b-8k

Para gestionar la integración con Archon:
```bash
# Verificar el estado de la integración
python archon_integration.py --status

# Actualizar manualmente la integración
python archon_integration.py --update
```

### Sistema de Tareas Programadas
El sistema incluye un programador de tareas que automatiza:
- Actualizaciones regulares de cada categoría según su frecuencia configurada
- Mantenimiento de la base de datos
- Verificación del estado del scraper
- Integración con Archon

Para iniciar el programador de tareas:
```bash
# Iniciar el programador en segundo plano
python scheduler.py
```

### Herramientas de Diagnóstico y Mantenimiento
El sistema incluye herramientas para mantener su salud operativa:
- `system_check.py`: Diagnóstico completo del sistema
- `fix_system_issues.py`: Reparación automática de problemas comunes
- `test_chatbot.py`: Pruebas del chatbot con la base de conocimiento
- `test_enhanced_scraper.py`: Pruebas del sistema de scraping

```bash
# Ejecutar diagnóstico del sistema
python system_check.py

# Reparar problemas del sistema
python fix_system_issues.py

# Probar el chatbot
python test_chatbot.py
```

## Resolución de Problemas Comunes

### Alto Uso de Memoria
Si el sistema muestra un alto uso de memoria, puede ejecutar:
```bash
python fix_system_issues.py
```
Esta herramienta implementa una limpieza agresiva de memoria y optimiza los componentes del sistema.

### Errores de Integración con Archon
Si experimenta problemas con la integración de Archon, verifique:
1. La configuración en `data/archon_integration_config.json`
2. La conexión con el servidor de Archon
3. Los modelos configurados en el entorno

Para solucionar problemas de integración:
```bash
python archon_integration.py --fix
```

### Base de Conocimiento Corrupta
Si la base de conocimiento muestra errores o está corrupta:
```bash
python fix_system_issues.py
```
Esta herramienta creará automáticamente una copia de seguridad y restaurará la estructura correcta.

## Integración con Archon

El sistema está configurado para utilizar Archon con:
- **Modelo Principal**: OpenRouter con gemini-pro
- **Embeddings**: OpenAI con text-embedding-3-small
- **Razonamiento**: deepseek-r1:7b-8k como modelo de razonamiento

La integración está configurada en v3-mcp-support versión de Archon.

## Actualizaciones Recientes

- **Optimización de Memoria**: Implementación de gestión de memoria mejorada
- **Sistema de Respuestas Predefinidas**: Respuestas para preguntas frecuentes como "¿cómo estás?" y "¿qué fiestas hay en Ibiza?"
- **Reparación Automática**: Sistema para detectar y solucionar problemas de forma autónoma
- **Programación Automática**: Configuración de tareas programadas para mantener el sistema actualizado

## Configuración e Instalación

### Requisitos

- Python 3.9+
- pip (gestor de paquetes de Python)
- Navegador web moderno

### Instalación

1. Clona el repositorio:
   ```
   git clone https://github.com/tu-usuario/tienda-web.git
   cd tienda-web
   ```

2. Ejecuta el script de instalación:
   ```
   powershell -ExecutionPolicy Bypass -File install.ps1
   ```

3. Configura las variables de entorno:
   ```
   cp .env.sample .env
   # Edita .env con tus configuraciones
   ```

4. Inicia el servidor:
   - **Modo desarrollo**: `python app.py`
   - **Modo producción**: `python production.py`

## Uso

### Endpoints Principales

- **Chat**: `/api/archon_chat` (POST) - Interactuar con el chatbot
- **Base de Conocimiento**: `/knowledge` - Visualizar la base de conocimiento
- **Scraping**: `/api/scrape` (POST) - Iniciar scraping manual
- **API**: `/api/data` - Obtener datos de la base de conocimiento
- **Documentación**: `/api-docs` - Documentación de la API

### Pruebas de Rendimiento

Para ejecutar pruebas de rendimiento:
```
python performance_test.py
```

## Personalización

### Configuración del Scraper

La configuración del scraper se encuentra en `data/scraper_config.json`.

Ejemplo:
```json
{
  "sources": {
    "events": [
      "https://www.ibiza-spotlight.com/events",
      "https://www.discoticketibiza.com/events"
    ]
  },
  "schedule": {
    "events": 24,
    "tickets": 12
  },
  "enabled": true
}
```

### Configuración de Seguridad

La configuración de seguridad se encuentra en `config/security.json`.

## Despliegue en Producción

Para un despliegue en producción, se recomienda:

1. Usar `production.py` en lugar de `app.py`
2. Configurar SSL para conexiones seguras
3. Implementar autenticación por API key
4. Configurar balanceo de carga si se espera alto tráfico

## Licencia

Este proyecto está licenciado bajo [Tu Licencia]. Consulta el archivo LICENSE para más detalles.

## Contribuir

Las contribuciones son bienvenidas. Por favor, lee las guías de contribución antes de enviar pull requests.

---

Desarrollado con ❤️ para los amantes de Ibiza
