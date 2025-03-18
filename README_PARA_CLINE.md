# Proyecto Tienda Web de Ibiza - Guía para Cline

## Configuración Inicial

### 1. Clonar el Repositorio

```bash
git clone https://github.com/sandmomy/sand.git
cd sand
```

### 2. Crear y Activar Entorno Virtual (Recomendado)

En Windows:
```bash
python -m venv venv
venv\Scripts\activate
```

En Mac/Linux:
```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Instalar Dependencias

```bash
pip install -r requirements.txt
```

## Ejecutar la Aplicación

### 1. Iniciar el Servidor de Desarrollo

```bash
python app_integrated.py
```

### 2. Acceder a la Aplicación

Abre tu navegador y visita:
- URL principal: http://localhost:5000
- Página del Agente IA: http://localhost:5000/agente_ia
- Scraping Automático: http://localhost:5000/scraping_automatico

## Modificar el Proyecto

### Estructura de Archivos Principales

- `app_integrated.py`: Archivo principal de la aplicación Flask
- `run_with_chatbot_scraper.py`: Script para ejecutar el chatbot y scraper juntos
- `templates/`: Directorio con todas las plantillas HTML
- `static/`: Directorio con archivos CSS, JavaScript e imágenes
- `chatbot_integration/`: Módulos para la integración del chatbot

### Modificar la Interfaz de Usuario

1. Las plantillas HTML se encuentran en `templates/`
2. Los estilos CSS están en `static/css/`
3. Los scripts JavaScript están en `static/js/`

### Añadir Nuevas Funcionalidades

1. Para añadir nuevas rutas, modifica `app_integrated.py`
2. Para añadir nuevas plantillas, crea archivos HTML en `templates/`
3. Para modificar la lógica del chatbot, edita los archivos en `chatbot_integration/`

### Pruebas

Después de realizar cambios, ejecuta la aplicación y verifica que todo funcione correctamente:

```bash
python app_integrated.py
```

### Guardar y Enviar Cambios

```bash
git add .
git commit -m "Descripción de los cambios realizados"
git push
```

## Notas Importantes

- La aplicación utiliza Flask para el backend
- Las plantillas HTML utilizan una combinación de HTML, CSS y JavaScript
- El chatbot está configurado para responder a preguntas frecuentes
- No hay autenticación implementada, así que cualquier usuario puede acceder a todas las funcionalidades

Si tienes alguna pregunta o problema, no dudes en contactarme directamente.

¡Buena suerte con las modificaciones!
