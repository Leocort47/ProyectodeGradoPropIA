#!/usr/bin/env python3
"""
Scraper FincaRaiz con Selenium - Versión Corregida
"""
import time
import random
import re
import json
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from urllib.parse import urljoin
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class FincaRaizSeleniumScraper:
    def __init__(self, headless=True):
        self.headless = headless
        self.base_url = "https://fincaraiz.com.co"
        self.driver = None
        
    def init_driver(self):
        """Inicializa el driver de Selenium"""
        print("🚀 Inicializando Chrome Driver...")
        chrome_options = Options()
        
        if self.headless:
            chrome_options.add_argument("--headless")
        
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument("--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
        
        # Configuraciones adicionales para evitar detección
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        
        try:
            self.driver = webdriver.Chrome(options=chrome_options)
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            print("✅ Chrome Driver inicializado correctamente")
        except Exception as e:
            print(f"❌ Error inicializando Chrome Driver: {e}")
            raise
    
    def close_driver(self):
        """Cierra el driver"""
        if self.driver:
            self.driver.quit()
            print("🔚 Chrome Driver cerrado")
    
    def scrape_propiedades(self, ciudad="bucaramanga", tipo_negocio="venta", max_paginas=1):
        """Scraping principal con Selenium"""
        print(f"\n🎯 INICIANDO SCRAPING: {ciudad}, {tipo_negocio}, {max_paginas} páginas")
        
        self.init_driver()
        all_properties = []
        
        try:
            for pagina in range(1, max_paginas + 1):
                print(f"\n📄 Procesando página {pagina}...")
                
                url = self._build_url(ciudad, tipo_negocio, pagina)
                print(f"🌐 Navegando a: {url}")
                
                page_properties = self._scrape_pagina(url)
                if page_properties:
                    all_properties.extend(page_properties)
                    print(f"✅ Página {pagina}: {len(page_properties)} propiedades encontradas")
                else:
                    print(f"⚠️  Página {pagina}: No se encontraron propiedades")
                    break
                
                # Espera entre páginas
                if pagina < max_paginas:
                    wait_time = random.uniform(3, 6)
                    print(f"⏳ Esperando {wait_time:.1f}s antes de la siguiente página...")
                    time.sleep(wait_time)
            
            print(f"\n🎉 SCRAPING COMPLETADO: {len(all_properties)} propiedades totales")
            return all_properties
            
        except Exception as e:
            print(f"❌ Error durante el scraping: {e}")
            return all_properties
        finally:
            self.close_driver()
    
    def _build_url(self, ciudad, tipo_negocio, pagina):
        """Construye la URL de búsqueda"""
        base = f"{self.base_url}/{tipo_negocio}/casas-y-apartamentos/{ciudad}/santander"
        if pagina > 1:
            return f"{base}?pagina={pagina}"
        return base
    
    def _scrape_pagina(self, url):
        """Scrapea una página individual"""
        try:
            self.driver.get(url)
            
            # Esperar a que cargue la página
            print("⏳ Esperando a que cargue la página...")
            time.sleep(5)
            
            # Hacer scroll para cargar contenido dinámico
            self._scroll_page()
            
            # Esperar a que aparezcan las propiedades
            print("🔍 Buscando propiedades...")
            WebDriverWait(self.driver, 15).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, '[class*="listing"]'))
            )
            
            # Encontrar contenedores de propiedades
            property_containers = self.driver.find_elements(By.CSS_SELECTOR, '[class*="listing"]')
            print(f"📦 Encontrados {len(property_containers)} contenedores de propiedades")
            
            properties = []
            for i, container in enumerate(property_containers):
                try:
                    print(f"  📍 Procesando propiedad {i+1}/{len(property_containers)}")
                    property_data = self._extract_property_data(container)
                    if property_data:
                        properties.append(property_data)
                        print(f"    ✅ Propiedad {i+1} extraída")
                    else:
                        print(f"    ⚠️  Propiedad {i+1} sin datos suficientes")
                    
                    # Pequeña pausa entre propiedades
                    time.sleep(0.5)
                    
                except Exception as e:
                    print(f"    ❌ Error en propiedad {i+1}: {e}")
                    continue
            
            return properties
            
        except TimeoutException:
            print("❌ Timeout: No se cargaron las propiedades")
            return []
        except Exception as e:
            print(f"❌ Error scrapeando página: {e}")
            return []
    
    def _scroll_page(self):
        """Hace scroll para cargar contenido dinámico"""
        try:
            # Scroll hasta el fondo de la página
            last_height = self.driver.execute_script("return document.body.scrollHeight")
            
            for i in range(3):  # Máximo 3 intentos de scroll
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                print(f"  📜 Scroll {i+1}/3...")
                time.sleep(2)
                
                new_height = self.driver.execute_script("return document.body.scrollHeight")
                if new_height == last_height:
                    break
                last_height = new_height
                    
        except Exception as e:
            print(f"⚠️  Error haciendo scroll: {e}")
    
    def _extract_property_data(self, container):
        """Extrae datos de un contenedor de propiedad"""
        try:
            property_data = {'portal': 'fincaraiz'}
            
            # LINK - Buscar enlace principal
            try:
                link_element = container.find_element(By.CSS_SELECTOR, 'a[href*="/inmueble/"]')
                property_data['link'] = urljoin(self.base_url, link_element.get_attribute('href'))
            except NoSuchElementException:
                print("      ⚠️  Sin link")
                return None
            
            # TÍTULO
            try:
                title_element = container.find_element(By.CSS_SELECTOR, '[class*="title"], [class*="name"]')
                property_data['titulo'] = title_element.text.strip()
            except NoSuchElementException:
                property_data['titulo'] = "Sin título"
            
            # PRECIO
            try:
                price_element = container.find_element(By.CSS_SELECTOR, '[class*="price"], [class*="value"]')
                price_text = price_element.text.strip()
                price_value = self._parse_price(price_text)
                if price_value:
                    property_data['precio'] = price_value
                    property_data['precio_formateado'] = f"${price_value:,}"
            except NoSuchElementException:
                property_data['precio'] = None
            
            # UBICACIÓN
            try:
                location_element = container.find_element(By.CSS_SELECTOR, '[class*="location"], [class*="address"]')
                property_data['ubicacion'] = location_element.text.strip()
            except NoSuchElementException:
                property_data['ubicacion'] = "Ubicación no especificada"
            
            # CARACTERÍSTICAS (habitaciones, baños, área)
            container_text = container.text.lower()
            
            # Habitaciones
            hab_match = re.search(r'(\d+)\s*(?:hab|habitaciones?|alcobas?)', container_text)
            if hab_match:
                property_data['habitaciones'] = int(hab_match.group(1))
            
            # Baños
            banos_match = re.search(r'(\d+)\s*(?:baños|banos|baths?)', container_text)
            if banos_match:
                property_data['banos'] = int(banos_match.group(1))
            
            # Área
            area_match = re.search(r'(\d+)\s*m²?', container_text)
            if area_match:
                property_data['area_m2'] = int(area_match.group(1))
            
            # Solo devolver si tiene al menos precio o área
            if property_data.get('precio') or property_data.get('area_m2'):
                return property_data
            else:
                print("      ⚠️  Propiedad sin precio ni área")
                return None
                
        except Exception as e:
            print(f"      ❌ Error extrayendo datos: {e}")
            return None
    
    def _parse_price(self, price_text):
        """Convierte texto de precio a número"""
        try:
            # Limpiar y extraer números
            clean_text = re.sub(r'[^\d,]', '', price_text)
            if ',' in clean_text:
                # Formato colombiano: 1.000.000,00 -> 1000000.00
                parts = clean_text.split(',')
                integer_part = parts[0].replace('.', '')
                if len(parts) > 1:
                    return int(integer_part + parts[1].ljust(2, '0')[:2])
                else:
                    return int(integer_part)
            else:
                return int(clean_text.replace('.', ''))
        except:
            return None

# Función de compatibilidad para el sistema existente
def scrape_fincaraiz(ciudad="bucaramanga", tipo_negocio="venta", max_paginas=1):
    """Función wrapper para compatibilidad con el sistema existente"""
    scraper = FincaRaizSeleniumScraper(headless=True)
    return scraper.scrape_propiedades(ciudad, tipo_negocio, max_paginas)

if __name__ == "__main__":
    # Prueba rápida
    scraper = FincaRaizSeleniumScraper(headless=False)  # Visible para debugging
    propiedades = scraper.scrape_propiedades(
        ciudad="bucaramanga", 
        tipo_negocio="venta", 
        max_paginas=1
    )
    
    print(f"\n📊 RESULTADOS DE PRUEBA:")
    print(f"Total propiedades: {len(propiedades)}")
    for i, prop in enumerate(propiedades[:3]):  # Mostrar primeras 3
        print(f"\n{i+1}. {prop.get('titulo', 'Sin título')}")
        print(f"   💰 {prop.get('precio_formateado', 'Precio no disponible')}")
        print(f"   📍 {prop.get('ubicacion', 'Ubicación no disponible')}")
        print(f"   🛏️  {prop.get('habitaciones', 'N/A')} hab | 🚿 {prop.get('banos', 'N/A')} baños | 📐 {prop.get('area_m2', 'N/A')} m²")
        print(f"   🔗 {prop.get('link', 'Sin link')}")