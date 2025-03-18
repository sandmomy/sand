/**
 * Videos Manager - Controlador para la gestión de videos
 * Este archivo gestiona la subida, visualización y gestión de videos en la plataforma
 * Actualizado: 2025-03-17 08:29
 */

document.addEventListener('DOMContentLoaded', function() {
    console.log('Videos Manager cargado correctamente - Actualizado 08:29');
    
    // Referencias a elementos del DOM
    const videoInput = document.getElementById('video-input');
    const uploadForm = document.getElementById('upload-video-form');
    const filterOptions = document.querySelectorAll('.filter-option');
    const fileCards = document.querySelectorAll('.file-card');
    
    // Inicializar la carga de videos
    if (videoInput) {
        // Manejar selección de videos
        videoInput.addEventListener('change', function() {
            if (this.files.length > 0) {
                console.log(`${this.files.length} videos seleccionados`);
                showVideoInfo(this.files);
            }
        });
        
        // Configurar área de arrastrar y soltar
        const dropArea = document.querySelector('.file-drop-area');
        
        if (dropArea) {
            ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
                dropArea.addEventListener(eventName, preventDefaults, false);
            });
            
            function preventDefaults(e) {
                e.preventDefault();
                e.stopPropagation();
            }
            
            ['dragenter', 'dragover'].forEach(eventName => {
                dropArea.addEventListener(eventName, highlight, false);
            });
            
            ['dragleave', 'drop'].forEach(eventName => {
                dropArea.addEventListener(eventName, unhighlight, false);
            });
            
            function highlight() {
                dropArea.classList.add('highlight');
            }
            
            function unhighlight() {
                dropArea.classList.remove('highlight');
            }
            
            dropArea.addEventListener('drop', handleDrop, false);
            
            function handleDrop(e) {
                const dt = e.dataTransfer;
                const files = dt.files;
                videoInput.files = files;
                
                // Disparar evento change manualmente
                const event = new Event('change');
                videoInput.dispatchEvent(event);
            }
        }
    }
    
    // Manejar envío del formulario
    if (uploadForm) {
        uploadForm.addEventListener('submit', function(e) {
            e.preventDefault();
            
            const files = videoInput.files;
            if (!files || files.length === 0) {
                showNotification('Selecciona al menos un video para subir', 'error');
                return;
            }
            
            const category = document.getElementById('video-category').value;
            const description = document.getElementById('video-description').value;
            
            // Simular carga de videos
            uploadVideos(files, category, description);
        });
    }
    
    // Manejar filtrado de videos
    if (filterOptions.length > 0 && fileCards.length > 0) {
        filterOptions.forEach(option => {
            option.addEventListener('click', function() {
                // Quitar clase active de todas las opciones
                filterOptions.forEach(opt => opt.classList.remove('active'));
                
                // Añadir clase active a la opción seleccionada
                this.classList.add('active');
                
                const filter = this.getAttribute('data-filter');
                
                // Filtrar videos
                fileCards.forEach(card => {
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
    
    // Manejar acciones de los videos
    const viewButtons = document.querySelectorAll('.view-btn');
    const downloadButtons = document.querySelectorAll('.download-btn');
    const deleteButtons = document.querySelectorAll('.delete-btn');
    
    viewButtons.forEach(btn => {
        btn.addEventListener('click', function() {
            const card = this.closest('.file-card');
            const fileName = card.querySelector('.file-name').textContent;
            const videoElement = card.querySelector('.file-icon video');
            
            if (videoElement) {
                // Crear un modal para ver el video en grande
                const modal = document.createElement('div');
                modal.className = 'video-modal';
                
                const modalContent = document.createElement('div');
                modalContent.className = 'modal-content';
                
                const closeBtn = document.createElement('span');
                closeBtn.className = 'modal-close';
                closeBtn.innerHTML = '&times;';
                closeBtn.onclick = function() {
                    document.body.removeChild(modal);
                };
                
                // Crear un elemento de video para el modal
                const video = document.createElement('video');
                video.src = videoElement.src;
                video.controls = true;
                video.autoplay = true;
                
                const caption = document.createElement('div');
                caption.className = 'modal-caption';
                caption.textContent = fileName;
                
                modalContent.appendChild(closeBtn);
                modalContent.appendChild(video);
                modalContent.appendChild(caption);
                modal.appendChild(modalContent);
                
                document.body.appendChild(modal);
            } else {
                showNotification(`Visualizando ${fileName}`, 'info');
            }
        });
    });
    
    downloadButtons.forEach(btn => {
        btn.addEventListener('click', function() {
            const card = this.closest('.file-card');
            const fileName = card.querySelector('.file-name').textContent;
            showNotification(`Descargando ${fileName}`, 'success');
            // En una implementación real, aquí iniciaríamos la descarga del video
        });
    });
    
    deleteButtons.forEach(btn => {
        btn.addEventListener('click', function() {
            const card = this.closest('.file-card');
            const fileName = card.querySelector('.file-name').textContent;
            
            if (confirm(`¿Estás seguro de que quieres eliminar ${fileName}?`)) {
                // Simular eliminación con animación
                card.classList.add('deleting');
                
                setTimeout(() => {
                    card.remove();
                    showNotification(`${fileName} eliminado correctamente`, 'success');
                }, 500);
            }
        });
    });
    
    // Funciones auxiliares
    
    /**
     * Muestra información de los videos seleccionados
     * @param {FileList} files - Lista de videos seleccionados
     */
    function showVideoInfo(files) {
        // En una implementación real, aquí mostraríamos vista previa de los videos
        console.log('Videos seleccionados:');
        
        for (let i = 0; i < files.length; i++) {
            const file = files[i];
            console.log(`- ${file.name} (${formatFileSize(file.size)})`);
        }
        
        showNotification(`${files.length} videos seleccionados`, 'info');
    }
    
    /**
     * Simula la carga de videos al servidor
     * @param {FileList} files - Lista de videos a subir
     * @param {string} category - Categoría seleccionada
     * @param {string} description - Descripción de los videos
     */
    function uploadVideos(files, category, description) {
        showNotification('Iniciando subida de videos...', 'info');
        
        // Simular progreso de carga
        let progress = 0;
        const interval = setInterval(() => {
            progress += 5; // Más lento para videos por ser archivos más grandes
            
            if (progress >= 100) {
                clearInterval(interval);
                
                setTimeout(() => {
                    completeUpload(files, category, description);
                }, 500);
            }
        }, 300);
    }
    
    /**
     * Completa el proceso de carga simulado
     * @param {FileList} files - Lista de videos subidos
     * @param {string} category - Categoría seleccionada
     * @param {string} description - Descripción de los videos
     */
    function completeUpload(files, category, description) {
        // Limpiar formulario
        uploadForm.reset();
        
        // Mostrar videos en la biblioteca
        const filesGrid = document.querySelector('.files-grid');
        
        if (filesGrid) {
            for (let i = 0; i < files.length; i++) {
                const file = files[i];
                
                // Crear elemento de tarjeta para el video
                const card = document.createElement('div');
                card.className = 'file-card';
                card.setAttribute('data-category', category);
                
                // Crear contenido HTML para la tarjeta
                card.innerHTML = `
                    <div class="file-icon">
                        <video src="${URL.createObjectURL(file)}" class="video-thumbnail"></video>
                        <div class="video-overlay">
                            <i class="fas fa-play"></i>
                        </div>
                    </div>
                    <div class="file-info">
                        <div class="file-name">${file.name}</div>
                        <div class="file-meta">${getFileExtension(file.name).toUpperCase()} - ${formatFileSize(file.size)}</div>
                        <div class="file-description">${description || 'Sin descripción'}</div>
                    </div>
                    <div class="file-actions">
                        <button class="file-btn view-btn"><i class="fas fa-eye"></i></button>
                        <button class="file-btn download-btn"><i class="fas fa-download"></i></button>
                        <button class="file-btn delete-btn"><i class="fas fa-trash"></i></button>
                    </div>
                `;
                
                // Añadir evento para el botón de ver
                card.querySelector('.view-btn').addEventListener('click', function() {
                    const fileName = card.querySelector('.file-name').textContent;
                    const videoElement = card.querySelector('.file-icon video');
                    
                    if (videoElement) {
                        // Crear un modal para ver el video en grande
                        const modal = document.createElement('div');
                        modal.className = 'video-modal';
                        
                        const modalContent = document.createElement('div');
                        modalContent.className = 'modal-content';
                        
                        const closeBtn = document.createElement('span');
                        closeBtn.className = 'modal-close';
                        closeBtn.innerHTML = '&times;';
                        closeBtn.onclick = function() {
                            document.body.removeChild(modal);
                        };
                        
                        // Crear un elemento de video para el modal
                        const video = document.createElement('video');
                        video.src = videoElement.src;
                        video.controls = true;
                        video.autoplay = true;
                        
                        const caption = document.createElement('div');
                        caption.className = 'modal-caption';
                        caption.textContent = fileName;
                        
                        modalContent.appendChild(closeBtn);
                        modalContent.appendChild(video);
                        modalContent.appendChild(caption);
                        modal.appendChild(modalContent);
                        
                        document.body.appendChild(modal);
                    }
                });
                
                // Añadir evento para el botón de descargar
                card.querySelector('.download-btn').addEventListener('click', function() {
                    const fileName = card.querySelector('.file-name').textContent;
                    showNotification(`Descargando ${fileName}`, 'success');
                });
                
                // Añadir evento para el botón de eliminar
                card.querySelector('.delete-btn').addEventListener('click', function() {
                    const fileName = card.querySelector('.file-name').textContent;
                    
                    if (confirm(`¿Estás seguro de que quieres eliminar ${fileName}?`)) {
                        // Simular eliminación con animación
                        card.classList.add('deleting');
                        
                        setTimeout(() => {
                            card.remove();
                            showNotification(`${fileName} eliminado correctamente`, 'success');
                        }, 500);
                    }
                });
                
                // Animación de entrada
                card.style.opacity = '0';
                filesGrid.appendChild(card);
                
                setTimeout(() => {
                    card.style.opacity = '1';
                }, 100);
            }
        }
        
        showNotification(`${files.length} videos subidos correctamente`, 'success');
    }
    
    /**
     * Formatea el tamaño del archivo a una unidad legible
     * @param {number} bytes - Tamaño en bytes
     * @returns {string} - Tamaño formateado
     */
    function formatFileSize(bytes) {
        if (bytes === 0) return '0 Bytes';
        
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        
        return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i];
    }
    
    /**
     * Obtiene la extensión de un archivo a partir de su nombre
     * @param {string} filename - Nombre del archivo
     * @returns {string} - Extensión del archivo
     */
    function getFileExtension(filename) {
        return filename.slice((filename.lastIndexOf('.') - 1 >>> 0) + 2);
    }
    
    /**
     * Muestra una notificación al usuario
     * @param {string} message - Mensaje a mostrar
     * @param {string} type - Tipo de notificación (success, error, info)
     */
    function showNotification(message, type = 'success') {
        // Verificar si ya existe un contenedor de notificaciones
        let notificationContainer = document.querySelector('.notification-container');
        
        if (!notificationContainer) {
            notificationContainer = document.createElement('div');
            notificationContainer.className = 'notification-container';
            document.body.appendChild(notificationContainer);
        }
        
        // Crear notificación
        const notification = document.createElement('div');
        notification.className = `notification ${type}`;
        
        // Contenido de la notificación
        notification.innerHTML = `
            <div class="notification-icon">
                <i class="${getNotificationIcon(type)}"></i>
            </div>
            <div class="notification-content">
                <p>${message}</p>
            </div>
            <button class="notification-close">&times;</button>
        `;
        
        // Añadir al contenedor
        notificationContainer.appendChild(notification);
        
        // Evento para cerrar notificación
        notification.querySelector('.notification-close').addEventListener('click', function() {
            notification.classList.add('closing');
            setTimeout(() => {
                notificationContainer.removeChild(notification);
            }, 300);
        });
        
        // Cerrar automáticamente después de un tiempo
        setTimeout(() => {
            if (notification.parentNode) {
                notification.classList.add('closing');
                setTimeout(() => {
                    if (notification.parentNode) {
                        notificationContainer.removeChild(notification);
                    }
                }, 300);
            }
        }, 5000);
    }
    
    /**
     * Obtiene el icono correspondiente al tipo de notificación
     * @param {string} type - Tipo de notificación
     * @returns {string} - Clase CSS para el icono
     */
    function getNotificationIcon(type) {
        switch (type) {
            case 'success':
                return 'fas fa-check-circle';
            case 'error':
                return 'fas fa-times-circle';
            case 'info':
                return 'fas fa-info-circle';
            case 'warning':
                return 'fas fa-exclamation-triangle';
            default:
                return 'fas fa-bell';
        }
    }
    
    // Estilos CSS adicionales para la sección de videos
    (function() {
        const style = document.createElement('style');
        style.textContent = `
            .video-thumbnail {
                width: 100%;
                height: 100%;
                object-fit: cover;
                border-radius: 8px;
            }
            
            .video-overlay {
                position: absolute;
                top: 0;
                left: 0;
                width: 100%;
                height: 100%;
                background-color: rgba(0, 0, 0, 0.3);
                border-radius: 8px;
                display: flex;
                justify-content: center;
                align-items: center;
                color: white;
                font-size: 24px;
            }
            
            .file-icon {
                position: relative;
            }
            
            .video-modal {
                display: block;
                position: fixed;
                z-index: 1000;
                padding-top: 50px;
                left: 0;
                top: 0;
                width: 100%;
                height: 100%;
                overflow: auto;
                background-color: rgba(0, 0, 0, 0.9);
            }
            
            .modal-content {
                margin: auto;
                display: block;
                width: 80%;
                max-width: 1000px;
                position: relative;
            }
            
            .modal-content video {
                width: 100%;
                height: auto;
                max-height: 70vh;
            }
            
            .modal-close {
                position: absolute;
                top: 15px;
                right: 35px;
                color: #f1f1f1;
                font-size: 40px;
                font-weight: bold;
                cursor: pointer;
                z-index: 1001;
            }
            
            .modal-caption {
                margin: auto;
                width: 80%;
                max-width: 1000px;
                text-align: center;
                color: #ccc;
                padding: 10px 0;
            }
        `;
        
        document.head.appendChild(style);
    })();
});
