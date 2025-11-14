# ============================================================================
# src/main.py - FASTAPI BACKEND PARA SCRAPING INMOBILIARIO
# ============================================================================

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from typing import Optional, List
import logging
from datetime import datetime
import importlib

# ============================================================================
# CONFIGURAR LOGGING
# ============================================================================
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("ARIA_BACKEND")

# ============================================================================
# DEFINICIÓN DE MÓDULOS DE SCRAPERS
# ============================================================================
SCRAPER_MODULES = {
    "fincaraiz": "src.scrapers.fincaraiz_adapter",
    "metrocuadrado": "src.scrapers.metrocuadrado_adapter",
    "lahaus": "src.scrapers.lahaus_adapter",
}

SCRAPERS = {}
USE_DEMO = False

# ============================================================================
# CARGA DINÁMICA DE SCRAPERS (AUTOMÁTICO Y ROBUSTO)
# ============================================================================
for portal, module_path in SCRAPER_MODULES.items():
    try:
        module = importlib.import_module(module_path)

        if not hasattr(module, "__all__") or len(module.__all__) == 0:
            raise ValueError(f"El módulo {module_path} no define __all__ correctamente.")

        class_name = module.__all__[0]
        scraper_class = getattr(module, class_name)

        SCRAPERS[portal] = scraper_class
        logger.info(f"✅ Scraper cargado correctamente: {portal} ({class_name})")

    except Exception as e:
        logger.warning(f"⚠️ No se pudo cargar el scraper de {portal}: {e}")
        USE_DEMO = True

# Si algún scraper falló → activar modo Demo
if USE_DEMO:
    logger.warning("🔄 MODO DEMO ACTIVADO: Al menos un scraper real no se pudo cargar.")

# ============================================================================
# CREAR APLICACIÓN FASTAPI
# ============================================================================
app = FastAPI(
    title="ARIA Real Estate API",
    description="API para scraping de propiedades inmobiliarias en Colombia",
    version="2.0.0",
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
# GENERADOR DEMO (SI NO HAY SCRAPERS)
# ============================================================================
def generate_demo_properties(portal: str, limit: int, negocio: str) -> List[dict]:
    import random

    tipos = ["Apartamento", "Casa", "Finca", "Local"]
    ubicaciones = ["Cabecera", "García Rovira", "Morrorico", "Provenza", "San Pío"]

    return [
        {
            "id": f"{portal}_{i+1}",
            "portal": portal.title(),
            "tipo": random.choice(tipos),
            "titulo": f"{random.choice(tipos)} en {random.choice(ubicaciones)}",
            "precio": (
                random.randint(150_000_000, 800_000_000)
                if negocio == "venta"
                else random.randint(800_000, 3_500_000)
            ),
            "negocio": negocio,
            "area_m2": random.randint(45, 180),
            "habitaciones": random.randint(1, 4),
            "banos": random.randint(1, 3),
            "ubicacion": random.choice(ubicaciones),
            "link": f"https://{portal}.com.co/propiedad/{i+1}",
            "fecha_scraping": datetime.now().isoformat()
        }
        for i in range(limit)
    ]

# ============================================================================
# EVENTO DE INICIO
# ============================================================================
@app.on_event("startup")
async def startup_event():
    logger.info(f"🚀 ARIA Backend iniciado en modo: {'DEMOSTRACIÓN' if USE_DEMO else 'PRODUCCIÓN'}")
    logger.info(f"📍 Scrapers cargados: {list(SCRAPERS.keys())}")

# ============================================================================
# RUTAS PRINCIPALES
# ============================================================================

@app.get("/")
async def root():
    return {
        "app": "ARIA Real Estate API",
        "version": "2.0.0",
        "mode": "demo" if USE_DEMO else "production",
        "timestamp": datetime.now().isoformat(),
    }


@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "mode": "demo" if USE_DEMO else "production",
        "timestamp": datetime.now().isoformat(),
    }

# ============================================================================
# SCRAPE DE TODOS LOS PORTALES
# ============================================================================
@app.get("/scrape/todos")
async def scrape_all(
    limit: int = Query(10, ge=1, le=100),
    negocio: str = Query("venta", regex="^(venta|arriendo)$")
):
    logger.info(f"🔍 Scrapeando TODOS LOS PORTALES → negocio={negocio}, limit={limit}")

    all_props = []

    for portal in SCRAPER_MODULES.keys():

        try:
            if USE_DEMO or portal not in SCRAPERS:
                properties = generate_demo_properties(portal, limit, negocio)
            else:
                scraper = SCRAPERS[portal]()
                properties = await scraper.scrape(
                    limit=limit,
                    negocio=negocio
                )

            logger.info(f"   - {portal}: {len(properties)} propiedades extraídas.")
            all_props.extend(properties)

        except Exception as e:
            logger.error(f"❌ Error en scraper {portal}: {e}")

    return {
        "success": True,
        "total": len(all_props),
        "properties": all_props,
        "timestamp": datetime.now().isoformat(),
    }

# ============================================================================
# SCRAPE POR PORTAL
# ============================================================================
@app.get("/scrape/{portal}")
async def scrape_portal(
    portal: str,
    limit: int = 10,
    negocio: str = "venta",
    ciudad: str = "bucaramanga"
):
    portal = portal.lower()

    if portal not in SCRAPER_MODULES:
        raise HTTPException(status_code=400, detail=f"Portal inválido: {portal}")

    logger.info(f"🏠 Scrapeando {portal} → ciudad={ciudad}, negocio={negocio}")

    try:
        if USE_DEMO or portal not in SCRAPERS:
            properties = generate_demo_properties(portal, limit, negocio)
        else:
            scraper = SCRAPERS[portal]()
            properties = await scraper.scrape(
                limit=limit,
                negocio=negocio,
                ciudad=ciudad
            )

        return {
            "success": True,
            "portal": portal,
            "ciudad": ciudad,
            "negocio": negocio,
            "total": len(properties),
            "properties": properties,
        }

    except Exception as e:
        logger.error(f"❌ Error ejecutando scraper {portal}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ============================================================================
# FILTROS DEMO
# ============================================================================
@app.get("/api/properties")
async def get_properties_filter(
    portal: Optional[str] = None,
    negocio: Optional[str] = None,
    precio_min: Optional[int] = None,
    precio_max: Optional[int] = None,
    habitaciones: Optional[int] = None
):
    logger.info(f"🔍 Filtrando propiedades en MODO DEMO")

    props = generate_demo_properties("demoportal", 25, negocio or "venta")

    if precio_min:
        props = [p for p in props if p["precio"] >= precio_min]
    if precio_max:
        props = [p for p in props if p["precio"] <= precio_max]
    if habitaciones:
        props = [p for p in props if p["habitaciones"] == habitaciones]

    return {
        "success": True,
        "total": len(props),
        "filtros": {
            "portal": portal,
            "negocio": negocio,
            "precio_min": precio_min,
            "precio_max": precio_max,
            "habitaciones": habitaciones,
        },
        "properties": props,
    }

# ============================================================================
# ENDPOINT DE DEBUG PARA EL FRONTEND
# ============================================================================
@app.get("/debug/frontend")
async def debug_frontend():
    return {
        "status": "success",
        "properties": [{
            "id": "debug-1",
            "titulo": "Propiedad de prueba",
            "precio": 250000000,
            "ubicacion": "Bucaramanga",
            "area_m2": 85,
            "habitaciones": 3,
            "banos": 2,
            "portal": "fincaraiz",
            "link": "https://fincaraiz.com.co/demo",
        }],
        "total": 1,
    }

# ============================================================================
# HANDLERS DE ERRORES
# ============================================================================
@app.exception_handler(404)
async def not_found_handler(request, exc):
    return JSONResponse(
        status_code=404,
        content={"error": "Endpoint no encontrado", "path": str(request.url)},
    )


@app.exception_handler(500)
async def server_error_handler(request, exc):
    logger.error(f"Error 500: {exc}")
    return JSONResponse(
        status_code=500,
        content={"error": "Error interno del servidor", "detail": str(exc)},
    )

# ============================================================================
# PUNTO DE ENTRADA
# ============================================================================
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("src.main:app", host="127.0.0.1", port=8000, reload=True)


# Agregar estas importaciones
from database.database import db, init_database
import json

# En la inicialización de FastAPI
@app.on_event("startup")
async def startup_event():
    await init_database()
    logger.info("✅ Base de datos inicializada")

@app.on_event("shutdown") 
async def shutdown_event():
    await close_database()
    logger.info("🔌 Base de datos cerrada")

# Endpoint para guardar propiedades
@app.post("/api/properties/save")
async def save_properties(properties: List[Dict]):
    """Guardar propiedades en la base de datos"""
    try:
        stats = await db.save_properties(properties)
        
        # Log de la sesión de scraping
        await db.log_scraping_session(
            portal="multiple",
            properties_found=len(properties),
            properties_saved=stats['guardadas'] + stats['actualizadas'],
            duration=0,  # Podrías calcular esto
            status="exitoso" if stats['errores'] == 0 else "parcial",
            search_params={"source": "api_save"}
        )
        
        return {
            "status": "success",
            "message": f"Propiedades guardadas: {stats['guardadas']} nuevas, {stats['actualizadas']} actualizadas",
            "stats": stats
        }
        
    except Exception as e:
        logger.error(f"❌ Error guardando propiedades: {e}")
        return {
            "status": "error",
            "message": str(e)
        }

# Endpoint para búsqueda en base de datos
@app.get("/api/properties/search")
async def search_properties(
    ciudad: str = None,
    tipo_negocio: str = "venta",
    tipo_propiedad: str = None,
    precio_min: float = None,
    precio_max: float = None,
    habitaciones_min: int = None,
    area_min: float = None,
    portal: str = None,
    limite: int = 50,
    ordenar_por: str = "fecha_actualizacion"
):
    """Buscar propiedades en la base de datos"""
    try:
        filters = {
            'ciudad': ciudad,
            'tipo_negocio': tipo_negocio,
            'tipo_propiedad': tipo_propiedad,
            'precio_min': precio_min,
            'precio_max': precio_max,
            'habitaciones_min': habitaciones_min,
            'area_min': area_min,
            'portal': portal,
            'limite': limite,
            'ordenar_por': ordenar_por
        }
        
        # Remover filtros None
        filters = {k: v for k, v in filters.items() if v is not None}
        
        properties = await db.search_properties(filters)
        
        return {
            "status": "success",
            "total": len(properties),
            "filters": filters,
            "properties": properties
        }
        
    except Exception as e:
        logger.error(f"❌ Error buscando propiedades: {e}")
        return {
            "status": "error",
            "message": str(e)
        }

# Endpoint para estadísticas
@app.get("/api/properties/stats")
async def get_properties_stats():
    """Obtener estadísticas de propiedades"""
    try:
        stats = await db.get_property_stats()
        return {
            "status": "success",
            "stats": stats
        }
    except Exception as e:
        logger.error(f"❌ Error obteniendo estadísticas: {e}")
        return {
            "status": "error",
            "message": str(e)
        }

# Endpoint combinado: scrapear y guardar
@app.post("/api/scrape-and-save")
async def scrape_and_save(
    portal: str,
    ciudad: str = "bucaramanga",
    tipo_negocio: str = "venta",
    limite: int = 10
):
    """Scrapear propiedades y guardarlas en la base de datos"""
    try:
        # Scrapear propiedades
        if portal == "fincaraiz":
            from scrapers.fincaraiz_adapter import FincaraizScraper
            scraper = FincaraizScraper()
        elif portal == "metrocuadrado":
            from scrapers.metrocuadrado_adapter import MetrocuadradoScraper
            scraper = MetrocuadradoScraper()
        else:
            return {"status": "error", "message": f"Portal no soportado: {portal}"}
        
        propiedades = await scraper.scrape(
            limit=limite,
            negocio=tipo_negocio,
            ciudad=ciudad
        )
        
        # Guardar en base de datos
        save_stats = await db.save_properties(propiedades)
        
        return {
            "status": "success",
            "scraping": {
                "portal": portal,
                "ciudad": ciudad,
                "tipo_negocio": tipo_negocio,
                "propiedades_encontradas": len(propiedades)
            },
            "database": save_stats
        }
        
    except Exception as e:
        logger.error(f"❌ Error en scrape-and-save: {e}")
        return {
            "status": "error",
            "message": str(e)
        }