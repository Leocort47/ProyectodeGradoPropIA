# src/scrapers/adapters.py - VERSIÓN ACTUALIZADA
"""
Adaptadores actualizados con datos realistas
"""

import asyncio
from datetime import datetime
import logging
import random

logger = logging.getLogger(__name__)

# Datos realistas de propiedades en Bucaramanga
BUCARAMANGA_PROPERTIES = [
    {
        'titulo': 'Apartamento en Cabecera - Bucaramanga',
        'precio': 380000000,
        'ubicacion': 'Cabecera del Llano, Bucaramanga',
        'area_m2': 85,
        'habitaciones': 3,
        'banos': 2,
        'portal': 'fincaraiz',
        'tipo': 'Apartamento',
        'proyecto': 'Edificio Altos de Cabecera',
        'descripcion': 'Hermoso apartamento en zona residencial exclusiva de Bucaramanga, cerca de centros comerciales y colegios.',
        'fotos': ['https://example.com/foto1.jpg', 'https://example.com/foto2.jpg'],
        'telefonos': '3157894562, 3174561238',
        'contacto': 'Inmobiliaria Santos'
    },
    {
        'titulo': 'Casa en Lagos del Cacique - Bucaramanga', 
        'precio': 550000000,
        'ubicacion': 'Lagos del Cacique, Bucaramanga',
        'area_m2': 120,
        'habitaciones': 4,
        'banos': 3,
        'portal': 'fincaraiz',
        'tipo': 'Casa',
        'descripcion': 'Amplia casa familiar con jardín, zona de parqueadero para 2 vehículos y acabados de lujo.',
        'parqueaderos': 2,
        'fotos': ['https://example.com/foto3.jpg', 'https://example.com/foto4.jpg'],
        'telefonos': '3189632587',
        'contacto': 'Constructora Norte'
    },
    {
        'titulo': 'Apartamento en Provenza - Bucaramanga',
        'precio': 280000000,
        'ubicacion': 'Provenza, Bucaramanga', 
        'area_m2': 65,
        'habitaciones': 2,
        'banos': 2,
        'portal': 'fincaraiz',
        'tipo': 'Apartamento',
        'descripcion': 'Acogedor apartamento en zona comercial y de entretenimiento, ideal para profesionales.',
        'fotos': ['https://example.com/foto5.jpg'],
        'telefonos': '3207418529, 3178529634',
        'contacto': 'Inmobiliaria Centro'
    },
    {
        'titulo': 'Casa en Floridablanca - Área Metropolitana',
        'precio': 420000000,
        'ubicacion': 'Floridablanca, Santander',
        'area_m2': 150, 
        'habitaciones': 3,
        'banos': 2,
        'portal': 'fincaraiz',
        'tipo': 'Casa',
        'descripcion': 'Casa campestre en Floridablanca con amplios espacios verdes y zona de recreación.',
        'parqueaderos': 3,
        'fotos': ['https://example.com/foto6.jpg', 'https://example.com/foto7.jpg'],
        'telefonos': '3196541237',
        'contacto': 'Inmobiliaria Campo Verde'
    },
    {
        'titulo': 'Apartamento Nuevo en Ciudadela Real de Minas',
        'precio': 320000000,
        'ubicacion': 'Real de Minas, Bucaramanga',
        'area_m2': 72,
        'habitaciones': 2,
        'banos': 2,
        'portal': 'fincaraiz',
        'tipo': 'Apartamento',
        'proyecto': 'Residencial Moderno',
        'descripcion': 'Apartamento de estreno en conjunto residencial con piscina, gimnasio y zonas comunes.',
        'fotos': ['https://example.com/foto8.jpg', 'https://example.com/foto9.jpg'],
        'telefonos': '3147852963',
        'contacto': 'Constructora Moderna'
    }
]

# Adapter actualizado para Fincaraíz
class FincaraizScraper:
    def __init__(self):
        logger.info("✅ FincaraizScraper con datos realistas inicializado")
    
    async def scrape(self, limit=10, negocio="venta", ciudad="bucaramanga"):
        """Devuelve datos realistas de propiedades"""
        logger.info(f"🔍 Simulando scraping Fincaraíz: {ciudad}, {negocio}")
        
        try:
            # Filtrar propiedades por ciudad
            filtered_props = []
            for prop in BUCARAMANGA_PROPERTIES:
                if ciudad.lower() in prop['ubicacion'].lower():
                    # Añadir campos adicionales
                    prop_copy = prop.copy()
                    prop_copy['precio_formateado'] = f"${prop['precio']:,.0f}"
                    prop_copy['tipo_negocio'] = negocio
                    prop_copy['fecha_extraccion'] = datetime.now().isoformat()
                    prop_copy['link'] = f"https://fincaraiz.com.co/inmueble/{prop['titulo'].lower().replace(' ', '-')}"
                    
                    filtered_props.append(prop_copy)
            
            # Limitar resultados
            if len(filtered_props) > limit:
                filtered_props = filtered_props[:limit]
            
            # Simular delay de scraping real
            await asyncio.sleep(random.uniform(1, 3))
            
            logger.info(f"✅ Fincaraíz: {len(filtered_props)} propiedades realistas")
            return filtered_props
            
        except Exception as e:
            logger.error(f"❌ Error en scraper simulado: {e}")
            return []
    
    async def scrape_table(self, pages=2, negocio="venta"):
        return [{"data": "Tabla Fincaraíz", "pages": pages, "negocio": negocio}]

# Los otros adapters pueden seguir igual...
class MetrocuadradoScraper:
    def __init__(self):
        logger.info("✅ MetrocuadradoScraper con datos realistas")
    
    async def scrape(self, limit=10, negocio="venta", ciudad="bucaramanga"):
        """Datos realistas para Metrocuadrado"""
        logger.info(f"🔍 Simulando scraping Metrocuadrado: {ciudad}")
        
        # Datos específicos de Metrocuadrado
        props = [
            {
                'titulo': 'Oficina en Centro - Bucaramanga',
                'precio': 180000000,
                'precio_formateado': '$180.000.000',
                'ubicacion': 'Centro, Bucaramanga',
                'area_m2': 45,
                'portal': 'metrocuadrado',
                'tipo': 'Oficina',
                'tipo_negocio': negocio,
                'fecha_extraccion': datetime.now().isoformat(),
                'link': 'https://metrocuadrado.com/oficina-centro-bucaramanga'
            },
            {
                'titulo': 'Local Comercial en Cañaveral',
                'precio': 650000000,
                'precio_formateado': '$650.000.000', 
                'ubicacion': 'Cañaveral, Bucaramanga',
                'area_m2': 80,
                'portal': 'metrocuadrado',
                'tipo': 'Local Comercial',
                'tipo_negocio': negocio,
                'fecha_extraccion': datetime.now().isoformat(),
                'link': 'https://metrocuadrado.com/local-cañaveral-bucaramanga'
            }
        ]
        
        await asyncio.sleep(random.uniform(1, 2))
        return props[:limit]
    
    async def scrape_table(self, pages=2, negocio="venta"):
        return [{"data": "Tabla Metrocuadrado", "pages": pages}]

class LaHausScraper:
    def __init__(self):
        logger.info("✅ LaHausScraper con datos realistas")
    
    async def scrape(self, limit=10, negocio="venta", ciudad="bucaramanga"):
        """Datos realistas para La Haus"""
        logger.info(f"🔍 Simulando scraping La Haus: {ciudad}")
        
        props = [
            {
                'titulo': 'Proyecto Nuevo - Residencial Altos de Provenza',
                'precio': 350000000,
                'precio_formateado': '$350.000.000',
                'ubicacion': 'Provenza, Bucaramanga',
                'area_m2': 78,
                'habitaciones': 3,
                'banos': 2,
                'portal': 'lahaus',
                'tipo': 'Apartamento',
                'proyecto': 'Altos de Provenza',
                'tipo_negocio': negocio,
                'fecha_extraccion': datetime.now().isoformat(),
                'link': 'https://lahaus.com/proyecto-altos-provenza'
            }
        ]
        
        await asyncio.sleep(random.uniform(1, 2))
        return props[:limit]
    
    async def scrape_table(self, pages=2, negocio="venta"):
        return [{"data": "Tabla La Haus", "pages": pages}]