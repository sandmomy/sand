/**
 * Web Analyzer - Controlador para el análisis de sitios web
 * Este archivo gestiona la funcionalidad básica de scraping y análisis de sitios web
 */

document.addEventListener('DOMContentLoaded', function() {
    console.log('Web Analyzer cargado correctamente');
    
    // Referencias a elementos del DOM
    const scrapingForm = document.getElementById('scraping-form');
    const urlInput = document.getElementById('url-input');
    const pasteUrlBtn = document.getElementById('paste-url-btn');
    const filterOptions = document.querySelectorAll('.filter-option');
    const siteCards = document.querySelectorAll('.site-card');
    const resultsModal = document.getElementById('results-modal');
    const modalClose = document.querySelector('.modal-close');
    
    // Configurar botón de pegar URL
    if (pasteUrlBtn && urlInput) {
        pasteUrlBtn.addEventListener('click', async function() {
            try {
                const text = await navigator.clipboard.readText();
                if (isValidUrl(text)) {
                    urlInput.value = text;
                } else {
                    showNotification('El texto copiado no es una URL válida', 'error');
                }
            } catch (err) {
                showNotification('No se pudo acceder al portapapeles', 'error');
            }
        });
    }
    
    // Gestionar envío del formulario de scraping
    if (scrapingForm) {
        scrapingForm.addEventListener('submit', function(e) {
            e.preventDefault();
            
            const url = urlInput.value.trim();
            if (!url || !isValidUrl(url)) {
                showNotification('Por favor, introduce una URL válida', 'error');
                return;
            }
            
            const scrapingTool = document.getElementById('scraping-tool').value;
            const analysisDepth = document.getElementById('analysis-depth').value;
            const dataCategory = document.getElementById('data-category').value;
            const extractImages = document.getElementById('extract-images').checked;
            const extractLinks = document.getElementById('extract-links').checked;
            const useAiSummary = document.getElementById('use-ai-summary').checked;
            const deepReasoning = document.getElementById('deep-reasoning').checked;
            
            // Iniciar análisis web
            startWebAnalysis(url, {
                tool: scrapingTool,
                depth: analysisDepth,
                category: dataCategory,
                extractImages,
                extractLinks,
                useAiSummary,
                deepReasoning
            });
        });
    }
    
    // Botón para limpiar formulario
    const clearFormBtn = document.getElementById('clear-form');
    if (clearFormBtn && scrapingForm) {
        clearFormBtn.addEventListener('click', function() {
            scrapingForm.reset();
        });
    }
    
    // Configurar modal de resultados
    if (resultsModal && modalClose) {
        modalClose.addEventListener('click', function() {
            resultsModal.style.display = 'none';
        });
        
        window.addEventListener('click', function(e) {
            if (e.target === resultsModal) {
                resultsModal.style.display = 'none';
            }
        });
    }
    
    // Manejar filtrado de sitios
    if (filterOptions.length > 0 && siteCards.length > 0) {
        filterOptions.forEach(option => {
            option.addEventListener('click', function() {
                // Quitar clase active de todas las opciones
                filterOptions.forEach(opt => opt.classList.remove('active'));
                
                // Añadir clase active a la opción seleccionada
                this.classList.add('active');
                
                const filter = this.getAttribute('data-filter');
                
                // Filtrar sitios
                siteCards.forEach(card => {
                    const category = card.getAttribute('data-category');
                    
                    if (filter === 'all' || category === filter) {
                        card.style.display = '';
                    } else {
                        card.style.display = 'none';
                    }
                });
            });
        });
    }
    
    // Configurar botones de acción para sitios existentes
    const siteActionButtons = document.querySelectorAll('.site-btn');
    if (siteActionButtons.length > 0) {
        siteActionButtons.forEach(btn => {
            btn.addEventListener('click', function() {
                const siteCard = this.closest('.site-card');
                const siteTitle = siteCard.querySelector('.site-title').textContent;
                
                if (this.classList.contains('analyze-btn')) {
                    const siteUrl = this.getAttribute('data-url');
                    if (urlInput) urlInput.value = siteUrl;
                    
                    showNotification(`Reanalizando sitio: ${siteTitle}`, 'info');
                    
                    // Iniciar análisis
                    startWebAnalysis(siteUrl, {
                        tool: 'auto',
                        depth: '2',
                        category: siteCard.getAttribute('data-category'),
                        extractImages: true,
                        extractLinks: true,
                        useAiSummary: false,
                        deepReasoning: false
                    });
                    
                } else if (this.classList.contains('view-data-btn')) {
                    showNotification(`Visualizando datos de ${siteTitle}`, 'info');
                    // En una implementación real, aquí mostraríamos los datos almacenados
                } else if (this.classList.contains('delete-btn')) {
                    if (confirm(`¿Estás seguro de que quieres eliminar el sitio "${siteTitle}" de la biblioteca?`)) {
                        siteCard.classList.add('deleting');
                        
                        setTimeout(() => {
                            siteCard.remove();
                            showNotification(`Sitio ${siteTitle} eliminado correctamente`, 'success');
                        }, 500);
                    }
                }
            });
        });
    }
    
    // Funciones auxiliares
    
    /**
     * Valida si una cadena es una URL válida
     * @param {string} string - Cadena a validar
     * @returns {boolean} - true si es una URL válida
     */
    function isValidUrl(string) {
        try {
            new URL(string);
            return true;
        } catch (_) {
            return false;
        }
    }
    
    /**
     * Inicia el análisis de un sitio web
     * @param {string} url - URL del sitio a analizar
     * @param {Object} options - Opciones de análisis
     */
    function startWebAnalysis(url, options) {
        showNotification(`Iniciando análisis de ${url}...`, 'info');
        
        // Mostrar modal de resultados
        const resultsContainer = document.querySelector('.scraping-results');
        if (resultsContainer && resultsModal) {
            resultsContainer.innerHTML = `
                <div class="analysis-progress">
                    <div class="progress-header">
                        <h3>Analizando: ${url}</h3>
                        <div class="progress-status">Conectando...</div>
                    </div>
                    <div class="progress-bar">
                        <div class="progress-fill" style="width: 0%"></div>
                    </div>
                    <div class="tool-info">
                        <span>Herramienta: ${getToolName(options.tool)}</span>
                        <span>Profundidad: ${options.depth}</span>
                        <span>Categoría: ${getCategoryName(options.category)}</span>
                    </div>
                    <div class="ai-info">
                        ${options.useAiSummary ? '<span class="ai-badge gemini">Gemini Pro</span>' : ''}
                        ${options.deepReasoning ? '<span class="ai-badge deepseek">DeepSeek R1</span>' : ''}
                    </div>
                </div>
                <div class="analysis-log"></div>
            `;
            
            resultsModal.style.display = 'block';
            
            // Simular progreso de análisis
            simulateAnalysisProgress(url, options);
        }
    }
    
    /**
     * Simula el progreso del análisis web
     * @param {string} url - URL del sitio a analizar
     * @param {Object} options - Opciones de análisis
     */
    function simulateAnalysisProgress(url, options) {
        const progressFill = document.querySelector('.progress-fill');
        const progressStatus = document.querySelector('.progress-status');
        const analysisLog = document.querySelector('.analysis-log');
        
        let progress = 0;
        const steps = [
            { percent: 10, status: 'Conectando con el servidor...', log: `Iniciando conexión con ${url}` },
            { percent: 20, status: 'Obteniendo HTML...', log: 'Descargando estructura de la página' },
            { percent: 30, status: 'Analizando estructura...', log: 'Procesando documento HTML' },
            { percent: 40, status: 'Extrayendo datos...', log: 'Identificando elementos principales' },
            { percent: 60, status: 'Procesando contenido...', log: options.extractImages ? 'Extrayendo imágenes (encontradas: 12)' : 'Analizando texto' },
            { percent: 70, status: 'Analizando enlaces...', log: options.extractLinks ? 'Procesando enlaces encontrados (32 enlaces)' : 'Completando análisis básico' },
            { percent: 80, status: 'Aplicando IA...', log: options.useAiSummary ? 'Generando resumen con Gemini Pro...' : 'Finalizando análisis' },
            { percent: 90, status: 'Razonamiento profundo...', log: options.deepReasoning ? 'Aplicando razonamiento con DeepSeek R1...' : 'Preparando resultados' },
            { percent: 100, status: 'Análisis completado', log: 'Sitio web analizado correctamente' }
        ];
        
        let currentStep = 0;
        
        const interval = setInterval(() => {
            if (currentStep < steps.length) {
                const step = steps[currentStep];
                progress = step.percent;
                
                if (progressFill) progressFill.style.width = `${progress}%`;
                if (progressStatus) progressStatus.textContent = step.status;
                
                if (analysisLog && step.log) {
                    const logEntry = document.createElement('div');
                    logEntry.className = 'log-entry';
                    logEntry.innerHTML = `
                        <span class="log-time">${getCurrentTime()}</span>
                        <span class="log-message">${step.log}</span>
                    `;
                    analysisLog.appendChild(logEntry);
                    analysisLog.scrollTop = analysisLog.scrollHeight;
                }
                
                currentStep++;
            } else {
                clearInterval(interval);
                
                // Añadir resultados tras completar el análisis
                setTimeout(() => {
                    showAnalysisResults(url, options);
                }, 1000);
            }
        }, 800);
    }
    
    /**
     * Muestra los resultados del análisis de un sitio web
     * @param {string} url - URL del sitio analizado
     * @param {Object} options - Opciones utilizadas en el análisis
     */
    function showAnalysisResults(url, options) {
        const analysisLog = document.querySelector('.analysis-log');
        
        if (analysisLog) {
            // Añadir resumen de resultados
            const resultsSection = document.createElement('div');
            resultsSection.className = 'analysis-results';
            
            let aiSummary = '';
            if (options.useAiSummary) {
                aiSummary = `
                    <div class="ai-summary">
                        <h4><i class="fas fa-robot"></i> Resumen generado por IA (Gemini Pro)</h4>
                        <p>Este sitio web parece ser un portal turístico sobre Ibiza que ofrece información sobre ${getCategoryName(options.category).toLowerCase()}. 
                        El sitio contiene aproximadamente 12 imágenes y 32 enlaces a recursos relacionados. La estructura es clara y la navegación bien organizada.</p>
                    </div>
                `;
            }
            
            // Generar un nombre de sitio basado en la URL
            const siteName = url.replace(/^https?:\/\/(?:www\.)?([^\/]+).*$/, '$1');
            
            resultsSection.innerHTML = `
                <h3>Resultados del análisis</h3>
                <div class="site-preview">
                    <img src="../static/img/site-preview-new.jpg" alt="${siteName}" onerror="this.src='https://via.placeholder.com/400x250?text=Vista+previa+no+disponible'">
                </div>
                <div class="site-details">
                    <h4>${siteName}</h4>
                    <p class="site-url">${url}</p>
                    <div class="stats-grid">
                        <div class="stat-item">
                            <span class="stat-value">32</span>
                            <span class="stat-label">Enlaces</span>
                        </div>
                        <div class="stat-item">
                            <span class="stat-value">12</span>
                            <span class="stat-label">Imágenes</span>
                        </div>
                        <div class="stat-item">
                            <span class="stat-value">4</span>
                            <span class="stat-label">Secciones</span>
                        </div>
                        <div class="stat-item">
                            <span class="stat-value">~5k</span>
                            <span class="stat-label">Palabras</span>
                        </div>
                    </div>
                </div>
                ${aiSummary}
                <div class="result-actions">
                    <button class="action-btn save-site-btn">
                        <i class="fas fa-save"></i> Guardar sitio
                    </button>
                    <button class="secondary-btn close-results-btn">
                        <i class="fas fa-times"></i> Cerrar
                    </button>
                </div>
            `;
            
            analysisLog.appendChild(resultsSection);
            
            // Configurar botones de acción
            const saveBtn = resultsSection.querySelector('.save-site-btn');
            const closeBtn = resultsSection.querySelector('.close-results-btn');
            
            if (saveBtn) {
                saveBtn.addEventListener('click', function() {
                    saveSiteToLibrary(url, siteName, options.category);
                });
            }
            
            if (closeBtn) {
                closeBtn.addEventListener('click', function() {
                    if (resultsModal) {
                        resultsModal.style.display = 'none';
                    }
                });
            }
        }
    }
    
    /**
     * Guarda un sitio web analizado en la biblioteca
     * @param {string} url - URL del sitio
     * @param {string} name - Nombre del sitio
     * @param {string} category - Categoría del sitio
     */
    function saveSiteToLibrary(url, name, category) {
        showNotification(`Guardando sitio: ${name}...`, 'info');
        
        // En una implementación real, aquí guardaríamos el sitio en la base de datos
        // Para esta demo, simplemente simulamos que se ha guardado
        
        setTimeout(() => {
            showNotification(`Sitio ${name} guardado correctamente`, 'success');
            
            // Cerrar modal de resultados
            if (resultsModal) {
                resultsModal.style.display = 'none';
            }
            
            // Añadir sitio a la biblioteca
            const sitesGrid = document.querySelector('.sites-grid');
            
            if (sitesGrid) {
                const siteCard = document.createElement('div');
                siteCard.className = 'site-card new-card';
                siteCard.setAttribute('data-category', category);
                
                // Obtener fecha actual formateada
                const date = new Date();
                const formattedDate = `${date.getDate()} ${getMonthName(date.getMonth())} ${date.getFullYear()}`;
                
                siteCard.innerHTML = `
                    <div class="site-preview">
                        <img src="../static/img/site-preview-new.jpg" alt="${name}" onerror="this.src='https://via.placeholder.com/400x250?text=Vista+previa+no+disponible'">
                        <div class="site-overlay">
                            <a href="${url}" target="_blank" class="visit-btn">
                                <i class="fas fa-external-link-alt"></i> Visitar
                            </a>
                        </div>
                    </div>
                    <div class="site-info">
                        <h3 class="site-title">${name}</h3>
                        <div class="site-url">${url.replace(/^https?:\/\/(?:www\.)?/, '').replace(/\/$/, '')}</div>
                        <p class="site-description">Sitio web relacionado con ${getCategoryName(category).toLowerCase()} en Ibiza.</p>
                        <div class="site-meta">
                            <span class="site-category">${getCategoryName(category)}</span>
                            <span class="site-date">Analizado: ${formattedDate}</span>
                        </div>
                    </div>
                    <div class="site-actions">
                        <button class="site-btn analyze-btn" data-url="${url}">
                            <i class="fas fa-sync-alt"></i> Reanalizar
                        </button>
                        <button class="site-btn view-data-btn">
                            <i class="fas fa-chart-bar"></i> Ver Datos
                        </button>
                        <button class="site-btn delete-btn">
                            <i class="fas fa-trash"></i>
                        </button>
                    </div>
                `;
                
                sitesGrid.prepend(siteCard);
                
                // Añadir efecto de entrada
                setTimeout(() => {
                    siteCard.classList.remove('new-card');
                }, 10);
                
                // Configurar botones
                const analyzeBtn = siteCard.querySelector('.analyze-btn');
                const viewDataBtn = siteCard.querySelector('.view-data-btn');
                const deleteBtn = siteCard.querySelector('.delete-btn');
                
                if (analyzeBtn) {
                    analyzeBtn.addEventListener('click', function() {
                        const siteUrl = this.getAttribute('data-url');
                        if (urlInput) urlInput.value = siteUrl;
                        startWebAnalysis(siteUrl, {
                            tool: 'auto',
                            depth: '2',
                            category: category,
                            extractImages: true,
                            extractLinks: true,
                            useAiSummary: false,
                            deepReasoning: false
                        });
                    });
                }
                
                if (viewDataBtn) {
                    viewDataBtn.addEventListener('click', function() {
                        showNotification(`Visualizando datos de ${name}`, 'info');
                    });
                }
                
                if (deleteBtn) {
                    deleteBtn.addEventListener('click', function() {
                        if (confirm(`¿Estás seguro de que quieres eliminar el sitio "${name}" de la biblioteca?`)) {
                            siteCard.classList.add('deleting');
                            
                            setTimeout(() => {
                                siteCard.remove();
                                showNotification(`Sitio ${name} eliminado correctamente`, 'success');
                            }, 500);
                        }
                    });
                }
            }
        }, 1000);
    }
    
    // Funciones auxiliares adicionales
    
    function getCurrentTime() {
        const now = new Date();
        return `${now.getHours().toString().padStart(2, '0')}:${now.getMinutes().toString().padStart(2, '0')}:${now.getSeconds().toString().padStart(2, '0')}`;
    }
    
    function getToolName(toolId) {
        const tools = {
            'auto': 'Automática',
            'beautifulsoup': 'Beautiful Soup',
            'scrapy': 'Scrapy',
            'selenium': 'Selenium',
            'playwright': 'Playwright'
        };
        return tools[toolId] || 'Automática';
    }
    
    function getCategoryName(category) {
        const categories = {
            'general': 'General',
            'eventos': 'Eventos y fiestas',
            'lugares': 'Lugares y atracciones',
            'restaurantes': 'Restaurantes y gastronomía',
            'playas': 'Playas e información costera'
        };
        return categories[category] || 'General';
    }
    
    function getMonthName(month) {
        const months = ['Ene', 'Feb', 'Mar', 'Abr', 'May', 'Jun', 'Jul', 'Ago', 'Sep', 'Oct', 'Nov', 'Dic'];
        return months[month];
    }
    
    /**
     * Muestra una notificación al usuario
     * @param {string} message - Mensaje a mostrar
     * @param {string} type - Tipo de notificación (success, error, info)
     */
    function showNotification(message, type = 'success') {
        // Comprobar si ya existe un elemento de notificación
        const existingNotification = document.querySelector('.notification');
        if (existingNotification) {
            existingNotification.remove();
        }
        
        // Crear elemento de notificación
        const notification = document.createElement('div');
        notification.className = `notification ${type}`;
        notification.innerHTML = `
            <div class="notification-content">
                <i class="fas ${getNotificationIcon(type)}"></i>
                <span>${message}</span>
            </div>
        `;
        
        // Añadir al DOM
        document.body.appendChild(notification);
        
        // Mostrar con animación
        setTimeout(() => {
            notification.classList.add('show');
        }, 10);
        
        // Eliminar después de un tiempo
        setTimeout(() => {
            notification.classList.remove('show');
            setTimeout(() => {
                document.body.removeChild(notification);
            }, 300);
        }, 3000);
    }
    
    /**
     * Obtiene el icono correspondiente al tipo de notificación
     * @param {string} type - Tipo de notificación
     * @returns {string} - Clase CSS para el icono
     */
    function getNotificationIcon(type) {
        const iconMap = {
            'success': 'fa-check-circle',
            'error': 'fa-exclamation-circle',
            'info': 'fa-info-circle',
            'warning': 'fa-exclamation-triangle'
        };
        
        return iconMap[type] || 'fa-info-circle';
    }
});
