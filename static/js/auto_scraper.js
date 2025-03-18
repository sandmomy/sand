/**
 * auto_scraper.js
 * 
 * Funcionalidad JavaScript para controlar el Auto-Scraping con búsquedas en Google
 * y otros portales, integrando la interfaz de usuario con la API del servidor.
 */

// Estado del scraper
let scraperStatus = {
    isActive: false,
    progress: 0,
    lastRun: null,
    schedulerRunning: false
};

// Inicializar cuando el DOM esté completamente cargado
document.addEventListener('DOMContentLoaded', function() {
    // Inicializar elementos UI
    initUI();
    
    // Cargar estado inicial
    loadScraperStatus();
    
    // Configurar intervalos para actualización de estado
    setInterval(loadScraperStatus, 10000); // Actualizar cada 10 segundos
});

/**
 * Inicializa los elementos de la interfaz de usuario y establece los event listeners
 */
function initUI() {
    const scrapingToggle = document.getElementById('scraping-toggle');
    const runNowBtn = document.getElementById('run-scraper-now');
    const testSearchBtn = document.getElementById('test-search');
    
    // Toggle para activar/desactivar el programador de scraping
    if (scrapingToggle) {
        scrapingToggle.addEventListener('change', function() {
            toggleScheduler(this.checked);
        });
    }
    
    // Botón para ejecutar scraping ahora
    if (runNowBtn) {
        runNowBtn.addEventListener('click', function() {
            runScrapingNow();
        });
    }
    
    // Botón para probar búsqueda
    if (testSearchBtn) {
        testSearchBtn.addEventListener('click', function() {
            testSearch();
        });
    }
    
    // Configurar formulario para añadir búsquedas
    const addSearchForm = document.getElementById('add-search-form');
    if (addSearchForm) {
        addSearchForm.addEventListener('submit', function(e) {
            e.preventDefault();
            addNewSearch(this);
        });
    }
}

/**
 * Carga el estado actual del Auto-Scraper desde el servidor
 */
function loadScraperStatus() {
    fetch('/api/auto-scraper/status')
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                updateStatusUI(data.status);
            } else {
                showNotification('Error al cargar estado: ' + data.error, 'error');
            }
        })
        .catch(error => {
            console.error('Error al cargar estado:', error);
        });
}

/**
 * Actualiza la interfaz de usuario con el estado actual del scraper
 */
function updateStatusUI(status) {
    // Actualizar variables de estado
    scraperStatus = status;
    
    // Actualizar indicador de estado
    const statusBadge = document.getElementById('scraping-status');
    if (statusBadge) {
        statusBadge.textContent = status.is_running ? 'Activo' : 'Inactivo';
        statusBadge.className = 'badge ' + (status.is_running ? 'bg-success' : 'bg-danger');
    }
    
    // Actualizar toggle de scraping automático
    const scrapingToggle = document.getElementById('scraping-toggle');
    if (scrapingToggle) {
        scrapingToggle.checked = status.is_running;
    }
    
    // Actualizar barra de progreso
    const progressBar = document.getElementById('scraping-progress-bar');
    const progressText = document.getElementById('progress-percentage');
    const progress = status.progress || 0;
    
    if (progressBar) {
        progressBar.style.width = progress + '%';
        progressBar.setAttribute('aria-valuenow', progress);
    }
    
    if (progressText) {
        progressText.textContent = progress + '%';
    }
    
    // Actualizar tiempo de última ejecución
    const lastRunTime = document.getElementById('last-run-time');
    if (lastRunTime) {
        lastRunTime.textContent = status.last_update || 'Nunca';
    }
    
    // Actualizar lista de búsquedas configuradas si existe
    const searchesList = document.getElementById('searches-list');
    if (searchesList && status.searches) {
        searchesList.innerHTML = '';
        
        status.searches.forEach(search => {
            const li = document.createElement('li');
            li.className = 'list-group-item d-flex justify-content-between align-items-center';
            
            // Crear contenido del elemento
            const searchInfo = document.createElement('div');
            searchInfo.innerHTML = `
                <strong>${search.name}</strong>
                <div class="text-muted small">Query: "${search.query}"</div>
                <div class="text-muted small">Categoría: ${search.category} | Motor: ${search.engine}</div>
            `;
            
            // Crear botones de acción
            const actionBtns = document.createElement('div');
            
            // Botón para ejecutar búsqueda
            const runBtn = document.createElement('button');
            runBtn.className = 'btn btn-sm btn-primary me-1';
            runBtn.innerHTML = '<i class="fas fa-play"></i>';
            runBtn.setAttribute('title', 'Ejecutar búsqueda');
            runBtn.addEventListener('click', function() {
                runSingleSearch(search.name);
            });
            
            // Botón para eliminar búsqueda
            const deleteBtn = document.createElement('button');
            deleteBtn.className = 'btn btn-sm btn-danger';
            deleteBtn.innerHTML = '<i class="fas fa-trash"></i>';
            deleteBtn.setAttribute('title', 'Eliminar búsqueda');
            deleteBtn.addEventListener('click', function() {
                deleteSearch(search.name);
            });
            
            actionBtns.appendChild(runBtn);
            actionBtns.appendChild(deleteBtn);
            
            li.appendChild(searchInfo);
            li.appendChild(actionBtns);
            
            searchesList.appendChild(li);
        });
    }
}

/**
 * Activa o desactiva el programador de tareas del Auto-Scraper
 */
function toggleScheduler(enable) {
    fetch('/api/auto-scraper/scheduler', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            action: enable ? 'start' : 'stop'
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showNotification(data.message, 'success');
            loadScraperStatus(); // Actualizar estado
        } else {
            showNotification('Error: ' + data.error, 'error');
            // Revertir cambio en el UI
            const scrapingToggle = document.getElementById('scraping-toggle');
            if (scrapingToggle) {
                scrapingToggle.checked = !enable;
            }
        }
    })
    .catch(error => {
        console.error('Error:', error);
        showNotification('Error de conexión', 'error');
    });
}

/**
 * Ejecuta el proceso de scraping completo inmediatamente
 */
function runScrapingNow() {
    // Mostrar modal o indicador de carga
    showLoading();
    
    fetch('/api/auto-scraper/update', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            type: 'all'
        })
    })
    .then(response => response.json())
    .then(data => {
        hideLoading();
        
        if (data.success) {
            showNotification('Scraping completado: ' + data.message, 'success');
            loadScraperStatus(); // Actualizar estado
            
            // Mostrar resultados detallados si están disponibles
            if (data.results && data.results.length > 0) {
                showScrapingResults(data.results);
            }
        } else {
            showNotification('Error: ' + data.error, 'error');
        }
    })
    .catch(error => {
        hideLoading();
        console.error('Error:', error);
        showNotification('Error de conexión', 'error');
    });
}

/**
 * Ejecuta una búsqueda específica
 */
function runSingleSearch(searchName) {
    // Mostrar modal o indicador de carga
    showLoading();
    
    fetch('/api/auto-scraper/update', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            type: 'search',
            name: searchName
        })
    })
    .then(response => response.json())
    .then(data => {
        hideLoading();
        
        if (data.success) {
            showNotification(data.message, 'success');
            loadScraperStatus(); // Actualizar estado
            
            // Mostrar resultados detallados si están disponibles
            if (data.result) {
                showSearchResult(data.result);
            }
        } else {
            showNotification('Error: ' + data.error, 'error');
        }
    })
    .catch(error => {
        hideLoading();
        console.error('Error:', error);
        showNotification('Error de conexión', 'error');
    });
}

/**
 * Ejecuta una prueba de búsqueda
 */
function testSearch() {
    // Abrir modal para seleccionar búsqueda de prueba
    const searchSelect = document.getElementById('test-search-select');
    
    // Realizar solicitud para probar la búsqueda seleccionada
    const selectedSearch = searchSelect ? searchSelect.value : null;
    
    if (!selectedSearch) {
        showNotification('Selecciona una búsqueda para probar', 'warning');
        return;
    }
    
    // Mostrar modal o indicador de carga
    showLoading();
    
    fetch('/api/auto-scraper/test-search', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            name: selectedSearch
        })
    })
    .then(response => response.json())
    .then(data => {
        hideLoading();
        
        if (data.success) {
            showNotification('Prueba completada', 'success');
            
            // Mostrar resultados detallados
            if (data.result) {
                showSearchResult(data.result);
            }
        } else {
            showNotification('Error: ' + data.error, 'error');
        }
    })
    .catch(error => {
        hideLoading();
        console.error('Error:', error);
        showNotification('Error de conexión', 'error');
    });
}

/**
 * Añade una nueva búsqueda a la configuración
 */
function addNewSearch(form) {
    // Obtener datos del formulario
    const formData = new FormData(form);
    const searchData = {
        name: formData.get('name'),
        query: formData.get('query'),
        category: formData.get('category'),
        engine: formData.get('engine') || 'google',
        max_results: parseInt(formData.get('max_results') || 5),
        max_depth: parseInt(formData.get('max_depth') || 1),
        frequency: formData.get('frequency'),
        enabled: true
    };
    
    // Validar datos
    if (!searchData.name || !searchData.query || !searchData.category || !searchData.frequency) {
        showNotification('Por favor completa todos los campos obligatorios', 'warning');
        return;
    }
    
    // Mostrar indicador de carga
    showLoading();
    
    fetch('/api/auto-scraper/add-search', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(searchData)
    })
    .then(response => response.json())
    .then(data => {
        hideLoading();
        
        if (data.success) {
            showNotification(data.message, 'success');
            form.reset(); // Limpiar formulario
            loadScraperStatus(); // Actualizar listado
        } else {
            showNotification('Error: ' + data.error, 'error');
        }
    })
    .catch(error => {
        hideLoading();
        console.error('Error:', error);
        showNotification('Error de conexión', 'error');
    });
}

/**
 * Elimina una búsqueda de la configuración
 */
function deleteSearch(searchName) {
    if (!confirm(`¿Estás seguro de que deseas eliminar la búsqueda "${searchName}"?`)) {
        return;
    }
    
    // Mostrar indicador de carga
    showLoading();
    
    fetch('/api/auto-scraper/delete-search', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            name: searchName
        })
    })
    .then(response => response.json())
    .then(data => {
        hideLoading();
        
        if (data.success) {
            showNotification(data.message, 'success');
            loadScraperStatus(); // Actualizar listado
        } else {
            showNotification('Error: ' + data.error, 'error');
        }
    })
    .catch(error => {
        hideLoading();
        console.error('Error:', error);
        showNotification('Error de conexión', 'error');
    });
}

/**
 * Muestra los resultados de una operación de scraping completa
 */
function showScrapingResults(results) {
    let resultHTML = '<h5>Resultados del Scraping</h5><ul class="list-group">';
    
    results.forEach(result => {
        const success = result.success ? 
            '<span class="badge bg-success">Éxito</span>' : 
            '<span class="badge bg-danger">Error</span>';
            
        resultHTML += `
            <li class="list-group-item">
                ${success} 
                <strong>${result.search_name || result.source_name || 'Desconocido'}</strong>
                ${result.results_count ? `<span class="badge bg-info">${result.results_count} resultados</span>` : ''}
                ${result.error ? `<div class="text-danger small">${result.error}</div>` : ''}
            </li>
        `;
    });
    
    resultHTML += '</ul>';
    
    // Mostrar en modal o área designada
    const resultsContainer = document.getElementById('scraping-results-container');
    if (resultsContainer) {
        resultsContainer.innerHTML = resultHTML;
        resultsContainer.style.display = 'block';
    } else {
        // Crear modal con resultados
        const modal = document.createElement('div');
        modal.className = 'modal fade';
        modal.id = 'resultsModal';
        modal.innerHTML = `
            <div class="modal-dialog modal-lg">
                <div class="modal-content">
                    <div class="modal-header">
                        <h5 class="modal-title">Resultados del Scraping</h5>
                        <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
                    </div>
                    <div class="modal-body">
                        ${resultHTML}
                    </div>
                    <div class="modal-footer">
                        <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cerrar</button>
                    </div>
                </div>
            </div>
        `;
        
        document.body.appendChild(modal);
        const bsModal = new bootstrap.Modal(modal);
        bsModal.show();
    }
}

/**
 * Muestra los resultados de una búsqueda específica
 */
function showSearchResult(result) {
    let resultHTML = `
        <h5>Resultados de la Búsqueda "${result.search_name || result.query || 'Desconocido'}"</h5>
        <div class="mb-3">
            <strong>Query:</strong> ${result.query || 'N/A'}<br>
            <strong>Motor:</strong> ${result.engine || 'google'}<br>
            <strong>Resultados:</strong> ${result.results_count || 0}
        </div>
    `;
    
    if (result.items && result.items.length > 0) {
        resultHTML += '<h6>Páginas Encontradas:</h6><ul class="list-group">';
        
        result.items.forEach(item => {
            resultHTML += `<li class="list-group-item">${item}</li>`;
        });
        
        resultHTML += '</ul>';
    }
    
    // Mostrar en modal
    const modal = document.createElement('div');
    modal.className = 'modal fade';
    modal.id = 'searchResultModal';
    modal.innerHTML = `
        <div class="modal-dialog modal-lg">
            <div class="modal-content">
                <div class="modal-header">
                    <h5 class="modal-title">Resultados de Búsqueda</h5>
                    <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
                </div>
                <div class="modal-body">
                    ${resultHTML}
                </div>
                <div class="modal-footer">
                    <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cerrar</button>
                </div>
            </div>
        </div>
    `;
    
    document.body.appendChild(modal);
    const bsModal = new bootstrap.Modal(modal);
    bsModal.show();
}

/**
 * Muestra una notificación al usuario
 */
function showNotification(message, type = 'info') {
    // Si existe toastr, usarlo
    if (typeof toastr !== 'undefined') {
        toastr[type](message);
        return;
    }
    
    // Alternativa simple si no hay toastr
    const notification = document.createElement('div');
    notification.className = `alert alert-${type} alert-dismissible fade show notification-toast`;
    notification.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
    `;
    
    // Estilos para la notificación
    notification.style.position = 'fixed';
    notification.style.top = '20px';
    notification.style.right = '20px';
    notification.style.zIndex = '9999';
    notification.style.minWidth = '300px';
    
    document.body.appendChild(notification);
    
    // Auto-eliminar después de 5 segundos
    setTimeout(() => {
        notification.remove();
    }, 5000);
}

/**
 * Muestra indicador de carga
 */
function showLoading() {
    let loadingEl = document.getElementById('global-loading');
    
    if (!loadingEl) {
        loadingEl = document.createElement('div');
        loadingEl.id = 'global-loading';
        loadingEl.innerHTML = `
            <div class="spinner-border text-primary" role="status">
                <span class="visually-hidden">Cargando...</span>
            </div>
        `;
        
        // Estilos para el indicador de carga
        loadingEl.style.position = 'fixed';
        loadingEl.style.top = '0';
        loadingEl.style.left = '0';
        loadingEl.style.width = '100%';
        loadingEl.style.height = '100%';
        loadingEl.style.backgroundColor = 'rgba(0, 0, 0, 0.5)';
        loadingEl.style.display = 'flex';
        loadingEl.style.justifyContent = 'center';
        loadingEl.style.alignItems = 'center';
        loadingEl.style.zIndex = '9999';
        
        document.body.appendChild(loadingEl);
    } else {
        loadingEl.style.display = 'flex';
    }
}

/**
 * Oculta indicador de carga
 */
function hideLoading() {
    const loadingEl = document.getElementById('global-loading');
    if (loadingEl) {
        loadingEl.style.display = 'none';
    }
}

/**
 * Exporta los datos del scraping en el formato especificado
 */
function exportScrapedData(format = 'json', category = 'all') {
    // Mostrar indicador de carga
    showLoading();
    
    fetch('/api/auto-scraper/export', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            format: format,
            category: category
        })
    })
    .then(response => {
        // Para descargar el archivo
        if (response.ok) {
            return response.blob();
        }
        throw new Error('Error al exportar datos');
    })
    .then(blob => {
        hideLoading();
        
        // Generar nombre de archivo con timestamp
        const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
        const fileName = `scraping-export-${category}-${timestamp}.${format}`;
        
        // Crear URL del blob y enlace para descargar
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = fileName;
        document.body.appendChild(a);
        a.click();
        
        // Limpiar
        setTimeout(() => {
            document.body.removeChild(a);
            URL.revokeObjectURL(url);
        }, 100);
    })
    .catch(error => {
        hideLoading();
        console.error('Error:', error);
        showNotification('Error al exportar datos', 'error');
    });
}
