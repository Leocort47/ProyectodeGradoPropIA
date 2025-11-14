# backend/src/scrapers/scraper_unificado.py
"""
Scraper unificado que coordina todos los scrapers individuales
"""

import asyncio
import concurrent.futures
from .fincaraiz_scraper import FincaraizScraper
from .metrocuadrado_scraper import MetrocuadradoScraper
from .lahaus_scraper import LaHausScraper

class ScraperUnificado:
    def __init__(self):
        self.scrapers = {
            'fincaraiz': FincaraizScraper(),
            'metrocuadrado': MetrocuadradoScraper(),
            'lahaus': LaHausScraper()
        }
    
    async def scrapear_propiedades(self, ciudad, tipo_negocio, portales=None, max_paginas=2):
        """Scrapea propiedades de múltiples portales en paralelo"""
        
        if portales is None:
            portales = ['fincaraiz', 'metrocuadrado', 'lahaus']
        
        print(f"🚀 Iniciando scraping en {ciudad}...")
        print(f"📊 Portales: {', '.join(portales)}")
        print(f"📄 Páginas: {max_paginas}")
        
        async def scrape_portal(portal):
            if portal in self.scrapers:
                scraper = self.scrapers[portal]
                try:
                    print(f"🎯 Ejecutando {portal}...")
                    # Ejecutar en thread separado para no bloquear
                    propiedades = await asyncio.get_event_loop().run_in_executor(
                        None,  # Usar el executor por defecto
                        scraper.scrape_propiedades, 
                        ciudad, tipo_negocio, max_paginas
                    )
                    print(f"✅ {portal.upper()}: {len(propiedades)} propiedades")
                    return propiedades
                except Exception as e:
                    print(f"❌ Error en {portal}: {e}")
                    return []
            return []
        
        # Ejecutar todos los scrapers en paralelo
        tareas = [scrape_portal(portal) for portal in portales]
        resultados = await asyncio.gather(*tareas, return_exceptions=True)
        
        # Combinar todos los resultados
        todas_propiedades = []
        for props in resultados:
            if isinstance(props, list):
                todas_propiedades.extend(props)
            elif isinstance(props, Exception):
                print(f"💥 Excepción en scraper: {props}")
        
        print(f"📊 TOTAL: {len(todas_propiedades)} propiedades encontradas")
        return todas_propiedades

# Función de conveniencia para uso directo
def scrapear_propiedades(ciudad="bucaramanga", tipo_negocio="venta", portales=None, max_paginas=2):
    """Función simple para scraping directo"""
    scraper = ScraperUnificado()
    return asyncio.run(scraper.scrapear_propiedades(ciudad, tipo_negocio, portales, max_paginas))