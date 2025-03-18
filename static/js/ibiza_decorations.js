// IbizaInfoBot - Decoraciones y efectos visuales
document.addEventListener('DOMContentLoaded', function() {
    // Crear elementos decorativos
    createDecorativeElements();
    
    // Añadir efectos a elementos existentes
    enhanceExistingElements();
    
    // Añadir animaciones a elementos importantes
    addAnimationsToElements();
});

// Función para crear elementos decorativos en el fondo
function createDecorativeElements() {
    const body = document.body;
    
    // Crear líneas decorativas
    const decorativeLine1 = document.createElement('div');
    decorativeLine1.className = 'decorative-line line-1';
    body.appendChild(decorativeLine1);
    
    const decorativeLine2 = document.createElement('div');
    decorativeLine2.className = 'decorative-line line-2';
    body.appendChild(decorativeLine2);
    
    // Crear burbujas/círculos decorativos flotantes
    for (let i = 0; i < 5; i++) {
        const bubble = document.createElement('div');
        bubble.className = 'decorative-bubble';
        bubble.style.left = `${Math.random() * 100}%`;
        bubble.style.top = `${Math.random() * 100}%`;
        bubble.style.width = `${50 + Math.random() * 100}px`;
        bubble.style.height = bubble.style.width;
        bubble.style.animationDelay = `${Math.random() * 5}s`;
        bubble.style.animationDuration = `${15 + Math.random() * 15}s`;
        body.appendChild(bubble);
    }
}

// Función para mejorar elementos existentes
function enhanceExistingElements() {
    // Añadir efectos a logos y títulos
    const logoText = document.querySelector('.logo-text');
    if (logoText) {
        logoText.innerHTML = `<span class="gradient-text">${logoText.textContent}</span>`;
    }
    
    // Añadir efectos a los títulos de sección
    const sectionTitles = document.querySelectorAll('.section-title');
    sectionTitles.forEach(title => {
        // Añadir línea decorativa debajo de los títulos
        const underline = document.createElement('div');
        underline.className = 'title-underline';
        title.appendChild(underline);
    });
    
    // Mejorar tarjetas
    const cards = document.querySelectorAll('.featured-card, .category');
    cards.forEach(card => {
        // Añadir brillo al hover
        card.addEventListener('mouseenter', function() {
            const shine = document.createElement('div');
            shine.className = 'card-shine';
            this.appendChild(shine);
            
            setTimeout(() => {
                shine.classList.add('animate');
            }, 10);
            
            this.addEventListener('mouseleave', function() {
                const shines = this.querySelectorAll('.card-shine');
                shines.forEach(el => el.remove());
            }, { once: true });
        });
    });
}

// Función para añadir animaciones a elementos importantes
function addAnimationsToElements() {
    // Añadir animación de entrada a los mensajes del chat
    const chatContainer = document.querySelector('.chat-messages');
    if (chatContainer) {
        // Observar nuevos mensajes añadidos
        const observer = new MutationObserver(mutations => {
            mutations.forEach(mutation => {
                if (mutation.type === 'childList' && mutation.addedNodes.length) {
                    mutation.addedNodes.forEach(node => {
                        if (node.nodeType === 1 && node.classList.contains('message')) {
                            // Aplicar animación de entrada
                            node.style.opacity = '0';
                            node.style.transform = 'translateY(10px)';
                            
                            setTimeout(() => {
                                node.style.transition = 'opacity 0.3s ease, transform 0.3s ease';
                                node.style.opacity = '1';
                                node.style.transform = 'translateY(0)';
                            }, 10);
                        }
                    });
                }
            });
        });
        
        observer.observe(chatContainer, { childList: true });
    }
    
    // Añadir efecto de pulsación a los botones
    const buttons = document.querySelectorAll('.btn, .chat-submit-button, .scraping-btn');
    buttons.forEach(button => {
        button.addEventListener('click', function() {
            this.classList.add('pulse-effect');
            setTimeout(() => {
                this.classList.remove('pulse-effect');
            }, 500);
        });
    });
}
