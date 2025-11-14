#!/usr/bin/env python3
# backend/src/tests/test_scrapers.py
"""
Tests completos para todos los scrapers de ARIA
Prueba Fincaraíz, Metrocuadrado y La Haus de manera integral
"""

import sys
import os
import json
import pandas as pd
import time
from datetime import datetime

# Agregar el directorio src al path para importar los módulos
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.src.scrapers.adapters import (
    FincaraizScraper, 
    MetrocuadradoScraper, 
    LaHausScraper, 
    ScraperUnificado,
    get_available_scrapers,
    validar_ciudad,
    validar_tipo_negocio,
    validar_portales
)

def test_scraper_individual(scraper_class, scraper_name, ciudad="bucaramanga", max_paginas=1):
    """Prueba un scraper individual"""
    print(f"\n🧪 TESTEANDO {scraper_name.upper()}")
    print("=" * 50)
    
    try:
        # Crear instancia del scraper
        scraper = scraper_class()
        print(f"✅ Scraper {scraper_name} creado correctamente")
        
        # Probar venta
        inicio = time.time()
        print(f"🔍 Buscando propiedades en VENTA...")
        propiedades_venta = scraper.scrape_propiedades(
            ciudad=ciudad,
            tipo_negocio="venta",
            max_paginas=max_paginas
        )
        tiempo_venta = time.time() - inicio
        
        # Probar arriendo
        inicio = time.time()
        print(f"🔍 Buscando propiedades en ARRIENDO...")
        propiedades_arriendo = scraper.scrape_propiedades(
            ciudad=ciudad,
            tipo_negocio="arriendo", 
            max_paginas=max_paginas
        )
        tiempo_arriendo = time.time() - inicio
        
        # Estadísticas
        total_propiedades = len(propiedades_venta) + len(propiedades_arriendo)
        
        print(f"📊 RESULTADOS {scraper_name.upper()}:")
        print(f"   🏠 Venta: {len(propiedades_venta)} propiedades ({tiempo_venta:.1f}s)")
        print(f"   🏘️  Arriendo: {len(propiedades_arriendo)} propiedades ({tiempo_arriendo:.1f}s)")
        print(f"   📈 Total: {total_propiedades} propiedades")
        
        # Análisis de calidad de datos
        if propiedades_venta:
            analizar_calidad_datos(propiedades_venta, f"{scraper_name} - Venta")
        if propiedades_arriendo:
            analizar_calidad_datos(propiedades_arriendo, f"{scraper_name} - Arriendo")
        
        return {
            'scraper': scraper_name,
            'venta': len(propiedades_venta),
            'arriendo': len(propiedades_arriendo),
            'total': total_propiedades,
            'tiempo_venta': tiempo_venta,
            'tiempo_arriendo': tiempo_arriendo,
            'propiedades_venta': propiedades_venta,
            'propiedades_arriendo': propiedades_arriendo
        }
        
    except Exception as e:
        print(f"❌ ERROR en {scraper_name}: {e}")
        return {
            'scraper': scraper_name,
            'venta': 0,
            'arriendo': 0,
            'total': 0,
            'error': str(e)
        }

def analizar_calidad_datos(propiedades, contexto):
    """Analiza la calidad de los datos extraídos"""
    if not propiedades:
        return
    
    print(f"\n   📋 ANÁLISIS DE CALIDAD - {contexto}:")
    
    total = len(propiedades)
    
    # Conteo de datos disponibles
    con_precio = sum(1 for p in propiedades if p.get('precio'))
    con_fotos = sum(1 for p in propiedades if p.get('fotos'))
    con_area = sum(1 for p in propiedades if p.get('area_m2'))
    con_habitaciones = sum(1 for p in propiedades if p.get('habitaciones'))
    con_banos = sum(1 for p in propiedades if p.get('banos'))
    con_ubicacion = sum(1 for p in propiedades if p.get('ubicacion'))
    con_link = sum(1 for p in propiedades if p.get('link'))
    
    print(f"   💰 Con precio: {con_precio}/{total} ({con_precio/total*100:.1f}%)")
    print(f"   📸 Con fotos: {con_fotos}/{total} ({con_fotos/total*100:.1f}%)")
    print(f"   📐 Con área: {con_area}/{total} ({con_area/total*100:.1f}%)")
    print(f"   🛏️  Con habitaciones: {con_habitaciones}/{total} ({con_habitaciones/total*100:.1f}%)")
    print(f"   🚿 Con baños: {con_banos}/{total} ({con_banos/total*100:.1f}%)")
    print(f"   📍 Con ubicación: {con_ubicacion}/{total} ({con_ubicacion/total*100:.1f}%)")
    print(f"   🔗 Con link: {con_link}/{total} ({con_link/total*100:.1f}%)")
    
    # Promedio de fotos
    if con_fotos > 0:
        avg_fotos = sum(len(p.get('fotos', [])) for p in propiedades) / con_fotos
        print(f"   🖼️  Promedio de fotos: {avg_fotos:.1f}")
    
    # Rango de precios
    precios = [p['precio'] for p in propiedades if p.get('precio')]
    if precios:
        print(f"   💵 Rango precios: ${min(precios):,} - ${max(precios):,}")

def test_scraper_unificado(ciudad="bucaramanga", max_paginas=1):
    """Prueba el scraper unificado"""
    print(f"\n🎯 TESTEANDO SCRAPER UNIFICADO")
    print("=" * 60)
    
    try:
        scraper = ScraperUnificado()
        print("✅ Scraper unificado creado correctamente")
        
        # Probar con todos los portales
        inicio = time.time()
        print("🔍 Ejecutando scraping unificado...")
        
        propiedades = scraper.scrapear_propiedades(
            ciudad=ciudad,
            tipo_negocio="venta",
            portales=["fincaraiz", "metrocuadrado", "lahaus"],
            max_paginas=max_paginas
        )
        
        tiempo_total = time.time() - inicio
        
        print(f"📊 RESULTADOS UNIFICADOS:")
        print(f"   ⏱️  Tiempo total: {tiempo_total:.1f}s")
        print(f"   📈 Total propiedades: {len(propiedades)}")
        
        # Análisis por portal
        portales = {}
        for prop in propiedades:
            portal = prop.get('portal', 'desconocido')
            portales[portal] = portales.get(portal, 0) + 1
        
        print(f"   🌐 Distribución por portal:")
        for portal, cantidad in portales.items():
            print(f"      {portal}: {cantidad} propiedades")
        
        # Análisis de calidad
        analizar_calidad_datos(propiedades, "Unificado")
        
        return {
            'total_propiedades': len(propiedades),
            'tiempo_total': tiempo_total,
            'distribucion_portales': portales,
            'propiedades': propiedades
        }
        
    except Exception as e:
        print(f"❌ ERROR en scraper unificado: {e}")
        return {'error': str(e)}

def test_validaciones():
    """Prueba las funciones de validación"""
    print(f"\n🔧 TESTEANDO VALIDACIONES")
    print("=" * 40)
    
    try:
        # Validar ciudad
        ciudad_valida = validar_ciudad("bucaramanga")
        print(f"✅ Ciudad válida: {ciudad_valida}")
        
        # Validar tipo negocio
        tipo_valido = validar_tipo_negocio("venta")
        print(f"✅ Tipo negocio válido: {tipo_valido}")
        
        # Validar portales
        portales_validos = validar_portales("fincaraiz,metrocuadrado,lahaus")
        print(f"✅ Portales válidos: {portales_validos}")
        
        # Probar validaciones que deberían fallar
        try:
            validar_ciudad("ciudad_inexistente")
        except ValueError as e:
            print(f"✅ Validación de ciudad falla correctamente: {e}")
        
        try:
            validar_tipo_negocio("tipo_invalido")
        except ValueError as e:
            print(f"✅ Validación de tipo falla correctamente: {e}")
            
        return True
        
    except Exception as e:
        print(f"❌ ERROR en validaciones: {e}")
        return False

def test_rendimiento_comparativo():
    """Compara el rendimiento de todos los scrapers"""
    print(f"\n⚡ TEST DE RENDIMIENTO COMPARATIVO")
    print("=" * 50)
    
    scrapers = {
        'fincaraiz': FincaraizScraper,
        'metrocuadrado': MetrocuadradoScraper, 
        'lahaus': LaHausScraper
    }
    
    resultados = {}
    
    for nombre, scraper_class in scrapers.items():
        print(f"\n🔍 Probando {nombre}...")
        inicio = time.time()
        
        try:
            scraper = scraper_class()
            propiedades = scraper.scrape_propiedades(
                ciudad="bucaramanga",
                tipo_negocio="venta",
                max_paginas=1
            )
            
            tiempo = time.time() - inicio
            resultados[nombre] = {
                'propiedades': len(propiedades),
                'tiempo': tiempo,
                'propiedades_por_segundo': len(propiedades) / tiempo if tiempo > 0 else 0,
                'estado': 'éxito'
            }
            
            print(f"   ✅ {len(propiedades)} propiedades en {tiempo:.1f}s")
            
        except Exception as e:
            tiempo = time.time() - inicio
            resultados[nombre] = {
                'propiedades': 0,
                'tiempo': tiempo,
                'propiedades_por_segundo': 0,
                'estado': f'error: {e}'
            }
            print(f"   ❌ Error: {e}")
    
    # Mostrar comparativa
    print(f"\n📊 COMPARATIVA DE RENDIMIENTO:")
    for nombre, datos in resultados.items():
        print(f"   {nombre.upper():<15} | {datos['propiedades']:>3} props | {datos['tiempo']:>5.1f}s | {datos['propiedades_por_segundo']:>5.1f} props/s | {datos['estado']}")
    
    return resultados

def guardar_resultados_test(resultados, nombre_test):
    """Guarda los resultados de los tests en archivos"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    directorio = f"test_results_{timestamp}"
    os.makedirs(directorio, exist_ok=True)
    
    # Guardar resumen JSON
    resumen_file = os.path.join(directorio, f"resumen_{nombre_test}.json")
    with open(resumen_file, 'w', encoding='utf-8') as f:
        json.dump(resultados, f, ensure_ascii=False, indent=2)
    
    # Guardar propiedades en CSV si existen
    todas_propiedades = []
    for resultado in resultados.values():
        if 'propiedades_venta' in resultado:
            todas_propiedades.extend(resultado['propiedades_venta'])
        if 'propiedades_arriendo' in resultado:
            todas_propiedades.extend(resultado['propiedades_arriendo'])
        if 'propiedades' in resultado and isinstance(resultado['propiedades'], list):
            todas_propiedades.extend(resultado['propiedades'])
    
    if todas_propiedades:
        csv_file = os.path.join(directorio, f"propiedades_{nombre_test}.csv")
        df = pd.DataFrame([
            {
                'portal': p.get('portal', ''),
                'titulo': p.get('titulo', ''),
                'precio': p.get('precio', ''),
                'precio_formateado': p.get('precio_formateado', ''),
                'ubicacion': p.get('ubicacion', ''),
                'area_m2': p.get('area_m2', ''),
                'habitaciones': p.get('habitaciones', ''),
                'banos': p.get('banos', ''),
                'num_fotos': len(p.get('fotos', [])),
                'link': p.get('link', ''),
                'tipo_negocio': 'venta' if 'venta' in str(p.get('link', '')).lower() else 'arriendo'
            }
            for p in todas_propiedades
        ])
        df.to_csv(csv_file, index=False, encoding='utf-8-sig')
        print(f"💾 Resultados guardados en: {directorio}/")
    
    return directorio

def test_todos_scrapers(ciudad="bucaramanga", max_paginas=1):
    """Ejecuta todos los tests de scrapers"""
    print("🚀 INICIANDO TEST COMPLETO DE SCRAPERS ARIA")
    print("=" * 70)
    print(f"📍 Ciudad: {ciudad}")
    print(f"📄 Páginas por scraper: {max_paginas}")
    print("=" * 70)
    
    inicio_total = time.time()
    resultados = {}
    
    try:
        # 1. Test de validaciones
        print("\n1️⃣  TEST DE VALIDACIONES")
        validaciones_ok = test_validaciones()
        resultados['validaciones'] = {'estado': 'éxito' if validaciones_ok else 'error'}
        
        # 2. Test de scrapers individuales
        print("\n2️⃣  TEST DE SCRAPERS INDIVIDUALES")
        scrapers_individuales = {
            'fincaraiz': FincaraizScraper,
            'metrocuadrado': MetrocuadradoScraper,
            'lahaus': LaHausScraper
        }
        
        for nombre, scraper_class in scrapers_individuales.items():
            resultado = test_scraper_individual(scraper_class, nombre, ciudad, max_paginas)
            resultados[nombre] = resultado
        
        # 3. Test de scraper unificado
        print("\n3️⃣  TEST DE SCRAPER UNIFICADO")
        resultado_unificado = test_scraper_unificado(ciudad, max_paginas)
        resultados['unificado'] = resultado_unificado
        
        # 4. Test de rendimiento comparativo
        print("\n4️⃣  TEST DE RENDIMIENTO")
        resultado_rendimiento = test_rendimiento_comparativo()
        resultados['rendimiento'] = resultado_rendimiento
        
        # Resumen final
        tiempo_total = time.time() - inicio_total
        print(f"\n🎉 TEST COMPLETADO EN {tiempo_total:.1f} SEGUNDOS")
        
        # Estadísticas finales
        total_propiedades = sum(
            r.get('total', 0) for r in resultados.values() 
            if isinstance(r, dict) and 'total' in r
        )
        
        scrapers_exitosos = sum(
            1 for nombre in ['fincaraiz', 'metrocuadrado', 'lahaus'] 
            if resultados.get(nombre, {}).get('total', 0) > 0
        )
        
        print(f"📈 ESTADÍSTICAS FINALES:")
        print(f"   🏠 Total propiedades encontradas: {total_propiedades}")
        print(f"   ✅ Scrapers exitosos: {scrapers_exitosos}/3")
        print(f"   ⏱️  Tiempo total: {tiempo_total:.1f}s")
        
        # Guardar resultados
        directorio_resultados = guardar_resultados_test(resultados, "completo")
        print(f"💾 Resultados detallados guardados en: {directorio_resultados}")
        
        return resultados
        
    except Exception as e:
        print(f"💥 ERROR CRÍTICO en test completo: {e}")
        return {'error': str(e)}

def test_rapido():
    """Test rápido para verificación básica"""
    print("⚡ TEST RÁPIDO DE SCRAPERS")
    
    scrapers = {
        'fincaraiz': FincaraizScraper,
        'metrocuadrado': MetrocuadradoScraper,
        'lahaus': LaHausScraper
    }
    
    for nombre, scraper_class in scrapers.items():
        try:
            print(f"\n🔍 Probando {nombre}...")
            scraper = scraper_class()
            propiedades = scraper.scrape_propiedades(
                ciudad="bucaramanga",
                tipo_negocio="venta", 
                max_paginas=1
            )
            print(f"   ✅ {len(propiedades)} propiedades")
            
            # Mostrar primera propiedad como ejemplo
            if propiedades:
                primera = propiedades[0]
                print(f"   📍 Ejemplo: {primera.get('titulo', 'Sin título')}")
                print(f"   💰 Precio: {primera.get('precio_formateado', 'N/A')}")
                
        except Exception as e:
            print(f"   ❌ Error: {e}")

if __name__ == "__main__":
    # Ejecutar test rápido por defecto
    if len(sys.argv) > 1 and sys.argv[1] == "completo":
        test_todos_scrapers(ciudad="bucaramanga", max_paginas=1)
    else:
        test_rapido()