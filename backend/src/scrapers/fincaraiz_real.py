# backend/src/scrapers/fincaraiz_real.py
import aiohttp
import asyncio
from bs4 import BeautifulSoup
import logging
from typing import Dict, List
import random
import time

logger = logging.getLogger(__name__)

class FincaraizRealScraper:
    def __init__(self):
        self.name = "fincaraiz"
        self.base_url = "https://www.fincaraiz.com.co"
        self.session = None
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'es-ES,es;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        }
    
    async def init_session(self):
        """Inicializar sesión aiohttp"""
        if not self.session:
            timeout = aiohttp.ClientTimeout(total=30)
            self.session = aiohttp.ClientSession(timeout=timeout, headers=self.headers)
    
    async def close_session(self):
        """Cerrar sesión"""
        if self.session:
            await self.session.close()
    
    def build_search_url(self, ciudad: str, negocio: str, pagina: int = 1) -> str:
        """Construir URL de búsqueda real para Fincaraíz"""
        ciudad_map = {
            "bogota": "bogota",
            "medellin": "medellin", 
            "cali": "cali",
            "bucaramanga": "bucaramanga"
        }
        
        ciudad_slug = ciudad_map.get(ciudad, ciudad)
        negocio_slug = "venta" if negocio == "venta" else "arriendo"
        
        return f"{self.base_url}/{negocio_slug}/inmuebles/{ciudad_slug}?pagina={pagina}"
    
    async def fetch_page(self, url: str) -> str:
        """Obtener HTML de la página"""
        await self.init_session()
        
        try:
            async with self.session.get(url) as response:
                if response.status == 200:
                    return await response.text()
                else:
                    logger.error(f"Error HTTP {response.status} para {url}")
                    return ""
        except Exception as e:
            logger.error(f"Error fetching {url}: {e}")
            return ""
    
    def parse_property_card(self, card) -> Dict:
        """Parsear una tarjeta de propiedad individual"""
        try:
            # Extraer título
            title_elem = card.find('h2') or card.find('h3') or card.find(['a', 'div'], class_=lambda x: x and 'title' in x.lower())
            title = title_elem.get_text(strip=True) if title_elem else "Sin título"
            
            # Extraer precio
            price_elem = card.find(class_=lambda x: x and 'price' in x.lower())
            price_text = price_elem.get_text(strip=True) if price_elem else ""
            price = self.extract_price(price_text)
            
            # Extraer ubicación
            location_elem = card.find(class_=lambda x: x and ('location' in x.lower() or 'address' in x.lower()))
            location = location_elem.get_text(strip=True) if location_elem else ""
            
            # Extraer imagen
            img_elem = card.find('img')
            image_url = img_elem.get('src') if img_elem else ""
            if image_url and image_url.startswith('//'):
                image_url = 'https:' + image_url
            elif image_url and image_url.startswith('/'):
                image_url = self.base_url + image_url
            
            # Extraer características
            features = self.extract_features(card)
            
            # Extraer link
            link_elem = card.find('a', href=True)
            link = link_elem.get('href') if link_elem else ""
            if link and link.startswith('/'):
                link = self.base_url + link
            
            return {
                "titulo": title,
                "precio": price,
                "precio_texto": price_text,
                "ubicacion": location,
                "imagen_url": image_url,
                "link": link,
                "habitaciones": features.get('habitaciones'),
                "banos": features.get('banos'),
                "area_m2": features.get('area'),
                "es_real": True,  # ← MARCADOR DE DATO REAL
                "portal": "fincaraiz"
            }
            
        except Exception as e:
            logger.error(f"Error parsing property card: {e}")
            return {}
    
    def extract_price(self, price_text: str) -> float:
        """Extraer precio numérico del texto"""
        try:
            # Limpiar texto: quitar símbolos y espacios
            cleaned = price_text.replace('$', '').replace('.', '').replace(' ', '').strip()
            
            # Identificar si está en millones o miles
            if 'millon' in price_text.lower() or 'm' in price_text.lower():
                # Asumir que es en millones
                number = float(cleaned.replace(',', '.').replace('m', '').replace('M', ''))
                return int(number * 1000000)
            else:
                # Intentar convertir directamente
                return int(float(cleaned))
        except:
            return 0
    
    def extract_features(self, card) -> Dict:
        """Extraer características de la propiedad"""
        features = {}
        
        # Buscar elementos de características
        features_elems = card.find_all(class_=lambda x: x and ('habitacion' in x.lower() or 'bano' in x.lower() or 'area' in x.lower() or 'm2' in x.lower()))
        
        for elem in features_elems:
            text = elem.get_text(strip=True).lower()
            if 'habit' in text:
                try:
                    features['habitaciones'] = int(''.join(filter(str.isdigit, text)))
                except:
                    pass
            elif 'baño' in text or 'bano' in text:
                try:
                    features['banos'] = int(''.join(filter(str.isdigit, text)))
                except:
                    pass
            elif 'm²' in text or 'm2' in text or 'area' in text:
                try:
                    features['area'] = float(''.join(filter(str.isdigit, text)))
                except:
                    pass
        
        return features
    
    async def scrape(self, params: Dict) -> Dict:
        """Método principal de scraping REAL"""
        limit = params.get('limit', 10)
        ciudad = params.get('ciudad', 'bogota')
        negocio = params.get('negocio', 'venta')
        
        logger.info(f"🚀 Iniciando scraping REAL de Fincaraíz: {ciudad}, {negocio}")
        
        propiedades = []
        pagina = 1
        
        while len(propiedades) < limit:
            url = self.build_search_url(ciudad, negocio, pagina)
            logger.info(f"📄 Obteniendo página {pagina}: {url}")
            
            html = await self.fetch_page(url)
            if not html:
                logger.warning("No se pudo obtener HTML, terminando scraping")
                break
            
            soup = BeautifulSoup(html, 'html.parser')
            
            # Buscar contenedores de propiedades (esto necesita ajustarse al HTML real de Fincaraíz)
            property_cards = soup.find_all('div', class_=lambda x: x and ('property' in x.lower() or 'card' in x.lower() or 'listing' in x.lower()))
            
            if not property_cards:
                logger.warning("No se encontraron propiedades en la página, terminando")
                break
            
            logger.info(f"🔍 Encontradas {len(property_cards)} tarjetas en página {pagina}")
            
            for card in property_cards:
                if len(propiedades) >= limit:
                    break
                
                propiedad = self.parse_property_card(card)
                if propiedad and propiedad.get('titulo') != "Sin título":
                    propiedades.append(propiedad)
            
            logger.info(f"✅ Página {pagina} procesada. Total: {len(propiedades)} propiedades")
            
            # Esperar antes de la siguiente página
            await asyncio.sleep(random.uniform(1, 3))
            pagina += 1
        
        await self.close_session()
        
        logger.info(f"🎉 Scraping REAL completado: {len(propiedades)} propiedades encontradas")
        
        return {
            "propiedades": propiedades,
            "total": len(propiedades),
            "fuente": "SCRAPING_REAL",
            "parametros": params
        }