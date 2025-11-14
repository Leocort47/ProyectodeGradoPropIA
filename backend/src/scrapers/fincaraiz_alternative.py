# src/scrapers/fincaraiz_alternative.py
"""
Scraper alternativo para Fincaraíz usando Selenium (navegador real)
"""

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import re
from datetime import datetime
import os

class FincaraizSeleniumScraper:
    def __init__(self):
        self.base_url = "https://fincaraiz.com.co"
        self.driver = self._setup_driver()
    
    def _setup_driver(self):
        """Configura ChromeDriver con opciones para evitar detección"""
        chrome_options = Options()
        chrome_options.add_argument("--headless")  # Ejecutar en background
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        chrome_options.add_argument("--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
        
        driver = webdriver.Chrome(options=chrome_options)
        driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        return driver
    
    def scrape_propiedades(self, ciudad="bucaramanga", tipo_negocio="venta", max_paginas=1):
        """Scraping usando Selenium para evitar bloqueos"""
        propiedades = []
        
        try:
            # Construir URL
            if tipo_negocio == "arriendo":
                url = f"{self.base_url}/arrendamiento/inmuebles/{ciudad}?pagina=1"
            else:
                url = f"{self.base_url}/venta/inmuebles/{ciudad}?pagina=1"
            
            print(f"🌐 Navegando a: {url}")
            self.driver.get(url)
            
            # Esperar a que cargue la página
            time.sleep(5)
            
            # Tomar screenshot para debugging
            self.driver.save_screenshot("fincaraiz_screenshot.png")
            print("📸 Screenshot guardado")
            
            # Obtener HTML actual
            html = self.driver.page_source
            with open("fincaraiz_selenium.html", "w", encoding="utf-8") as f:
                f.write(html)
            print("💾 HTML con Selenium guardado")
            
            # Buscar propiedades en el HTML
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(html, 'html.parser')
            
            # Estrategias de búsqueda ampliada
            property_elements = self._find_property_elements(soup)
            print(f"🔍 Encontrados {len(property_elements)} elementos de propiedad")
            
            # Extraer datos básicos
            for i, element in enumerate(property_elements[:5]):  # Limitar a 5 para prueba
                prop = self._extract_basic_info(element)
                if prop:
                    propiedades.append(prop)
                    print(f"✅ Propiedad {i+1}: {prop.get('titulo', 'Sin título')}")
            
        except Exception as e:
            print(f"❌ Error con Selenium: {e}")
        finally:
            self.driver.quit()
        
        return propiedades
    
    def _find_property_elements(self, soup):
        """Buscar elementos de propiedad con múltiples estrategias"""
        elements = []
        
        # Buscar cualquier elemento que contenga texto de propiedad
        all_elements = soup.find_all(['div', 'article', 'section', 'a'])
        
        for elem in all_elements:
            text = elem.get_text().lower()
            # Si tiene indicadores de propiedad y no es muy pequeño
            if (any(keyword in text for keyword in ['$', 'precio', 'habitacion', 'm²', 'apartamento', 'casa']) 
                and len(text) > 20):
                elements.append(elem)
        
        return elements
    
    def _extract_basic_info(self, element):
        """Extraer información básica de un elemento"""
        try:
            prop = {}
            text = element.get_text()
            
            # Título (primer línea con texto significativo)
            lines = [line.strip() for line in text.split('\n') if line.strip()]
            if lines:
                prop['titulo'] = lines[0][:100]
            
            # Precio
            price_match = re.search(r'\$[\d\.,]+\s*(?:mil|millones?|mn|m)?', text)
            if price_match:
                prop['precio_texto'] = price_match.group(0)
            
            # Link
            link_elem = element.find('a', href=True)
            if link_elem:
                href = link_elem['href']
                if href.startswith('/'):
                    prop['link'] = self.base_url + href
                else:
                    prop['link'] = href
            
            prop['portal'] = 'fincaraiz'
            prop['fecha_extraccion'] = datetime.now().isoformat()
            
            return prop if prop.get('titulo') or prop.get('link') else None
            
        except Exception as e:
            print(f"⚠️ Error extrayendo info: {e}")
            return None

# Prueba rápida
if __name__ == "__main__":
    scraper = FincaraizSeleniumScraper()
    props = scraper.scrape_propiedades(ciudad="bucaramanga/santander")
    print(f"📊 Resultado: {len(props)} propiedades")