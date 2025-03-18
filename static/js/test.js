document.addEventListener('DOMContentLoaded', function() {
    console.log('JavaScript de prueba cargado correctamente');
    
    // Añadir algo de interactividad para verificar que el JavaScript funciona
    const navbar = document.querySelector('.navbar');
    if (navbar) {
        navbar.addEventListener('click', function() {
            console.log('Navbar clickeada - JavaScript funcionando');
        });
    }
    
    // Crear algunos efectos visuales para mostrar que funciona
    const h1 = document.querySelector('h1');
    if (h1) {
        h1.style.textShadow = '0 0 10px #FFD700';
        h1.style.transition = 'all 0.3s ease';
        
        h1.addEventListener('mouseover', function() {
            this.style.textShadow = '0 0 20px #FFD700';
        });
        
        h1.addEventListener('mouseout', function() {
            this.style.textShadow = '0 0 10px #FFD700';
        });
    }
});
