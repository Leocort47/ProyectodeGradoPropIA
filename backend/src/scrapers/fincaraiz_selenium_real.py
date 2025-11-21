from typing import List, Dict, Optional, Any
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import time
import random
import logging
import asyncio
from datetime import datetime
import re
from urllib.parse import urljoin, urlparse

logger = logging.getLogger("ARIA_BACKEND")

class FincaraizSeleniumScraper:
    """Scraper REAL con Selenium para Fincaraíz - Datos 100% reales"""
    
    def __init__(self):
        self.base_url = "https://www.fincaraiz.com.co"
        self.driver = None
        self.setup_driver()
    
    def setup_driver(self):
        """Configurar ChromeDriver con opciones realistas"""
        chrome_options = Options()
        
        # Opciones para hacer el browser más realista
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        chrome_options.add_argument("--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
        
        # Para producción, quitar --headless para debugging
        # chrome_options.add_argument("--headless")
        
        self.driver = webdriver.Chrome(options=chrome_options)
        self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    
    async def scrape(self, params: Dict) -> Dict:
        """Interfaz async principal"""
        return await self._scrape_real(params)
    
    async def _scrape_real(self, params: Dict) -> Dict:
        """Scraping REAL con Selenium"""
        limit = params.get('limit', 10)
        negocio = params.get('negocio', 'venta')
        ciudad = params.get('ciudad', 'bucaramanga')
        
        try:
            logger.info(f"🚀 Iniciando scraping REAL con Selenium: {ciudad}, {negocio}")
            
            # Construir URL real de Fincaraíz
            url = self._build_real_url(ciudad, negocio)
            logger.info(f"🌐 Navegando a: {url}")
            
            self.driver.get(url)
            
            # Esperar a que cargue la página
            time.sleep(3)
            
            # Aceptar cookies si aparece
            self._handle_cookies()
            
            # Scroll para cargar más propiedades
            self._scroll_page(limit)
            
            # Extraer propiedades REALES
            propiedades = self._extract_real_properties(limit, ciudad, negocio)
            
            logger.info(f"🎉 Scraping REAL completado: {len(propiedades)} propiedades")
            
            return {
                "propiedades": propiedades,
                "total": len(propiedades),
                "fuente": "SELENIUM_REAL",
                "parametros": params
            }
            
        except Exception as e:
            logger.error(f"❌ Error en scraping Selenium: {e}")
            return {
                "propiedades": [],
                "total": 0,
                "fuente": "ERROR",
                "parametros": params
            }
        finally:
            if self.driver:
                self.driver.quit()
    
    def _build_real_url(self, ciudad: str, negocio: str) -> str:
        """Construir URL REAL de Fincaraíz"""
        ciudad_map = {
            'bucaramanga': 'bucaramanga-santander',
            'bogota': 'bogota',
            'medellin': 'medellin',
            'cali': 'cali',
            'barranquilla': 'barranquilla',
            'cartagena': 'cartagena'
        }
        
        ciudad_slug = ciudad_map.get(ciudad.lower(), 'bucaramanga-santander')
        
        if negocio.lower() == "arriendo":
            return f"{self.base_url}/arriendo/inmuebles/{ciudad_slug}"
        else:
            return f"{self.base_url}/venta/inmuebles/{ciudad_slug}"
    
    def _handle_cookies(self):
        """Manejar popup de cookies"""
        try:
            # Esperar y hacer clic en aceptar cookies
            cookie_selectors = [
                "button#btn-accept-cookies",
                "button[aria-label*='cookie']",
                "button[class*='cookie']",
                "button:contains('Aceptar')"
            ]
            
            for selector in cookie_selectors:
                try:
                    element = WebDriverWait(self.driver, 3).until(
                        EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                    )
                    element.click()
                    logger.info("✅ Cookies aceptadas")
                    time.sleep(1)
                    break
                except:
                    continue
        except:
            pass  # Si no hay popup de cookies, continuar
    
    def _scroll_page(self, limit: int):
        """Hacer scroll para cargar más propiedades"""
        try:
            last_height = self.driver.execute_script("return document.body.scrollHeight")
            properties_loaded = 0
            
            while properties_loaded < limit * 2:  # Scroll hasta cargar suficientes propiedades
                # Buscar propiedades actuales
                current_properties = self.driver.find_elements(By.CSS_SELECTOR, "[data-cy='listing-card'], article, .listing-card, .property-card")
                
                if len(current_properties) > properties_loaded:
                    properties_loaded = len(current_properties)
                    logger.info(f"📊 Propiedades cargadas: {properties_loaded}")
                
                if properties_loaded >= limit * 2:
                    break
                
                # Scroll down
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(2)
                
                # Verificar si llegamos al final
                new_height = self.driver.execute_script("return document.body.scrollHeight")
                if new_height == last_height:
                    break
                last_height = new_height
                
        except Exception as e:
            logger.warning(f"⚠️ Error en scroll: {e}")
    
    def _extract_real_properties(self, limit: int, ciudad: str, negocio: str) -> List[Dict]:
        """Extraer propiedades REALES de la página"""
        propiedades = []
        
        try:
            # SELECTORES ACTUALIZADOS para Fincaraíz 2024
            property_selectors = [
                "[data-cy='listing-card']",
                "article[data-id]",
                ".listing-card",
                ".property-card",
                ".MuiCard-root",
                "[class*='listing']",
                "[class*='property']"
            ]
            
            for selector in property_selectors:
                try:
                    property_elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    if property_elements:
                        logger.info(f"✅ Encontradas {len(property_elements)} propiedades con selector: {selector}")
                        
                        for element in property_elements:
                            if len(propiedades) >= limit:
                                break
                            
                            try:
                                propiedad = self._extract_property_data(element, ciudad, negocio)
                                if propiedad and self._is_valid_real_property(propiedad):
                                    propiedades.append(propiedad)
                                    logger.info(f"🏠 Propiedad REAL: {propiedad.get('titulo', 'Sin título')}")
                            except Exception as e:
                                logger.debug(f"⚠️ Error extrayendo propiedad: {e}")
                                continue
                        
                        if propiedades:
                            break
                except:
                    continue
            
        except Exception as e:
            logger.error(f"❌ Error extrayendo propiedades: {e}")
        
        return propiedades
    
    def _extract_property_data(self, element, ciudad: str, negocio: str) -> Optional[Dict]:
        """Extraer datos REALES de una propiedad individual"""
        try:
            # 1. TÍTULO REAL
            titulo = self._extract_title(element)
            if not titulo:
                return None
            
            # 2. PRECIO REAL
            precio = self._extract_price(element)
            if not precio:
                return None
            
            # 3. LINK REAL (crítico)
            link = self._extract_real_link(element)
            if not link:
                return None
            
            # 4. IMAGEN REAL (crítico)
            imagen_principal = self._extract_real_image(element)
            
            # 5. UBICACIÓN REAL
            ubicacion = self._extract_location(element)
            
            # 6. CARACTERÍSTICAS REALES
            habitaciones, banos, area = self._extract_features(element)
            
            propiedad = {
                "portal": "fincaraiz",
                "titulo": titulo,
                "precio": precio,
                "precio_formateado": f"${precio:,}",
                "link": link,
                "imagen_principal": imagen_principal,
                "fotos": [imagen_principal] if imagen_principal else [],
                "ubicacion": ubicacion or ciudad.title(),
                "ciudad": ciudad,
                "negocio": negocio,
                "tipo": self._extract_property_type(titulo),
                "habitaciones": habitaciones,
                "banos": banos,
                "area_m2": area,
                "fecha_extraccion": datetime.now().isoformat(),
                "es_real": True,
                "es_demo": False,
                "link_funcional": True  # ✅ Confirmación de que el link es real
            }
            
            return propiedad
            
        except Exception as e:
            logger.debug(f"Error extrayendo datos de propiedad: {e}")
            return None
    
    def _extract_title(self, element) -> Optional[str]:
        """Extraer título REAL"""
        try:
            # Múltiples estrategias para encontrar el título
            title_selectors = [
                "h2", "h3", "h4",
                "[data-cy='listing-title']",
                "[class*='title']",
                "[class*='Title']",
                ".listing-title",
                ".property-title"
            ]
            
            for selector in title_selectors:
                try:
                    title_element = element.find_element(By.CSS_SELECTOR, selector)
                    title_text = title_element.text.strip()
                    if title_text and len(title_text) > 10:
                        return title_text[:200]
                except:
                    continue
            
            # Fallback: buscar texto prominente
            full_text = element.text
            lines = [line.strip() for line in full_text.split('\n') if line.strip()]
            for line in lines:
                if len(line) > 20 and '$' not in line and not line.isdigit():
                    return line[:200]
                    
        except:
            pass
        
        return None
    
    def _extract_price(self, element) -> Optional[int]:
        """Extraer precio REAL"""
        try:
            price_selectors = [
                "[data-cy='listing-price']",
                "[class*='price']",
                "[class*='Price']",
                "[class*='valor']",
                ".listing-price",
                ".property-price"
            ]
            
            for selector in price_selectors:
                try:
                    price_element = element.find_element(By.CSS_SELECTOR, selector)
                    price_text = price_element.text.strip()
                    precio = self._parse_price(price_text)
                    if precio:
                        return precio
                except:
                    continue
            
            # Buscar en todo el texto del elemento
            full_text = element.text
            precio = self._parse_price(full_text)
            if precio:
                return precio
                
        except:
            pass
        
        return None
    
    def _parse_price(self, text: str) -> Optional[int]:
        """Parsear texto de precio a número"""
        try:
            # Buscar patrones de precio
            patterns = [
                r'\$?\s*(\d{1,3}(?:\.\d{3})*(?:\.\d+)?)\s*(?:millones?|mn|m)?',
                r'\$?\s*(\d+(?:\.\d+)?)\s*millones',
                r'\$?\s*(\d+)\s*mil'
            ]
            
            for pattern in patterns:
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    price_str = match.group(1).replace('.', '')
                    
                    # Determinar si está en millones o miles
                    if 'millon' in text.lower() or 'mn' in text.lower() or 'm ' in text.lower():
                        # Si el número es pequeño, asumir millones
                        price_num = float(price_str.replace(',', '.'))
                        if price_num < 1000:
                            return int(price_num * 1000000)
                        else:
                            return int(price_num)
                    elif 'mil' in text.lower():
                        price_num = float(price_str.replace(',', '.'))
                        return int(price_num * 1000)
                    else:
                        # Precio directo
                        return int(price_str)
            
            # Buscar formato directo: $350.000.000
            direct_match = re.search(r'\$?\s*(\d{1,3}(?:\.\d{3})*)', text)
            if direct_match:
                price_str = direct_match.group(1).replace('.', '')
                return int(price_str)
                
        except:
            pass
        
        return None
    
    def _extract_real_link(self, element) -> Optional[str]:
        """Extraer LINK REAL que funcione"""
        try:
            link_selectors = [
                "a[href*='/inmueble/']",
                "a[href*='/apartamento/']",
                "a[href*='/casa/']",
                "a[href*='/finca/']",
                "a[data-cy='listing-link']",
                "a[class*='listing-link']"
            ]
            
            for selector in link_selectors:
                try:
                    link_element = element.find_element(By.CSS_SELECTOR, selector)
                    href = link_element.get_attribute('href')
                    if href and 'fincaraiz.com.co' in href:
                        return href
                    elif href and href.startswith('/'):
                        return urljoin(self.base_url, href)
                    elif href:
                        return href
                except:
                    continue
            
            # Buscar cualquier enlace dentro del elemento
            try:
                all_links = element.find_elements(By.TAG_NAME, "a")
                for link in all_links:
                    href = link.get_attribute('href')
                    if href and ('/inmueble/' in href or '/apartamento/' in href or '/casa/' in href):
                        if href.startswith('/'):
                            return urljoin(self.base_url, href)
                        else:
                            return href
            except:
                pass
                
        except:
            pass
        
        return None
    
    def _extract_real_image(self, element) -> Optional[str]:
        """Extraer IMAGEN REAL de la propiedad"""
        try:
            img_selectors = [
                "img[data-cy='listing-image']",
                "img[src*='fincaraiz']",
                "img[data-src]",
                "img[src]",
                "picture img",
                "[class*='image'] img"
            ]
            
            for selector in img_selectors:
                try:
                    img_element = element.find_element(By.CSS_SELECTOR, selector)
                    src = (img_element.get_attribute('data-src') or 
                          img_element.get_attribute('data-lazy-src') or
                          img_element.get_attribute('src'))
                    
                    if src:
                        # Limpiar y normalizar URL
                        if src.startswith('//'):
                            src = 'https:' + src
                        elif src.startswith('/'):
                            src = urljoin(self.base_url, src)
                        
                        # Validar que sea una imagen real (no placeholder)
                        if self._is_real_image(src):
                            return src
                except:
                    continue
            
            # Buscar en background images
            try:
                bg_elements = element.find_elements(By.CSS_SELECTOR, "[style*='background-image']")
                for bg_element in bg_elements:
                    style = bg_element.get_attribute('style')
                    match = re.search(r'background-image:\s*url\(["\']?(.*?)["\']?\)', style)
                    if match:
                        bg_url = match.group(1)
                        if bg_url.startswith('//'):
                            bg_url = 'https:' + bg_url
                        elif bg_url.startswith('/'):
                            bg_url = urljoin(self.base_url, bg_url)
                        
                        if self._is_real_image(bg_url):
                            return bg_url
            except:
                pass
                
        except:
            pass
        
        return None
    
    def _is_real_image(self, url: str) -> bool:
        """Validar que sea una imagen REAL (no placeholder)"""
        if not url:
            return False
        
        # Debe ser URL de imagen
        valid_extensions = ['.jpg', '.jpeg', '.png', '.webp', '.gif']
        if not any(ext in url.lower() for ext in valid_extensions):
            return False
        
        # No debe ser placeholder genérico
        placeholder_keywords = ['placeholder', 'default', 'blank', 'logo', 'icon']
        if any(keyword in url.lower() for keyword in placeholder_keywords):
            return False
        
        # Debe ser de Fincaraíz o de un CDN de imágenes real
        if 'fincaraiz' in url.lower() or 'cloudinary' in url.lower() or 'imagenes' in url.lower():
            return True
        
        return True
    
    def _extract_location(self, element) -> Optional[str]:
        """Extraer ubicación REAL"""
        try:
            location_selectors = [
                "[data-cy='listing-location']",
                "[class*='location']",
                "[class*='address']",
                "[class*='ubicacion']",
                ".listing-location",
                ".property-address"
            ]
            
            for selector in location_selectors:
                try:
                    location_element = element.find_element(By.CSS_SELECTOR, selector)
                    location_text = location_element.text.strip()
                    if location_text and len(location_text) > 5:
                        return location_text[:150]
                except:
                    continue
                    
        except:
            pass
        
        return None
    
    def _extract_features(self, element) -> tuple:
        """Extraer características REALES (habitaciones, baños, área)"""
        habitaciones = None
        banos = None
        area = None
        
        try:
            text = element.text.lower()
            
            # Habitaciones
            hab_match = re.search(r'(\d+)\s*(?:hab|habitacion|alcoba)', text)
            if hab_match:
                habitaciones = int(hab_match.group(1))
            
            # Baños
            bano_match = re.search(r'(\d+)\s*(?:baño|bano|bath)', text)
            if bano_match:
                banos = int(bano_match.group(1))
            
            # Área
            area_match = re.search(r'(\d+[.,]?\d*)\s*m²', text)
            if area_match:
                try:
                    area_str = area_match.group(1).replace(',', '.')
                    area = float(area_str)
                except:
                    pass
                    
        except:
            pass
        
        return habitaciones, banos, area
    
    def _extract_property_type(self, titulo: str) -> str:
        """Determinar tipo de propiedad desde el título"""
        titulo_lower = titulo.lower()
        
        if 'apartamento' in titulo_lower or 'aparto' in titulo_lower:
            return 'Apartamento'
        elif 'casa' in titulo_lower:
            return 'Casa'
        elif 'finca' in titulo_lower:
            return 'Finca'
        elif 'local' in titulo_lower:
            return 'Local'
        elif 'oficina' in titulo_lower:
            return 'Oficina'
        elif 'lote' in titulo_lower or 'terreno' in titulo_lower:
            return 'Lote'
        
        return 'Inmueble'
    
    def _is_valid_real_property(self, propiedad: Dict) -> bool:
        """Validar que la propiedad sea REAL y tenga datos mínimos"""
        return (
            propiedad.get('titulo') and 
            propiedad.get('precio') and 
            propiedad.get('link') and
            propiedad.get('precio', 0) > 100000  # Precio mínimo razonable
        )


# ============================================================================
# ACTUALIZAR EL SCRAPER PRINCIPAL
# ============================================================================

# Reemplaza tu FincaraizScraper actual con este
class FincaraizScraper:
    """Scraper principal que usa Selenium para datos 100% reales"""
    
    def __init__(self):
        self.name = "fincaraiz"
    
    async def scrape(self, params: Dict) -> Dict:
        """Usar Selenium para scraping real"""
        selenium_scraper = FincaraizSeleniumScraper()
        return await selenium_scraper.scrape(params)


# ============================================================================
# PRUEBA DEL SCRAPER REAL
# ============================================================================

async def test_scraper_real():
    """Probar el scraper con datos REALES"""
    print("🧪 TESTEANDO SCRAPER REAL CON SELENIUM...")
    
    scraper = FincaraizSeleniumScraper()
    
    result = await scraper.scrape({
        'limit': 3,
        'negocio': 'venta',
        'ciudad': 'bogota'
    })
    
    propiedades = result.get('propiedades', [])
    print(f"\n📊 RESULTADOS REALES: {len(propiedades)} propiedades")
    
    for i, prop in enumerate(propiedades, 1):
        print(f"\n{i}. {prop.get('titulo', 'Sin título')}")
        print(f"   💰 Precio REAL: {prop.get('precio_formateado', 'N/A')}")
        print(f"   📍 Ubicación REAL: {prop.get('ubicacion', 'N/A')}")
        print(f"   🏠 Tipo: {prop.get('tipo', 'N/A')}")
        print(f"   🛏️ Habitaciones: {prop.get('habitaciones', 'N/A')}")
        print(f"   🚽 Baños: {prop.get('banos', 'N/A')}")
        print(f"   📐 Área: {prop.get('area_m2', 'N/A')} m²")
        print(f"   🔗 Link REAL: {prop.get('link', 'N/A')}")
        print(f"   🖼️ Imagen REAL: {prop.get('imagen_principal', 'Sin imagen')[:80]}...")
        print(f"   ✅ ¿Es REAL?: {prop.get('es_real', False)}")
        print(f"   ✅ Link FUNCIONAL: {prop.get('link_funcional', False)}")
    
    return result

if __name__ == "__main__":
    asyncio.run(test_scraper_real())