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
