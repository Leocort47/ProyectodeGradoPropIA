# src/scrapers/fincaraiz_selenium.py
"""
Scraper para Fincaraíz usando Selenium (navegador real)
Para evitar protección anti-bot y contenido cifrado
"""

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service
import time
import re
import json
from datetime import datetime
import os

class FincaraizSeleniumScraper:
    def __init__(self):
        self.base_url = "https://fincaraiz.com.co"
        self.driver = self._setup_driver()
    
    def _setup_driver(self):
        """Configurar ChromeDriver para evitar detección"""
        print("🚀 Inicializando ChromeDriver...")
        
        chrome_options = Options()
        
        # Opciones para evitar detección
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        
        # User-Agent real
        chrome_options.add_argument("--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
        
        # Para desarrollo: quitar --headless para ver qué pasa
        # chrome_options.add_argument("--headless")
        
        try:
            service = Service(ChromeDriverManager().install())
            driver = webdriver.Chrome(service=service, options=chrome_options)
            
            # Ocultar webdriver
            driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            
            print("✅ ChromeDriver inicializado correctamente")
            return driver
            
        except Exception as e:
            print(f"❌ Error inicializando ChromeDriver: {e}")
            raise
    
    def scrape_propiedades(self, ciudad="bucaramanga/santander", tipo_negocio="venta", max_paginas=1):
        """Scraping principal usando Selenium"""
        print(f"🔍 Iniciando scraping Fincaraíz con Selenium: {ciudad}")
        
        propiedades = []
        
        try:
            # Construir URL
            if tipo_negocio == "arriendo":
                url = f"{self.base_url}/arrendamiento/inmuebles/{ciudad}?pagina=1"
            else:
                url = f"{self.base_url}/venta/inmuebles/{ciudad}?pagina=1"
            
            print(f"🌐 Navegando a: {url}")
            self.driver.get(url)
            
            # Esperar a que cargue
            time.sleep(5)
            
            # Tomar screenshot para debugging
            self.driver.save_screenshot("fincaraiz_selenium.png")
            print("📸 Screenshot guardado: fincaraiz_selenium.png")
            
            # Obtener HTML después de que JavaScript cargue
            html = self.driver.page_source
            
            # Guardar HTML para análisis
            with open("fincaraiz_selenium.html", "w", encoding="utf-8") as f:
                f.write(html)
            print("💾 HTML con Selenium guardado")
            
            # Verificar si el contenido es legible
            if "acceso denegado" in html.lower() or "cloudflare" in html.lower():
                print("❌ Cloudflare está bloqueando el acceso")
                return []
            
            # Buscar propiedades en el HTML renderizado
            propiedades = self._extract_properties_from_html(html)
            
            print(f"✅ Encontradas {len(propiedades)} propiedades")
            
            return propiedades
            
        except Exception as e:
            print(f"❌ Error durante scraping: {e}")
            return []
        finally:
            self.driver.quit()
    
    def _extract_properties_from_html(self, html):
        """Extraer propiedades del HTML renderizado"""
        propiedades = []
        
        # Buscar enlaces a propiedades
        property_links = re.findall(r'href=\"(/inmueble/[^\"]+)\"', html)
        unique_links = list(set(property_links))
        
        print(f"🔗 Encontrados {len(unique_links)} enlaces a propiedades")
        
        # Buscar datos estructurados
        script_data = self._extract_script_data(html)
        
        # Buscar elementos visibles en la página
        visible_props = self._extract_visible_properties()
        
        # Combinar resultados
        for i, link in enumerate(unique_links[:10]):  # Limitar para prueba
            prop = {
                'link': self.base_url + link,
                'titulo': f'Propiedad Fincaraíz {i+1}',
                'portal': 'fincaraiz',
                'fecha_extraccion': datetime.now().isoformat()
            }
            
            # Añadir datos de scripts si están disponibles
            if i < len(script_data):
                prop.update(script_data[i])
            
            propiedades.append(prop)
        
        # Añadir propiedades visibles
        for visible_prop in visible_props:
            if visible_prop not in propiedades:
                propiedades.append(visible_prop)
        
        return propiedades
    
    def _extract_script_data(self, html):
        """Extraer datos de scripts JSON-LD"""
        propiedades = []
        
        try:
            # Buscar JSON-LD
            script_pattern = r'<script type=\"application/ld\+json\">(.*?)</script>'
            matches = re.findall(script_pattern, html, re.DOTALL)
            
            for match in matches:
                try:
                    data = json.loads(match)
                    prop = self._parse_ld_json(data)
                    if prop:
                        propiedades.append(prop)
                except:
                    continue
                    
        except Exception as e:
            print(f"⚠️ Error extrayendo datos de scripts: {e}")
        
        return propiedades
    
    def _parse_ld_json(self, data):
        """Parsear JSON-LD"""
        prop = {}
        
        try:
            if isinstance(data, dict):
                # Producto individual
                if data.get('@type') == 'Product':
                    prop['titulo'] = data.get('name', '')
                    prop['descripcion'] = data.get('description', '')
                    
                    # Precio
                    offers = data.get('offers', {})
                    if isinstance(offers, dict):
                        price = offers.get('price')
                        if price:
                            prop['precio'] = float(price)
                            prop['precio_formateado'] = f"${prop['precio']:,.0f}"
                
                # Lista de productos
                elif data.get('@type') == 'ItemList':
                    items = data.get('itemListElement', [])
                    for item in items:
                        if isinstance(item, dict):
                            item_data = item.get('item', {})
                            if item_data.get('@type') == 'Product':
                                prop = self._parse_ld_json(item_data)
                                if prop:
                                    break
        
        except Exception as e:
            print(f"⚠️ Error parseando JSON-LD: {e}")
        
        return prop if prop else None
    
    def _extract_visible_properties(self):
        """Extraer propiedades de elementos visibles en la página"""
        propiedades = []
        
        try:
            # Buscar elementos que parecen propiedades
            property_selectors = [
                "[class*='property']",
                "[class*='card']", 
                "[class*='listing']",
                "article",
                ".MuiCard-root"
            ]
            
            for selector in property_selectors:
                try:
                    elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    for element in elements[:5]:  # Limitar para prueba
                        try:
                            text = element.text
                            if text and len(text) > 50:  # Texto significativo
                                prop = self._parse_visible_element(element, text)
                                if prop:
                                    propiedades.append(prop)
                        except:
                            continue
                except:
                    continue
                    
        except Exception as e:
            print(f"⚠️ Error extrayendo elementos visibles: {e}")
        
        return propiedades
    
    def _parse_visible_element(self, element, text):
        """Parsear elemento visible"""
        prop = {
            'titulo': 'Propiedad Fincaraíz',
            'portal': 'fincaraiz',
            'fecha_extraccion': datetime.now().isoformat()
        }
        
        try:
            # Buscar precio en el texto
            price_match = re.search(r'\$[\d\.,]+\s*(?:mil|millones?)?', text)
            if price_match:
                prop['precio_texto'] = price_match.group(0)
            
            # Buscar título (primera línea con texto)
            lines = [line.strip() for line in text.split('\n') if line.strip()]
            if lines and len(lines[0]) > 10:
                prop['titulo'] = lines[0]
            
            # Intentar obtener link
            try:
                link_elem = element.find_element(By.TAG_NAME, "a")
                href = link_elem.get_attribute("href")
                if href and '/inmueble/' in href:
                    prop['link'] = href
            except:
                pass
                
        except Exception as e:
            print(f"⚠️ Error parseando elemento visible: {e}")
        
        return prop if prop.get('titulo') or prop.get('link') else None

# Función de prueba
def test_selenium_scraper():
    """Probar el scraper con Selenium"""
    print("🧪 PROBANDO SELENIUM SCRAPER...")
    
    try:
        scraper = FincaraizSeleniumScraper()
        propiedades = scraper.scrape_propiedades(ciudad="bucaramanga/santander")
        
        print(f"\n📊 RESULTADOS SELENIUM:")
        print(f"   Total propiedades: {len(propiedades)}")
        
        for i, prop in enumerate(propiedades):
            print(f"🏠 {i+1}. {prop.get('titulo', 'Sin título')}")
            if prop.get('precio_formateado'):
                print(f"   💰 {prop.get('precio_formateado')}")
            if prop.get('link'):
                print(f"   🔗 {prop.get('link')}")
            print()
                
    except Exception as e:
        print(f"💥 Error en prueba: {e}")

if __name__ == "__main__":
    test_selenium_scraper()