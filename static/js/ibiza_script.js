// IbizaInfoBot - Script simplificado con función global
document.addEventListener('DOMContentLoaded', function() {
    // Inicializar elementos
    const chatMessages = document.getElementById('messages-container');
    const userInput = document.getElementById('user-input');
    const chatContainer = document.getElementById('chat-container');
    const scrollAnchor = document.getElementById('scroll-anchor');
    
    console.log('Elementos inicializados:', chatMessages, userInput, chatContainer, scrollAnchor);
    
    // Respuestas predefinidas
    const predefinedResponses = {
        "hola": "¡Hola! Soy IbizaInfoBot. ¿En qué puedo ayudarte con información sobre Ibiza?",
        "cómo estás": "Estoy bien, gracias por preguntar. ¿En qué puedo ayudarte con información sobre Ibiza?",
        "qué fiestas hay en ibiza": "Ibiza es famosa por sus fiestas y discotecas. Algunos de los clubs más populares son Pacha, Amnesia, Ushuaïa y Hï Ibiza. Cada verano hay eventos especiales con DJs internacionales. ¿Te interesa alguna fecha o lugar en particular?",
        "mejores playas": "Algunas de las mejores playas de Ibiza son Ses Salines, Cala Comte, Cala d'Hort (con vistas a Es Vedrà), Playa d'en Bossa y Cala Bassa. Cada una tiene su encanto particular. ¿Quieres información sobre alguna en específico?",
        "restaurantes recomendados": "Hay excelentes restaurantes en Ibiza, como Sa Capella (en un antiguo convento), Es Torrent (mariscos frescos), Can Carlitos (junto al mar en Formentera), La Paloma (cocina mediterránea ecológica) y Es Xarcu (pescado fresco). ¿Tienes alguna preferencia gastronómica?"
    };
    
    // Método directo para scrollear al final
    function scrollToBottom() {
        if (chatContainer) {
            chatContainer.scrollTop = chatContainer.scrollHeight + 1000;
            
            // Intentar nuevamente en caso de que algún contenido aún se esté cargando
            setTimeout(() => {
                chatContainer.scrollTop = chatContainer.scrollHeight + 1000;
            }, 100);
            
            // Y una vez más para estar seguros
            setTimeout(() => {
                chatContainer.scrollTop = chatContainer.scrollHeight + 1000;
            }, 300);
        }
    }
    
    // Función para añadir mensaje - Simplificada
    function addMessage(text, className) {
        if (!chatMessages) return;
        
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${className}`;
        messageDiv.textContent = text;
        
        // Insertar antes del ancla de scroll si existe
        if (scrollAnchor) {
            chatMessages.insertBefore(messageDiv, scrollAnchor);
        } else {
            chatMessages.appendChild(messageDiv);
        }
        
        // Scroll inmediato
        scrollToBottom();
    }
    
    // FUNCIÓN PRINCIPAL EXPUESTA GLOBALMENTE
    // Esta función es llamada desde el formulario HTML
    window.sendMessageToBot = function(message) {
        // Si no hay mensaje o no está inicializado, salir
        if (!message || message === '') return;
        
        console.log('Enviando mensaje:', message);
        
        // Añadir mensaje del usuario
        addMessage(message, 'user-message');
        
        // Limpiar campo de entrada
        if (userInput) {
            userInput.value = '';
        }
        
        // Scroll para ver el mensaje enviado
        scrollToBottom();
        
        // Comprobar respuestas predefinidas
        const lowerMessage = message.toLowerCase();
        let responded = false;
        
        // Verificar respuestas predefinidas
        for (const [key, response] of Object.entries(predefinedResponses)) {
            if (lowerMessage.includes(key)) {
                // Simular pequeña demora
                setTimeout(() => {
                    addMessage(response, 'bot-message');
                    scrollToBottom();
                }, 500);
                
                responded = true;
                break;
            }
        }
        
        // Si no hay respuesta predefinida, usar el endpoint
        if (!responded) {
            // Mostrar indicador de carga
            const loadingIndicator = document.createElement('div');
            loadingIndicator.className = 'message bot-message loading';
            loadingIndicator.innerHTML = '<div class="loading-dots"><div></div><div></div><div></div></div>';
            chatMessages.appendChild(loadingIndicator);
            
            scrollToBottom();
            
            // Hacer la petición al servidor
            fetch('/api/bot_chat', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ message: message })
            })
            .then(response => response.json())
            .then(data => {
                // Eliminar indicador de carga
                const loadingElement = document.querySelector('.message.bot-message.loading');
                if (loadingElement) {
                    loadingElement.remove();
                }
                
                if (data.success) {
                    addMessage(data.message, 'bot-message');
                } else {
                    addMessage('Lo siento, ha ocurrido un error. Por favor, intenta de nuevo.', 'bot-message error');
                }
                
                scrollToBottom();
            })
            .catch(error => {
                console.error('Error:', error);
                const loadingElement = document.querySelector('.message.bot-message.loading');
                if (loadingElement) {
                    loadingElement.remove();
                }
                addMessage('Error de conexión. Por favor, verifica tu conexión a internet e intenta de nuevo.', 'bot-message error');
                scrollToBottom();
            });
        }
    };
    
    // Mensaje de bienvenida
    if (chatMessages) {
        // Dar un momento para que se cargue todo
        setTimeout(() => {
            scrollToBottom();
        }, 500);
    }
    
    // Detectar cambios en el contenedor de chat para forzar scroll
    if (chatContainer && window.MutationObserver) {
        const observer = new MutationObserver(scrollToBottom);
        observer.observe(chatMessages, { 
            childList: true, 
            subtree: true, 
            attributes: false, 
            characterData: false 
        });
    }
});
