# -*- coding: utf-8 -*-
# SCRAPER FINCARAIZ BUCARAMANGA - VERSIÓN OPTIMIZADA CON IMÁGENES

import requests, json, re, time, random, pandas as pd
from requests.adapters import HTTPAdapter, Retry
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from datetime import datetime

BASE_URL = "https://www.fincaraiz.com.co"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "es-CO,es;q=0.9",
    "Referer": "https://www.fincaraiz.com.co"
}

def clean(text):
    if not text or str(text).strip() in ['', 'None', 'N/A']:
        return None
    return ' '.join(str(text).strip().split())

def create_session():
    s = requests.Session()
    retry = Retry(total=3, backoff_factor=1, status_forcelist=[429,500,502,503])
    adapter = HTTPAdapter(max_retries=retry)
    s.mount('http://', adapter)
    s.mount('https://', adapter)
    s.headers.update(HEADERS)
    return s

# --------- extracción desde tarjeta (CON IMAGEN) ----------
def extract_from_card(card):
    data = {}
    
    # Link
    link = card.find('a', href=True)
    if link:
        data['link'] = urljoin(BASE_URL, link['href'])
    
    # ========== EXTRACCIÓN DE IMAGEN DESDE TARJETA ==========
    img_url = None
    
    # Busca img en la tarjeta con varios atributos
    img_elem = (
        card.find('img', src=True) or
        card.find('img', attrs={'data-src': True}) or
        card.find('img', attrs={'data-lazy-src': True})
    )
    
    if img_elem:
        img_url = (
            img_elem.get('data-src') or 
            img_elem.get('data-lazy-src') or 
            img_elem.get('src')
        )
        
        # Normaliza URL
        if img_url:
            if img_url.startswith('//'):
                img_url = 'https:' + img_url
            elif img_url.startswith('/'):
                img_url = urljoin(BASE_URL, img_url)
            
            # Filtra placeholders y logos
            if any(skip in img_url.lower() for skip in ['logo', 'icon', 'blank', 'placeholder']):
                img_url = None
    
    # Fallback placeholder
    if not img_url:
        img_url = "https://via.placeholder.com/400x300/1a2332/6ae6ff?text=Sin+Imagen"
    
    data['image_url'] = img_url
    # ========== FIN EXTRACCIÓN IMAGEN ==========
    
    # Precio en tarjeta
    price_text = ''
    price_elem = card.select_one('[class*="price"], [class*="Price"], [class*="valor"], [data-price]')
    if price_elem:
        price_text = price_elem.get('data-price') if price_elem.has_attr('data-price') else price_elem.get_text(" ", strip=True)
    else:
        full_text = card.get_text(" ", strip=True)
        m = re.search(r'\$\s*[\d.,]+', full_text)
        price_text = m.group(0) if m else ''
    
    if price_text:
        m = re.search(r'([\d.,]+)', price_text)
        if m:
            try:
                data['precio'] = int(m.group(1).replace('.', '').replace(',', ''))
            except:
                pass
    
    # Texto para features
    full_text = ' '.join([t.get_text(" ", strip=True) for t in card.find_all(['li','span','div'])])
    full_text = re.sub(r'\s+', ' ', full_text)
    
    m = re.search(r'(\d+)\s*(?:hab|habitaciones|alcobas?)', full_text, re.I)
    if m:
        data['habitaciones'] = int(m.group(1))
    
    m = re.search(r'(\d+)\s*(?:ba[ñn]os?|baths?)', full_text, re.I)
    if m:
        data['banos'] = int(m.group(1))
    
    m = re.search(r'([\d.,]+)\s*m', full_text, re.I)
    if m:
        try:
            data['area_m2'] = float(m.group(1).replace(',', '.'))
        except:
            pass
    
    return data

# --------- extracción detallada (MANTIENE IMAGEN DE TARJETA) ----------
def extract_details(session, url, card_data):
    print(f"\n  🔗 {url[:70]}...")
    try:
        response = session.get(url, timeout=25)
        soup = BeautifulSoup(response.text, 'html.parser')
        data = {'link': url}
        
        # MANTIENE imagen de tarjeta si existe
        data['image_url'] = card_data.get('image_url') or "https://via.placeholder.com/400x300/1a2332/6ae6ff?text=Sin+Imagen"
        
        # Intenta mejorar imagen si no hay una buena
        if 'placeholder' in data['image_url'] or not data['image_url']:
            og_img = soup.select_one('meta[property="og:image"]')
            if og_img and og_img.get('content'):
                data['image_url'] = og_img['content']
        
        # Precio (JSON-LD, visible, data-price)
        price = None
        for script in soup.find_all('script', type='application/ld+json'):
            try:
                j = json.loads(script.string)
                items = [j] if isinstance(j, dict) else j
                for it in items:
                    if isinstance(it, dict):
                        off = it.get('offers')
                        if isinstance(off, dict) and off.get('price'):
                            price = int(float(off['price']))
                            break
            except:
                continue
        
        if not price:
            m = re.search(r'\$\s*([\d.,]+)', soup.get_text())
            if m:
                try:
                    v = int(m.group(1).replace('.', '').replace(',', ''))
                    if v > 1_000_000:
                        price = v
                except:
                    pass
        
        if not price:
            elem = soup.select_one('[data-price]')
            if elem and elem.has_attr('data-price'):
                try:
                    price = int(re.sub(r'[^\d]', '', elem['data-price']))
                except:
                    pass
        
        data['precio'] = price or card_data.get('precio')
        
        text = soup.get_text(" ", strip=True)
        
        # Nombre y tipo
        h1 = soup.find('h1')
        if h1:
            h1_text = h1.get_text(strip=True)
            data['nombre'] = h1_text
            tl = h1_text.lower()
            if 'apartamento' in tl:
                data['tipo'] = "Apartamento"
            elif 'casa' in tl:
                data['tipo'] = "Casa"
            elif 'finca' in tl:
                data['tipo'] = "Finca"
            else:
                data['tipo'] = "No especificado"
        
        # Hab/baños/área
        data['habitaciones'] = card_data.get('habitaciones')
        if not data['habitaciones']:
            m = re.search(r'(\d+)\s*(?:hab|habitaciones|alcobas?)', text, re.I)
            if m:
                data['habitaciones'] = int(m.group(1))
        
        data['banos'] = card_data.get('banos')
        if not data['banos']:
            m = re.search(r'(\d+)\s*(?:ba[ñn]os?|baths?)', text, re.I)
            if m:
                data['banos'] = int(m.group(1))
        
        data['area_m2'] = card_data.get('area_m2')
        if not data['area_m2']:
            m = re.search(r'([\d.,]+)\s*m', text, re.I)
            if m:
                try:
                    val = float(m.group(1).replace(',', '.'))
                    if 20 <= val <= 10000:
                        data['area_m2'] = val
                except:
                    pass
        
        # Teléfonos
        phones = set()
        for a in soup.find_all('a', href=True):
            href = a['href']
            if 'tel:' in href or 'wa.me' in href or 'whatsapp' in href.lower():
                phones.update(re.findall(r'3\d{9}', href))
        
        for elem in soup.find_all(['button','div','span','a']):
            for attr in ['data-phone','data-tel','data-number','data-contact']:
                if elem.has_attr(attr):
                    phones.update(re.findall(r'\d{7,10}', elem[attr]))
        
        nums_sep = re.findall(r'3[\d\s\-\.)]{9,}', text)
        digits = lambda s: re.sub(r'\D', '', s)
        phones.update([digits(n) for n in nums_sep])
        
        valids = [p for p in phones if len(p) == 10 and p.startswith('3')]
        data['telefonos'] = ', '.join(sorted(valids)) if valids else None
        
        # Contacto
        contact = None
        for elem in soup.find_all(['div','span','p']):
            t = elem.get_text(strip=True)
            if any(w in t.lower() for w in ['inmobiliaria','propietario','contacto','asesor','agente']):
                if 3 < len(t) < 120:
                    contact = t
                    break
        data['contacto'] = contact
        
        # Ubicación
        m = re.search(r'en\s+([^,]+),\s*\w+', text, re.I)
        if m:
            data['ubicacion'] = clean(m.group(1))
        
        # Administración
        m = re.search(r'(?:administraci[oó]n)\s*\$?\s*([\d.,]+)', text, re.I)
        if m:
            try:
                admin = int(m.group(1).replace('.', '').replace(',', ''))
                if 10_000 <= admin <= 5_000_000:
                    data['administracion'] = f"${admin:,}"
            except:
                pass
        
        # Descripción
        meta = soup.select_one('meta[property="og:description"]')
        if meta and meta.get('content'):
            data['descripcion'] = clean(meta['content'])
        
        print(f"    💰 ${data.get('precio','N/A'):,} | 📞 {data.get('telefonos','-')} | 🛏️ {data.get('habitaciones','-')} | 📷 {'✓' if data.get('image_url') and 'placeholder' not in data['image_url'] else '✗'}")
        return data
    
    except Exception as e:
        print(f"    ❌ Error: {str(e)[:80]}")
        return {
            'link': url, 
            'image_url': card_data.get('image_url') or "https://via.placeholder.com/400x300/1a2332/ff6b6b?text=Error"
        }

# --------- conversión a tarjetas ----------
def to_cards(properties):
    """Convierte propiedades a formato de tarjetas para UI"""
    cards = []
    for p in properties:
        cards.append({
            "title": p.get("nombre") or p.get("tipo") or "Propiedad",
            "price": p.get("precio"),
            "price_text": f"${int(p['precio']):,}" if p.get("precio") else "Consultar",
            "location": p.get("ubicacion") or "Bucaramanga",
            "area_m2": p.get("area_m2"),
            "bedrooms": p.get("habitaciones"),
            "bathrooms": p.get("banos"),
            "admin": p.get("administracion"),
            "phone": p.get("telefonos"),
            "contact": p.get("contacto"),
            "description": p.get("descripcion"),
            "image_url": p.get("image_url") or "https://via.placeholder.com/400x300/1a2332/6ae6ff?text=Sin+Imagen",
            "link": p.get("link")
        })
    return cards

# --------- scraping paginado ----------
def scrape_page(session, page_num, negocio="venta", ciudad="bucaramanga"):
    url = f"{BASE_URL}/{negocio}/casas-y-apartamentos/{ciudad}/santander/pagina-{page_num}"
    print(f"\n{'='*80}\nPÁGINA {page_num}\n{'='*80}\n{url}")
    resp = session.get(url, timeout=20)
    soup = BeautifulSoup(resp.text, 'html.parser')
    cards = (soup.select('article') or soup.select('[data-cy*="listing"]') or
             soup.select('[class*="Listing"]') or soup.select('[class*="result"]'))
    print(f"\n✓ {len(cards)} propiedades encontradas\n")
    if not cards:
        with open(f'dump_page_{page_num}.html','w',encoding='utf-8') as f:
            f.write(resp.text)
    
    props = []
    for idx, card in enumerate(cards, 1):
        print(f"[{idx}/{len(cards)}]")
        card_data = extract_from_card(card)
        if not card_data.get('link'):
            print("  ⚠️ Sin link")
            continue
        full_data = extract_details(session, card_data['link'], card_data)
        if full_data.get('precio') or full_data.get('area_m2'):
            props.append(full_data)
            print("  ✅ GUARDADA")
        else:
            print("  ⚠️ Omitida (sin datos)")
        time.sleep(random.uniform(1.5,2.5))  # ← Reducido para más rapidez
    return props

def scrape_fincaraiz(num_pages=10, negocio="venta", ciudad="bucaramanga",  # ← Aumentado a 10 por defecto
                     min_price=None, max_price=None,
                     min_area=None, max_area=None, min_rooms=None, max_rooms=None):
    """Scraper principal con soporte de ciudad"""
    print(f"\n🏠 SCRAPER FINCARAIZ - {negocio.upper()} en {ciudad.upper()}\n⏰ {datetime.now().strftime('%H:%M:%S')}\n")
    session = create_session()
    all_props = []
    
    for page in range(1, num_pages+1):
        props = scrape_page(session, page, negocio, ciudad)
        if not props:
            break
        all_props.extend(props)
        print(f"\n📊 TOTAL ACUMULADO: {len(all_props)} propiedades\n")
        if page < num_pages:
            time.sleep(random.uniform(2,3))  # ← Reducido
    
    # Filtros en memoria
    if min_price:
        all_props = [p for p in all_props if p.get('precio') and p['precio'] >= min_price]
    if max_price:
        all_props = [p for p in all_props if p.get('precio') and p['precio'] <= max_price]
    if min_area:
        all_props = [p for p in all_props if p.get('area_m2') and p['area_m2'] >= min_area]
    if max_area:
        all_props = [p for p in all_props if p.get('area_m2') and p['area_m2'] <= max_area]
    if min_rooms:
        all_props = [p for p in all_props if p.get('habitaciones') and p['habitaciones'] >= min_rooms]
    if max_rooms:
        all_props = [p for p in all_props if p.get('habitaciones') and p['habitaciones'] <= max_rooms]
    
    return all_props

# --------- tabla final ----------
def create_table(properties):
    """Convierte lista de propiedades a DataFrame de pandas"""
    if not properties:
        return pd.DataFrame()
    
    df = pd.DataFrame(properties).drop_duplicates(subset=['link'], keep='first')
    
    # Formatear precio
    df['precio_fmt'] = df['precio'].apply(
        lambda x: f"${int(x):,}" if pd.notna(x) and x else "Consultar"
    )
    
    # Seleccionar y ordenar columnas
    cols = ['link', 'nombre', 'tipo', 'ubicacion', 'area_m2', 'habitaciones', 'banos',
            'precio_fmt', 'administracion', 'telefonos', 'contacto', 'descripcion', 'image_url']
    df = df[[c for c in cols if c in df.columns]]
    
    # Renombrar columnas para UI
    df = df.rename(columns={
        'link': 'Link',
        'nombre': 'Nombre',
        'tipo': 'Tipo',
        'ubicacion': 'Ubicación',
        'area_m2': 'Área (m²)',
        'habitaciones': 'Habitaciones',
        'banos': 'Baños',
        'precio_fmt': 'Precio',
        'administracion': 'Administración',
        'telefonos': 'Teléfonos',
        'contacto': 'Contacto',
        'descripcion': 'Descripción',
        'image_url': 'Imagen'
    }).fillna('')
    
    return df

# --------- ejecución directa ----------
if __name__ == "__main__":
    NUM_PAGINAS = 10  # ← Aumentado
    props = scrape_fincaraiz(num_pages=NUM_PAGINAS, negocio="venta")
    df = create_table(props)
    if not df.empty:
        pd.set_option('display.max_columns', None)
        pd.set_option('display.width', None)
        print(f"\n📊 TABLA ({len(df)} registros)\n")
        print(df.head(20).to_string(index=False))
    else:
        print("\n❌ No se extrajeron propiedades")
