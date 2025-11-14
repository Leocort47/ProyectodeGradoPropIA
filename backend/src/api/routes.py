# src/api/routes.py
from fastapi import APIRouter, Query

router = APIRouter(prefix="/api")

@router.post("/scrape/fincaraiz/table")
def scrape_finca_table(pages: int = Query(1, ge=1), negocio: str = Query("venta")):
    return {"ok": True, "pages": pages, "negocio": negocio}
