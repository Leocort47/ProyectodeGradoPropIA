"""
ARIA - Asistente Inmobiliario Inteligente
Backend para scraping y análisis de propiedades inmobiliarias en Colombia.
"""

__version__ = "3.0.0"
__author__ = "ARIA Team"
__description__ = "Sistema inteligente de búsqueda y análisis de propiedades"

# ============================================================================
# EXPORTAR APP Y SCRAPERS
# ============================================================================

__all__ = []

# Exportar aplicación FastAPI
try:
    from .main import app
    __all__.append('app')
except ImportError as e:
    print(f"⚠️ No se pudo importar app: {e}")
    
    # Placeholder si falla
    class DummyApp:
        pass
    app = DummyApp()
    __all__.append('app')

# ============================================================================
# EXPORTAR SCRAPERS (CON NOMBRES CORRECTOS)
# ============================================================================

# Fincaraíz Scraper
try:
    from .scrapers.fincaraiz_scraper import FincaraizScraper
    __all__.append('FincaraizScraper')
except ImportError as e:
    print(f"⚠️ FincaraizScraper no disponible: {e}")

# Metrocuadrado Scraper
try:
    from .scrapers.metrocuadrado_scraper import MetrocuadradoScraper
    __all__.append('MetrocuadradoScraper')
except ImportError as e:
    print(f"⚠️ MetrocuadradoScraper no disponible: {e}")

# LaHaus Scraper
try:
    from .scrapers.lahaus_scraper import LaHausScraper
    __all__.append('LaHausScraper')
except ImportError as e:
    print(f"⚠️ LaHausScraper no disponible: {e}")

# Scraper Unificado (si existe)
try:
    from .scrapers.scraper_unificado import ScraperUnificado
    __all__.append('ScraperUnificado')
except ImportError as e:
    print(f"⚠️ ScraperUnificado no disponible: {e}")

# ============================================================================
# UTILIDADES
# ============================================================================

def get_version() -> str:
    """Retorna la versión del sistema"""
    return __version__

def get_system_info() -> dict:
    """Retorna información del sistema"""
    return {
        "name": "ARIA Backend",
        "version": __version__,
        "author": __author__,
        "description": __description__,
        "scrapers_disponibles": [
            item for item in __all__ 
            if item.endswith('Scraper')
        ]
    }

def get_available_scrapers() -> list:
    """Retorna lista de scrapers disponibles"""
    return [
        item for item in __all__ 
        if item.endswith('Scraper')
    ]

# ============================================================================
# INFORMACIÓN AL IMPORTAR
# ============================================================================

if __name__ == "__main__":
    print(f"🚀 ARIA Backend v{__version__}")
    print(f"📝 {__description__}")
    print(f"📦 Componentes disponibles: {', '.join(__all__)}")
    
    info = get_system_info()
    print(f"\n📊 Scrapers disponibles:")
    for scraper in info['scrapers_disponibles']:
        print(f"   - {scraper}")
else:
    # Solo mostrar al importar por primera vez
    import sys
    if 'src' not in sys.modules or sys.modules['src'] == sys.modules[__name__]:
        print(f"✅ ARIA Backend v{__version__} cargado")
        scrapers = get_available_scrapers()
        if scrapers:
            print(f"   Scrapers: {', '.join(scrapers)}")