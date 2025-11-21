# ============================================================================
# backend/src/main.py - FASTAPI BACKEND PARA SCRAPING REAL DE PROPIEDADES
# ============================================================================

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from typing import Optional, List, Dict, Any
import logging
import sys
from pathlib import Path
from datetime import datetime
import asyncio

# Agregar directorio raíz al path
sys.path.insert(0, str(Path(__file__).parent.parent))

# ============================================================================
# CONFIGURAR LOGGING
# ============================================================================
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("ARIA_BACKEND")

# ============================================================================
# CREAR APLICACIÓN FASTAPI
# ============================================================================
app = FastAPI(
    title="ARIA Real Estate API",
    description="API para scraping REAL de propiedades en Colombia",
    version="3.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# ============================================================================
# CORS
# ============================================================================
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================================================
# IMPORTAR SCRAPERS (CON MANEJO ROBUSTO DE ERRORES)
# ============================================================================
SCRAPERS = {}
SCRAPER_ERRORS = {}

try:
    from src.scrapers.fincaraiz_scraper import FincaraizScraper
    SCRAPERS['fincaraiz'] = FincaraizScraper
    logger.info("✅ Fincaraíz scraper cargado correctamente")
except Exception as e:
    SCRAPER_ERRORS['fincaraiz'] = str(e)
    logger.warning(f"⚠️ Fincaraíz scraper no disponible: {e}")

try:
    from src.scrapers.metrocuadrado_scraper import MetrocuadradoScraper
    SCRAPERS['metrocuadrado'] = MetrocuadradoScraper
    logger.info("✅ Metrocuadrado scraper cargado")
except Exception as e:
    SCRAPER_ERRORS['metrocuadrado'] = str(e)
    logger.warning(f"⚠️ Metrocuadrado scraper no disponible: {e}")

try:
    from src.scrapers.lahaus_scraper import LaHausScraper
    SCRAPERS['lahaus'] = LaHausScraper
    logger.info("✅ LaHaus scraper cargado")
except Exception as e:
    SCRAPER_ERRORS['lahaus'] = str(e)
    logger.warning(f"⚠️ LaHaus scraper no disponible: {e}")

# ============================================================================
# IMPORTAR BASE DE DATOS (OPCIONAL)
# ============================================================================
DB_AVAILABLE = False
db = None

try:
    from src.database.database import Database
    db = Database()
    DB_AVAILABLE = True
    logger.info("✅ Base de datos disponible")
except Exception as e:
    logger.warning(f"⚠️ Base de datos no disponible: {e}")
    logger.info("💡 La API funcionará sin persistencia de datos")

# ============================================================================
# EVENTOS DE CICLO DE VIDA
# ============================================================================

@app.on_event("startup")
async def startup_event():
    """Inicializar aplicación"""
    logger.info("=" * 80)
    logger.info("🚀 ARIA Backend iniciado correctamente")
    logger.info("=" * 80)
    logger.info(f"📊 Scrapers disponibles: {', '.join(SCRAPERS.keys()) or 'NINGUNO'}")
    
    if SCRAPER_ERRORS:
        logger.warning("⚠️ Scrapers con errores:")
        for portal, error in SCRAPER_ERRORS.items():
            logger.warning(f"   - {portal}: {error}")
    
    logger.info(f"💾 Base de datos: {'DISPONIBLE' if DB_AVAILABLE else 'NO DISPONIBLE'}")
    logger.info("📍 Endpoints:")
    logger.info("   - GET  /              → Info de la API")
    logger.info("   - GET  /health        → Estado del servicio")
    logger.info("   - GET  /docs          → Documentación interactiva")
    logger.info("   - GET  /scrape/todos  → Scrapear todos los portales")
    logger.info("   - GET  /scrape/{portal} → Scrapear portal específico")
    logger.info("   - GET  /scrape/fincaraiz/busqueda → BÚSQUEDA AVANZADA ⭐")
    logger.info("   - POST /api/scrape/fincaraiz/table → Múltiples páginas")
    logger.info("=" * 80)
    
    if DB_AVAILABLE and db:
        try:
            await db.init_database()
            logger.info("✅ Base de datos inicializada")
        except Exception as e:
            logger.error(f"❌ Error inicializando base de datos: {e}")

@app.on_event("shutdown")
async def shutdown_event():
    """Cerrar aplicación"""
    logger.info("👋 Cerrando ARIA Backend...")
    
    if DB_AVAILABLE and db:
        try:
            await db.close_database()
            logger.info("✅ Base de datos cerrada")
        except Exception as e:
            logger.error(f"❌ Error cerrando base de datos: {e}")

# ============================================================================
# ENDPOINTS
# ============================================================================

@app.get("/", tags=["General"])
async def root():
    """Información de la API"""
    return {
        "app": "ARIA Real Estate API",
        "version": "3.0.0",
        "status": "online",
        "scrapers_disponibles": list(SCRAPERS.keys()),
        "scrapers_con_error": list(SCRAPER_ERRORS.keys()),
        "database": "available" if DB_AVAILABLE else "unavailable",
        "timestamp": datetime.now().isoformat(),
        "endpoints": {
            "docs": "/docs",
            "health": "/health",
            "scrape_all": "/scrape/todos",
            "scrape_fincaraiz": "/scrape/fincaraiz?limit=10&negocio=venta&ciudad=bucaramanga",
            "busqueda_avanzada": "/scrape/fincaraiz/busqueda?tipo_propiedad=apartamento&ciudad=bucaramanga&habitaciones=3",
            "scrape_metrocuadrado": "/scrape/metrocuadrado",
            "scrape_lahaus": "/scrape/lahaus"
        }
    }

@app.get("/health", tags=["General"])
async def health_check():
    """Estado del servicio"""
    return {
        "status": "healthy",
        "scrapers_activos": list(SCRAPERS.keys()),
        "scrapers_inactivos": list(SCRAPER_ERRORS.keys()),
        "errores": SCRAPER_ERRORS if SCRAPER_ERRORS else None,
        "database": DB_AVAILABLE,
        "timestamp": datetime.now().isoformat()
    }

@app.get("/scrape/todos", tags=["Scraping"])
async def scrape_all(
    limit: int = Query(10, ge=1, le=100, description="Propiedades por portal"),
    negocio: str = Query("venta", regex="^(venta|arriendo)$"),
    ciudad: str = Query("bucaramanga", description="Ciudad")
):
    """Scrapear todos los portales disponibles"""
    logger.info(f"🔍 Scraping TODOS los portales: ciudad={ciudad}, negocio={negocio}, limit={limit}")
    
    if not SCRAPERS:
        raise HTTPException(
            status_code=503,
            detail={
                "error": "No hay scrapers disponibles",
                "errores": SCRAPER_ERRORS
            }
        )
    
    all_properties = []
    results = {}
    
    for portal_name, ScraperClass in SCRAPERS.items():
        try:
            logger.info(f"🏠 Iniciando scraping de {portal_name.upper()}...")
            
            scraper = ScraperClass()
            properties = await scraper.scrape(limit=limit, negocio=negocio, ciudad=ciudad)
            
            all_properties.extend(properties)
            results[portal_name] = {
                "total": len(properties),
                "status": "success"
            }
            logger.info(f"✅ {portal_name.upper()}: {len(properties)} propiedades extraídas")
            
        except Exception as e:
            results[portal_name] = {
                "total": 0,
                "status": "error",
                "error": str(e)
            }
            logger.error(f"❌ {portal_name.upper()}: {e}", exc_info=True)
    
    if DB_AVAILABLE and db and all_properties:
        try:
            await db.save_properties(all_properties)
            logger.info(f"💾 {len(all_properties)} propiedades guardadas en BD")
        except Exception as e:
            logger.error(f"❌ Error guardando en BD: {e}")
    
    return {
        "success": True,
        "total": len(all_properties),
        "portales": results,
        "propiedades": all_properties,
        "timestamp": datetime.now().isoformat()
    }

@app.get("/scrape/{portal}", tags=["Scraping"])
async def scrape_portal(
    portal: str,
    limit: int = Query(10, ge=1, le=100, description="Número de propiedades"),
    negocio: str = Query("venta", regex="^(venta|arriendo)$", description="venta o arriendo"),
    ciudad: str = Query("bucaramanga", description="Ciudad a buscar"),
    tipo_propiedad: str = Query("apartamento", description="Tipo de propiedad"),
    habitaciones: Optional[int] = Query(None, ge=1, le=10, description="Número de habitaciones")
):
    """Scrapear un portal específico"""
    portal_lower = portal.lower()
    
    logger.info(f"🏠 Scraping {portal_lower.upper()}: ciudad={ciudad}, negocio={negocio}, limit={limit}")
    
    if portal_lower not in SCRAPERS:
        available = ', '.join(SCRAPERS.keys()) if SCRAPERS else 'ninguno'
        raise HTTPException(
            status_code=400,
            detail=f"Portal '{portal}' no disponible. Disponibles: {available}"
        )
    
    try:
        ScraperClass = SCRAPERS[portal_lower]
        scraper = ScraperClass()
        
        # Ejecutar scraping con parámetros adicionales
        properties = await scraper.scrape(
            limit=limit, 
            negocio=negocio, 
            ciudad=ciudad,
            tipo_propiedad=tipo_propiedad,
            habitaciones=habitaciones
        )
        
        logger.info(f"✅ {portal_lower.upper()}: {len(properties)} propiedades extraídas")
        
        if DB_AVAILABLE and db and properties:
            try:
                await db.save_properties(properties)
                logger.info(f"💾 {len(properties)} propiedades guardadas en BD")
            except Exception as e:
                logger.error(f"❌ Error guardando en BD: {e}")
        
        return {
            "success": True,
            "portal": portal_lower,
            "ciudad": ciudad,
            "negocio": negocio,
            "total": len(properties),
            "propiedades": properties,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"❌ Error en scraping de {portal}: {e}", exc_info=True)
        raise HTTPException(
            status_code=500, 
            detail={
                "error": f"Error en scraping de {portal}",
                "detalle": str(e)
            }
        )

# ============================================================================
# 🤖 ENDPOINT DE IA: ARIA ASISTENTE INTELIGENTE
# ============================================================================

@app.post("/api/aria/search", tags=["ARIA IA"])
async def aria_search(request: Dict[str, Any]):
    """
    🤖 ARIA - Búsqueda con Inteligencia Artificial
    
    Procesa lenguaje natural y retorna propiedades
    
    Body JSON:
    {
        "query": "apartamento en Cabecera con 3 habitaciones",
        "limit": 20
    }
    
    Ejemplos de queries:
    - "apartamento en Cabecera con 3 habitaciones"
    - "casa para comprar en Bucaramanga"
    - "arriendo apartaestudio en Provenza"
    - "busco casa hasta 400 millones"
    """
    try:
        query = request.get('query', '').strip()
        limit = request.get('limit', 20)
        
        if not query:
            raise HTTPException(
                status_code=400,
                detail="Por favor proporciona una consulta en 'query'"
            )
        
        logger.info(f"🤖 ARIA recibió: '{query}'")
        
        # Importar motor de IA
        from src.ai.aria_intelligence import buscar_con_ia
        
        # Procesar con IA
        resultado = await buscar_con_ia(query, limit)
        
        return {
            **resultado,
            "timestamp": datetime.now().isoformat()
        }
    
    except Exception as e:
        logger.error(f"❌ Error en ARIA: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail={
                "error": "Error procesando tu búsqueda",
                "detalle": str(e),
                "mensaje_aria": "Lo siento, tuve un problema. ¿Podrías intentar de otra forma?"
            }
        )

# ============================================================================
# 🔥 NUEVO ENDPOINT: BÚSQUEDA AVANZADA
# ============================================================================

@app.get("/scrape/fincaraiz/busqueda", tags=["Scraping"])
async def busqueda_avanzada_fincaraiz(
    # Parámetros del formulario de búsqueda
    tipo_propiedad: str = Query("todos", description="Tipo de propiedad o 'todos'"),
    ciudad: str = Query("todas", description="Ciudad o 'todas'"),
    habitaciones: str = Query("cualquiera", description="Número de habitaciones o 'cualquiera'"),
    barrio: Optional[str] = Query(None, description="Barrio/zona específica"),
    negocio: str = Query("comprar", description="comprar, arrendar o proyectos"),
    precio_min: Optional[int] = Query(None, description="Precio mínimo"),
    precio_max: Optional[int] = Query(None, description="Precio máximo"),
    area_min: Optional[int] = Query(None, description="Área mínima en m²"),
    limit: int = Query(20, ge=1, le=100, description="Límite de resultados")
):
    """
    🔍 BÚSQUEDA AVANZADA - Replica el formulario del frontend
    
    Parámetros:
    - tipo_propiedad: "todos", "apartamento", "casa", "apartaestudio", etc.
    - ciudad: "todas", "bucaramanga", "bogota", "medellin", "cali"
    - habitaciones: "cualquiera", "1", "2", "3", "4", "5+"
    - barrio: Texto libre para filtrar por barrio/zona
    - negocio: "comprar" (venta), "arrendar" (arriendo) o "proyectos"
    - precio_min/max: Rango de precios
    - area_min: Área mínima en m²
    - limit: Máximo de resultados
    
    Ejemplo:
    /scrape/fincaraiz/busqueda?tipo_propiedad=apartamento&ciudad=bucaramanga&habitaciones=3&limit=10
    """
    try:
        logger.info("=" * 80)
        logger.info("🔍 BÚSQUEDA AVANZADA FINCARAIZ")
        logger.info(f"   Tipo: {tipo_propiedad} | Ciudad: {ciudad} | Hab: {habitaciones}")
        if barrio:
            logger.info(f"   Barrio: {barrio}")
        logger.info("=" * 80)
        
        if 'fincaraiz' not in SCRAPERS:
            raise HTTPException(
                status_code=503,
                detail="Scraper de Fincaraíz no disponible"
            )
        
        # Mapear negocio
        negocio_map = {
            "comprar": "venta",
            "arrendar": "arriendo",
            "proyectos": "venta"
        }
        negocio_real = negocio_map.get(negocio.lower(), "venta")
        
        # Ciudades a scrapear
        ciudades_a_scrapear = []
        if ciudad.lower() == "todas":
            ciudades_a_scrapear = ["bucaramanga", "bogota", "medellin", "cali"]
        else:
            ciudades_a_scrapear = [ciudad.lower()]
        
        # Tipos de propiedad
        tipos_a_scrapear = []
        if tipo_propiedad.lower() == "todos":
            tipos_a_scrapear = ["apartamento", "casa"]
        else:
            tipos_a_scrapear = [tipo_propiedad.lower()]
        
        # Parsear habitaciones
        hab_num = None
        if habitaciones and habitaciones.lower() != "cualquiera":
            try:
                if habitaciones.endswith('+'):
                    hab_num = int(habitaciones[:-1])
                else:
                    hab_num = int(habitaciones)
            except:
                pass
        
        # Scraping
        ScraperClass = SCRAPERS['fincaraiz']
        todas_propiedades = []
        
        total_combinaciones = len(ciudades_a_scrapear) * len(tipos_a_scrapear)
        limite_por_combinacion = max(5, limit // total_combinaciones)
        
        for ciudad_item in ciudades_a_scrapear:
            for tipo_item in tipos_a_scrapear:
                try:
                    logger.info(f"   🔍 Scraping: {ciudad_item} - {tipo_item}")
                    
                    scraper = ScraperClass()
                    props = await scraper.scrape(
                        limit=limite_por_combinacion,
                        negocio=negocio_real,
                        ciudad=ciudad_item,
                        tipo_propiedad=tipo_item,
                        habitaciones=hab_num
                    )
                    
                    todas_propiedades.extend(props)
                    logger.info(f"      ✅ {len(props)} propiedades")
                    
                except Exception as e:
                    logger.error(f"      ❌ Error: {e}")
                    continue
        
        # Filtros post-scraping
        propiedades_filtradas = todas_propiedades
        
        # Filtrar por barrio
        if barrio:
            barrio_lower = barrio.lower()
            propiedades_filtradas = [
                p for p in propiedades_filtradas
                if barrio_lower in p.get('ubicacion', '').lower() or 
                   barrio_lower in p.get('titulo', '').lower()
            ]
        
        # Filtrar por precio
        if precio_min:
            propiedades_filtradas = [p for p in propiedades_filtradas if p.get('precio', 0) >= precio_min]
        
        if precio_max:
            propiedades_filtradas = [p for p in propiedades_filtradas if p.get('precio', 0) <= precio_max]
        
        # Filtrar por área
        if area_min:
            propiedades_filtradas = [p for p in propiedades_filtradas if p.get('area_m2', 0) >= area_min]
        
        # Filtrar por habitaciones "4+"
        if habitaciones and habitaciones.endswith('+'):
            hab_min = int(habitaciones[:-1])
            propiedades_filtradas = [p for p in propiedades_filtradas if p.get('habitaciones', 0) >= hab_min]
        
        # Limitar resultados
        propiedades_filtradas = propiedades_filtradas[:limit]
        
        logger.info(f"✅ BÚSQUEDA COMPLETADA: {len(propiedades_filtradas)} resultados")
        logger.info("=" * 80)
        
        return {
            "success": True,
            "count": len(propiedades_filtradas),
            "propiedades": propiedades_filtradas,
            "filtros_aplicados": {
                "tipo_propiedad": tipo_propiedad,
                "ciudad": ciudad,
                "habitaciones": habitaciones,
                "barrio": barrio,
                "negocio": negocio,
                "precio_min": precio_min,
                "precio_max": precio_max,
                "area_min": area_min
            },
            "timestamp": datetime.now().isoformat()
        }
    
    except Exception as e:
        logger.error(f"❌ Error en búsqueda: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail={
                "error": "Error en búsqueda avanzada",
                "detalle": str(e)
            }
        )

# ============================================================================
# ENDPOINTS ORIGINALES
# ============================================================================

@app.post("/api/scrape/fincaraiz/table", tags=["Scraping"])
async def scrape_fincaraiz_table(
    pages: int = Query(2, ge=1, le=10, description="Número de páginas"),
    negocio: str = Query("venta", regex="^(venta|arriendo)$")
):
    """Scrapear múltiples páginas de Fincaraíz"""
    logger.info(f"📊 Scraping Fincaraíz tabla: {pages} páginas, {negocio}")
    
    if 'fincaraiz' not in SCRAPERS:
        raise HTTPException(
            status_code=503,
            detail="Scraper de Fincaraíz no disponible"
        )
    
    try:
        total_limit = pages * 20
        
        ScraperClass = SCRAPERS['fincaraiz']
        scraper = ScraperClass()
        
        properties = await scraper.scrape(limit=total_limit, negocio=negocio, ciudad="bucaramanga")
        
        logger.info(f"✅ {len(properties)} propiedades extraídas")
        
        if DB_AVAILABLE and db and properties:
            try:
                await db.save_properties(properties)
                logger.info(f"💾 Propiedades guardadas en BD")
            except Exception as e:
                logger.error(f"❌ Error guardando en BD: {e}")
        
        return {
            "success": True,
            "portal": "fincaraiz",
            "pages": pages,
            "negocio": negocio,
            "total": len(properties),
            "propiedades": properties,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"❌ Error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/propiedades", tags=["Database"])
async def get_properties_from_db(
    portal: Optional[str] = Query(None, description="Filtrar por portal"),
    negocio: Optional[str] = Query(None, regex="^(venta|arriendo)$"),
    ciudad: Optional[str] = Query(None, description="Filtrar por ciudad"),
    tipo: Optional[str] = Query(None, description="Tipo de propiedad"),
    precio_min: Optional[int] = Query(None, ge=0, description="Precio mínimo"),
    precio_max: Optional[int] = Query(None, ge=0, description="Precio máximo"),
    habitaciones: Optional[int] = Query(None, ge=1, le=10),
    limit: int = Query(50, ge=1, le=500, description="Número máximo de resultados")
):
    """Obtener propiedades de la base de datos con filtros"""
    
    if not DB_AVAILABLE or not db:
        raise HTTPException(
            status_code=503,
            detail="Base de datos no disponible. La API funciona solo con scraping directo."
        )
    
    try:
        filters = {
            "portal": portal,
            "negocio": negocio,
            "ciudad": ciudad,
            "tipo": tipo,
            "precio_min": precio_min,
            "precio_max": precio_max,
            "habitaciones": habitaciones,
            "limit": limit
        }
        
        filters = {k: v for k, v in filters.items() if v is not None}
        
        properties = await db.search_properties(filters)
        
        return {
            "success": True,
            "filtros_aplicados": filters,
            "total": len(properties),
            "propiedades": properties,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"❌ Error consultando BD: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

# ============================================================================
# MANEJADORES DE ERRORES
# ============================================================================

@app.exception_handler(404)
async def not_found(request, exc):
    return JSONResponse(
        status_code=404,
        content={
            "error": "Endpoint no encontrado",
            "path": str(request.url.path),
            "method": request.method,
            "endpoints_disponibles": [
                "GET /",
                "GET /health",
                "GET /docs",
                "GET /scrape/todos",
                "GET /scrape/{portal}",
                "GET /scrape/fincaraiz/busqueda",
                "POST /api/scrape/fincaraiz/table",
                "GET /api/propiedades"
            ],
            "ejemplo": "GET /scrape/fincaraiz/busqueda?tipo_propiedad=apartamento&ciudad=bucaramanga&habitaciones=3"
        }
    )

@app.exception_handler(500)
async def internal_error(request, exc):
    logger.error(f"Error 500: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "error": "Error interno del servidor",
            "detalle": str(exc),
            "timestamp": datetime.now().isoformat()
        }
    )

# ============================================================================
# PUNTO DE ENTRADA
# ============================================================================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "src.main:app",
        host="127.0.0.1",
        port=8000,
        reload=True,
        log_level="info"
    )