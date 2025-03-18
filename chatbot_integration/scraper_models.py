"""
Modelos Pydantic para el sistema de scraping automático.
Estos modelos proporcionan estructura y validación para los datos utilizados en el scraper.
"""
from pydantic import BaseModel, Field, HttpUrl, validator
from typing import List, Optional, Dict, Any, Union
from datetime import datetime
from enum import Enum

class FrequencyType(str, Enum):
    """Tipos de frecuencia para las actualizaciones de scraping"""
    HOURLY = "hourly"
    DAILY = "daily"
    WEEKLY = "weekly"
    BIWEEKLY = "biweekly"
    MONTHLY = "monthly"
    CUSTOM = "custom"

class CategoryType(str, Enum):
    """Categorías de contenido para clasificación"""
    EVENTOS = "eventos"
    PLAYAS = "playas"
    RESTAURANTES = "restaurantes"
    HOTELES = "hoteles"
    OCIO = "ocio"
    GENERAL = "general"
    CUSTOM = "custom"

class SourceConfig(BaseModel):
    """Configuración de una fuente de scraping"""
    id: Optional[str] = Field(None, description="ID único de la fuente")
    name: str = Field(..., description="Nombre descriptivo de la fuente")
    url: str = Field(..., description="URL de la fuente a scrapear")
    category: CategoryType = Field(CategoryType.GENERAL, description="Categoría del contenido")
    frequency: FrequencyType = Field(FrequencyType.DAILY, description="Frecuencia de actualización")
    enabled: bool = Field(True, description="Si la fuente está habilitada")
    last_scraped: Optional[datetime] = Field(None, description="Última vez que se scrapeó esta fuente")
    
    @validator('url')
    def validate_url(cls, v):
        """Validar que la URL tenga un formato correcto"""
        # Validación básica de URL
        if not v.startswith(('http://', 'https://')):
            raise ValueError('La URL debe comenzar con http:// o https://')
        return v
    
    class Config:
        schema_extra = {
            "example": {
                "id": "src_ibiza_spotlight_eventos",
                "name": "Ibiza Spotlight Eventos",
                "url": "https://www.ibiza-spotlight.com/events",
                "category": "eventos",
                "frequency": "daily",
                "enabled": True
            }
        }

class SearchConfig(BaseModel):
    """Configuración de una búsqueda programada"""
    id: Optional[str] = Field(None, description="ID único de la búsqueda")
    name: str = Field(..., description="Nombre descriptivo de la búsqueda")
    query: str = Field(..., description="Consulta de búsqueda")
    engine: str = Field("google", description="Motor de búsqueda a utilizar")
    category: CategoryType = Field(CategoryType.GENERAL, description="Categoría de la búsqueda")
    max_results: int = Field(5, description="Número máximo de resultados a procesar")
    max_depth: int = Field(1, description="Profundidad máxima de las páginas a scrapear")
    frequency: FrequencyType = Field(FrequencyType.WEEKLY, description="Frecuencia de ejecución")
    enabled: bool = Field(True, description="Si la búsqueda está habilitada")
    last_executed: Optional[datetime] = Field(None, description="Última vez que se ejecutó esta búsqueda")
    
    class Config:
        schema_extra = {
            "example": {
                "id": "search_eventos_ibiza_2025",
                "name": "Eventos Ibiza 2025",
                "query": "eventos ibiza 2025 fechas discotecas fiestas",
                "engine": "google",
                "category": "eventos",
                "max_results": 5,
                "max_depth": 1,
                "frequency": "weekly",
                "enabled": True
            }
        }

class ContentSegment(BaseModel):
    """Segmento de contenido extraído de una página"""
    content: str = Field(..., description="Texto del contenido")
    type: str = Field("text", description="Tipo de contenido (texto, título, lista, etc.)")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Metadatos adicionales")
    embedding: Optional[List[float]] = Field(None, description="Vector de embedding del contenido")

class ExtractedDocument(BaseModel):
    """Documento extraído de una fuente"""
    url: str = Field(..., description="URL de origen del documento")
    title: str = Field(..., description="Título del documento")
    source_id: Optional[str] = Field(None, description="ID de la fuente o búsqueda de origen")
    category: CategoryType = Field(CategoryType.GENERAL, description="Categoría del documento")
    extraction_date: datetime = Field(default_factory=datetime.now, description="Fecha de extracción")
    last_updated: Optional[datetime] = Field(None, description="Última actualización conocida")
    content_segments: List[ContentSegment] = Field(default_factory=list, description="Segmentos de contenido extraídos")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Metadatos adicionales")
    
    class Config:
        schema_extra = {
            "example": {
                "url": "https://www.ibiza-spotlight.com/events/2025-summer",
                "title": "Eventos de Verano 2025 en Ibiza",
                "source_id": "src_ibiza_spotlight_eventos",
                "category": "eventos",
                "extraction_date": "2025-03-10T15:30:00",
                "content_segments": [
                    {
                        "content": "Los eventos más esperados del verano 2025 en Ibiza",
                        "type": "title",
                        "metadata": {"importance": "high"}
                    }
                ]
            }
        }

class ScraperOptions(BaseModel):
    """Opciones generales para el scraper"""
    update_time: str = Field("02:00", description="Hora para actualizaciones diarias (formato 24h)")
    update_day: str = Field("Monday", description="Día para actualizaciones semanales")
    update_date: int = Field(1, description="Día del mes para actualizaciones mensuales")
    export_data: bool = Field(True, description="Exportar datos para uso en otro sistema")
    export_path: str = Field("exports/", description="Ruta para exportación de datos")
    use_headless: bool = Field(True, description="Ejecutar navegador en modo headless")
    max_concurrent_tasks: int = Field(3, description="Máximo de tareas concurrentes")
    request_delay: float = Field(1.0, description="Retraso entre solicitudes (segundos)")
    log_level: str = Field("INFO", description="Nivel de logging")

class ScraperStatus(BaseModel):
    """Estado actual del scraper"""
    is_running: bool = Field(False, description="Si el scraper está actualmente en ejecución")
    current_task: Optional[str] = Field(None, description="Tarea actual en ejecución")
    progress: int = Field(0, description="Progreso en porcentaje (0-100)")
    completed_tasks: int = Field(0, description="Número de tareas completadas")
    total_tasks: int = Field(0, description="Número total de tareas")
    start_time: Optional[datetime] = Field(None, description="Hora de inicio de la ejecución actual")
    last_completed_time: Optional[datetime] = Field(None, description="Hora de la última tarea completada")
    errors: List[str] = Field(default_factory=list, description="Errores encontrados durante la ejecución")

class ScraperConfig(BaseModel):
    """Configuración completa del scraper"""
    sources: List[SourceConfig] = Field(default_factory=list, description="Fuentes de contenido a scrapear")
    searches: List[SearchConfig] = Field(default_factory=list, description="Búsquedas programadas")
    options: ScraperOptions = Field(default_factory=ScraperOptions, description="Opciones generales")
    completed_tasks: int = Field(0, description="Número total de tareas completadas")
    last_run: Optional[Dict[str, Any]] = Field(None, description="Detalles de la última ejecución")
    
    class Config:
        schema_extra = {
            "example": {
                "sources": [
                    {
                        "id": "src_ibiza_spotlight_eventos",
                        "name": "Ibiza Spotlight Eventos",
                        "url": "https://www.ibiza-spotlight.com/events",
                        "category": "eventos",
                        "frequency": "daily",
                        "enabled": True
                    }
                ],
                "searches": [
                    {
                        "id": "search_eventos_ibiza_2025",
                        "name": "Eventos Ibiza 2025",
                        "query": "eventos ibiza 2025 fechas discotecas fiestas",
                        "engine": "google",
                        "category": "eventos",
                        "max_results": 5,
                        "frequency": "weekly",
                        "enabled": True
                    }
                ],
                "options": {
                    "update_time": "02:00",
                    "export_data": True,
                    "use_headless": True
                }
            }
        }

class ScrapingTask(BaseModel):
    """Tarea individual de scraping"""
    id: str = Field(..., description="ID único de la tarea")
    type: str = Field(..., description="Tipo de tarea (source, search)")
    config_id: str = Field(..., description="ID de la configuración (fuente o búsqueda)")
    status: str = Field("pending", description="Estado de la tarea")
    created_at: datetime = Field(default_factory=datetime.now, description="Fecha de creación")
    started_at: Optional[datetime] = Field(None, description="Fecha de inicio")
    completed_at: Optional[datetime] = Field(None, description="Fecha de finalización")
    result: Optional[Dict[str, Any]] = Field(None, description="Resultado de la tarea")
    error: Optional[str] = Field(None, description="Error si la tarea falló")

class KnowledgeBase(BaseModel):
    """Base de conocimiento del scraper"""
    documents: List[ExtractedDocument] = Field(default_factory=list, description="Documentos extraídos")
    last_updated: datetime = Field(default_factory=datetime.now, description="Última actualización")
    stats: Dict[str, Any] = Field(default_factory=dict, description="Estadísticas")
