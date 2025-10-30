# -*- coding: utf-8 -*-
# SCRAPER FINCARAIZ BUCARAMANGA - API REST COMPLETA

from fastapi import FastAPI, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import httpx
from bs4 import BeautifulSoup
from datetime import datetime
import re
import asyncio
import random
from urllib.parse import urljoin
from fastapi import Body

app = FastAPI(
    title="Real Estate Scraper API Colombia",
    description="API para scraping de propiedades inmobiliarias",
    version="3.1.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://localhost:3000",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

BASE_URL = "https://www.fincaraiz.com.co"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "es-CO,es;q=0.9,en;q=0.8",
    "Referer": "https://www.fincaraiz.com.co"
}

class PropertyCard(BaseModel):
    title: str
    price: Optional[int] = None
    price_text: str = "Consultar"
    location: Optional[str] = "Bucaramanga"
    area_m2: Optional[str] = None
    bedrooms: Optional[int] = None
    bathrooms: Optional[int] = None
    admin: Optional[str] = None
    description: Optional[str] = None
    phone: Optional[str] = None
    contact: Optional[str] = None
    link: Optional[str] = None
    image_url: Optional[str] = None
    images: List[str] = []
    original_url: Optional[str] = None

class PropertyResponse(BaseModel):
    cards: List[PropertyCard]
    total: int

def clean(text):
    if not text or str(text).strip() in ['', 'None', 'N/A']:
        return None
    return ' '.join(str(text).strip().split())

def extract_from_card(card):
    """Extrae datos básicos de una tarjeta de propiedad (versión robusta)"""
    data = {}

    # ---------- LINK ----------
    # Link robusto
    link_tag = (
        card.select_one('a[href*="/inmueble/"]') or
        card.select_one('a[href*="/propiedad/"]') or
        card.find('a', href=True)
    )
    href = link_tag['href'] if link_tag and link_tag.has_attr('href') else None
    if href:
        if href.startswith('//'): href = 'https:' + href
        elif href.startswith('/'): href = urljoin(BASE_URL, href)
        if data.get('link') or data.get('image_url'):
            props.append(data)
        if '/inmueble/' in href or '/propiedad/' in href:
            data['link'] = href
            


    href = link_tag['href'] if link_tag and link_tag.has_attr('href') else None
    if href:
        href = href.strip()
        # Normalizar relativos
        if href.startswith('//'):
            href = 'https:' + href
        elif href.startswith('/'):
            href = urljoin(BASE_URL, href)

        # Filtrar enlaces de navegación conocidos, pero permitir trailing slash
        bad_parts = ['/pagina-', '/santander/pagina', '/contacto', '/favoritos', '/comparar']
        is_bad = any(bp in href for bp in bad_parts) or href.rstrip('/') in (BASE_URL, f"{BASE_URL}")
        if (not is_bad) and len(href) > 20:
            data['link'] = href
        # Debug opcional:
        # print("  → link extraído:", href)

    # ---------- IMAGEN ----------
    img = card.find('img')
    img_url = None
    if img:
        img_url = img.get('data-src') or img.get('data-lazy-src') or img.get('data-original') or img.get('src')
        if img_url:
            if img_url.startswith('//'):
                img_url = 'https:' + img_url
            elif img_url.startswith('/'):
                img_url = urljoin(BASE_URL, img_url)
            if any(x in img_url.lower() for x in ['logo', 'icon', '1x1', 'placeholder']):
                img_url = None
    data['image_url'] = img_url or "https://via.placeholder.com/800x600/1a2332/6ae6ff?text=Propiedad"

    # ---------- PRECIO ----------
    text_card = card.get_text(" ", strip=True)
    price_elem = (card.select_one('[data-price]') or
                  card.select_one('[class*="price"]') or
                  card.select_one('[class*="valor"]'))
    price_text = ''
    if price_elem:
        price_text = price_elem.get('data-price', '') or price_elem.get_text(" ", strip=True)
    else:
        m = re.search(r'\$\s*([\d.,]+)', text_card)
        price_text = m.group(0) if m else ''

    if price_text:
        try:
            val = re.sub(r'[^\d]', '', price_text)
            if val:
                data['precio'] = int(val)
                data['precio_texto'] = f"${int(val):,}"
        except:
            data['precio_texto'] = "Consultar"

    # ---------- FEATURES ----------
    low = text_card.lower()
    m = re.search(r'(\d+)\s*(?:hab|habitaciones|alcobas|cuartos)', low)
    if m:
        data['habitaciones'] = int(m.group(1))
    m = re.search(r'(\d+)\s*(?:ba[ñn]os?|bathrooms?)', low)
    if m:
        data['banos'] = int(m.group(1))
    m = re.search(r'([\d.,]+)\s*m[²2]?', low)
    if m:
        try:
            area = float(m.group(1).replace(',', '.'))
            if 15 <= area <= 10000:
                data['area_m2'] = str(int(area))
        except:
            pass

    # IMPORTANTE: return SIEMPRE al final de la función (sin indentación extra)
    return data


async def extract_details(client, url, card_data):
    try:
        r = await client.get(url, timeout=20.0)
        s = BeautifulSoup(r.text, 'html.parser')
        data = {'link': url}

        # Imagen destacada
        data['image_url'] = card_data.get('image_url')
        og = s.select_one('meta[property="og:image"]')
        if og and og.get('content'):
            data['image_url'] = og['content']

        # Galería
        images = []
        for img in s.find_all('img', src=True):
            src = img.get('src') or img.get('data-src')
            if not src: continue
            if any(x in src.lower() for x in ['logo', 'icon', 'placeholder']): continue
            if src.startswith('//'): src = 'https:' + src
            if src.startswith('/'): src = urljoin(BASE_URL, src)
            if src not in images: images.append(src)
        data['images'] = images[:12]

        # Título y ubicación
        h1 = s.find('h1')
        data['nombre'] = h1.get_text(strip=True) if h1 else "Propiedad en Bucaramanga"
        data['ubicacion'] = "Bucaramanga, Santander"
        txt = s.get_text(" ", strip=True)
        m = re.search(r'en\s+([^,]+),\s*\w+', txt, re.I)
        if m: data['ubicacion'] = clean(m.group(1)) or data['ubicacion']

        # Reusar datos de la card
        data['precio'] = card_data.get('precio')
        data['precio_texto'] = card_data.get('precio_texto', 'Consultar')
        data['habitaciones'] = card_data.get('habitaciones')
        data['banos'] = card_data.get('banos')
        data['area_m2'] = card_data.get('area_m2')

        # Teléfonos simples
        phones = re.findall(r'3\d{9}', r.text)
        data['telefonos'] = ', '.join(sorted(set(phones))[:3]) if phones else None

        # Descripción
        desc = s.select_one('meta[property="og:description"]')
        if desc and desc.get('content'):
            data['descripcion'] = clean(desc['content'])[:300]

        return data

    except Exception:
        return {
            'link': url,
            'nombre': 'Propiedad en Bucaramanga',
            'image_url': card_data.get('image_url'),
            'images': [card_data.get('image_url')] if card_data.get('image_url') else [],
            'precio': card_data.get('precio'),
            'precio_texto': card_data.get('precio_texto', 'Consultar'),
            'habitaciones': card_data.get('habitaciones'),
            'banos': card_data.get('banos'),
            'area_m2': card_data.get('area_m2'),
            'ubicacion': 'Bucaramanga, Santander'
        }

def build_listing_urls(negocio: str, ciudad: str, page: int) -> List[str]:
    # Variantes de URL que FincaRaíz usa según categoría/SEO
    return [
        f"{BASE_URL}/{negocio}/casas-y-apartamentos/{ciudad}/santander/pagina-{page}",
        f"{BASE_URL}/{negocio}/casas/{ciudad}/santander/pagina-{page}",
        f"{BASE_URL}/{negocio}/apartamentos/{ciudad}/santander/pagina-{page}",
    ]

async def scrape_page(client, page_num, negocio="venta", ciudad="bucaramanga"):
    urls = build_listing_urls(negocio, ciudad, page_num)
    print(f"\n📄 Página {page_num}: probando {len(urls)} variantes")
    all_cards = []

    # Probar variantes hasta obtener resultados
    for url in urls:
        try:
            r = await client.get(url, timeout=30.0)
            s = BeautifulSoup(r.text, 'html.parser')
            cards = []

            # 1. El selector más robusto de FincaRaiz en 2024/2025:
            cards.extend(s.select('[data-cy="property-list-item"]'))   # NUEVO, muy importante

            # 2. Compatibilidad con versiones previas:
            cards.extend(s.select('article'))
            cards.extend(s.select('[data-cy*="listing"]'))
            cards.extend(s.select('[class*="Listing"]'))
            cards.extend(s.select('[class*="PropertyCard"]'))
            cards.extend(s.select('[class*="property-card"]'))
            cards.extend(s.select('.MuiCard-root'))
            cards.extend(s.select('[class*="result"]'))

            # 3. Fallback: buscar por enlaces a fichas reales (ruta /inmueble/ o /propiedad/)
            for a in s.find_all('a', href=True):
                if '/inmueble/' in a['href'] or '/propiedad/' in a['href']:
                    parent = a.find_parent(['div', 'article', 'li'])
                    if parent and parent not in cards:
                        cards.append(parent)

            # 4. Eliminación de duplicados conservando el orden
            cards = list({id(c): c for c in cards if c}.values())

            if cards:
                all_cards = cards
                print(f"  ✅ {len(cards)} cards desde {url}")
                break

        except Exception as e:
            print(f"  ⚠️ Error cargando {url}: {e}")

    if not all_cards:
        print("  ⚠️ Sin resultados en esta página")
        return []

    # Deduplicar
    seen, unique = set(), []
    for c in all_cards:
        if id(c) not in seen:
            seen.add(id(c))
            unique.append(c)
    cards = unique

    props = []
    for idx, card in enumerate(cards, 1):
        if idx % 6 == 0:
            print(f"  🔄 Procesadas {idx}/{len(cards)} cards...")
        card_data = extract_from_card(card)
        link = card_data.get('link', '')
        # Filtro de link más permisivo
        if not link or link.startswith('javascript:') or link.startswith('mailto:'):
            continue
        if link.rstrip('/') in (BASE_URL, f"{BASE_URL}"):
            continue
        if re.search(r'/pagina-\d+/?$', link):
            continue
        try:
            detail = await asyncio.wait_for(extract_details(client, link, card_data), timeout=20.0)
            if any(detail.get(k) for k in ['precio','area_m2','habitaciones','nombre']):
                props.append(detail)
        except asyncio.TimeoutError:
            # Fallback a datos de la card
            props.append({
                'link': link,
                'nombre': 'Propiedad en Bucaramanga',
                'precio': card_data.get('precio'),
                'precio_texto': card_data.get('precio_texto', 'Consultar'),
                'image_url': card_data.get('image_url'),
                'images': [card_data.get('image_url')] if card_data.get('image_url') else [],
                'habitaciones': card_data.get('habitaciones'),
                'banos': card_data.get('banos'),
                'area_m2': card_data.get('area_m2'),
                'ubicacion': 'Bucaramanga, Santander'
            })
        await asyncio.sleep(random.uniform(0.2, 0.5))

    print(f"  ✅ Propiedades extraídas en p{page_num}: {len(props)}")
    return props

def to_card_format(p):
    return PropertyCard(
        title=p.get("nombre") or "Propiedad en Bucaramanga",
        price=p.get("precio"),
        price_text=p.get("precio_texto","Consultar"),
        location=p.get("ubicacion") or "Bucaramanga, Santander",
        area_m2=str(p.get("area_m2")) if p.get("area_m2") else None,
        bedrooms=p.get("habitaciones"),
        bathrooms=p.get("banos"),
        phone=p.get("telefonos"),
        description=p.get("descripcion"),
        image_url=p.get("image_url") or "https://via.placeholder.com/800x600/1a2332/6ae6ff?text=Sin+Imagen",
        images=p.get("images", [p.get("image_url")]) if p.get("image_url") else p.get("images", []),
        link=p.get("link"),
        original_url=p.get("link")
    )

@app.get("/")
def read_root():
    return {
        "message": "🏡 Real Estate Scraper API - Colombia 2025",
        "status": "online",
        "version": "3.1.0",
        "endpoints": {
            "scrape": "GET /scrape/fincaraiz?limit=50&negocio=venta&ciudad=bucaramanga",
            "docs": "GET /docs"
        }
    }

@app.get("/health")
def health_check():
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

@app.post("/api/scrape/fincaraiz/cards", response_model=PropertyResponse)
async def run_cards(
    pages: int = Body(10, embed=True),          # Número de páginas a scrapear (default 10)
    limit: int = Body(100, embed=True),          # Máximo de propiedades a retornar
    negocio: str = Body("arriendo", embed=True), # 'venta' o 'arriendo'
    ciudad: str = Body("bucaramanga", embed=True)
):
    """
    Retorna tarjetas de propiedades de FincaRaiz en formato PropertyCard, usando scraping y configurando cuántas páginas quieres.
    """
    all_props = []
    try:
        async with httpx.AsyncClient(
            headers=HEADERS, timeout=60.0, follow_redirects=True,
            limits=httpx.Limits(max_keepalive_connections=6, max_connections=12)
        ) as client:
            for page in range(1, pages + 1):
                props = await scrape_page(client, page, negocio, ciudad)
                all_props.extend(props)
                if len(all_props) >= limit:
                    break
                if not props and page > 1:
                    break
                await asyncio.sleep(random.uniform(1.2, 2.0))

        # Formatear como tarjetas y limitar
        cards = [to_card_format(p) for p in all_props[:limit]]
        return PropertyResponse(cards=cards, total=len(cards))

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error en scrapeo: {str(e)}")

@app.get("/scrape/fincaraiz", response_model=PropertyResponse)
async def scrape_fincaraiz_endpoint(
    limit: int = Query(50, ge=1, le=120, description="Número de propiedades"),
    negocio: str = Query("venta", pattern="^(venta|arriendo)$", description="venta o arriendo"),
    ciudad: str = Query("bucaramanga", description="Ciudad")
):
    print(f"\n{'='*80}")
    print(f"🚀 SCRAPING: {negocio.upper()} en {ciudad.upper()} | Límite {limit}")
    print(f"{'='*80}\n")

    all_props = []
    # Páginas estimadas a 18 props/página
    pages_to_scrape = min(12, max(1, (limit + 17) // 18))

    try:
        async with httpx.AsyncClient(
            headers=HEADERS, timeout=60.0, follow_redirects=True,
            limits=httpx.Limits(max_keepalive_connections=6, max_connections=12)
        ) as client:
            for page in range(1, pages_to_scrape + 1):
                props = await scrape_page(client, page, negocio, ciudad)
                all_props.extend(props)
                print(f"📊 Acumuladas: {len(all_props)} / {limit}")
                if len(all_props) >= limit:
                    break
                if not props and page > 1:
                    break
                await asyncio.sleep(random.uniform(1.2, 2.0))

        cards = [to_card_format(p) for p in all_props[:limit]]
        print(f"\n✅ Total entregadas: {len(cards)}\n")
        return PropertyResponse(cards=cards, total=len(cards))

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error de scraping: {str(e)}")
    

