/**
 * Files Manager - Controlador para la gestión de archivos
 * Este archivo gestiona la subida, visualización y gestión de archivos en la plataforma
 */

document.addEventListener('DOMContentLoaded', function() {
    console.log('Files Manager cargado correctamente');
    
    // Referencias a elementos del DOM
    const fileInput = document.getElementById('file-input');
    const uploadForm = document.getElementById('upload-file-form');
    const filterOptions = document.querySelectorAll('.filter-option');
    const fileCards = document.querySelectorAll('.file-card');
    
    // Inicializar la carga de archivos
    if (fileInput) {
        // Manejar selección de archivos
        fileInput.addEventListener('change', function() {
            if (this.files.length > 0) {
                console.log(`${this.files.length} archivos seleccionados`);
                showFileInfo(this.files);
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
                fileInput.files = files;
                
                // Disparar evento change manualmente
                const event = new Event('change');
                fileInput.dispatchEvent(event);
            }
        }
    }
    
    // Manejar envío del formulario
    if (uploadForm) {
        uploadForm.addEventListener('submit', function(e) {
            e.preventDefault();
            
            const files = fileInput.files;
            if (!files || files.length === 0) {
                showNotification('Selecciona al menos un archivo para subir', 'error');
                return;
            }
            
            const category = document.getElementById('file-category').value;
            const description = document.getElementById('file-description').value;
            
            // Simular carga de archivos
            uploadFiles(files, category, description);
        });
    }
    
    // Manejar filtrado de archivos
    if (filterOptions.length > 0 && fileCards.length > 0) {
        filterOptions.forEach(option => {
            option.addEventListener('click', function() {
                // Quitar clase active de todas las opciones
                filterOptions.forEach(opt => opt.classList.remove('active'));
                
                // Añadir clase active a la opción seleccionada
                this.classList.add('active');
                
                const filter = this.getAttribute('data-filter');
                
                // Filtrar archivos
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
    
    // Manejar acciones de los archivos
    const viewButtons = document.querySelectorAll('.view-btn');
    const downloadButtons = document.querySelectorAll('.download-btn');
    const deleteButtons = document.querySelectorAll('.delete-btn');
    
    viewButtons.forEach(btn => {
        btn.addEventListener('click', function() {
            const card = this.closest('.file-card');
            const fileName = card.querySelector('.file-name').textContent;
            showNotification(`Visualizando ${fileName}`, 'info');
            // En una implementación real, aquí abriríamos una vista previa del archivo
        });
    });
    
    downloadButtons.forEach(btn => {
        btn.addEventListener('click', function() {
            const card = this.closest('.file-card');
            const fileName = card.querySelector('.file-name').textContent;
            showNotification(`Descargando ${fileName}`, 'success');
            // En una implementación real, aquí iniciaríamos la descarga del archivo
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
     * Muestra información de los archivos seleccionados
     * @param {FileList} files - Lista de archivos seleccionados
     */
    function showFileInfo(files) {
        // En una implementación real, aquí mostraríamos información de los archivos seleccionados
        // como vista previa, tamaño, etc.
        console.log('Archivos seleccionados:');
        
        for (let i = 0; i < files.length; i++) {
            const file = files[i];
            console.log(`- ${file.name} (${formatFileSize(file.size)})`);
        }
        
        showNotification(`${files.length} archivos seleccionados`, 'info');
    }
    
    /**
     * Simula la carga de archivos al servidor
     * @param {FileList} files - Lista de archivos a subir
     * @param {string} category - Categoría seleccionada
     * @param {string} description - Descripción de los archivos
     */
    function uploadFiles(files, category, description) {
        showNotification('Iniciando subida de archivos...', 'info');
        
        // Simular progreso de carga
        let progress = 0;
        const interval = setInterval(() => {
            progress += 10;
            
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
     * @param {FileList} files - Lista de archivos subidos
     * @param {string} category - Categoría seleccionada
     * @param {string} description - Descripción de los archivos
     */
    function completeUpload(files, category, description) {
        // Simular finalización de la carga
        showNotification(`${files.length} archivos subidos correctamente`, 'success');
        
        // En una implementación real, aquí actualizaríamos la biblioteca con los nuevos archivos
        // Para esta demo, simplemente reiniciamos el formulario
        uploadForm.reset();
        
        // Añadir tarjetas de ejemplo para los archivos subidos
        const filesGrid = document.querySelector('.files-grid');
        
        if (filesGrid) {
            for (let i = 0; i < files.length; i++) {
                const file = files[i];
                const fileExt = getFileExtension(file.name);
                const iconClass = getFileIconClass(fileExt);
                
                const fileCard = document.createElement('div');
                fileCard.className = 'file-card new-card';
                fileCard.setAttribute('data-category', category);
                
                fileCard.innerHTML = `
                    <div class="file-icon">
                        <i class="${iconClass}"></i>
                    </div>
                    <div class="file-info">
                        <div class="file-name">${file.name}</div>
                        <div class="file-meta">${fileExt.toUpperCase()} - ${formatFileSize(file.size)}</div>
                        <div class="file-description">${description}</div>
                    </div>
                    <div class="file-actions">
                        <button class="file-btn view-btn"><i class="fas fa-eye"></i></button>
                        <button class="file-btn download-btn"><i class="fas fa-download"></i></button>
                        <button class="file-btn delete-btn"><i class="fas fa-trash"></i></button>
                    </div>
                `;
                
                filesGrid.prepend(fileCard);
                
                // Añadir efecto de entrada
                setTimeout(() => {
                    fileCard.classList.remove('new-card');
                }, 10);
                
                // Configurar nuevos botones
                const newViewBtn = fileCard.querySelector('.view-btn');
                const newDownloadBtn = fileCard.querySelector('.download-btn');
                const newDeleteBtn = fileCard.querySelector('.delete-btn');
                
                newViewBtn.addEventListener('click', function() {
                    showNotification(`Visualizando ${file.name}`, 'info');
                });
                
                newDownloadBtn.addEventListener('click', function() {
                    showNotification(`Descargando ${file.name}`, 'success');
                });
                
                newDeleteBtn.addEventListener('click', function() {
                    if (confirm(`¿Estás seguro de que quieres eliminar ${file.name}?`)) {
                        fileCard.classList.add('deleting');
                        
                        setTimeout(() => {
                            fileCard.remove();
                            showNotification(`${file.name} eliminado correctamente`, 'success');
                        }, 500);
                    }
                });
            }
        }
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
        
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    }
    
    /**
     * Obtiene la extensión de un archivo a partir de su nombre
     * @param {string} filename - Nombre del archivo
     * @returns {string} - Extensión del archivo
     */
    function getFileExtension(filename) {
        return filename.split('.').pop().toLowerCase();
    }
    
    /**
     * Determina el icono a mostrar según la extensión del archivo
     * @param {string} ext - Extensión del archivo
     * @returns {string} - Clase CSS para el icono
     */
    function getFileIconClass(ext) {
        const iconMap = {
            'pdf': 'fas fa-file-pdf',
            'doc': 'fas fa-file-word',
            'docx': 'fas fa-file-word',
            'xls': 'fas fa-file-excel',
            'xlsx': 'fas fa-file-excel',
            'ppt': 'fas fa-file-powerpoint',
            'pptx': 'fas fa-file-powerpoint',
            'jpg': 'fas fa-file-image',
            'jpeg': 'fas fa-file-image',
            'png': 'fas fa-file-image',
            'gif': 'fas fa-file-image',
            'txt': 'fas fa-file-alt',
            'zip': 'fas fa-file-archive',
            'rar': 'fas fa-file-archive',
            'mp3': 'fas fa-file-audio',
            'wav': 'fas fa-file-audio',
            'mp4': 'fas fa-file-video',
            'avi': 'fas fa-file-video',
            'html': 'fas fa-file-code',
            'css': 'fas fa-file-code',
            'js': 'fas fa-file-code'
        };
        
        return iconMap[ext] || 'fas fa-file';
    }
    
    /**
     * Muestra una notificación al usuario
     * @param {string} message - Mensaje a mostrar
     * @param {string} type - Tipo de notificación (success, error, info)
     */
    function showNotification(message, type = 'success') {
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
    
    // Estilos CSS adicionales para la sección de archivos
    (function() {
        const style = document.createElement('style');
        style.textContent = `
            .file-drop-area {
                border: 2px dashed rgba(255, 215, 0, 0.5);
                border-radius: 8px;
                padding: 30px;
                text-align: center;
                transition: all 0.3s;
                margin-bottom: 20px;
                background-color: rgba(0, 0, 0, 0.2);
            }
            
            .file-drop-area.highlight {
                border-color: #FFD700;
                background-color: rgba(255, 215, 0, 0.05);
            }
            
            .file-drop-area i {
                font-size: 48px;
                color: rgba(255, 215, 0, 0.7);
                margin-bottom: 15px;
            }
            
            .file-select-btn {
                display: inline-block;
                padding: 8px 16px;
                background: linear-gradient(45deg, #222, #333);
                border: 1px solid #FFD700;
                color: #FFD700;
                border-radius: 4px;
                cursor: pointer;
                transition: all 0.3s;
                font-weight: 500;
                margin-top: 10px;
            }
            
            .file-select-btn:hover {
                background: linear-gradient(45deg, #333, #444);
                box-shadow: 0 0 8px rgba(255, 215, 0, 0.6);
            }
            
            .files-filter {
                display: flex;
                gap: 10px;
                margin-bottom: 20px;
                flex-wrap: wrap;
            }
            
            .filter-option {
                padding: 5px 12px;
                background-color: #222;
                border: 1px solid #333;
                border-radius: 4px;
                cursor: pointer;
                transition: all 0.3s;
            }
            
            .filter-option:hover {
                background-color: #333;
                border-color: #444;
            }
            
            .filter-option.active {
                background-color: rgba(255, 215, 0, 0.1);
                border-color: rgba(255, 215, 0, 0.4);
                color: #FFD700;
            }
            
            .files-grid {
                display: grid;
                grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
                gap: 20px;
            }
            
            .file-card {
                background-color: #1a1a1a;
                border: 1px solid #333;
                border-radius: 8px;
                padding: 15px;
                display: flex;
                align-items: center;
                transition: all 0.3s;
                transform-origin: center;
                animation: fileCardAppear 0.3s forwards;
            }
            
            .file-card:hover {
                transform: translateY(-3px);
                box-shadow: 0 5px 15px rgba(0, 0, 0, 0.2);
                border-color: rgba(255, 215, 0, 0.3);
            }
            
            .file-card.new-card {
                opacity: 0;
                transform: translateY(20px);
            }
            
            .file-card.deleting {
                transform: scale(0.8);
                opacity: 0;
            }
            
            .file-icon {
                font-size: 28px;
                color: #FFD700;
                margin-right: 15px;
                width: 40px;
                text-align: center;
            }
            
            .file-info {
                flex: 1;
            }
            
            .file-name {
                font-weight: 500;
                margin-bottom: 5px;
                white-space: nowrap;
                overflow: hidden;
                text-overflow: ellipsis;
            }
            
            .file-meta {
                font-size: 0.8em;
                color: #888;
                margin-bottom: 5px;
            }
            
            .file-description {
                font-size: 0.9em;
                color: #aaa;
                overflow: hidden;
                display: -webkit-box;
                -webkit-line-clamp: 2;
                -webkit-box-orient: vertical;
            }
            
            .file-actions {
                display: flex;
                gap: 5px;
            }
            
            .file-btn {
                width: 30px;
                height: 30px;
                border-radius: 50%;
                display: flex;
                align-items: center;
                justify-content: center;
                border: none;
                background-color: #333;
                color: #ccc;
                cursor: pointer;
                transition: all 0.2s;
            }
            
            .file-btn:hover {
                background-color: #444;
                color: #fff;
            }
            
            .view-btn:hover {
                background-color: #2c6aa0;
            }
            
            .download-btn:hover {
                background-color: #2a8747;
            }
            
            .delete-btn:hover {
                background-color: #a93131;
            }
            
            @keyframes fileCardAppear {
                from {
                    opacity: 0;
                    transform: translateY(20px);
                }
                to {
                    opacity: 1;
                    transform: translateY(0);
                }
            }
            
            .notification {
                position: fixed;
                top: 20px;
                right: -300px;
                width: 280px;
                padding: 15px;
                background-color: rgba(25, 25, 25, 0.95);
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
            
            .notification.info {
                border-left: 4px solid #3298dc;
            }
            
            .notification.info i {
                color: #3298dc;
            }
        `;
        
        document.head.appendChild(style);
    })();
});
