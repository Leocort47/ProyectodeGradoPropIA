# backend/diagnostic_correct.py
import sys
import os

print("=== 🎯 DIAGNÓSTICO CORRECTO DESDE BACKEND ===")
print(f"📁 Directorio actual: {os.getcwd()}")

# Verificar estructura de carpetas
print("\n1. 📁 ESTRUCTURA DE CARPETAS:")
print("-" * 40)

paths_to_check = [
    'src',
    'src/scrapers', 
    'src/scrapers/adapters',
    'src/__init__.py',
    'src/scrapers/__init__.py'
]

for path in paths_to_check:
    exists = os.path.exists(path)
    print(f"   {'✅' if exists else '❌'} {path}: {'EXISTE' if exists else 'NO EXISTE'}")

# Buscar archivos scraper específicos
print("\n2. 🔍 BUSCANDO ARCHIVOS SCRAPER:")
print("-" * 40)

scraper_patterns = [
    '*fincara*.py',
    '*metro*.py', 
    '*lahaus*.py'
]

for pattern in scraper_patterns:
    found_files = []
    for root, dirs, files in os.walk('src'):
        for file in files:
            if file.lower().endswith('.py') and pattern.replace('*', '').lower() in file.lower():
                found_files.append(os.path.join(root, file))
    
    if found_files:
        for file in found_files:
            print(f"   ✅ {file}")
    else:
        print(f"   ❌ No se encontraron archivos con patrón: {pattern}")

print("\n3. 🔧 ANALIZANDO src/scrapers/__init__.py:")
print("-" * 40)

init_path = 'src/scrapers/__init__.py'
if os.path.exists(init_path):
    with open(init_path, 'r') as f:
        content = f.read()
    
    # Verificar funciones críticas
    critical_functions = ['get_available_scrapers', 'get_scraper', 'FincaraizScraper', 'MetrocuadradoScraper', 'LaHausScraper']
    
    for func in critical_functions:
        if func in content:
            print(f"   ✅ '{func}' encontrado en __init__.py")
        else:
            print(f"   ❌ '{func}' NO encontrado en __init__.py")
    
    # Mostrar primeras 10 líneas para debugging
    lines = content.split('\n')[:15]
    print(f"\n   📄 Primeras 15 líneas de __init__.py:")
    for i, line in enumerate(lines, 1):
        print(f"      {i:2}: {line}")
else:
    print("   ❌ src/scrapers/__init__.py NO EXISTE")

print("\n4. 🐛 PROBANDO IMPORTACIONES CON SYS.PATH CORRECTO:")
print("-" * 40)

# Agregar src al path de Python
sys.path.insert(0, 'src')
print("   ✅ 'src' agregado a sys.path")

try:
    # Intentar importar scrapers
    import scrapers
    print("   ✅ Módulo 'scrapers' importado")
    
    # Verificar atributos disponibles
    attrs = [attr for attr in dir(scrapers) if not attr.startswith('_')]
    print(f"   📋 Atributos disponibles: {attrs}")
    
    # Probar función crítica
    if hasattr(scrapers, 'get_available_scrapers'):
        scrapers_list = scrapers.get_available_scrapers()
        print(f"   ✅ get_available_scrapers() = {scrapers_list}")
    else:
        print("   ❌ get_available_scrapers NO disponible")
        
except Exception as e:
    print(f"   ❌ Error importando scrapers: {e}")
    import traceback
    traceback.print_exc()

print("\n=== 🎊 DIAGNÓSTICO COMPLETADO ===")