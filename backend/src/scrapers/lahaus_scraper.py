"""
src/scrapers/lahaus_scraper.py
Scraper para La Haus (Colombia) - versión mejorada para obtener fotos y descripciones.
Mantiene LaHausScraper y la interfaz async scrape(...) (compatible con main.py).
"""

from typing import List, Dict, Optional, Any
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import re
import json
import time
import random
import logging
import asyncio
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor

logger = logging.getLogger("ARIA_BACKEND")
logger.setLevel(logging.INFO)

__all__ = ["LaHausScraper"]


class LaHausScraper:
    def __init__(self, *, session: Optional[requests.Session] = None):
        self.base_url = "https://www.lahaus.com"
        self.api_base = "https://api.lahaus.com"
        self.session = session or self._create_session()
        self._executor = ThreadPoolExecutor(max_workers=4)
        self._last_request = 0.0

    def _create_session(self) -> requests.Session:
        session = requests.Session()
        session.headers.update({
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                          "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "es-CO,es;q=0.9,en;q=0.8",
            "Referer": "https://www.lahaus.com/",
            "Connection": "keep-alive",
        })
        return session

    # Public async method for main.py compatibility
    async def scrape(self, limit: int = 10, negocio: str = "venta", ciudad: str = "bucaramanga") -> List[Dict]:
        loop = asyncio.get_running_loop()
        # Run sync pipeline in threadpool so FastAPI loop isn't blocked
        return await loop.run_in_executor(
            self._executor,
            lambda: self._scrape_sync(limit=limit, negocio=negocio, ciudad=ciudad)
        )

    # --- synchronous pipeline executed in threadpool ---
    def _scrape_sync(self, limit: int = 10, negocio: str = "venta", ciudad: str = "bucaramanga") -> List[Dict]:
        try:
            logger.info(f"🔍 LaHausScraper start: ciudad={ciudad}, negocio={negocio}, limit={limit}")
            ciudad_slug = ciudad.strip().lower().replace(" ", "-")
            properties: List[Dict] = []

            # 1) Try API first (fast, stable)
            try:
                api_items = self._scrape_via_api(ciudad_slug, negocio, pages=2, per_page=limit)
                if api_items:
                    logger.info(f"✅ La Haus API returned {len(api_items)} items")
                    properties.extend(api_items[:limit])
            except Exception as e:
                logger.debug(f"⚠️ API probe failed: {e}")

            # 2) If not enough, fallback to HTML scraping
            if len(properties) < limit:
                needed = limit - len(properties)
                logger.info(f"🔄 Complementing via web scraping (need {needed})")
                web_items = self._scrape_via_web(ciudad_slug, negocio, pages=2, per_page=needed)
                if web_items:
                    properties.extend(web_items[:needed])

            # 3) Deduplicate by link
            deduped = []
            seen = set()
            for p in properties:
                link = p.get("link")
                if not link:
                    continue
                if link not in seen:
                    seen.add(link)
                    deduped.append(p)

            if not deduped:
                logger.warning("⚠️ No real items extracted; returning demo data")
                return self._generar_datos_demo(ciudad, negocio, limit)

            logger.info(f"📦 Returning {len(deduped)} properties")
            return deduped

        except Exception as e:
            logger.exception("❌ Critical error in LaHausScraper._scrape_sync")
            return self._generar_datos_demo(ciudad, negocio, limit)

    # -----------------------
    # Strategy A: API probing & normalizing
    # -----------------------
    def _scrape_via_api(self, ciudad_slug: str, tipo_negocio: str, pages: int = 2, per_page: int = 20) -> List[Dict]:
        results = []
        api_url = f"{self.api_base}/v1/properties"
        for page in range(1, pages + 1):
            params = {
                "city": ciudad_slug,
                "operation": "sale" if tipo_negocio == "venta" else "rental",
                "page": page,
                "limit": per_page,
                "sort": "updated_at",
                "order": "desc"
            }
            try:
                self._throttle()
                r = self.session.get(api_url, params=params, timeout=12)
                if r.status_code != 200:
                    logger.debug(f"API {api_url} returned {r.status_code}")
                    break
                data = r.json()
                items = data.get("data") or data.get("results") or data.get("items") or []
                if not items:
                    break
                for it in items:
                    p = self._procesar_datos_api(it)
                    if p:
                        results.append(p)
                if len(items) < per_page:
                    break
            except Exception as e:
                logger.debug(f"⚠️ Error calling La Haus API: {e}")
                break
        return results

    def _procesar_datos_api(self, property_data: dict) -> Optional[Dict]:
        try:
            p: Dict[str, Any] = {"portal": "lahaus", "fecha_extraccion": datetime.now().isoformat()}
            pid = property_data.get("id") or property_data.get("slug") or property_data.get("uuid")
            p["id"] = pid
            slug = property_data.get("slug")
            if slug:
                p["link"] = urljoin(self.base_url, f"/propiedad/{slug}")
            else:
                p["link"] = property_data.get("url") or urljoin(self.base_url, f"/propiedad/{pid}")

            p["titulo"] = property_data.get("title") or property_data.get("name")
            p["descripcion"] = property_data.get("description") or property_data.get("summary")

            # price
            price = None
            if isinstance(property_data.get("price"), dict):
                price = property_data["price"].get("value")
            else:
                price = property_data.get("price") or property_data.get("valor") or property_data.get("amount")
            try:
                p["precio"] = int(price) if price is not None else None
            except Exception:
                p["precio"] = None
            if p.get("precio"):
                p["precio_formateado"] = f"${p['precio']:,.0f}"

            # location
            loc = property_data.get("location") or {}
            p["ubicacion"] = loc.get("formatted_address") or loc.get("address") or loc.get("city") or loc.get("neighborhood")
            p["ciudad"] = loc.get("city") or None
            p["barrio"] = loc.get("neighborhood") or None

            # attrs
            attrs = property_data.get("attributes") or property_data.get("attributes_map") or {}
            p["area_m2"] = attrs.get("area") or attrs.get("surface") or None
            p["habitaciones"] = attrs.get("bedrooms") or attrs.get("rooms") or None
            p["banos"] = attrs.get("bathrooms") or None
            p["parqueaderos"] = attrs.get("parking_lots") or attrs.get("parking") or None

            # images
            images = property_data.get("images") or property_data.get("photos") or []
            if images and isinstance(images, list):
                p["fotos"] = [self._normalize_image_url(x) for x in images if x]
                p["imagen_principal"] = p["fotos"][0] if p.get("fotos") else None

            proj = property_data.get("project") or {}
            if proj:
                p["proyecto"] = proj.get("name") or proj.get("title")
                p["constructora"] = proj.get("builder_name") or proj.get("builder")

            p["estado"] = property_data.get("status") or None

            if not (p.get("precio") or p.get("area_m2") or p.get("imagen_principal")):
                return None
            return p
        except Exception as e:
            logger.debug(f"⚠️ Error processing API item: {e}")
            return None

    # -----------------------
    # Strategy B: HTML scraping (cards + detail)
    # -----------------------
    def _scrape_via_web(self, ciudad_slug: str, tipo_negocio: str, pages: int = 2, per_page: int = 10) -> List[Dict]:
        results: List[Dict] = []
        for page in range(1, pages + 1):
            if tipo_negocio == "venta":
                url = f"{self.base_url}/buscar/proyectos-vivienda-nueva/{ciudad_slug}?page={page}"
            else:
                url = f"{self.base_url}/buscar/arriendo/{ciudad_slug}?page={page}"
            try:
                self._throttle()
                r = self.session.get(url, timeout=15)
                if r.status_code != 200:
                    logger.debug(f"Search page {url} returned {r.status_code}")
                    continue
                soup = BeautifulSoup(r.text, "html.parser")

                # Try JSON-LD / microdata first
                items = []
                items.extend(self._extract_json_ld_listings(soup))
                items.extend(self._extract_microdata_listings(soup))

                if not items:
                    cards = self._encontrar_propiedades_web(soup)
                    for card in cards[:per_page]:
                        basic = self._extraer_desde_card_web(card)
                        if basic and basic.get("link"):
                            # If missing image/description -> visit detail
                            if not basic.get("imagen_principal") or not basic.get("descripcion"):
                                detail = self._extraer_detalles_propiedad_web(basic["link"])
                                if detail:
                                    # merge: prefer detail fields if present
                                    merged = {**basic, **{k: v for k, v in detail.items() if v is not None}}
                                    results.append(merged)
                                else:
                                    results.append(basic)
                            else:
                                results.append(basic)
                else:
                    # items from jsonld / microdata
                    for it in items[:per_page]:
                        if it.get("link"):
                            detail = self._extraer_detalles_propiedad_web(it["link"])
                            if detail:
                                merged = {**it, **{k: v for k, v in detail.items() if v is not None}}
                                results.append(merged)
                            else:
                                results.append(it)
                        else:
                            results.append(it)

            except Exception as e:
                logger.debug(f"⚠️ Error scraping page {url}: {e}")
                continue
        return results

    # JSON-LD helpers (robust against @graph / arrays)
    def _extract_json_ld_listings(self, soup: BeautifulSoup) -> List[Dict]:
        found = []
        for script in soup.find_all("script", type="application/ld+json"):
            try:
                raw = script.string
                if not raw:
                    continue
                data = json.loads(raw)
                # normalize to list of dicts
                candidates = []
                if isinstance(data, dict):
                    # @graph
                    if "@graph" in data and isinstance(data["@graph"], list):
                        candidates.extend(data["@graph"])
                    elif data.get("itemListElement") and isinstance(data.get("itemListElement"), list):
                        for el in data["itemListElement"]:
                            if isinstance(el, dict):
                                item = el.get("item") or el.get("result") or el
                                if isinstance(item, dict):
                                    candidates.append(item)
                    else:
                        candidates.append(data)
                elif isinstance(data, list):
                    candidates.extend(data)
                for cand in candidates:
                    if isinstance(cand, dict):
                        p = self._parse_json_ld_item(cand)
                        if p:
                            found.append(p)
            except Exception:
                continue
        return found

    def _parse_json_ld_item(self, data: dict) -> Optional[Dict]:
        try:
            p = {"portal": "lahaus", "fecha_extraccion": datetime.now().isoformat()}
            p["titulo"] = data.get("name") or data.get("headline")
            offers = data.get("offers") or {}
            if isinstance(offers, dict):
                price = offers.get("price") or offers.get("priceAmount")
                try:
                    p["precio"] = int(price)
                    p["precio_formateado"] = f"${p['precio']:,.0f}"
                except Exception:
                    p["precio"] = None
            # url
            p["link"] = data.get("url")
            # address
            addr = data.get("address") or {}
            if isinstance(addr, dict):
                p["ubicacion"] = addr.get("streetAddress") or addr.get("addressLocality")
            imgs = data.get("image") or data.get("images") or []
            if isinstance(imgs, list) and imgs:
                p["fotos"] = [self._normalize_image_url(x) for x in imgs if x]
                p["imagen_principal"] = p["fotos"][0] if p.get("fotos") else None
            elif isinstance(imgs, str):
                p["fotos"] = [self._normalize_image_url(imgs)]
                p["imagen_principal"] = p["fotos"][0]
            # description
            if data.get("description"):
                p["descripcion"] = data.get("description")
            return p if p.get("link") or p.get("precio") else None
        except Exception:
            return None

    def _extract_microdata_listings(self, soup: BeautifulSoup) -> List[Dict]:
        found = []
        elems = soup.find_all(attrs={"itemtype": True})
        for el in elems:
            try:
                parsed = self._parse_microdata(el)
                if parsed:
                    found.append(parsed)
            except Exception:
                continue
        return found

    def _parse_microdata(self, el) -> Optional[Dict]:
        try:
            p = {"portal": "lahaus", "fecha_extraccion": datetime.now().isoformat()}
            for tag in el.find_all(attrs={"itemprop": True}):
                key = tag.get("itemprop")
                val = tag.get("content") or tag.get_text(strip=True)
                if key and val:
                    if key.lower() in ("name", "titulo", "title"):
                        p["titulo"] = val
                    elif key.lower() in ("price", "precio"):
                        parsed = self._procesar_precio_texto(val)
                        if parsed:
                            p["precio"] = parsed
                            p["precio_formateado"] = f"${parsed:,.0f}"
                    elif key.lower() == "url":
                        p["link"] = urljoin(self.base_url, val)
                    elif key.lower() in ("address", "ubicacion", "streetaddress"):
                        p["ubicacion"] = val
            return p if p.get("precio") or p.get("link") else None
        except Exception:
            return None

    # Card extraction (improved)
    def _encontrar_propiedades_web(self, soup: BeautifulSoup) -> List[Any]:
        cards = []
        cards.extend(soup.find_all("div", {"data-testid": re.compile(r".*property.*", re.I)}))
        selectors = ['[data-cy="property-card"]', '.property-card', '.project-card', '[class*="property"]', 'article']
        for sel in selectors:
            found = soup.select(sel)
            if found:
                cards.extend(found)
                break
        if not cards:
            links = soup.find_all("a", href=re.compile(r"/propiedad/"))
            for a in links:
                parent = a.find_parent(['div', 'article', 'section'])
                if parent and parent not in cards:
                    cards.append(parent)
        # dedupe
        unique = []
        seen = set()
        for c in cards:
            key = getattr(c, "attrs", {}).get("data-testid") or (c.get("id") if hasattr(c, "get") else None) or str(c)[:160]
            if key not in seen:
                seen.add(key)
                unique.append(c)
        return unique

    def _extraer_desde_card_web(self, card) -> Optional[Dict]:
        try:
            p = {"portal": "lahaus", "fecha_extraccion": datetime.now().isoformat()}
            # link
            a = card.find("a", href=re.compile(r"/propiedad/"))
            if a and a.get("href"):
                p["link"] = urljoin(self.base_url, a["href"])
            else:
                return None
            # title
            title = None
            for tag in ("h1", "h2", "h3", "h4"):
                el = card.find(tag)
                if el:
                    title = el.get_text(strip=True)
                    break
            if not title:
                el = card.select_one('[class*="title"],[class*="name"]')
                if el:
                    title = el.get_text(strip=True)
            p["titulo"] = title

            # description (many possible places)
            desc = None
            desc_selectors = [
                '[data-testid*="description"]',
                '[class*="description"]',
                '[class*="subtitle"]',
                '[class*="detail"]',
                'p',
                'small',
                'span'
            ]
            for sel in desc_selectors:
                el = card.select_one(sel)
                if el:
                    txt = el.get_text(" ", strip=True)
                    if txt and len(txt) > 20:
                        desc = txt
                        break
            # sometimes title attribute or aria-label
            if not desc:
                if a and a.get("title"):
                    txt = a.get("title").strip()
                    if txt and len(txt) > 20:
                        desc = txt
                elif card.get("title"):
                    txt = card.get("title").strip()
                    if txt and len(txt) > 20:
                        desc = txt
            if desc:
                p["descripcion"] = desc

            # image - support many lazy-loading patterns and style background
            img_url = None
            # 1) <picture><source srcset=...>
            picture = card.find("picture")
            if picture:
                source = picture.find("source", srcset=True)
                if source and source.get("srcset"):
                    img_url = self._pick_from_srcset(source.get("srcset"))
            # 2) img tags with data-src, data-lazy-src, srcset
            if not img_url:
                img = card.find("img")
                if img:
                    img_url = img.get("data-src") or img.get("data-lazy-src") or img.get("data-srcset") or img.get("srcset") or img.get("src")
                    if img_url and img_url == img.get("srcset"):
                        # if srcset string, pick best
                        img_url = self._pick_from_srcset(img_url)
            # 3) background-image style
            if not img_url:
                style = card.get("style", "") or (card.attrs.get("style") if hasattr(card, "attrs") else "")
                bg = None
                if style:
                    m = re.search(r'background-image\s*:\s*url\([\'"]?(.*?)[\'"]?\)', style, flags=re.I)
                    if m:
                        bg = m.group(1)
                if bg:
                    img_url = bg
            # 4) data attributes like data-bg or data-image
            if not img_url:
                for attr in ("data-src", "data-bg", "data-image", "data-lazy", "data-background"):
                    v = card.attrs.get(attr) if hasattr(card, "attrs") else None
                    if v:
                        img_url = v
                        break
            if img_url:
                p["imagen_principal"] = self._normalize_image_url(img_url)
            # price
            price = self._extraer_precio_web(card)
            if price:
                p["precio"] = price
                p["precio_formateado"] = f"${price:,.0f}"
            # location
            loc = card.select_one('[class*="location"],[class*="address"],[data-testid*="address"],[class*="ubicacion"]')
            if loc:
                p["ubicacion"] = loc.get_text(" ", strip=True)
            # basic attributes
            self._extraer_caracteristicas_web(card, p)
            return p
        except Exception as e:
            logger.debug(f"⚠️ Error extracting card: {e}")
            return None

    # detail page extraction (enriches card data)
    def _extraer_detalles_propiedad_web(self, url: str) -> Optional[Dict]:
        try:
            self._throttle()
            r = self.session.get(url, timeout=15)
            if r.status_code != 200:
                logger.debug(f"Detail {url} returned {r.status_code}")
                return None
            soup = BeautifulSoup(r.text, "html.parser")
            prop = {"portal": "lahaus", "link": url, "fecha_extraccion": datetime.now().isoformat()}
            jsonld = self._extraer_jsonld(soup)
            if jsonld:
                self._procesar_jsonld(jsonld, prop)
            fotos = self._extraer_fotos_web(soup)
            if fotos:
                prop["fotos"] = fotos
                prop["imagen_principal"] = fotos[0]
            self._extraer_informacion_web(soup, prop)
            if not prop.get("precio"):
                precio = self._extraer_precio_pagina(soup)
                if precio:
                    prop["precio"] = precio
                    prop["precio_formateado"] = f"${precio:,.0f}"
            return prop
        except Exception as e:
            logger.debug(f"⚠️ Error extracting detail {url}: {e}")
            return None

    def _extraer_jsonld(self, soup: BeautifulSoup) -> Optional[dict]:
        # Return first useful JSON-LD object (support @graph and arrays)
        for script in soup.find_all("script", type="application/ld+json"):
            try:
                raw = script.string
                if not raw:
                    continue
                data = json.loads(raw)
                # data may be dict/list
                if isinstance(data, dict):
                    # search in @graph
                    if "@graph" in data and isinstance(data["@graph"], list):
                        for node in data["@graph"]:
                            if isinstance(node, dict) and any(t in str(node.get("@type", "")).lower() for t in ("offer", "realestate", "product")):
                                return node
                    if data.get("@type") and any(t in str(data.get("@type")).lower() for t in ("offer", "realestate", "product")):
                        return data
                    # itemListElement
                    if data.get("itemListElement"):
                        items = data.get("itemListElement")
                        if isinstance(items, list) and items:
                            first = items[0]
                            candidate = first.get("item") if isinstance(first, dict) else first
                            if isinstance(candidate, dict) and any(t in str(candidate.get("@type", "")).lower() for t in ("offer", "realestate", "product")):
                                return candidate
                elif isinstance(data, list):
                    for node in data:
                        if isinstance(node, dict) and any(t in str(node.get("@type", "")).lower() for t in ("offer", "realestate", "product")):
                            return node
            except Exception:
                continue
        return None

    def _procesar_jsonld(self, json_data: dict, prop: dict):
        try:
            offers = json_data.get("offers") or {}
            if isinstance(offers, dict):
                price = offers.get("price") or offers.get("priceAmount")
                if price:
                    try:
                        prop["precio"] = int(float(price))
                        prop["precio_formateado"] = f"${prop['precio']:,.0f}"
                    except Exception:
                        pass
            if json_data.get("name") and not prop.get("titulo"):
                prop["titulo"] = json_data.get("name")
            if json_data.get("description") and not prop.get("descripcion"):
                prop["descripcion"] = json_data.get("description")
            imgs = json_data.get("image") or json_data.get("images") or []
            if imgs:
                if isinstance(imgs, list):
                    prop["fotos"] = [self._normalize_image_url(x) for x in imgs if x]
                    prop["imagen_principal"] = prop["fotos"][0] if prop.get("fotos") else None
                elif isinstance(imgs, str):
                    prop["fotos"] = [self._normalize_image_url(imgs)]
                    prop["imagen_principal"] = prop["fotos"][0]
        except Exception:
            pass

    def _extraer_fotos_web(self, soup: BeautifulSoup) -> List[str]:
        photos = []
        selectors = [
            '[data-testid*="gallery"] img',
            'picture source[srcset]',
            '.gallery img',
            '.carousel img',
            '[class*="slick"] img',
            'img'
        ]
        for sel in selectors:
            for img in soup.select(sel):
                try:
                    src = None
                    if img.name == "source" and img.get("srcset"):
                        src = self._pick_from_srcset(img.get("srcset"))
                    else:
                        src = img.get("data-src") or img.get("data-lazy-src") or img.get("data-srcset") or img.get("srcset") or img.get("src")
                        if src and " " in src and "," in src:
                            # srcset string -> pick best
                            src = self._pick_from_srcset(src)
                    if not src:
                        continue
                    if src.startswith("//"):
                        src = "https:" + src
                    elif src.startswith("/"):
                        src = urljoin(self.base_url, src)
                    if self._is_image_url(src) and src not in photos:
                        photos.append(src)
                except Exception:
                    continue
            if photos:
                break
        meta = soup.find("meta", property="og:image")
        if meta and meta.get("content"):
            og = meta["content"]
            if og not in photos and self._is_image_url(og):
                photos.insert(0, og)
        return photos[:12]

    # price parsing
    def _extraer_precio_web(self, card) -> Optional[int]:
        price_text = ""
        price_selectors = [
            '[class*="price"]',
            '[class*="Price"]',
            '[data-testid*="price"]',
            '.currency',
            '.price-tag',
        ]
        for sel in price_selectors:
            el = card.select_one(sel)
            if el:
                price_text = el.get_text(" ", strip=True)
                if "$" in price_text or re.search(r'\d', price_text):
                    break
        if not price_text:
            txt = card.get_text(" ", strip=True)
            m = re.search(r'\$\s*[\d.,]+', txt)
            if m:
                price_text = m.group(0)
        return self._procesar_precio_texto(price_text) if price_text else None

    def _procesar_precio_texto(self, texto: str) -> Optional[int]:
        if not texto:
            return None
        texto_limpio = re.sub(r'[^\d,.\s]', '', texto).strip()
        if not texto_limpio:
            return None
        texto_limpio = texto_limpio.replace(" ", "")
        try:
            if texto_limpio.count(".") > 1:
                texto_num = texto_limpio.replace(".", "").split(",")[0]
                return int(float(texto_num))
            if "," in texto_limpio and "." in texto_limpio:
                texto_num = texto_limpio.replace(".", "").replace(",", ".")
                return int(float(texto_num))
            if "," in texto_limpio:
                texto_num = texto_limpio.replace(",", "")
                return int(float(texto_num))
            texto_num = texto_limpio.replace(".", "")
            return int(float(texto_num))
        except Exception:
            return None

    def _extraer_informacion_web(self, soup: BeautifulSoup, prop: Dict):
        txt = soup.get_text(" ", strip=True)
        if "area_m2" not in prop:
            m = re.search(r'(\d+[\.,]?\d*)\s*m²', txt, flags=re.I)
            if m:
                try:
                    prop["area_m2"] = float(m.group(1).replace(",", "."))
                except Exception:
                    pass
        if "habitaciones" not in prop:
            m = re.search(r'(\d+)\s*(?:hab|habitaciones|alcobas?)', txt, flags=re.I)
            if m:
                prop["habitaciones"] = int(m.group(1))
        if "banos" not in prop:
            m = re.search(r'(\d+)\s*(?:ba[ñn]os?|baths?)', txt, flags=re.I)
            if m:
                prop["banos"] = int(m.group(1))
        if not prop.get("tipo"):
            title_text = (prop.get("titulo") or "").lower()
            if "apartamento" in title_text or "apto" in title_text:
                prop["tipo"] = "Apartamento"
            elif "casa" in title_text:
                prop["tipo"] = "Casa"
            elif "finca" in title_text:
                prop["tipo"] = "Finca"
            else:
                prop["tipo"] = "Inmueble"
        # description fallback: look for meta description
        if not prop.get("descripcion"):
            meta = soup.find("meta", attrs={"name": "description"})
            if meta and meta.get("content"):
                prop["descripcion"] = meta["content"]

    # helper: pick best url from srcset
    def _pick_from_srcset(self, srcset: str) -> Optional[str]:
        try:
            parts = [p.strip() for p in srcset.split(",") if p.strip()]
            # choose the last part (usually highest res) and its url
            last = parts[-1]
            url = last.split(" ")[0]
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
        if not url:
            return False
        return any(url.lower().split("?")[0].endswith(ext) for ext in (".jpg", ".jpeg", ".png", ".webp", ".gif"))

    def _throttle(self, min_delay: float = 0.8, max_delay: float = 1.6):
        now = time.time()
        elapsed = now - self._last_request
        if elapsed < min_delay:
            wait = random.uniform(min_delay - elapsed, max_delay - elapsed)
            time.sleep(wait)
        self._last_request = time.time()

    def _generar_datos_demo(self, ciudad: str, negocio: str, limit: int) -> List[Dict]:
        tipos = ["Apartamento", "Casa", "Finca", "Oficina"]
        zonas = ["Norte", "Centro", "Cabecera", "Provenza", "García Rovira"]
        props = []
        for i in range(limit):
            tipo = random.choice(tipos)
            zona = random.choice(zonas)
            precio = random.randint(100_000_000, 800_000_000) if negocio == "venta" else random.randint(800_000, 4_000_000)
            props.append({
                "id": f"lahaus-demo-{i}",
                "portal": "lahaus",
                "titulo": f"{tipo} en {zona}, {ciudad.title()}",
                "precio": precio,
                "precio_formateado": f"${precio:,}",
                "ubicacion": f"{zona}, {ciudad.title()}",
                "area_m2": random.randint(45, 220),
                "habitaciones": random.randint(1, 5),
                "banos": random.randint(1, 4),
                "fotos": [f"https://picsum.photos/400/300?{i}"],
                "imagen_principal": f"https://picsum.photos/400/300?{i}",
                "link": f"{self.base_url}/propiedad/demo-{i}",
                "fecha_extraccion": datetime.now().isoformat()
            })
        return props
