/**
 * Archon Integration - Controlador para la integración con Archon AI
 * Este archivo gestiona la interacción con los modelos de Archon, configuración
 * y funcionalidades avanzadas
 */

document.addEventListener('DOMContentLoaded', function() {
    console.log('Archon Integration cargado correctamente');
    
    // Referencias a elementos del DOM
    const modelTemp = document.getElementById('model-temp');
    const tempDisplay = modelTemp ? modelTemp.nextElementSibling : null;
    const toolButtons = document.querySelectorAll('.tool-select-btn');
    const saveConfigBtn = document.querySelector('.save-config-btn');
    
    // Configuración predeterminada de Archon
    const archonConfig = {
        modelTemp: 0.7,
        maxTokens: 4096, 
        reasoningDepth: 'medium',
        webAccess: true,
        activeModel: 'gemini-pro',
        defaultEmbeddings: 'text-embedding-3-small'
    };
    
    // Inicializar visualización de valores
    if (modelTemp && tempDisplay) {
        modelTemp.addEventListener('input', function() {
            tempDisplay.textContent = this.value;
            archonConfig.modelTemp = parseFloat(this.value);
        });
    }
    
    // Manejar selección de herramientas
    if (toolButtons && toolButtons.length > 0) {
        toolButtons.forEach(button => {
            button.addEventListener('click', function() {
                const tool = this.getAttribute('data-tool');
                activateTool(tool);
            });
        });
    }
    
    // Guardar configuración
    if (saveConfigBtn) {
        saveConfigBtn.addEventListener('click', function() {
            saveArchonConfig();
            
            // Efecto visual al guardar
            this.classList.add('saving');
            setTimeout(() => {
                this.classList.remove('saving');
                showNotification('Configuración guardada correctamente');
            }, 1000);
        });
    }
    
    // Manejadores de eventos para los selectores
    const maxTokensSelect = document.getElementById('max-tokens');
    const reasoningDepthSelect = document.getElementById('reasoning-depth');
    const webAccessToggle = document.getElementById('web-access');
    
    if (maxTokensSelect) {
        maxTokensSelect.addEventListener('change', function() {
            archonConfig.maxTokens = parseInt(this.value);
        });
    }
    
    if (reasoningDepthSelect) {
        reasoningDepthSelect.addEventListener('change', function() {
            archonConfig.reasoningDepth = this.value;
        });
    }
    
    if (webAccessToggle) {
        webAccessToggle.addEventListener('change', function() {
            archonConfig.webAccess = this.checked;
        });
    }
    
    // Funciones de utilidad
    
    /**
     * Activa una herramienta específica de Archon
     * @param {string} toolName - Nombre de la herramienta a activar
     */
    function activateTool(toolName) {
        console.log(`Activando herramienta: ${toolName}`);
        
        // Ocultar sección principal y mostrar la herramienta específica
        const mainContent = document.querySelector('.content');
        const scrapingSection = document.querySelector('.scraping-section');
        const chatSection = document.querySelector('.sidebar');
        
        // Resaltar el botón activo
        toolButtons.forEach(btn => {
            if (btn.getAttribute('data-tool') === toolName) {
                btn.classList.add('active-tool');
            } else {
                btn.classList.remove('active-tool');
            }
        });
        
        // Mostrar la herramienta correspondiente
        switch(toolName) {
            case 'scraping':
                if (mainContent) mainContent.style.display = 'none';
                if (scrapingSection) {
                    scrapingSection.style.display = 'block';
                    scrapingSection.scrollIntoView({ behavior: 'smooth' });
                }
                break;
                
            case 'chat':
                if (mainContent) mainContent.style.display = 'none';
                if (chatSection) {
                    chatSection.classList.add('sidebar-expanded');
                    document.querySelector('.main-container').classList.add('chat-active');
                }
                focusChatInput();
                break;
                
            case 'planner':
                showNotification('Planificador de Itinerarios - Funcionalidad en desarrollo');
                break;
                
            case 'events':
                showNotification('Eventos y Tendencias - Funcionalidad en desarrollo');
                break;
                
            default:
                showNotification('Herramienta no implementada');
        }
    }
    
    /**
     * Guarda la configuración de Archon
     */
    function saveArchonConfig() {
        console.log('Guardando configuración de Archon:', archonConfig);
        localStorage.setItem('archonConfig', JSON.stringify(archonConfig));
        
        // Aplicar configuración al agente
        applyArchonConfig();
    }
    
    /**
     * Aplica la configuración guardada al agente de Archon
     */
    function applyArchonConfig() {
        // Aquí se integraría con la API de Archon cuando esté disponible
        fetch('/api/archon_config', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(archonConfig)
        })
        .then(response => response.json())
        .then(data => {
            console.log('Respuesta de configuración:', data);
        })
        .catch(error => {
            console.error('Error al configurar Archon:', error);
            showNotification('Error al aplicar configuración', 'error');
        });
    }
    
    /**
     * Muestra una notificación al usuario
     * @param {string} message - Mensaje a mostrar
     * @param {string} type - Tipo de notificación (success, error, warning)
     */
    function showNotification(message, type = 'success') {
        // Crear elemento de notificación
        const notification = document.createElement('div');
        notification.className = `notification ${type}`;
        notification.innerHTML = `
            <div class="notification-content">
                <i class="fas ${type === 'error' ? 'fa-exclamation-circle' : 'fa-check-circle'}"></i>
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
     * Enfoca el input del chat
     */
    function focusChatInput() {
        const chatInput = document.getElementById('chat-input');
        if (chatInput) {
            setTimeout(() => {
                chatInput.focus();
            }, 300);
        }
    }
    
    // Cargar configuración guardada si existe
    function loadSavedConfig() {
        const savedConfig = localStorage.getItem('archonConfig');
        if (savedConfig) {
            try {
                const parsedConfig = JSON.parse(savedConfig);
                Object.assign(archonConfig, parsedConfig);
                
                // Actualizar UI con valores guardados
                if (modelTemp && tempDisplay) {
                    modelTemp.value = archonConfig.modelTemp;
                    tempDisplay.textContent = archonConfig.modelTemp;
                }
                
                if (maxTokensSelect) {
                    maxTokensSelect.value = archonConfig.maxTokens;
                }
                
                if (reasoningDepthSelect) {
                    reasoningDepthSelect.value = archonConfig.reasoningDepth;
                }
                
                if (webAccessToggle) {
                    webAccessToggle.checked = archonConfig.webAccess;
                }
                
                console.log('Configuración cargada:', archonConfig);
            } catch (e) {
                console.error('Error al cargar configuración:', e);
            }
        }
    }
    
    // Inicializar carga de configuración
    loadSavedConfig();
});

// Estilos CSS para notificaciones
(function() {
    const style = document.createElement('style');
    style.textContent = `
        .notification {
            position: fixed;
            top: 20px;
            right: -300px;
            width: 280px;
            padding: 15px;
            background-color: rgba(20, 20, 20, 0.95);
            border-left: 4px solid #FFD700;
            box-shadow: 0 4px 15px rgba(0, 0, 0, 0.5);
            border-radius: 4px;
            z-index: 9999;
            transition: right 0.3s ease;
        }
        
        .notification.show {
            right: 20px;
        }
        
        .notification-content {
            display: flex;
            align-items: center;
            color: #fff;
        }
        
        .notification-content i {
            font-size: 1.5rem;
            color: #FFD700;
            margin-right: 15px;
        }
        
        .notification.error {
            border-left: 4px solid #ff3860;
        }
        
        .notification.error i {
            color: #ff3860;
        }
        
        .save-config-btn.saving {
            background: linear-gradient(45deg, #222, #444);
            opacity: 0.7;
            pointer-events: none;
        }
        
        .active-tool {
            background: linear-gradient(45deg, #333, #555) !important;
            box-shadow: 0 0 20px rgba(255, 215, 0, 0.6) !important;
            transform: translateY(-2px);
        }
    `;
    document.head.appendChild(style);
})();
