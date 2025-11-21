"""
ARIA - Scrapers Inmobiliarios
Módulo unificado para scrapers de portales inmobiliarios colombianos.
"""

import logging
from typing import Dict, List, Optional, Type

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

__version__ = "3.0.0"
__author__ = "ARIA Team"
__description__ = "Scrapers para propiedades inmobiliarias en Colombia"

# ============================================================================
# CONFIGURACIÓN GLOBAL
# ============================================================================

CIUDADES_DISPONIBLES = {
    "bucaramanga": {
        "fincaraiz": "bucaramanga-santander",
        "metrocuadrado": "bucaramanga",
        "lahaus": "bucaramanga",
    },
    "bogota": {
        "fincaraiz": "bogota-distrito-capital",
        "metrocuadrado": "bogota",
        "lahaus": "bogota",
    },
    "medellin": {
        "fincaraiz": "medellin-antioquia",
        "metrocuadrado": "medellin",
        "lahaus": "medellin",
    },
    "cali": {
        "fincaraiz": "cali-valle-del-cauca",
        "metrocuadrado": "cali",
        "lahaus": "cali",
    },
}

TIPOS_NEGOCIO = ["venta", "arriendo"]

# ============================================================================
# IMPORTAR SCRAPERS REALES
# ============================================================================

SCRAPERS_DISPONIBLES: Dict[str, Type] = {}
SCRAPER_ERRORS: Dict[str, str] = {}

# En src/scrapers/__init__.py - actualizar importación
try:
    from .fincaraiz_selenium_real import FincaraizScraper
    SCRAPERS_DISPONIBLES['fincaraiz'] = FincaraizScraper
    logger.info("✅ FincaraizScraper REAL con Selenium cargado")
except Exception as e:
    logger.error(f"❌ Error cargando FincaraizScraper Selenium: {e}")
    # Fallback al scraper anterior si es necesario
    from .fincaraiz_scraper import FincaraizScraper
    SCRAPERS_DISPONIBLES['fincaraiz'] = FincaraizScraper

# Fincaraíz
try:
    from .fincaraiz_scraper import FincaraizScraper
    SCRAPERS_DISPONIBLES['fincaraiz'] = FincaraizScraper
    logger.info("✅ FincaraizScraper cargado")
except Exception as e:
    error_msg = f"Error cargando FincaraizScraper: {e}"
    SCRAPER_ERRORS['fincaraiz'] = error_msg
    logger.warning(f"⚠️ {error_msg}")
    FincaraizScraper = None


try:
    from .fincaraiz_api_real import FincaraizScraper
    SCRAPERS_DISPONIBLES['fincaraiz'] = FincaraizScraper
    logger.info("✅ FincaraizScraper REAL con API cargado")
except Exception as e:
    logger.error(f"❌ Error cargando FincaraizScraper API: {e}")

# Metrocuadrado
try:
    from .metrocuadrado_scraper import MetrocuadradoScraper
    SCRAPERS_DISPONIBLES['metrocuadrado'] = MetrocuadradoScraper
    logger.info("✅ MetrocuadradoScraper cargado")
except Exception as e:
    error_msg = f"Error cargando MetrocuadradoScraper: {e}"
    SCRAPER_ERRORS['metrocuadrado'] = error_msg
    logger.warning(f"⚠️ {error_msg}")
    MetrocuadradoScraper = None

# LaHaus
try:
    from .lahaus_scraper import LaHausScraper
    SCRAPERS_DISPONIBLES['lahaus'] = LaHausScraper
    logger.info("✅ LaHausScraper cargado")
except Exception as e:
    error_msg = f"Error cargando LaHausScraper: {e}"
    SCRAPER_ERRORS['lahaus'] = error_msg
    logger.warning(f"⚠️ {error_msg}")
    LaHausScraper = None

# ============================================================================
# FUNCIONES PÚBLICAS PRINCIPALES
# ============================================================================

def get_available_scrapers() -> Dict[str, Dict]:
    """Obtener scrapers activos"""
    scrapers_info = {}
    
    if FincaraizScraper is not None:
        scrapers_info['fincaraiz'] = {
            "name": "Fincaraíz",
            "class": FincaraizScraper,
            "status": "active"
        }
    
    if MetrocuadradoScraper is not None:
        scrapers_info['metrocuadrado'] = {
            "name": "Metrocuadrado", 
            "class": MetrocuadradoScraper,
            "status": "active"
        }
    
    if LaHausScraper is not None:
        scrapers_info['lahaus'] = {
            "name": "La Haus",
            "class": LaHausScraper,
            "status": "active"
        }
    
    return scrapers_info

def get_scraper(scraper_name: str):
    """Obtener un scraper por nombre"""
    available = get_available_scrapers()
    if scraper_name in available:
        scraper_class = available[scraper_name]["class"]
        return scraper_class()
    return None

# ============================================================================
# API PÚBLICA
# ============================================================================

__all__ = [
    # Clases de scrapers
    "FincaraizScraper",
    "MetrocuadradoScraper", 
    "LaHausScraper",
    
    # Funciones principales
    "get_available_scrapers",
    "get_scraper",
    
    # Constantes
    "CIUDADES_DISPONIBLES",
    "TIPOS_NEGOCIO",
    "SCRAPER_ERRORS",
]

# ============================================================================
# INFORMACIÓN AL IMPORTAR
# ============================================================================

if __name__ == "__main__":
    print(f"📦 ARIA Scrapers v{__version__}")
    available = get_available_scrapers()
    print(f"✅ Scrapers disponibles: {list(available.keys())}")
else:
    available_count = len(get_available_scrapers())
    logger.info(f"🎯 Módulo scrapers cargado con {available_count} scrapers disponibles")
