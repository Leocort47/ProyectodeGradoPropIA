"""
ARIA - Scrapers Inmobiliarios
Módulo unificado para scrapers de portales inmobiliarios colombianos.
"""

from __future__ import annotations

import logging
from typing import List, Dict, Optional, Type, Any

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
    "barranquilla": {
        "fincaraiz": "barranquilla-atlantico",
        "metrocuadrado": "barranquilla",
        "lahaus": "barranquilla",
    },
    "cartagena": {
        "fincaraiz": "cartagena-bolivar",
        "metrocuadrado": "cartagena",
        "lahaus": "cartagena",
    },
}

TIPOS_NEGOCIO = ["venta", "arriendo"]

# ============================================================================
# IMPORTAR SCRAPERS REALES
# ============================================================================

SCRAPERS_DISPONIBLES: Dict[str, Type] = {}
SCRAPER_ERRORS: Dict[str, str] = {}

# Fincaraíz
try:
    from .fincaraiz_scraper import FincaraizScraper
    SCRAPERS_DISPONIBLES['fincaraiz'] = FincaraizScraper
    logger.info("✅ FincaraizScraper cargado")
except Exception as e:
    SCRAPER_ERRORS['fincaraiz'] = str(e)
    logger.warning(f"⚠️ FincaraizScraper no disponible: {e}")
    FincaraizScraper = None

# Metrocuadrado
try:
    from .metrocuadrado_scraper import MetrocuadradoScraper
    SCRAPERS_DISPONIBLES['metrocuadrado'] = MetrocuadradoScraper
    logger.info("✅ MetrocuadradoScraper cargado")
except Exception as e:
    SCRAPER_ERRORS['metrocuadrado'] = str(e)
    logger.warning(f"⚠️ MetrocuadradoScraper no disponible: {e}")
    MetrocuadradoScraper = None

# LaHaus
try:
    from .lahaus_scraper import LaHausScraper
    SCRAPERS_DISPONIBLES['lahaus'] = LaHausScraper
    logger.info("✅ LaHausScraper cargado")
except Exception as e:
    SCRAPER_ERRORS['lahaus'] = str(e)
    logger.warning(f"⚠️ LaHausScraper no disponible: {e}")
    LaHausScraper = None

# ============================================================================
# METADATA DE SCRAPERS
# ============================================================================

SCRAPERS_INFO = {
    "fincaraiz": {
        "name": "Fincaraíz",
        "class": FincaraizScraper,
        "description": "Portal inmobiliario líder en Colombia",
        "status": "active" if FincaraizScraper else "inactive",
        "base_url": "https://www.fincaraiz.com.co",
    },
    "metrocuadrado": {
        "name": "Metrocuadrado",
        "class": MetrocuadradoScraper,
        "description": "Portal especializado en propiedades",
        "status": "active" if MetrocuadradoScraper else "inactive",
        "base_url": "https://www.metrocuadrado.com",
    },
    "lahaus": {
        "name": "La Haus",
        "class": LaHausScraper,
        "description": "Plataforma de propiedades nuevas",
        "status": "active" if LaHausScraper else "inactive",
        "base_url": "https://www.lahaus.com",
    },
}

# ============================================================================
# FUNCIONES DE VALIDACIÓN
# ============================================================================

def validar_ciudad(ciudad: str) -> str:
    """Validar que la ciudad esté disponible"""
    c = ciudad.lower()
    if c not in CIUDADES_DISPONIBLES:
        disponibles = list(CIUDADES_DISPONIBLES.keys())
        raise ValueError(f"Ciudad '{ciudad}' no disponible. Ciudades válidas: {disponibles}")
    return c

def validar_tipo_negocio(tipo: str) -> str:
    """Validar tipo de negocio (venta/arriendo)"""
    t = tipo.lower()
    if t not in TIPOS_NEGOCIO:
        raise ValueError(f"Tipo '{tipo}' no válido. Tipos válidos: {TIPOS_NEGOCIO}")
    return t

def validar_portales(portales: Optional[List[str]] = None) -> List[str]:
    """Validar y filtrar portales disponibles"""
    if not portales:
        return list(get_available_scrapers().keys())
    
    if isinstance(portales, str):
        portales = [p.strip() for p in portales.split(",")]
    
    validos: List[str] = []
    disponibles = get_available_scrapers()
    
    for p in portales:
        key = p.lower()
        if key in disponibles:
            validos.append(key)
        else:
            logger.warning(f"⚠️ Portal '{p}' no disponible, ignorando...")
    
    if not validos:
        raise ValueError(f"No hay portales válidos. Disponibles: {list(disponibles.keys())}")
    
    return validos

# ============================================================================
# FUNCIONES PÚBLICAS
# ============================================================================

def get_available_scrapers() -> Dict[str, Dict]:
    """Obtener scrapers activos"""
    return {
        name: info 
        for name, info in SCRAPERS_INFO.items() 
        if info["status"] == "active"
    }

def create_scraper(portal_name: str):
    """Crear instancia de un scraper específico"""
    portal = portal_name.lower()
    
    if portal not in SCRAPERS_INFO:
        available = list(get_available_scrapers().keys())
        raise ValueError(f"Portal '{portal}' no válido. Disponibles: {available}")
    
    info = SCRAPERS_INFO[portal]
    
    if info["status"] != "active":
        raise ValueError(f"Portal '{portal}' no está disponible actualmente")
    
    ScraperClass = info["class"]
    return ScraperClass()

def get_scraper_info(portal_name: str) -> Dict:
    """Obtener información de un scraper"""
    return SCRAPERS_INFO.get(portal_name.lower(), {})

def get_ciudad_config(ciudad: str, portal: str) -> str:
    """Obtener configuración de ciudad para un portal"""
    ciudad_lower = ciudad.lower()
    portal_lower = portal.lower()
    
    if ciudad_lower not in CIUDADES_DISPONIBLES:
        return ciudad_lower
    
    ciudad_config = CIUDADES_DISPONIBLES[ciudad_lower]
    return ciudad_config.get(portal_lower, ciudad_lower)

# ============================================================================
# SCRAPER UNIFICADO
# ============================================================================

class ScraperUnificado:
    """
    Orquestador que ejecuta múltiples scrapers en paralelo.
    """
    
    def __init__(self):
        """Inicializar con todos los scrapers disponibles"""
        self.scrapers = {}
        
        for portal_name, ScraperClass in SCRAPERS_DISPONIBLES.items():
            try:
                self.scrapers[portal_name] = ScraperClass()
                logger.info(f"✅ {portal_name} instanciado")
            except Exception as e:
                logger.error(f"❌ Error instanciando {portal_name}: {e}")
        
        logger.info(f"🎯 ScraperUnificado listo con {len(self.scrapers)} scrapers")
    
    async def scrapear_propiedades(
        self,
        ciudad: str,
        tipo_negocio: str,
        portales: Optional[List[str]] = None,
        limit: int = 10
    ) -> List[Dict]:
        """
        Scrapear propiedades de múltiples portales.
        
        Args:
            ciudad: Ciudad a buscar
            tipo_negocio: "venta" o "arriendo"
            portales: Lista de portales (None = todos)
            limit: Número máximo de propiedades por portal
            
        Returns:
            Lista de propiedades de todos los portales
        """
        # Validar parámetros
        ciudad = validar_ciudad(ciudad)
        tipo_negocio = validar_tipo_negocio(tipo_negocio)
        portales_validos = validar_portales(portales)
        
        todas_propiedades: List[Dict] = []
        
        # Ejecutar cada scraper
        for portal_name in portales_validos:
            if portal_name not in self.scrapers:
                logger.warning(f"⚠️ Scraper {portal_name} no disponible")
                continue
            
            try:
                scraper = self.scrapers[portal_name]
                logger.info(f"🔍 Scrapeando {portal_name}...")
                
                # Ejecutar scraping
                propiedades = await scraper.scrape(
                    limit=limit,
                    negocio=tipo_negocio,
                    ciudad=ciudad
                )
                
                # Agregar metadatos
                for prop in propiedades:
                    prop.setdefault("portal", portal_name)
                    prop.setdefault("ciudad", ciudad)
                    prop.setdefault("tipo_negocio", tipo_negocio)
                
                todas_propiedades.extend(propiedades)
                logger.info(f"✅ {portal_name}: {len(propiedades)} propiedades")
                
            except Exception as e:
                logger.error(f"❌ Error en {portal_name}: {e}", exc_info=True)
                continue
        
        logger.info(f"🎉 Total: {len(todas_propiedades)} propiedades de {len(portales_validos)} portales")
        return todas_propiedades

# ============================================================================
# FUNCIÓN DE CONVENIENCIA
# ============================================================================

async def scrapear_propiedades(
    ciudad: str,
    tipo_negocio: str,
    portales: Optional[List[str]] = None,
    limit: int = 10
) -> List[Dict]:
    """
    Función de conveniencia para scrapear propiedades.
    
    Ejemplo:
        propiedades = await scrapear_propiedades(
            ciudad="bucaramanga",
            tipo_negocio="venta",
            portales=["fincaraiz", "metrocuadrado"],
            limit=20
        )
    """
    scraper_unificado = ScraperUnificado()
    return await scraper_unificado.scrapear_propiedades(
        ciudad=ciudad,
        tipo_negocio=tipo_negocio,
        portales=portales,
        limit=limit
    )

# ============================================================================
# API PÚBLICA
# ============================================================================

__all__ = [
    # Clases de scrapers
    "FincaraizScraper",
    "MetrocuadradoScraper",
    "LaHausScraper",
    "ScraperUnificado",
    
    # Funciones principales
    "scrapear_propiedades",
    "get_available_scrapers",
    "create_scraper",
    "get_scraper_info",
    
    # Validadores
    "validar_ciudad",
    "validar_tipo_negocio",
    "validar_portales",
    
    # Utilidades
    "get_ciudad_config",
    
    # Constantes
    "CIUDADES_DISPONIBLES",
    "TIPOS_NEGOCIO",
    "SCRAPERS_INFO",
]

# ============================================================================
# INFORMACIÓN AL IMPORTAR
# ============================================================================

if __name__ == "__main__":
    print(f"📦 ARIA Scrapers v{__version__}")
    print(f"📝 {__description__}")
    print(f"\n✅ Scrapers disponibles:")
    for name, info in get_available_scrapers().items():
        print(f"   - {name}: {info['name']}")
    
    if SCRAPER_ERRORS:
        print(f"\n⚠️ Scrapers con errores:")
        for name, error in SCRAPER_ERRORS.items():
            print(f"   - {name}: {error}")
else:
    # Log al importar
    scrapers_activos = len(SCRAPERS_DISPONIBLES)
    scrapers_error = len(SCRAPER_ERRORS)
    
    if scrapers_activos > 0:
        logger.info(f"✅ {scrapers_activos} scrapers disponibles: {', '.join(SCRAPERS_DISPONIBLES.keys())}")
    
    if scrapers_error > 0:
        logger.warning(f"⚠️ {scrapers_error} scrapers no disponibles")