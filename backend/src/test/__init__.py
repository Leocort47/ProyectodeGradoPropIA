"""
ARIA - Tests Unitarios e Integrales
Paquete de tests para el sistema de scraping inmobiliario ARIA.

Tests disponibles:
- test_lahaus: Tests específicos para el scraper de La Haus
- test_scrapers: Tests completos para todos los scrapers
"""

__version__ = "1.0.0"
__author__ = "ARIA Team"
__description__ = "Suite de tests para scrapers inmobiliarios"

import sys
import os

# Agregar el directorio src al path para imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Importar tests individuales con manejo robusto de errores
try:
    from .test_lahaus import (
        test_lahaus_scraper,
        test_lahaus_basico,
        mostrar_resultados_detallados,
        generar_estadisticas,
        guardar_resultados
    )
    
    from .test_scrapers import (
        test_todos_scrapers,
        test_scraper_individual,
        test_scraper_unificado,
        test_validaciones,
        test_rendimiento_comparativo,
        test_rapido,
        analizar_calidad_datos,
        guardar_resultados_test
    )
    
    # Lista de tests disponibles
    TESTS_DISPONIBLES = {
        'lahaus': {
            'test_lahaus_scraper': test_lahaus_scraper,
            'test_lahaus_basico': test_lahaus_basico,
            'mostrar_resultados_detallados': mostrar_resultados_detallados,
            'generar_estadisticas': generar_estadisticas,
            'guardar_resultados': guardar_resultados
        },
        'scrapers': {
            'test_todos_scrapers': test_todos_scrapers,
            'test_scraper_individual': test_scraper_individual,
            'test_scraper_unificado': test_scraper_unificado,
            'test_validaciones': test_validaciones,
            'test_rendimiento_comparativo': test_rendimiento_comparativo,
            'test_rapido': test_rapido,
            'analizar_calidad_datos': analizar_calidad_datos,
            'guardar_resultados_test': guardar_resultados_test
        }
    }
    
    __all__ = [
        # Tests La Haus
        'test_lahaus_scraper',
        'test_lahaus_basico', 
        'mostrar_resultados_detallados',
        'generar_estadisticas',
        'guardar_resultados',
        
        # Tests generales
        'test_todos_scrapers',
        'test_scraper_individual',
        'test_scraper_unificado',
        'test_validaciones',
        'test_rendimiento_comparativo',
        'test_rapido',
        'analizar_calidad_datos',
        'guardar_resultados_test',
        
        # Utilidades
        'TESTS_DISPONIBLES',
        'get_available_tests',
        'run_test',
        'run_all_tests'
    ]
    
    print("✅ Módulo de tests cargado correctamente")
    
except ImportError as e:
    print(f"⚠️ Advertencia: No se pudieron importar todos los tests: {e}")
    
    # Crear placeholders para evitar errores
    def test_no_disponible(nombre_test):
        def placeholder(*args, **kwargs):
            print(f"⚠️ Test no disponible: {nombre_test}")
            return {"error": f"Test {nombre_test} no disponible"}
        return placeholder
    
    # Placeholders para tests de La Haus
    test_lahaus_scraper = test_no_disponible("test_lahaus_scraper")
    test_lahaus_basico = test_no_disponible("test_lahaus_basico")
    
    def mostrar_resultados_detallados(*args, **kwargs):
        print("⚠️ Función no disponible: mostrar_resultados_detallados")
    
    def generar_estadisticas(*args, **kwargs):
        print("⚠️ Función no disponible: generar_estadisticas")
        return {}
    
    def guardar_resultados(*args, **kwargs):
        print("⚠️ Función no disponible: guardar_resultados")
        return "no_disponible"
    
    # Placeholders para tests generales
    test_todos_scrapers = test_no_disponible("test_todos_scrapers")
    test_scraper_individual = test_no_disponible("test_scraper_individual")
    test_scraper_unificado = test_no_disponible("test_scraper_unificado")
    test_validaciones = test_no_disponible("test_validaciones")
    test_rendimiento_comparativo = test_no_disponible("test_rendimiento_comparativo")
    test_rapido = test_no_disponible("test_rapido")
    
    def analizar_calidad_datos(*args, **kwargs):
        print("⚠️ Función no disponible: analizar_calidad_datos")
    
    def guardar_resultados_test(*args, **kwargs):
        print("⚠️ Función no disponible: guardar_resultados_test")
        return "no_disponible"
    
    TESTS_DISPONIBLES = {}
    
    __all__ = [
        'test_lahaus_scraper',
        'test_lahaus_basico',
        'mostrar_resultados_detallados', 
        'generar_estadisticas',
        'guardar_resultados',
        'test_todos_scrapers',
        'test_scraper_individual',
        'test_scraper_unificado',
        'test_validaciones',
        'test_rendimiento_comparativo',
        'test_rapido',
        'analizar_calidad_datos',
        'guardar_resultados_test',
        'TESTS_DISPONIBLES',
        'get_available_tests',
        'run_test',
        'run_all_tests'
    ]

# Funciones de utilidad para gestión de tests
def get_available_tests():
    """
    Retorna información sobre los tests disponibles
    
    Returns:
        dict: Diccionario con información de tests disponibles
    """
    return TESTS_DISPONIBLES

def run_test(test_name, *args, **kwargs):
    """
    Ejecuta un test específico por nombre
    
    Args:
        test_name (str): Nombre del test a ejecutar
        *args: Argumentos para el test
        **kwargs: Keyword arguments para el test
    
    Returns:
        object: Resultado del test
    
    Raises:
        ValueError: Si el test no existe
    """
    # Buscar en todos los grupos de tests
    for group_name, tests_group in TESTS_DISPONIBLES.items():
        if test_name in tests_group:
            test_function = tests_group[test_name]
            print(f"🎯 Ejecutando test: {test_name}")
            return test_function(*args, **kwargs)
    
    # Si no se encuentra
    available_tests = []
    for group_name, tests_group in TESTS_DISPONIBLES.items():
        available_tests.extend(tests_group.keys())
    
    raise ValueError(
        f"Test '{test_name}' no encontrado. Tests disponibles: {available_tests}"
    )

def run_test_group(group_name, *args, **kwargs):
    """
    Ejecuta todos los tests de un grupo específico
    
    Args:
        group_name (str): Nombre del grupo de tests
        *args: Argumentos para los tests
        **kwargs: Keyword arguments para los tests
    
    Returns:
        dict: Resultados de todos los tests del grupo
    """
    if group_name not in TESTS_DISPONIBLES:
        available_groups = list(TESTS_DISPONIBLES.keys())
        raise ValueError(
            f"Grupo de tests '{group_name}' no encontrado. Grupos disponibles: {available_groups}"
        )
    
    print(f"🎯 Ejecutando grupo de tests: {group_name.upper()}")
    resultados = {}
    
    for test_name, test_function in TESTS_DISPONIBLES[group_name].items():
        if not test_name.startswith('_'):  # Ignorar métodos privados
            print(f"  🔍 Ejecutando: {test_name}")
            try:
                resultado = test_function(*args, **kwargs)
                resultados[test_name] = resultado
                print(f"  ✅ {test_name}: COMPLETADO")
            except Exception as e:
                resultados[test_name] = {'error': str(e)}
                print(f"  ❌ {test_name}: ERROR - {e}")
    
    return resultados

def run_all_tests(ciudad="bucaramanga", max_paginas=1, verbose=True):
    """
    Ejecuta todos los tests disponibles
    
    Args:
        ciudad (str): Ciudad para las pruebas
        max_paginas (int): Número máximo de páginas a scrapear
        verbose (bool): Mostrar output detallado
    
    Returns:
        dict: Resultados de todos los tests
    """
    print("🚀 INICIANDO SUITE COMPLETA DE TESTS ARIA")
    print("=" * 60)
    print(f"📍 Ciudad de prueba: {ciudad}")
    print(f"📄 Páginas por test: {max_paginas}")
    print("=" * 60)
    
    import time
    inicio_total = time.time()
    
    resultados_totales = {}
    
    try:
        # Ejecutar tests de scrapers generales
        if 'scrapers' in TESTS_DISPONIBLES:
            print("\n📊 EJECUTANDO TESTS DE SCRAPERS GENERALES")
            resultados_scrapers = run_test_group(
                'scrapers', 
                ciudad=ciudad, 
                max_paginas=max_paginas
            )
            resultados_totales['scrapers'] = resultados_scrapers
        
        # Ejecutar tests específicos de La Haus
        if 'lahaus' in TESTS_DISPONIBLES:
            print("\n🏠 EJECUTANDO TESTS ESPECÍFICOS DE LA HAUS")
            resultados_lahaus = run_test_group(
                'lahaus',
                ciudad=ciudad,
                max_paginas=max_paginas
            )
            resultados_totales['lahaus'] = resultados_lahaus
        
        # Calcular estadísticas finales
        tiempo_total = time.time() - inicio_total
        
        print(f"\n🎉 SUITE DE TESTS COMPLETADA")
        print("=" * 50)
        print(f"⏱️  Tiempo total: {tiempo_total:.1f} segundos")
        
        # Contar tests ejecutados
        total_tests = 0
        tests_exitosos = 0
        
        for grupo, tests in resultados_totales.items():
            for test_name, resultado in tests.items():
                total_tests += 1
                if not resultado.get('error'):
                    tests_exitosos += 1
        
        print(f"📈 Resumen:")
        print(f"   ✅ Tests exitosos: {tests_exitosos}/{total_tests}")
        print(f"   📊 Grupos ejecutados: {len(resultados_totales)}")
        
        # Guardar resultados si hay funciones disponibles
        if 'guardar_resultados_test' in globals():
            directorio = guardar_resultados_test(resultados_totales, "suite_completa")
            print(f"💾 Resultados guardados en: {directorio}")
        
        return resultados_totales
        
    except Exception as e:
        print(f"💥 ERROR en suite de tests: {e}")
        return {'error': str(e)}

def test_health_check():
    """
    Test de salud básica del sistema de tests
    
    Returns:
        dict: Estado de salud del sistema
    """
    print("❤️  TEST DE SALUD DEL SISTEMA DE TESTS")
    print("=" * 40)
    
    estado = {
        'timestamp': __import__('datetime').datetime.now().isoformat(),
        'version': __version__,
        'tests_disponibles': len(TESTS_DISPONIBLES),
        'grupos_tests': list(TESTS_DISPONIBLES.keys()),
        'estado': 'healthy'
    }
    
    # Verificar imports básicos
    try:
        import requests
        estado['requests'] = '✅ Disponible'
    except ImportError:
        estado['requests'] = '❌ No disponible'
    
    try:
        import pandas as pd
        estado['pandas'] = '✅ Disponible'
    except ImportError:
        estado['pandas'] = '❌ No disponible'
    
    try:
        from backend.src.scrapers.adapters import get_available_scrapers
        scrapers = get_available_scrapers()
        estado['scrapers'] = f"✅ {len(scrapers)} disponibles"
    except ImportError:
        estado['scrapers'] = '❌ No disponibles'
    
    # Mostrar resultados
    for key, value in estado.items():
        if key not in ['timestamp']:
            print(f"   {key}: {value}")
    
    return estado

def list_tests():
    """
    Lista todos los tests disponibles con información
    """
    print("📋 TESTS DISPONIBLES EN ARIA")
    print("=" * 50)
    
    if not TESTS_DISPONIBLES:
        print("⚠️ No hay tests disponibles")
        return
    
    for group_name, tests in TESTS_DISPONIBLES.items():
        print(f"\n🎯 {group_name.upper()} ({len(tests)} tests):")
        for test_name in tests.keys():
            if not test_name.startswith('_'):
                print(f"   • {test_name}")

# Ejemplo de uso
def ejemplo_uso():
    """
    Muestra ejemplos de cómo usar el sistema de tests
    """
    print("🔧 EJEMPLOS DE USO - SISTEMA DE TESTS ARIA")
    print("=" * 50)
    
    print("\n1. Ejecutar test específico:")
    print("   from tests import run_test")
    print('   resultado = run_test("test_rapido")')
    
    print("\n2. Ejecutar grupo de tests:")
    print("   from tests import run_test_group") 
    print('   resultados = run_test_group("scrapers")')
    
    print("\n3. Ejecutar todos los tests:")
    print("   from tests import run_all_tests")
    print('   resultados = run_all_tests(ciudad=\"bucaramanga\")')
    
    print("\n4. Ver tests disponibles:")
    print("   from tests import list_tests")
    print("   list_tests()")
    
    print("\n5. Verificar salud del sistema:")
    print("   from tests import test_health_check")
    print("   estado = test_health_check()")

# Inicialización al importar el módulo
if __name__ == "__main__":
    print(f"🧪 ARIA Tests v{__version__}")
    print(f"📝 {__description__}")
    
    # Mostrar información al ejecutar directamente
    test_health_check()
    print()
    list_tests()
    print()
    ejemplo_uso()
    
    # Ejecutar test rápido si se solicita
    if len(sys.argv) > 1 and sys.argv[1] == "run":
        print("\n" + "="*50)
        run_all_tests(ciudad="bucaramanga", max_paginas=1)