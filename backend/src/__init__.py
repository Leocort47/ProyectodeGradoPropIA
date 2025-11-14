"""
ARIA - Asistente Inmobiliario Inteligente
Backend para scraping y análisis de propiedades inmobiliarias en Colombia.
"""

__version__ = "2.0.0"
__author__ = "ARIA Team"
__description__ = "Sistema inteligente de búsqueda y análisis de propiedades"

# Exportar componentes principales
try:
    from .main import app
    from .scrapers import (
        FincaraizScraper,
        MetrocuadradoScraper,
        LaHausScraper,
        ScraperUnificado,
        scrapear_propiedades
    )
    
    __all__ = [
        'app',
        'FincaraizScraper',
        'MetrocuadradoScraper', 
        'LaHausScraper',
        'ScraperUnificado',
        'scrapear_propiedades'
    ]
    
except ImportError as e:
    print(f"⚠️ No se pudieron importar todos los módulos: {e}")
    
    # Placeholders
    class DummyApp:
        pass
    
    app = DummyApp()
    
    __all__ = ['app']

def get_version():
    """Retorna la versión del sistema"""
    return __version__

def get_system_info():
    """Retorna información del sistema"""
    return {
        "name": "ARIA Backend",
        "version": __version__,
        "author": __author__,
        "description": __description__
    }

if __name__ == "__main__":
    print(f"🚀 ARIA Backend v{__version__}")
    print(f"📝 {__description__}")