# backend/src/scrapers/fincaraiz_scraper.py
"""
Scraper ACTUALIZADO para Fincaraíz Colombia (correcciones).
Clase: FincaraizScraper (no cambiar nombre).
Interfaz pública: async def scrape(limit, negocio, ciudad) -> List[dict]
"""

from typing import List, Dict, Optional, Any
import requests
import re
import json
import time
import random
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from datetime import datetime
import logging
import asyncio
from concurrent.futures import ThreadPoolExecutor

logger = logging.getLogger("ARIA_BACKEND")
logger.setLevel(logging.INFO)

__all__ = ["FincaraizScraper"]


class FincaraizScraper:
    def __init__(self, *, session: Optional[requests.Session] = None):
        self.base_url = "https://fincaraiz.com.co"
        self.session = session or self._create_session()
        self._executor = ThreadPoolExecutor(max_workers=3)
        self._last_request = 0.0

    def _create_session(self) -> requests.Session:
        session = requests.Session()
        session.headers.update({
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                          "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "es-CO,es;q=0.9,en;q=0.8",
            "Referer": "https://fincaraiz.com.co/",
            "Connection": "keep-alive",
        })
        return session

    # Public async interface (compatible con main.py)
    async def scrape(self, limit: int = 10, negocio: str = "venta", ciudad: str = "bucaramanga") -> List[Dict]:
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(
            self._executor,
            lambda: self._scrape_sync(limit=limit, negocio=negocio, ciudad=ciudad)
        )

    # ---------- synchronous pipeline (runs in threadpool) ----------
    def _scrape_sync(self, limit: int = 10, negocio: str = "venta", ciudad: str = "bucaramanga") -> List[Dict]:
        try:
            logger.info(f"🚀 FincaraizScraper: ciudad={ciudad}, negocio={negocio}, limit={limit}")
            ciudad_path_map = {
                'bucaramanga': 'bucaramanga/santander',
                'bogota': 'bogota',
                'medellin': 'medellin/antioquia',
                'cali': 'cali/valle-del-cauca',
                'barranquilla': 'barranquilla/atlantico',
                'cartagena': 'cartagena/bolivar'
            }
            ciudad_path = ciudad_path_map.get(ciudad.lower(), ciudad_path_map['bucaramanga'])
            properties: List[Dict] = []

            pages = max(1, (limit // 10) + 1)
            pages = min(pages, 5)  # safety cap

            for pagina in range(1, pages + 1):
                if negocio == "arriendo":
                    url = f"{self.base_url}/arrendamiento/inmuebles/{ciudad_path}?pagina={pagina}"
                else:
                    url = f"{self.base_url}/venta/inmuebles/{ciudad_path}?pagina={pagina}"

                logger.debug(f"🔎 Fetching search page: {url}")
                try:
                    self._throttle()
                    r = self.session.get(url, timeout=15)
                    if r.status_code != 200:
                        logger.warning(f"Search page returned {r.status_code}: {url}")
                        continue
                    soup = BeautifulSoup(r.text, "html.parser")

                    cards = self._encontrar_propiedades_actualizado(soup)
                    logger.info(f"   📊 Página {pagina}: {len(cards)} tarjetas encontradas")

                    for card in cards:
                        item_basic = self._extraer_desde_card(card)
                        if not item_basic or not item_basic.get('link'):
                            continue

                        # Si falta imagen o descripción, visitar detalle
                        if not item_basic.get('imagen_principal') or not item_basic.get('descripcion'):
                            detail = self._extraer_detalles_propiedad(item_basic['link'])
                            if detail:
                                # Merge: detail overrides missing fields
                                merged = {**item_basic, **{k: v for k, v in detail.items() if v is not None}}
                                properties.append(merged)
                            else:
                                properties.append(item_basic)
                        else:
                            properties.append(item_basic)

                        if len(properties) >= limit:
                            break

                        time.sleep(random.uniform(0.5, 1.1))  # small delay between cards

                    if len(properties) >= limit:
                        break
                    time.sleep(random.uniform(1.5, 3.0))  # delay between pages

                except Exception as e:
                    logger.exception(f"❌ Error scraping search page {url}: {e}")
                    continue

            # Deduplicate by link
            unique_props: List[Dict] = []
            seen = set()
            for p in properties:
                link = p.get("link")
                if link and link not in seen:
                    seen.add(link)
                    unique_props.append(p)
                if len(unique_props) >= limit:
                    break

            if not unique_props:
                logger.warning("⚠️ No properties extracted — returning demo dataset")
                return self._generar_datos_demo(ciudad, negocio, limit)

            logger.info(f"✅ FincaraizScraper finished: {len(unique_props)} properties")
            return unique_props

        except Exception as e:
            logger.exception("❌ Fatal error in FincaraizScraper._scrape_sync")
            return self._generar_datos_demo(ciudad, negocio, limit)

    # ---------- search page helpers ----------
    def _encontrar_propiedades_actualizado(self, soup: BeautifulSoup) -> List[Any]:
        cards = []

        # Strategy 1: data-testid / modern attributes
        cards.extend(soup.find_all('div', {'data-testid': re.compile(r'.*(property|posting|card).*', re.I)}))
        if cards:
            return cards

        # Strategy 2: data-cy & selectors commonly used
        selectors_bt = [
            'div[data-cy="listing-card"]',
            'article[data-cy="property-card"]',
            'div[data-cy*="property"]',
            'div[data-cy*="listing"]',
            'a[data-cy*="property"]'
        ]
        for sel in selectors_bt:
            found = soup.select(sel)
            if found:
                return found

        # Strategy 3: class-based modern selectors
        class_selectors = [
            'div[class*="PropertyCard"]',
            'div[class*="property-card"]',
            'div[class*="listing-card"]',
            'article[class*="property"]',
            'div[class*="AdCard"]',
            '.MuiGrid-item',
            '[class*="PostingCard"]',
            '.card'
        ]
        for sel in class_selectors:
            found = soup.select(sel)
            if found:
                filtered = [c for c in found if self._parece_propiedad_actualizado(c)]
                if filtered:
                    return filtered

        # Fallback: links
        links = soup.find_all('a', href=re.compile(r'/inmueble/'))
        parents = []
        for a in links:
            parent = a.find_parent(['div', 'article', 'section'])
            if parent and parent not in parents:
                parents.append(parent)
        return parents

    def _parece_propiedad_actualizado(self, element) -> bool:
        text = (element.get_text(" ", strip=True) or "").lower()
        positives = ['$','precio','habitacion','baño','m²','m2','apartamento','casa','inmueble','venta','arriendo']
        negatives = ['footer','header','nav','menu','logo','publicidad','advertisement','sponsor']
        classes = ' '.join(element.get('class', [])).lower()
        if any(neg in classes for neg in negatives):
            return False
        return any(pos in text for pos in positives)

    # ---------- card extraction ----------
    def _extraer_desde_card(self, card) -> Optional[Dict]:
        try:
            prop: Dict[str, Any] = {"portal": "fincaraiz", "fecha_extraccion": datetime.now().isoformat()}

            # link
            a = card.find('a', href=re.compile(r'/inmueble/'))
            if a and a.get('href'):
                prop['link'] = urljoin(self.base_url, a['href'])
            else:
                # try data attributes
                href = card.get('data-href') or card.get('data-link')
                if href:
                    prop['link'] = urljoin(self.base_url, href)
                else:
                    return None

            # precio (card)
            precio = self._extraer_precio_fincaraiz(card)
            if precio:
                prop['precio'] = precio
                prop['precio_formateado'] = f"${precio:,.0f}"

            # titulo
            titulo = self._extraer_titulo_fincaraiz(card)
            if titulo:
                prop['titulo'] = titulo

            # ubicacion
            ubic = self._extraer_ubicacion_fincaraiz(card)
            if ubic:
                prop['ubicacion'] = ubic

            # imagen principal (from card)
            img = self._extraer_imagen_card_fincaraiz(card)
            if img:
                prop['imagen_principal'] = img

            # basic features
            self._extraer_caracteristicas_fincaraiz(card, prop)

            return prop

        except Exception as e:
            logger.debug(f"⚠️ Error parsing card: {e}")
            return None

    def _extraer_precio_fincaraiz(self, card) -> Optional[int]:
        price_selectors = [
            '.MuiTypography-h6', '.MuiTypography-h5',
            '[class*="price"]', '[class*="Price"]',
            '.price-value', '.listing-price', '.property-price'
        ]
        texto = ""
        for sel in price_selectors:
            el = card.select_one(sel)
            if el:
                texto = el.get_text(" ", strip=True)
                if '$' in texto or re.search(r'\d', texto):
                    break
        if not texto:
            texto_all = card.get_text(" ", strip=True)
            m = re.search(r'\$\s*[\d.,]+(?:\s*(?:mil|millones|mn|m))?', texto_all, re.I)
            if m:
                texto = m.group(0)
        return self._procesar_precio_texto(texto) if texto else None

    def _procesar_precio_texto(self, texto: str) -> Optional[int]:
        if not texto:
            return None
        texto = texto.strip().lower()
        # remove currency symbols and keep digits, dots, commas and spaces
        cleaned = re.sub(r'[^\d\.,\s]', '', texto).strip()
        if not cleaned:
            return None
        cleaned = cleaned.replace(" ", "")
        try:
            # handle "2.500.000" or "2,5 millones"
            if re.search(r'millon|millones|mn|m\b', texto):
                # extract float-like number
                num = re.sub(r'[^\d,\.]', '', texto)
                num = num.replace('.', '').replace(',', '.')
                val = float(num)
                if val < 1000:
                    return int(val * 1_000_000)
                return int(val)
            if re.search(r'mil\b', texto):
                num = re.sub(r'[^\d,\.]', '', texto)
                num = num.replace('.', '').replace(',', '.')
                val = float(num)
                if val < 1000:
                    return int(val * 1000)
                return int(val)
            # general numbers
            if cleaned.count('.') > 1:
                return int(cleaned.replace('.', ''))
            if ',' in cleaned and '.' in cleaned:
                cleaned = cleaned.replace('.', '').replace(',', '.')
                return int(float(cleaned))
            if ',' in cleaned:
                # if comma separators -> remove
                parts = cleaned.split(',')
                if len(parts[-1]) == 2:  # maybe decimal
                    cleaned = cleaned.replace('.', '').replace(',', '.')
                    return int(float(cleaned))
                else:
                    return int(cleaned.replace(',', ''))
            return int(cleaned.replace('.', ''))
        except Exception:
            return None

    def _extraer_titulo_fincaraiz(self, card) -> Optional[str]:
        title_selectors = ['.MuiTypography-h6', '.MuiTypography-h5', '[class*="title"]', 'h2', 'h3', 'h4']
        for sel in title_selectors:
            el = card.select_one(sel)
            if el:
                txt = el.get_text(" ", strip=True)
                if txt and len(txt) > 3:
                    return txt
        return None

    def _extraer_ubicacion_fincaraiz(self, card) -> Optional[str]:
        location_selectors = ['[class*="location"]', '[class*="address"]', '.listing-location', '.listing-address']
        for sel in location_selectors:
            el = card.select_one(sel)
            if el:
                txt = el.get_text(" ", strip=True)
                if txt and len(txt) > 3 and not re.search(r'\$|\d{3,}', txt):
                    return txt
        return None

    # ---------- images helpers ----------
    def _extraer_imagen_card_fincaraiz(self, card) -> Optional[str]:
        # 1) picture / source srcset
        pic = card.find('picture')
        if pic:
            src = None
            source = pic.find('source', srcset=True)
            if source and source.get('srcset'):
                src = self._pick_from_srcset(source.get('srcset'))
            if src:
                return self._normalize_image_url(src)

        # 2) img tag handling lazy attributes and srcset
        img = card.find('img')
        if img:
            src = (img.get('data-src') or img.get('data-lazy-src') or img.get('data-original') or
                   img.get('data-srcset') or img.get('srcset') or img.get('src'))
            if src and isinstance(src, str) and (' ' in src or ',' in src) and 'srcset' in (img.attrs or {}):
                src = self._pick_from_srcset(src)
            if src:
                src = self._normalize_image_url(src)
                if self._is_image_url(src) and self._es_imagen_propiedad_fincaraiz(src):
                    return src

        # 3) style background-image search
        for elem in card.find_all(['div', 'figure']):
            style = elem.get('style') or ''
            m = re.search(r'background-image\s*:\s*url\((["\']?)(.*?)\1\)', style, flags=re.I)
            if m:
                src = m.group(2)
                src = self._normalize_image_url(src)
                if self._is_image_url(src) and self._es_imagen_propiedad_fincaraiz(src):
                    return src

        # 4) any data attributes that might contain image
        for attr in ('data-bg', 'data-image', 'data-src'):
            v = card.attrs.get(attr)
            if v:
                v = self._normalize_image_url(v)
                if self._is_image_url(v) and self._es_imagen_propiedad_fincaraiz(v):
                    return v

        return None

    def _obtener_src_imagen_fincaraiz(self, img_element) -> Optional[str]:
        if not img_element:
            return None
        src = (img_element.get('data-src') or img_element.get('data-lazy-src') or
               img_element.get('data-original') or img_element.get('src') or img_element.get('srcset'))
        if not src:
            return None
        if ',' in src or ' ' in src:
            picked = self._pick_from_srcset(src)
            if picked:
                src = picked
        return self._normalize_image_url(src)

    def _pick_from_srcset(self, srcset: str) -> Optional[str]:
        try:
            parts = [p.strip() for p in srcset.split(',') if p.strip()]
            # choose the last (usually highest resolution)
            last = parts[-1]
            url = last.split(' ')[0]
            return url
        except Exception:
            return None

    def _normalize_image_url(self, url: str) -> str:
        if not url:
            return url
        url = url.strip()
        if url.startswith("//"):
            return "https:" + url
        if url.startswith("/"):
            return urljoin(self.base_url, url)
        return url

    def _is_image_url(self, url: str) -> bool:
        if not url or len(url) < 8:
            return False
        return any(url.lower().split("?")[0].endswith(ext) for ext in ('.jpg', '.jpeg', '.png', '.webp', '.gif'))

    def _es_imagen_propiedad_fincaraiz(self, url: str) -> bool:
        if not url:
            return False
        low = url.lower()
        excludes = ['logo', 'icon', 'avatar', 'placeholder', 'banner', 'ad', 'sponsor', 'loading']
        if any(ex in low for ex in excludes):
            return False
        patterns = ['cloudfront.net', 'amazonaws.com', 'fincaraiz.com.co', '/inmueble/', '/property/', 'fotos', 'images', 'img']
        return any(p in low for p in patterns)

    # ---------- detail page extraction ----------
    def _extraer_detalles_propiedad(self, url: str) -> Optional[Dict]:
        try:
            if not url:
                return None
            logger.debug(f"  🔗 Fetching detail: {url}")
            self._throttle()
            r = self.session.get(url, timeout=18)
            if r.status_code != 200:
                logger.debug(f"Detail page returned {r.status_code} for {url}")
                return None
            soup = BeautifulSoup(r.text, "html.parser")
            prop: Dict[str, Any] = {"portal": "fincaraiz", "link": url, "fecha_extraccion": datetime.now().isoformat()}

            # images: gallery, og:image, json-ld, scripts
            fotos = self._extraer_fotos_reales_fincaraiz(soup, url)
            if fotos:
                prop['fotos'] = fotos
                prop['imagen_principal'] = fotos[0]

            # price: JSON-LD, meta, selectors
            precio = self._extraer_precio_detallado_fincaraiz(soup)
            if precio:
                prop['precio'] = precio
                prop['precio_formateado'] = f"${precio:,.0f}"

            # basic info: title, location, description
            self._extraer_informacion_basica_fincaraiz(soup, prop)
            desc = self._extraer_descripcion_fincaraiz(soup)
            if desc:
                prop['descripcion'] = desc

            # detailed features
            self._extraer_caracteristicas_detalladas_fincaraiz(soup, prop)

            # contact
            self._extraer_contacto_fincaraiz(soup, prop)

            return prop
        except Exception as e:
            logger.debug(f"⚠️ Error extracting detail {url}: {e}")
            return None

    def _extraer_fotos_reales_fincaraiz(self, soup: BeautifulSoup, url: str) -> List[str]:
        fotos = []
        try:
            gallery_selectors = [
                '[data-cy="gallery-image"]', '.property-gallery img', '.slick-slide img',
                '[class*="gallery"] img', '[class*="carousel"] img', '.MuiGrid-item img', 'picture source'
            ]
            for sel in gallery_selectors:
                for img in soup.select(sel):
                    try:
                        if img.name == "source" and img.get("srcset"):
                            src = self._pick_from_srcset(img.get("srcset"))
                        else:
                            src = (img.get('data-src') or img.get('data-lazy-src') or img.get('data-original')
                                   or img.get('srcset') or img.get('src'))
                            if src and ',' in src:
                                src = self._pick_from_srcset(src)
                        if not src:
                            continue
                        src = self._normalize_image_url(src)
                        if self._is_image_url(src) and self._es_imagen_propiedad_fincaraiz(src) and src not in fotos:
                            fotos.append(src)
                    except Exception:
                        continue
                if fotos:
                    break

            # og:image
            meta_og = soup.find('meta', property='og:image')
            if meta_og and meta_og.get('content'):
                og = self._normalize_image_url(meta_og['content'])
                if self._is_image_url(og) and og not in fotos:
                    fotos.insert(0, og)

            # JSON-LD images
            for script in soup.find_all('script', type='application/ld+json'):
                try:
                    data = json.loads(script.string or "{}")
                    imgs = self._extraer_imagenes_jsonld(data)
                    for img in imgs:
                        imgn = self._normalize_image_url(img)
                        if self._is_image_url(imgn) and imgn not in fotos:
                            fotos.append(imgn)
                except Exception:
                    continue

            # Search scripts for image urls
            for script in soup.find_all('script'):
                text = script.string
                if not text:
                    continue
                matches = re.findall(r'https?://[^"\']+\.(?:jpg|jpeg|png|webp|gif)[^\s"\']*', text, re.I)
                for m in matches:
                    mnorm = self._normalize_image_url(m)
                    if self._is_image_url(mnorm) and self._es_imagen_propiedad_fincaraiz(mnorm) and mnorm not in fotos:
                        fotos.append(mnorm)

            # fallback: any img tag
            if not fotos:
                for img in soup.find_all('img', src=True):
                    try:
                        src = self._obtener_src_imagen_fincaraiz(img)
                        if src and self._is_image_url(src) and self._es_imagen_propiedad_fincaraiz(src) and src not in fotos:
                            fotos.append(src)
                    except Exception:
                        continue

            fotos = list(dict.fromkeys(fotos))[:12]
        except Exception as e:
            logger.debug(f"⚠️ Error extracting photos: {e}")
        return fotos

    def _extraer_imagenes_jsonld(self, data: Any) -> List[str]:
        images = []
        try:
            if isinstance(data, dict):
                # @graph handling
                if "@graph" in data and isinstance(data["@graph"], list):
                    for node in data["@graph"]:
                        images.extend(self._extraer_imagenes_jsonld(node))
                for key in ('image', 'images', 'photo', 'thumbnail', 'url'):
                    if key in data:
                        v = data[key]
                        if isinstance(v, str):
                            images.append(v)
                        elif isinstance(v, list):
                            images.extend([i for i in v if isinstance(i, str)])
                # traverse
                for v in data.values():
                    if isinstance(v, dict):
                        images.extend(self._extraer_imagenes_jsonld(v))
                    elif isinstance(v, list):
                        for it in v:
                            if isinstance(it, dict):
                                images.extend(self._extraer_imagenes_jsonld(it))
            elif isinstance(data, list):
                for it in data:
                    images.extend(self._extraer_imagenes_jsonld(it))
        except Exception:
            pass
        return images

    def _extraer_precio_detallado_fincaraiz(self, soup: BeautifulSoup) -> Optional[int]:
        # JSON-LD first (robust)
        for script in soup.find_all('script', type='application/ld+json'):
            try:
                data = json.loads(script.string or "{}")
                # @graph
                candidates = []
                if isinstance(data, dict):
                    if "@graph" in data and isinstance(data["@graph"], list):
                        candidates.extend(data["@graph"])
                    else:
                        candidates.append(data)
                elif isinstance(data, list):
                    candidates.extend(data)
                for cand in candidates:
                    if isinstance(cand, dict):
                        offers = cand.get('offers') or {}
                        if isinstance(offers, dict) and offers.get('price'):
                            try:
                                return int(float(offers['price']))
                            except:
                                continue
            except Exception:
                continue

        # meta tags
        for meta in soup.find_all('meta'):
            prop = meta.get('property') or meta.get('name') or ''
            content = meta.get('content') or ''
            if 'price' in prop.lower() and content:
                try:
                    v = int(float(re.sub(r'[^\d.]', '', content)))
                    if v > 10000:
                        return v
                except:
                    continue

        # visible selectors
        price_selectors = ['.MuiTypography-h4', '.MuiTypography-h5', '[class*="price"]', '.property-price', '.listing-price']
        for sel in price_selectors:
            el = soup.select_one(sel)
            if el:
                val = self._procesar_precio_texto(el.get_text(" ", strip=True))
                if val:
                    return val
        return None

    def _extraer_informacion_basica_fincaraiz(self, soup: BeautifulSoup, propiedad: Dict):
        # title
        if not propiedad.get('titulo'):
            h1 = soup.find('h1') or soup.find('title')
            if h1:
                propiedad['titulo'] = h1.get_text(" ", strip=True)
        # location
        if not propiedad.get('ubicacion'):
            loc_selectors = ['[class*="location"]', '[class*="address"]', '.property-address', '.listing-address']
            for sel in loc_selectors:
                el = soup.select_one(sel)
                if el:
                    text = el.get_text(" ", strip=True)
                    if text and len(text) > 3:
                        propiedad['ubicacion'] = text
                        break

    def _extraer_descripcion_fincaraiz(self, soup: BeautifulSoup) -> Optional[str]:
        # meta description
        meta = soup.find('meta', attrs={'name': 'description'})
        if meta and meta.get('content'):
            txt = meta['content'].strip()
            if len(txt) > 20:
                return txt
        # JSON-LD
        for script in soup.find_all('script', type='application/ld+json'):
            try:
                data = json.loads(script.string or "{}")
                if isinstance(data, dict):
                    desc = data.get('description') or data.get('about') or None
                    if desc and isinstance(desc, str) and len(desc) > 30:
                        return desc.strip()
                    # @graph
                    if "@graph" in data and isinstance(data["@graph"], list):
                        for g in data["@graph"]:
                            if isinstance(g, dict) and g.get('description') and len(g.get('description')) > 30:
                                return g.get('description').strip()
            except Exception:
                continue
        # selectors
        desc_selectors = ['[class*="description"]', '.property-description', '.listing-description', '.MuiTypography-body1']
        for sel in desc_selectors:
            el = soup.select_one(sel)
            if el:
                text = el.get_text(" ", strip=True)
                if text and len(text) > 50:
                    return text
        # long paragraph fallback
        for p in soup.find_all('p'):
            txt = p.get_text(" ", strip=True)
            if 100 < len(txt) < 4000:
                return txt
        return None

    def _extraer_caracteristicas_detalladas_fincaraiz(self, soup: BeautifulSoup, propiedad: Dict):
        text = soup.get_text(" ", strip=True)
        if 'area_m2' not in propiedad:
            m = re.search(r'(\d+[\.,]?\d*)\s*m²', text, re.I)
            if m:
                try:
                    propiedad['area_m2'] = float(m.group(1).replace(',', '.'))
                except:
                    pass
        if 'habitaciones' not in propiedad:
            m = re.search(r'(\d+)\s*(?:hab|habitaciones|alcobas?)', text, re.I)
            if m:
                propiedad['habitaciones'] = int(m.group(1))
        if 'banos' not in propiedad:
            m = re.search(r'(\d+)\s*(?:ba[ñn]os?|baths?)', text, re.I)
            if m:
                propiedad['banos'] = int(m.group(1))
        # tipo inference
        if not propiedad.get('tipo'):
            ttxt = (propiedad.get('titulo') or '').lower() + " " + text.lower()
            if 'apartamento' in ttxt or 'apto' in ttxt:
                propiedad['tipo'] = "Apartamento"
            elif 'casa' in ttxt:
                propiedad['tipo'] = "Casa"
            elif 'finca' in ttxt:
                propiedad['tipo'] = "Finca"
            else:
                propiedad['tipo'] = "Inmueble"

    def _extraer_contacto_fincaraiz(self, soup: BeautifulSoup, propiedad: Dict):
        text = soup.get_text(" ", strip=True)
        phones = set()
        patterns = [r'3\d{2}[\s\-]?\d{3}[\s\-]?\d{4}', r'\(\d{3}\)\s*\d{3}\s*\d{4}', r'\b\d{7,10}\b']
        for pat in patterns:
            for m in re.findall(pat, text):
                clean = re.sub(r'[^\d]', '', m)
                if len(clean) >= 7:
                    phones.add(clean)
        # tel: links
        for a in soup.find_all('a', href=True):
            if 'tel:' in a['href']:
                ph = a['href'].split('tel:')[-1]
                phc = re.sub(r'[^\d]', '', ph)
                if len(phc) >= 7:
                    phones.add(phc)
        if phones:
            propiedad['telefonos'] = ", ".join(sorted(phones)[:3])

    # ---------- utilities ----------
    def _throttle(self, min_delay: float = 0.6, max_delay: float = 1.4):
        now = time.time()
        elapsed = now - self._last_request
        if elapsed < min_delay:
            wait = random.uniform(min_delay - elapsed, max_delay - elapsed)
            time.sleep(wait)
        self._last_request = time.time()

    def _generar_datos_demo(self, ciudad: str, negocio: str, limit: int) -> List[Dict]:
        tipos = ["Apartamento", "Casa", "Finca"]
        zonas = ["Cabecera", "Norte", "Centro", "Provenza", "García Rovira"]
        props = []
        for i in range(limit):
            tipo = random.choice(tipos)
            zona = random.choice(zonas)
            precio = random.randint(180_000_000, 600_000_000) if negocio == "venta" else random.randint(800_000, 4_000_000)
            props.append({
                "id": f"fincaraiz-demo-{i}",
                "portal": "fincaraiz",
                "titulo": f"{tipo} en {zona}, {ciudad.title()}",
                "precio": precio,
                "precio_formateado": f"${precio:,}",
                "ubicacion": f"{zona}, {ciudad.title()}",
                "area_m2": random.randint(60, 220),
                "habitaciones": random.randint(2, 5),
                "banos": random.randint(1, 4),
                "fotos": [f"https://picsum.photos/400/300?{i}"],
                "imagen_principal": f"https://picsum.photos/400/300?{i}",
                "link": f"{self.base_url}/inmueble/demo-{i}",
                "fecha_extraccion": datetime.now().isoformat()
            })
        return props
