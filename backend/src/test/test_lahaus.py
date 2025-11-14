#!/usr/bin/env python3
# backend/src/tests/test_lahaus.py
"""
Script de prueba para el scraper de La Haus
Prueba la extracción de propiedades reales con fotos reales
"""

import sys
import os
import json
import pandas as pd
from datetime import datetime

# Agregar el directorio src al path para importar los módulos
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scrapers.lahaus_scraper import LaHausScraper

def test_lahaus_basico():
    """Prueba básica del scraper de La Haus"""
    print("🚀 INICIANDO PRUEBA DE LA HAUS SCRAPER")
    print("=" * 60)
    
    scraper = LaHausScraper()
    
    print("🔍 Configurando parámetros de búsqueda...")
    print("   Ciudad: Bucaramanga")
    print("   Tipo: Venta")
    print("   Páginas: 2")
    print("=" * 60)
    
    try:
        propiedades = scraper.scrape_propiedades(
            ciudad="bucaramanga",
            tipo_negocio="venta",
            max_paginas=2
        )
        
        print(f"✅ EXTRACCIÓN COMPLETADA")
        print(f"📊 Total propiedades encontradas: {len(propiedades)}")
        print("=" * 60)
        
        return propiedades
        
    except Exception as e:
        print(f"❌ ERROR en la extracción: {e}")
        return []

def mostrar_resultados_detallados(propiedades):
    """Muestra resultados detallados de las propiedades"""
    if not propiedades:
        print("📭 No se encontraron propiedades para mostrar")
        return
    
    print(f"\n📋 DETALLES DE {len(propiedades)} PROPIEDADES")
    print("=" * 80)
    
    for i, prop in enumerate(propiedades, 1):
        print(f"\n🏠 PROPIEDAD {i}:")
        print(f"   📍 Título: {prop.get('titulo', 'N/A')}")
        print(f"   💰 Precio: {prop.get('precio_formateado', 'Consultar')}")
        
        if prop.get('ubicacion'):
            print(f"   🗺️  Ubicación: {prop['ubicacion']}")
        
        # Características
        detalles = []
        if prop.get('area_m2'):
            detalles.append(f"📐 {prop['area_m2']} m²")
        if prop.get('habitaciones'):
            detalles.append(f"🛏️  {prop['habitaciones']} hab")
        if prop.get('banos'):
            detalles.append(f"🚿 {prop['banos']} baños")
        if prop.get('parqueaderos'):
            detalles.append(f"🚗 {prop['parqueaderos']} parq")
        
        if detalles:
            print(f"   {' | '.join(detalles)}")
        
        # Fotos
        if prop.get('fotos'):
            print(f"   📸 Fotos: {len(prop['fotos'])} imágenes")
            # Mostrar primera foto como ejemplo
            if prop['fotos']:
                print(f"   🔗 Ejemplo: {prop['fotos'][0][:80]}...")
        
        # Tipo y proyecto
        if prop.get('tipo'):
            print(f"   🏢 Tipo: {prop['tipo']}")
        
        if prop.get('proyecto'):
            print(f"   🏗️  Proyecto: {prop['proyecto']}")
        
        if prop.get('constructora'):
            print(f"   👷 Constructora: {prop['constructora']}")
        
        # Link
        if prop.get('link'):
            print(f"   🔗 Enlace: {prop['link']}")
        
        print("   " + "─" * 50)

def generar_estadisticas(propiedades):
    """Genera estadísticas de las propiedades encontradas"""
    if not propiedades:
        print("📊 No hay datos para generar estadísticas")
        return
    
    print(f"\n📈 ESTADÍSTICAS DE EXTRACCIÓN")
    print("=" * 50)
    
    # Conteo básico
    total_propiedades = len(propiedades)
    print(f"📊 Total propiedades: {total_propiedades}")
    
    # Propiedades con precio
    con_precio = sum(1 for p in propiedades if p.get('precio'))
    print(f"💰 Con precio: {con_precio}/{total_propiedades} ({con_precio/total_propiedades*100:.1f}%)")
    
    # Propiedades con fotos
    con_fotos = sum(1 for p in propiedades if p.get('fotos'))
    print(f"📸 Con fotos: {con_fotos}/{total_propiedades} ({con_fotos/total_propiedades*100:.1f}%)")
    
    # Promedio de fotos por propiedad
    if con_fotos > 0:
        avg_fotos = sum(len(p.get('fotos', [])) for p in propiedades) / con_fotos
        print(f"🖼️  Promedio de fotos: {avg_fotos:.1f}")
    
    # Propiedades con área
    con_area = sum(1 for p in propiedades if p.get('area_m2'))
    print(f"📐 Con área: {con_area}/{total_propiedades} ({con_area/total_propiedades*100:.1f}%)")
    
    # Tipos de propiedades
    tipos = {}
    for prop in propiedades:
        tipo = prop.get('tipo', 'No especificado')
        tipos[tipo] = tipos.get(tipo, 0) + 1
    
    if tipos:
        print(f"\n🏢 DISTRIBUCIÓN POR TIPO:")
        for tipo, cantidad in tipos.items():
            print(f"   {tipo}: {cantidad} ({cantidad/total_propiedades*100:.1f}%)")
    
    # Rango de precios
    precios = [p['precio'] for p in propiedades if p.get('precio')]
    if precios:
        print(f"\n💵 RANGO DE PRECIOS:")
        print(f"   Mínimo: ${min(precios):,}")
        print(f"   Máximo: ${max(precios):,}")
        print(f"   Promedio: ${sum(precios)/len(precios):,.0f}")

def guardar_resultados(propiedades, formato='both'):
    """Guarda los resultados en diferentes formatos"""
    if not propiedades:
        print("📭 No hay propiedades para guardar")
        return
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename_base = f"lahaus_test_{timestamp}"
    
    # Guardar como JSON
    if formato in ['json', 'both']:
        json_filename = f"{filename_base}.json"
        with open(json_filename, 'w', encoding='utf-8') as f:
            json.dump(propiedades, f, ensure_ascii=False, indent=2)
        print(f"💾 JSON guardado: {json_filename}")
    
    # Guardar como CSV
    if formato in ['csv', 'both']:
        # Crear DataFrame
        df_data = []
        for prop in propiedades:
            row = {
                'titulo': prop.get('titulo', ''),
                'precio': prop.get('precio', ''),
                'precio_formateado': prop.get('precio_formateado', ''),
                'tipo': prop.get('tipo', ''),
                'ubicacion': prop.get('ubicacion', ''),
                'area_m2': prop.get('area_m2', ''),
                'habitaciones': prop.get('habitaciones', ''),
                'banos': prop.get('banos', ''),
                'parqueaderos': prop.get('parqueaderos', ''),
                'proyecto': prop.get('proyecto', ''),
                'constructora': prop.get('constructora', ''),
                'num_fotos': len(prop.get('fotos', [])),
                'imagen_principal': prop.get('imagen_principal', ''),
                'link': prop.get('link', ''),
                'portal': prop.get('portal', ''),
                'fecha_extraccion': prop.get('fecha_extraccion', '')
            }
            df_data.append(row)
        
        df = pd.DataFrame(df_data)
        csv_filename = f"{filename_base}.csv"
        df.to_csv(csv_filename, index=False, encoding='utf-8-sig')
        print(f"💾 CSV guardado: {csv_filename}")
        
        # Mostrar resumen del CSV
        print(f"📋 Columnas en CSV: {', '.join(df.columns)}")

def test_lahaus_multiple_ciudades():
    """Prueba el scraper con múltiples ciudades"""
    print("\n🌆 PRUEBA CON MÚLTIPLES CIUDADES")
    print("=" * 50)
    
    ciudades = ['bucaramanga', 'bogota', 'medellin']
    scraper = LaHausScraper()
    
    resultados = {}
    
    for ciudad in ciudades:
        print(f"\n🔍 Probando {ciudad.upper()}...")
        try:
            propiedades = scraper.scrape_propiedades(
                ciudad=ciudad,
                tipo_negocio="venta",
                max_paginas=1  # Solo 1 página por ciudad para prueba rápida
            )
            resultados[ciudad] = propiedades
            print(f"✅ {ciudad}: {len(propiedades)} propiedades")
            
            # Pequeño delay entre ciudades
            import time
            time.sleep(2)
            
        except Exception as e:
            print(f"❌ Error en {ciudad}: {e}")
            resultados[ciudad] = []
    
    # Resumen múltiples ciudades
    print(f"\n📊 RESUMEN MULTICIUDAD:")
    for ciudad, props in resultados.items():
        print(f"   {ciudad.upper()}: {len(props)} propiedades")

def test_rendimiento():
    """Prueba de rendimiento del scraper"""
    print("\n⚡ PRUEBA DE RENDIMIENTO")
    print("=" * 40)
    
    import time
    
    scraper = LaHausScraper()
    
    inicio = time.time()
    
    propiedades = scraper.scrape_propiedades(
        ciudad="bucaramanga",
        tipo_negocio="venta", 
        max_paginas=1
    )
    
    fin = time.time()
    tiempo_total = fin - inicio
    
    print(f"⏱️  Tiempo total: {tiempo_total:.2f} segundos")
    print(f"📊 Propiedades por segundo: {len(propiedades)/tiempo_total:.2f}")
    print(f"🕒 Tiempo por propiedad: {tiempo_total/len(propiedades) if propiedades else 0:.2f} segundos")

def main():
    """Función principal con menú de pruebas"""
    print("🧪 TESTER LA HAUS SCRAPER")
    print("=" * 50)
    print("Opciones disponibles:")
    print("1. Prueba básica (Bucaramanga, venta, 2 páginas)")
    print("2. Prueba con múltiples ciudades")
    print("3. Prueba de rendimiento")
    print("4. Todas las pruebas")
    print("=" * 50)
    
    try:
        opcion = input("Selecciona una opción (1-4): ").strip()
        
        if opcion == '1':
            propiedades = test_lahaus_basico()
            if propiedades:
                mostrar_resultados_detallados(propiedades)
                generar_estadisticas(propiedades)
                guardar_resultados(propiedades)
                
        elif opcion == '2':
            test_lahaus_multiple_ciudades()
            
        elif opcion == '3':
            test_rendimiento()
            
        elif opcion == '4':
            print("🔄 Ejecutando todas las pruebas...")
            
            # Prueba básica
            propiedades = test_lahaus_basico()
            if propiedades:
                mostrar_resultados_detallados(propiedades[:3])  # Mostrar solo 3 para no saturar
                generar_estadisticas(propiedades)
                guardar_resultados(propiedades)
            
            # Otras pruebas
            test_lahaus_multiple_ciudades()
            test_rendimiento()
            
        else:
            print("❌ Opción no válida")
            
    except KeyboardInterrupt:
        print("\n⏹️  Prueba interrumpida por el usuario")
    except Exception as e:
        print(f"❌ Error inesperado: {e}")

if __name__ == "__main__":
    # Si se ejecuta directamente sin parámetros, hacer prueba básica
    if len(sys.argv) == 1:
        propiedades = test_lahaus_basico()
        if propiedades:
            mostrar_resultados_detallados(propiedades)
            generar_estadisticas(propiedades)
            guardar_resultados(propiedades)
    else:
        # Permitir ejecución con parámetros
        main()