# backend/test_scrapers_individual.py
import sys
import os

sys.path.append('src')

print("=== 🧪 TESTEANDO SCRAPERS INDIVIDUALES ===")

# Test Fincaraiz
print("\n1. Testing FincaraizScraper...")
try:
    from scrapers.fincaraiz_scraper import FincaraizScraper
    scraper = FincaraizScraper()
    print("✅ FincaraizScraper - IMPORTADO E INSTANCIADO")
    
    # Verificar que tenga el método scrape
    if hasattr(scraper, 'scrape'):
        print("✅ FincaraizScraper - TIENE MÉTODO SCRAPE")
    else:
        print("❌ FincaraizScraper - NO TIENE MÉTODO SCRAPE")
        
except Exception as e:
    print(f"❌ FincaraizScraper - ERROR: {e}")

# Test Metrocuadrado
print("\n2. Testing MetrocuadradoScraper...")
try:
    from scrapers.metrocuadrado_scraper import MetrocuadradoScraper
    scraper = MetrocuadradoScraper()
    print("✅ MetrocuadradoScraper - IMPORTADO E INSTANCIADO")
    
    if hasattr(scraper, 'scrape'):
        print("✅ MetrocuadradoScraper - TIENE MÉTODO SCRAPE")
    else:
        print("❌ MetrocuadradoScraper - NO TIENE MÉTODO SCRAPE")
        
except Exception as e:
    print(f"❌ MetrocuadradoScraper - ERROR: {e}")

# Test LaHaus
print("\n3. Testing LaHausScraper...")
try:
    from scrapers.lahaus_scraper import LaHausScraper
    scraper = LaHausScraper()
    print("✅ LaHausScraper - IMPORTADO E INSTANCIADO")
    
    if hasattr(scraper, 'scrape'):
        print("✅ LaHausScraper - TIENE MÉTODO SCRAPE")
    else:
        print("❌ LaHausScraper - NO TIENE MÉTODO SCRAPE")
        
except Exception as e:
    print(f"❌ LaHausScraper - ERROR: {e}")

print("\n=== 🎊 TEST COMPLETADO ===")