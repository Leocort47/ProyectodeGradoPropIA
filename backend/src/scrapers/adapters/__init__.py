"""
ARIA - Scrapers Inmobiliarios
Paquete que contiene los adapters para portales inmobiliarios colombianos.
"""

from __future__ import annotations

import logging
from importlib import import_module
from typing import List, Dict, Optional, Type

# API pública del paquete adapters
__all__ = [
    "FincaraizScraper",
    "MetrocuadradoScraper",
    "LaHausScraper",
    "ScraperUnificado",
    "get_available_scrapers",
    "create_scraper",
    "get_scraper_info",
    "validar_ciudad",
    "validar_tipo_negocio",
    "validar_portales",
    "scrapear_propiedades",
]

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

__version__ = "2.1.0"
__author__ = "ARIA Team"
__description__ = "Scrapers unificados para propiedades inmobiliarias en Colombia"

# Mapa canónico de adapters: módulo → clase
ADAPTERS_INDEX: Dict[str, str] = {
    "fincaraiz_adapter": "FincaraizScraper",
    "metrocuadrado_adapter": "MetrocuadradoScraper",
    "lahaus_adapter": "LaHausScraper",
}

# Carga robusta con rutas absolutas de paquete
def _import_scraper(module_name: str, class_name: str):
    """
    Importa un scraper con ruta absoluta del paquete.
    Espera que este __init__ viva en 'src.scrapers.adapters'.
    """
    package_root = __name__.rsplit(".", 1)[0]  # 'src.scrapers'
    full_module = f"{package_root}.adapters.{module_name}"
    module = import_module(full_module)
    return getattr(module, class_name)

def _crear_dummy(nombre: str):
    class DummyScraper:
        def __init__(self):
            self.nombre = nombre
            logger.warning(f"⚠️ Usando {nombre} dummy - Scraper no disponible")

        async def scrape(self, limit: int = 10, negocio: str = "venta", ciudad: str = "bucaramanga"):
            return [{
                "id": f"{self.nombre.lower()}-dummy-1",
                "titulo": f"Propiedad demo en {ciudad} - {negocio}",
                "precio": 250000000,
                "precio_formateado": "$250,000,000",
                "ubicacion": f"Centro, {ciudad}",
                "area_m2": 85,
                "habitaciones": 3,
                "banos": 2,
                "portal": self.nombre.lower().replace('scraper', ''),
                "tipo": "Apartamento",
                "tipo_negocio": negocio,
                "ciudad": ciudad,
                "fecha_extraccion": "2024-01-01T00:00:00",
                "link": f"https://{self.nombre.lower().replace('scraper', '')}.com.co/demo",
                "imagen": "https://picsum.photos/400/300",
                "estado": "Disponible"
            }]
    return DummyScraper

def importar_scrapers() -> Dict[str, Type]:
    """
    Importa todos los scrapers declarados en ADAPTERS_INDEX.
    No manipula sys.path. Falla de forma visible y deja dummy como fallback.
    """
    scrapers: Dict[str, Type] = {}
    for module_name, class_name in ADAPTERS_INDEX.items():
        try:
            cls = _import_scraper(module_name, class_name)
            scrapers[class_name] = cls
            logger.info(f"✅ {class_name} importado correctamente")
        except Exception as e:
            logger.warning(f"❌ No se pudo importar {class_name} desde {module_name}: {e}")
            scrapers[class_name] = _crear_dummy(class_name)
    return scrapers

SCRAPERS_DISPONIBLES = importar_scrapers()

# Alias exportados
FincaraizScraper = SCRAPERS_DISPONIBLES.get("FincaraizScraper")
MetrocuadradoScraper = SCRAPERS_DISPONIBLES.get("MetrocuadradoScraper")
LaHausScraper = SCRAPERS_DISPONIBLES.get("LaHausScraper")

# Metadata de los scrapers
SCRAPERS_INFO = {
    "fincaraiz": {
        "name": "Fincaraíz",
        "class": FincaraizScraper,
        "description": "Portal inmobiliario líder en Colombia",
        "status": "active" if FincaraizScraper else "inactive",
        "base_url": "https://fincaraiz.com.co",
    },
    "metrocuadrado": {
        "name": "Metrocuadrado",
        "class": MetrocuadradoScraper,
        "description": "Portal especializado en metros cuadrados",
        "status": "active" if MetrocuadradoScraper else "inactive",
        "base_url": "https://www.metrocuadrado.com",
    },
    "lahaus": {
        "name": "La Haus",
        "class": LaHausScraper,
        "description": "Plataforma de propiedades nuevas y usadas",
        "status": "active" if LaHausScraper else "inactive",
        "base_url": "https://www.lahaus.com",
    },
}

# Configuración global
CIUDADES_DISPONIBLES = {
    "bucaramanga": {
        "fincaraiz": "bucaramanga/santander",
        "metrocuadrado": "bucaramanga",
        "lahaus": "bucaramanga",
    },
    "bogota": {
        "fincaraiz": "bogota/bogota-d.c.",
        "metrocuadrado": "bogota",
        "lahaus": "bogota",
    },
    "medellin": {
        "fincaraiz": "medellin/antioquia",
        "metrocuadrado": "medellin",
        "lahaus": "medellin",
    },
    "cali": {
        "fincaraiz": "cali/valle-del-cauca",
        "metrocuadrado": "cali",
        "lahaus": "cali",
    },
    "barranquilla": {
        "fincaraiz": "barranquilla/atlantico",
        "metrocuadrado": "barranquilla",
        "lahaus": "barranquilla",
    },
    "cartagena": {
        "fincaraiz": "cartagena/bolivar",
        "metrocuadrado": "cartagena",
        "lahaus": "cartagena",
    },
}

TIPOS_NEGOCIO = ["venta", "arriendo"]

# Utilidades públicas
def get_available_scrapers():
    return {name: info for name, info in SCRAPERS_INFO.items() if info["status"] == "active"}

def create_scraper(portal_name: str):
    portal = portal_name.lower()
    if portal not in SCRAPERS_INFO:
        available = list(get_available_scrapers().keys())
        raise ValueError(f"Portal '{portal}' no válido. Disponibles: {available}")
    info = SCRAPERS_INFO[portal]
    if info["status"] != "active":
        raise ValueError(f"Portal '{portal}' no está disponible actualmente")
    return info["class"]()

def get_scraper_info(portal_name: str):
    return SCRAPERS_INFO.get(portal_name.lower(), {})

def validar_ciudad(ciudad: str) -> str:
    c = ciudad.lower()
    if c not in CIUDADES_DISPONIBLES:
        disponibles = list(CIUDADES_DISPONIBLES.keys())
        raise ValueError(f"Ciudad '{ciudad}' no disponible. Ciudades: {disponibles}")
    return c

def validar_tipo_negocio(tipo: str) -> str:
    t = tipo.lower()
    if t not in TIPOS_NEGOCIO:
        raise ValueError(f"Tipo de negocio '{tipo}' no válido. Tipos: {TIPOS_NEGOCIO}")
    return t

def validar_portales(portales) -> List[str]:
    if isinstance(portales, str):
        portales = [p.strip() for p in portales.split(",")]
    validos: List[str] = []
    disponibles = get_available_scrapers()
    for p in portales or []:
        key = p.lower()
        if key in disponibles:
            validos.append(key)
        else:
            logger.warning(f"⚠️ Portal ignorado: {p} (no disponible)")
    if not validos:
        raise ValueError(f"No hay portales válidos. Disponibles: {list(disponibles.keys())}")
    return validos

# Orquestador
class ScraperUnificado:
    def __init__(self):
        self.scrapers = []
        if FincaraizScraper:
            self.scrapers.append(FincaraizScraper())
            logger.info("✅ FincaraizScraper instanciado")
        if MetrocuadradoScraper:
            self.scrapers.append(MetrocuadradoScraper())
            logger.info("✅ MetrocuadradoScraper instanciado")
        if LaHausScraper:
            self.scrapers.append(LaHausScraper())
            logger.info("✅ LaHausScraper instanciado")
        logger.info(f"🎯 {len(self.scrapers)} scrapers listos para usar")

    async def scrapear_propiedades(
        self, ciudad: str, tipo_negocio: str, portales: Optional[List[str]] = None, limit: int = 10
    ) -> List[Dict]:
        todas: List[Dict] = []
        for scraper in self.scrapers:
            nombre = scraper.__class__.__name__
            portal_key = nombre.replace("Scraper", "").lower()
            if portales and portal_key not in [p.lower() for p in portales]:
                continue
            try:
                logger.info(f"🔍 Ejecutando {nombre}...")
                props = await scraper.scrape(limit=limit, negocio=tipo_negocio, ciudad=ciudad)
                for prop in props:
                    prop.setdefault("portal", portal_key)
                todas.extend(props)
                logger.info(f"✅ {nombre}: {len(props)} propiedades")
            except Exception as e:
                logger.error(f"❌ Error en {nombre}: {e}")
                continue
        return todas

# Facade de conveniencia
async def scrapear_propiedades(ciudad: str, tipo_negocio: str, portales: Optional[List[str]] = None, limit: int = 10):
    return await ScraperUnificado().scrapear_propiedades(ciudad, tipo_negocio, portales, limit)
