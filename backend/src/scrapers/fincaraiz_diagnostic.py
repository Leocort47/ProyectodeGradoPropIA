#!/usr/bin/env python3
"""
Diagnóstico para FincaRaiz - Identifica por qué no se extraen propiedades
"""
import requests
from bs4 import BeautifulSoup
import re
import json
import os
from urllib.parse import urljoin
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class FincaRaizDiagnostic:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "es-CO,es;q=0.9,en;q=0.8",
        })
        self.base_url = "https://fincaraiz.com.co"
    
    def analyze_page_structure(self, url):
        """Analiza la estructura completa de la página"""
        print(f"\n🔍 ANALIZANDO: {url}")
        
        try:
            response = self.session.get(url, timeout=15)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # 1. Guardar HTML completo para análisis
            debug_file = "fincaraiz_diagnostic.html"
            with open(debug_file, "w", encoding="utf-8") as f:
                f.write(soup.prettify())
            print(f"💾 HTML guardado en: {debug_file}")
            
            # 2. Analizar estructura de la página
            print("\n📊 ANÁLISIS DE ESTRUCTURA:")
            print(f"   Título: {soup.title.string if soup.title else 'No encontrado'}")
            
            # 3. Buscar scripts con datos
            scripts = soup.find_all('script')
            print(f"   Scripts encontrados: {len(scripts)}")
            
            for i, script in enumerate(scripts):
                if script.string:
                    script_content = script.string
                    # Buscar JSON data
                    if 'window.__' in script_content or 'JSON' in script_content:
                        print(f"   🎯 Script {i} contiene datos potenciales")
                        if 'initial' in script_content.lower() or 'state' in script_content.lower():
                            print(f"   📦 Script {i} parece contener INITIAL STATE")
                            # Guardar este script para análisis
                            with open(f"script_{i}.js", "w", encoding="utf-8") as f:
                                f.write(script_content[:5000])  # Primeros 5000 caracteres
            
            # 4. Buscar contenedores de propiedades
            print("\n🔎 BUSCANDO CONTENEDORES DE PROPIEDADES:")
            
            # Selectores comunes
            selectors = [
                'article',
                '[data-cy*="listing"]',
                '[class*="listing"]',
                '[class*="property"]', 
                '[class*="card"]',
                '[class*="advertisement"]',
                '.MuiCard-root',  # Material-UI
                '.card',
                '.property-item'
            ]
            
            for selector in selectors:
                elements = soup.select(selector)
                if elements:
                    print(f"   ✅ Selector '{selector}': {len(elements)} elementos")
                    # Mostrar el primer elemento como ejemplo
                    if elements:
                        first_elem = elements[0]
                        text_preview = first_elem.get_text(strip=True)[:100]
                        print(f"      Ejemplo: {text_preview}...")
                        
                        # Buscar links dentro del elemento
                        links = first_elem.find_all('a', href=True)
                        property_links = [a['href'] for a in links if '/inmueble/' in a['href']]
                        if property_links:
                            print(f"      🔗 Links de propiedades: {len(property_links)}")
            
            # 5. Buscar todos los links a propiedades
            print("\n🔗 BUSCANDO LINKS A PROPIEDADES:")
            all_links = soup.find_all('a', href=True)
            property_links = []
            
            for link in all_links:
                href = link['href']
                if any(pattern in href for pattern in ['/inmueble/', '/propiedad/', '/property/']):
                    full_url = urljoin(self.base_url, href)
                    property_links.append(full_url)
            
            property_links = list(set(property_links))  # Remover duplicados
            print(f"   📍 Links únicos a propiedades: {len(property_links)}")
            
            for i, link in enumerate(property_links[:5]):  # Mostrar primeros 5
                print(f"      {i+1}. {link}")
            
            # 6. Buscar datos en meta tags
            print("\n🔍 BUSCANDO META TAGS:")
            meta_tags = soup.find_all('meta')
            relevant_meta = []
            
            for meta in meta_tags:
                name = meta.get('name', '') or meta.get('property', '')
                content = meta.get('content', '')
                if any(keyword in name.lower() for keyword in ['description', 'title', 'property', 'product']):
                    relevant_meta.append((name, content[:100]))
            
            print(f"   Meta tags relevantes: {len(relevant_meta)}")
            for name, content in relevant_meta[:3]:
                print(f"      {name}: {content}...")
            
            return {
                'property_links': property_links,
                'total_scripts': len(scripts),
                'has_listings': len(property_links) > 0
            }
            
        except Exception as e:
            print(f"❌ ERROR analizando página: {e}")
            return {'error': str(e)}
    
    def test_search_urls(self):
        """Prueba diferentes URLs de búsqueda"""
        test_urls = [
            "https://fincaraiz.com.co/venta/casas-y-apartamentos/bucaramanga/santander",
            "https://fincaraiz.com.co/arriendo/casas-y-apartamentos/bucaramanga/santander",
            "https://fincaraiz.com.co/venta/apartamentos/bucaramanga",
            "https://fincaraiz.com.co/inmuebles/venta/bucaramanga"
        ]
        
        results = {}
        for url in test_urls:
            print(f"\n{'='*60}")
            result = self.analyze_page_structure(url)
            results[url] = result
            
            if result.get('has_listings'):
                print(f"🎯 URL VÁLIDA ENCONTRADA: {url}")
                break
        
        return results

def main():
    diagnostic = FincaRaizDiagnostic()
    
    print("🚀 INICIANDO DIAGNÓSTICO COMPLETO DE FINCARAIZ")
    print("=" * 70)
    
    # Probar diferentes URLs
    results = diagnostic.test_search_urls()
    
    # Resumen
    print(f"\n{'='*70}")
    print("📋 RESUMEN DEL DIAGNÓSTICO:")
    
    valid_urls = [url for url, result in results.items() if result.get('has_listings')]
    if valid_urls:
        print(f"✅ URLs válidas encontradas: {len(valid_urls)}")
        for url in valid_urls:
            print(f"   🔗 {url}")
    else:
        print("❌ No se encontraron URLs con propiedades")
        print("💡 Posibles problemas:")
        print("   - Sitio requiere JavaScript")
        print("   - Bloqueo por anti-bot")
        print("   - Estructura HTML cambiada")
        print("   - URLs incorrectas")

if __name__ == "__main__":
    main()