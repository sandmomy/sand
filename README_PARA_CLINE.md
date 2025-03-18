# Proyecto Web "Tienda Web" - Guía para Cline

## Estructura y Propósito
Este es un proyecto web basado en Flask que integra:
- Sitio de información sobre Ibiza
- Chatbot de IA (utilizando Archon)
- Sistema de scraping automático
- Gestión de archivos, imágenes y videos

## Archivos Principales
- `app_integrated.py`: Punto de entrada principal, contiene todas las rutas Flask
- `run_with_chatbot_scraper.py`: Script para iniciar el servidor con integración de chatbot y scraper
- `templates/`: Contiene todas las plantillas HTML
  - `ibiza_info.html`: Página principal
  - `agente_ia.html`: Interfaz del chat IA
  - `scraping_automatico.html`: Interfaz para scraping automatizado

## Estado Actual
- Se han corregido los enlaces de navegación en todas las plantillas
- Se ha mejorado la visibilidad de la barra de navegación con estilos CSS
- El chatbot tiene un sistema de respuestas predefinidas implementado

## Configuración
- El servidor se ejecuta en http://192.168.0.24:5000
- Archon está configurado para usar:
  - OpenRouter como servicio LLM principal con el modelo gemini-pro
  - OpenAI para embeddings con text-embedding-3-small

## Problemas Solucionados Recientemente
- Corrección de enlaces en la barra de navegación (eliminación de extensiones .html)
- Mejora de visibilidad de la barra de navegación
- Implementación de respuestas predefinidas para el chatbot

## Checkpoints de Seguridad
- Checkpoint 4 (19/03/2025): Versión con navegación corregida

## Para Iniciar el Proyecto
1. Navega a la carpeta del proyecto: `C:\Users\Usuario\CascadeProjects\tienda-web`
2. Ejecuta: `python run_with_chatbot_scraper.py`
3. Accede a: http://127.0.0.1:5000 o http://192.168.0.24:5000

## Tareas Pendientes
- Integración más profunda entre el chatbot y el scraper
- Mejoras visuales adicionales
- Optimización de consultas y respuestas del chatbot
