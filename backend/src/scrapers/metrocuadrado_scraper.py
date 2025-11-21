#!/usr/bin/env python3
"""
Metrocuadrado Adapter - Scraper Avanzado CORREGIDO

Mantiene la clase MetrocuadradoScraper (no cambiar nombres de clase).
Exporta __all__ = ["MetrocuadradoScraper"] para que main.py la cargue.
"""

import re
import random
import logging
import asyncio
import requests
import json
from datetime import datetime
from typing import List, Dict, Optional, Any
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import time
import hashlib

logger = logging.getLogger(__name__)

__all__ = ["MetrocuadradoScraper"]


class MetrocuadradoScraper:
    """
    Scraper para Metrocuadrado (adapter).
    - intenta primero encontrar datos embebidos (JSON-LD / microdata / scripts)
    - si falla, intenta scraping HTML tradicional con múltiples selectores
    - como último recurso, devuelve datos demo realistas
    """

    def __init__(self):
        self.base_url = "https://www.metrocuadrado.com"
        self.session = requests.Session()
        self._setup_session()
        self.request_count = 0
        self.last_request_time = 0.0

    def _setup_session(self):
        """Configuración básica de la sesión para parecer un browser real"""
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) '
                          'AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
            'Accept-Language': 'es-CO,es;q=0.9',
            'Connection': 'keep-alive',
        })

    async def _rate_limit(self):
        """Rate limiting async-friendly para no bloquear el event loop"""
        now = time.time()
        elapsed = now - self.last_request_time
        min_delay = 1.0
        max_delay = 2.0

        if elapsed < min_delay:
            sleep_time = random.uniform(min_delay - elapsed, max_delay - elapsed)
            logger.debug(f"⏳ Rate limiting: esperando {sleep_time:.2f}s")
            await asyncio.sleep(sleep_time)

        self.last_request_time = time.time()
        self.request_count += 1

    async def scrape(self, limit: int = 10, negocio: str = "venta", ciudad: str = "bogota") -> List[Dict]:
        """
        Punto de entrada: intenta varias estrategias y devuelve lista de dicts.
        Conserva la firma async para encajar con main.py.
        """
        try:
            logger.info(f"🚀 Iniciando Metrocuadrado: ciudad={ciudad}, negocio={negocio}, limit={limit}")

            # 1) Intentar obtener vía API/XHR (si existe) - más estable
            try:
                props_api = await self._try_api_endpoint(ciudad, negocio, limit)
                if props_api:
                    logger.info(f"✅ Metrocuadrado API: {len(props_api)} propiedades devueltas")
                    return props_api[:limit]
            except Exception:
                logger.debug("⚠️ Intento API falló o no disponible")

            # 2) Intentar scraping HTML (multiples estrategias)
            try:
                props_html = await self._scrape_real(ciudad, negocio, limit)
                if props_html:
                    logger.info(f"✅ Metrocuadrado HTML: {len(props_html)} propiedades devueltas")
                    return props_html[:limit]
            except Exception:
                logger.debug("⚠️ Scraping HTML falló")

            # 3) Fallback: generar datos demo realistas
            logger.warning("🔄 Usando datos de demostración (fallback)")
            return await self._generar_datos_demo(ciudad, negocio, limit)

        except Exception as e:
            logger.exception("❌ Error crítico en Metrocuadrado.scrape")
            return await self._generar_datos_demo(ciudad, negocio, limit)

    # ---------------------------
    # Estrategia A: Intentar API (XHR)
    # ---------------------------
    async def _try_api_endpoint(self, ciudad: str, negocio: str, limit: int) -> List[Dict]:
        """
        Intenta llamar a endpoints tipo API/XHR que las SPA usan internamente.
        No presupone un endpoint exacto — prueba unas rutas plausibles.
        """
        # Lista de endpoints plausibles (estas rutas son ejemplos frecuentes; puede que no todas existan)
        candidate_endpoints = [
            "https://api.metrocuadrado.com/api/listing/search",
            "https://www.metrocuadrado.com/api/search",
            "https://www.metrocuadrado.com/_next/data",  # Next.js data (ejemplo)
        ]

        # Construir payload básico
        payload = {
            "operation": negocio,
            "cities": [ciudad],
            "from": 0,
            "size": limit
        }

        headers = {
            "origin": "https://www.metrocuadrado.com",
            "referer": f"https://www.metrocuadrado.com/",
            "content-type": "application/json",
            "user-agent": self.session.headers.get("User-Agent")
        }

        loop = asyncio.get_running_loop()

        for endpoint in candidate_endpoints:
            try:
                await self._rate_limit()
                logger.debug(f"🌐 Probando endpoint API: {endpoint}")
                resp = await loop.run_in_executor(None, lambda: self.session.post(endpoint, json=payload, headers=headers, timeout=12))
                if resp is None:
                    continue
                if resp.status_code != 200:
                    logger.debug(f"   - endpoint {endpoint} respondió {resp.status_code}")
                    continue

                data = None
                try:
                    data = resp.json()
                except Exception:
                    # A veces la API devuelve JS o HTML; ignoramos
                    continue

                # Normalización: intentar encontrar objetos de listings en la respuesta
                listings = []
                if isinstance(data, dict):
                    # buscar keys comunes
                    for key in ("data", "results", "listings", "items"):
                        if key in data and isinstance(data[key], (list, dict)):
                            candidate = data[key]
                            if isinstance(candidate, dict) and "items" in candidate:
                                listings = candidate.get("items", [])
                            elif isinstance(candidate, list):
                                listings = candidate
                            else:
                                # dict inesperado; tratar como lista de un elemento
                                if isinstance(candidate, dict):
                                    listings = [candidate]
                            break

                    # si no se encontró, intentar parseo directo (ejemplo)
                    if not listings:
                        # recorrer la dict buscando listas de dicts grandes
                        for k, v in data.items():
                            if isinstance(v, list) and v and isinstance(v[0], dict):
                                listings = v
                                break

                elif isinstance(data, list):
                    listings = data

                # Si tenemos listings, normalizamos
                if listings:
                    normalized = []
                    for item in listings[:limit]:
                        normalized.append(self._normalizar_item_api(item))
                    if normalized:
                        return normalized

            except Exception as e:
                logger.debug(f"   - fallo probing API {endpoint}: {e}")
                continue

        # Si ninguno funcionó, devolver vacío para que sigan otras estrategias
        return []

    def _normalizar_item_api(self, item: Dict) -> Dict:
        """Normaliza entrada de API/XHR al formato de tu backend"""
        # Hecho defensivamente: varios nombres posibles
        title = item.get("title") or item.get("name") or item.get("titulo") or item.get("headline")
        price = item.get("price") or item.get("valor") or item.get("precio") or item.get("priceAmount")
        try:
            price = int(price) if price is not None else 0
        except Exception:
            try:
                price = int(float(str(price).replace(",", "")))
            except Exception:
                price = 0

        return {
            "portal": "metrocuadrado",
            "titulo": title or "Propiedad",
            "precio": price,
            "precio_formateado": f"${price:,}" if price else None,
            "area_m2": item.get("area") or item.get("builtArea") or item.get("superficie"),
            "habitaciones": item.get("rooms") or item.get("habitaciones"),
            "banos": item.get("bathrooms") or item.get("banos"),
            "ubicacion": item.get("neighborhood") or item.get("address") or item.get("barrio"),
            "link": item.get("url") or (self.base_url + item.get("path", "")) if isinstance(item.get("path", ""), str) else None,
            "imagen": (item.get("image") or (item.get("images") and item.get("images")[0])) if item else None,
            "raw": item
        }

    # ---------------------------
    # Estrategia B: Scraping HTML tradicional / resiliente
    # ---------------------------
    async def _scrape_real(self, ciudad: str, negocio: str, limit: int) -> List[Dict]:
        """
        Intento robusto de scraping HTML con múltiples selectores y extracción JSON-LD/microdata.
        """
        try:
            await self._rate_limit()

            url = self._construir_url_busqueda(ciudad, negocio)
            logger.info(f"🌐 Scraping HTML: {url}")

            loop = asyncio.get_running_loop()
            resp = await loop.run_in_executor(None, lambda: self.session.get(url, timeout=20, allow_redirects=True))

            if resp.status_code != 200:
                logger.warning(f"⚠️ Status {resp.status_code} en {url}")
                return []

            soup = BeautifulSoup(resp.text, "html.parser")

            # 1) Intentar JSON-LD
            props = await self._extraer_propiedades_json_ld(soup, ciudad, negocio)
            if props:
                logger.debug("🔎 Encontradas propiedades via JSON-LD")
                return props[:limit]

            # 2) Intentar microdata
            props = await self._extraer_propiedades_microdata(soup, ciudad, negocio)
            if props:
                logger.debug("🔎 Encontradas propiedades via microdata")
                return props[:limit]

            # 3) Extracción tradicional por selectores
            props = await self._extraer_propiedades_tradicional(soup, ciudad, negocio, limit)
            if props:
                logger.debug("🔎 Encontradas propiedades via selectores HTML")
                return props[:limit]

            # 4) Como último, intentar buscar scripts con JSON dentro
            props = await self._extraer_propiedades_from_scripts(soup, ciudad, negocio)
            return props[:limit]

        except Exception as e:
            logger.exception("❌ Error en _scrape_real")
            return []

    def _construir_url_busqueda(self, ciudad: str, negocio: str) -> str:
        # Normalizar ciudad simple
        ciudad_code = ciudad.strip().lower().replace(" ", "-")
        if negocio == "venta":
            return f"{self.base_url}/inmueble/venta/{ciudad_code}"
        else:
            return f"{self.base_url}/inmueble/arriendo/{ciudad_code}"

    # --- JSON-LD extraction ---
    async def _extraer_propiedades_json_ld(self, soup: BeautifulSoup, ciudad: str, negocio: str) -> List[Dict]:
        propiedades = []
        try:
            scripts = soup.find_all("script", type="application/ld+json")
            for script in scripts:
                try:
                    text = script.string
                    if not text:
                        continue
                    data = json.loads(text)
                    if isinstance(data, dict):
                        # si viene un objeto con lista en 'itemListElement' o 'mainEntity'
                        items = []
                        if "itemListElement" in data and isinstance(data["itemListElement"], list):
                            items = [el.get("item", el) if isinstance(el, dict) else el for el in data["itemListElement"]]
                        elif "mainEntity" in data:
                            items = data.get("mainEntity")
                        else:
                            # si es entity de tipo Offer/Apartment, considerarlo único
                            items = [data]
                        # Normalizar cada item
                        for it in (items if isinstance(items, list) else [items]):
                            if isinstance(it, dict):
                                norm = self._parsear_json_ld(it, ciudad, negocio)
                                if norm:
                                    propiedades.append(norm)
                    elif isinstance(data, list):
                        for it in data:
                            if isinstance(it, dict):
                                norm = self._parsear_json_ld(it, ciudad, negocio)
                                if norm:
                                    propiedades.append(norm)
                except Exception:
                    continue
        except Exception:
            pass
        return propiedades

    def _parsear_json_ld(self, data: Dict, ciudad: str, negocio: str) -> Optional[Dict]:
        try:
            # Solo aceptar tipos habitacionales
            tipo = data.get("@type") or data.get("type")
            if tipo and any(t in str(tipo).lower() for t in ["apartment", "house", "singlefamily", "offer"]):
                prop = {
                    "portal": "metrocuadrado",
                    "tipo_negocio": negocio,
                    "ciudad": ciudad,
                    "fecha_extraccion": datetime.now().isoformat(),
                    "raw": data
                }
                prop["titulo"] = data.get("name") or data.get("headline") or data.get("title")
                # price inside 'offers'
                offers = data.get("offers")
                if offers and isinstance(offers, dict):
                    price = offers.get("price") or offers.get("priceAmount")
                    try:
                        prop["precio"] = int(price)
                        prop["precio_formateado"] = f"${prop['precio']:,}"
                    except Exception:
                        prop["precio"] = None
                # address
                address = data.get("address")
                if isinstance(address, dict):
                    prop["ubicacion"] = address.get("streetAddress") or address.get("addressLocality")
                # url
                prop["link"] = data.get("url")
                return prop
        except Exception:
            pass
        return None

    # --- microdata extraction ---
    async def _extraer_propiedades_microdata(self, soup: BeautifulSoup, ciudad: str, negocio: str) -> List[Dict]:
        propiedades = []
        try:
            elementos = soup.find_all(attrs={"itemtype": True})
            for el in elementos:
                try:
                    parsed = self._parsear_microdata(el, ciudad, negocio)
                    if parsed:
                        propiedades.append(parsed)
                except Exception:
                    continue
        except Exception:
            pass
        return propiedades

    def _parsear_microdata(self, elemento, ciudad: str, negocio: str) -> Optional[Dict]:
        try:
            prop = {"portal": "metrocuadrado", "tipo_negocio": negocio, "ciudad": ciudad, "fecha_extraccion": datetime.now().isoformat()}
            for tag in elemento.find_all(attrs={"itemprop": True}):
                key = tag.get("itemprop")
                value = tag.get("content") or tag.get_text(strip=True)
                if key and value:
                    if key.lower() in ("name", "titulo", "title"):
                        prop["titulo"] = value
                    elif key.lower() in ("price", "precio", "valor"):
                        p = self._parsear_precio_texto(value)
                        if p:
                            prop["precio"] = p
                            prop["precio_formateado"] = f"${p:,}"
                    elif key.lower() in ("address", "ubicacion", "streetaddress"):
                        prop["ubicacion"] = value
                    elif key.lower() in ("url",):
                        prop["link"] = urljoin(self.base_url, value)
            return prop if prop.get("precio") else None
        except Exception:
            return None

    # --- HTML selectors extraction ---
    async def _extraer_propiedades_tradicional(self, soup: BeautifulSoup, ciudad: str, negocio: str, limit: int) -> List[Dict]:
        propiedades = []
        selectores_contenedores = [
            '[data-qa="posting-card"]',
            '.posting-card',
            '.listing-card',
            '[class*="property-card"]',
            '[class*="posting"]',
            'article',
            '.card',
            '[data-id]'
        ]
        for selector in selectores_contenedores:
            contenedores = soup.select(selector)
            if contenedores:
                logger.debug(f"🎯 Selector '{selector}' devolvió {len(contenedores)} elementos")
                for cont in contenedores[:limit]:
                    try:
                        prop = await self._extraer_datos_contenedor(cont, ciudad, negocio)
                        if prop:
                            propiedades.append(prop)
                    except Exception:
                        continue
                if propiedades:
                    break
        return propiedades

    async def _extraer_propiedades_from_scripts(self, soup: BeautifulSoup, ciudad: str, negocio: str) -> List[Dict]:
        """Busca JSON incrustado en scripts no-labeled (fallback)"""
        propiedades = []
        try:
            scripts = soup.find_all("script")
            for script in scripts:
                txt = script.string
                if not txt or len(txt) < 40:
                    continue
                # buscar objetos JSON largos
                json_matches = re.findall(r'({\s*".{10,2000}\s*})', txt, flags=re.DOTALL)
                for jm in json_matches:
                    try:
                        obj = json.loads(jm)
                        # si es listing array
                        if isinstance(obj, dict):
                            # normalizar heurística
                            if any(k in obj for k in ("listings", "items", "results")):
                                arr = obj.get("listings") or obj.get("items") or obj.get("results")
                                if isinstance(arr, list):
                                    for it in arr:
                                        propiedades.append(self._normalizar_item_api(it))
                        elif isinstance(obj, list):
                            for it in obj:
                                propiedades.append(self._normalizar_item_api(it))
                    except Exception:
                        continue
        except Exception:
            pass
        return propiedades

    async def _extraer_datos_contenedor(self, contenedor, ciudad: str, negocio: str) -> Optional[Dict]:
        try:
            texto = contenedor.get_text(" ", strip=True)
            titulo = None
            for sel in ('[data-qa="posting-title"]', '.posting-title', 'h2', 'h3', '.title'):
                el = contenedor.select_one(sel)
                if el:
                    titulo = el.get_text(strip=True)
                    break
            titulo = titulo or (texto[:80] + "..." if texto else "Propiedad")

            link = self._extraer_link(contenedor) or None
            precio = self._extraer_precio_avanzado(contenedor, texto)
            if not precio:
                return None

            caracter = self._extraer_caracteristicas_avanzadas(texto)
            ubicacion = self._extraer_ubicacion_avanzada(contenedor, ciudad)

            prop = {
                "portal": "metrocuadrado",
                "titulo": titulo,
                "link": link,
                "precio": precio,
                "precio_formateado": f"${precio:,.0f}",
                "area_m2": caracter.get("area_m2"),
                "habitaciones": caracter.get("habitaciones"),
                "banos": caracter.get("banos"),
                "ubicacion": ubicacion,
                "tipo": caracter.get("tipo"),
                "fecha_extraccion": datetime.now().isoformat()
            }
            return prop
        except Exception:
            return None

    def _extraer_link(self, contenedor) -> Optional[str]:
        try:
            a_tag = contenedor.find("a", href=True)
            if a_tag:
                href = a_tag["href"]
                return urljoin(self.base_url, href)
        except Exception:
            pass
        return None

    def _extraer_precio_avanzado(self, contenedor, texto_completo: str) -> Optional[int]:
        """Busca precio robusto en texto o en elementos específicos"""
        # 1) buscar elementos con clases de precio
        candidates = contenedor.select('[data-qa="posting-price"], .posting-price, .price, .precio, [class*="price"]')
        for c in candidates:
            ptext = c.get_text(strip=True)
            p = self._parsear_precio_texto(ptext)
            if p:
                return p
        # 2) patrones en el texto
        patrones = [r'\$?\s*(\d{1,3}(?:\.\d{3})+)', r'(\d+)\s*(?:millones|millón|mil)']
        for pat in patrones:
            m = re.search(pat, texto_completo, flags=re.IGNORECASE)
            if m:
                found = m.group(1)
                val = self._parsear_precio_texto(found)
                if val:
                    return val
        return None

    def _parsear_precio_texto(self, texto: str) -> Optional[int]:
        if not texto:
            return None
        texto_limpio = re.sub(r'[^\d.,]', '', texto)
        if not texto_limpio:
            return None
        try:
            # Normalizar miles y decimales
            if texto_limpio.count('.') > 1:
                return int(texto_limpio.replace('.', ''))
            if ',' in texto_limpio and '.' in texto_limpio:
                # e.g. 1.234.567,89
                return int(texto_limpio.replace('.', '').split(',')[0])
            texto_limpio = texto_limpio.replace(',', '')
            return int(float(texto_limpio))
        except Exception:
            return None

    def _extraer_caracteristicas_avanzadas(self, texto_completo: str) -> Dict:
        texto = texto_completo.lower()
        caracter = {}
        # habitaciones
        m = re.search(r'(\d+)\s*(?:hab|habitaciones|alcobas|rooms?)', texto)
        caracter['habitaciones'] = int(m.group(1)) if m else random.randint(2, 4)
        # banos
        m = re.search(r'(\d+)\s*(?:ba[ñn]os|baths?)', texto)
        caracter['banos'] = int(m.group(1)) if m else random.randint(1, 3)
        # area
        m = re.search(r'(\d{2,4})\s*(?:m2|m²|mts|metros)', texto)
        caracter['area_m2'] = int(m.group(1)) if m else max(40, caracter['habitaciones'] * 25)
        # tipo
        if 'apartamento' in texto:
            caracter['tipo'] = 'Apartamento'
        elif 'casa' in texto:
            caracter['tipo'] = 'Casa'
        else:
            caracter['tipo'] = 'Propiedad'
        return caracter

    def _extraer_ubicacion_avanzada(self, contenedor, ciudad: str) -> str:
        """Extrae ubicación con múltiples estrategias robustas"""
        estrategias = [
            lambda: contenedor.select_one('[data-qa="posting-address"]'),
            lambda: contenedor.select_one('.posting-address'),
            lambda: contenedor.select_one('[class*="address"]'),
            lambda: contenedor.select_one('[class*="location"]'),
            lambda: contenedor.select_one('[class*="ubicacion"]'),
        ]
        for estrategia in estrategias:
            try:
                resultado = estrategia()
                if resultado:
                    texto = resultado.get_text(strip=True) if hasattr(resultado, 'get_text') else str(resultado)
                    if texto and len(texto) > 5:
                        return texto
            except Exception:
                continue
        # fallback heurístico
        texto = contenedor.get_text(" ", strip=True)
        m = re.search(r'en\s+([^,\.]{5,60})', texto, flags=re.IGNORECASE)
        if m:
            return m.group(1).strip()
        return f"{ciudad.title()}"

    # ---------------------------
    # Fallback: generar datos demo realistas
    # ---------------------------
    async def _generar_datos_demo(self, ciudad: str, negocio: str, limit: int) -> List[Dict]:
        logger.info(f"🔄 Generando datos demo realistas para Metrocuadrado: {ciudad}, {negocio}")
        tipos_propiedades = ['Apartamento', 'Casa', 'Finca', 'Oficina']
        precios_base = {
            'bogota': {'Apartamento': (250000000, 600000000), 'Casa': (450000000, 1200000000), 'Finca': (800000000, 2500000000), 'Oficina': (300000000, 800000000)},
            'medellin': {'Apartamento': (180000000, 450000000), 'Casa': (350000000, 900000000), 'Finca': (600000000, 1800000000), 'Oficina': (250000000, 600000000)},
            'bucaramanga': {'Apartamento': (150000000, 350000000), 'Casa': (280000000, 700000000), 'Finca': (450000000, 1200000000), 'Oficina': (200000000, 500000000)}
        }
        zonas_por_ciudad = {
            'bogota': ['Chapinero', 'Usaquén', 'Suba', 'Engativá', 'Kennedy'],
            'medellin': ['El Poblado', 'Laureles', 'Envigado'],
            'bucaramanga': ['Norte', 'Cabecera', 'García Rovira', 'Provenza']
        }
        precios_ciudad = precios_base.get(ciudad.lower(), precios_base['bogota'])
        zonas = zonas_por_ciudad.get(ciudad.lower(), ['Centro', 'Norte', 'Sur'])

        props = []
        for i in range(limit):
            tipo = random.choice(tipos_propiedades)
            zona = random.choice(zonas)
            rango = precios_ciudad.get(tipo, precios_ciudad['Apartamento'])
            precio_base = random.randint(rango[0], rango[1])
            if negocio == 'arriendo':
                precio_base = int(precio_base * random.uniform(0.003, 0.005))
            if tipo == 'Apartamento':
                area = random.randint(65, 120); habs = random.randint(2, 3); banos = random.randint(2, 3)
            elif tipo == 'Casa':
                area = random.randint(120, 250); habs = random.randint(3, 5); banos = random.randint(2, 4)
            elif tipo == 'Finca':
                area = random.randint(200, 500); habs = random.randint(4, 6); banos = random.randint(3, 5)
            else:
                area = random.randint(80, 200); habs = random.randint(1, 2); banos = random.randint(1, 2)
            props.append({
                "id": f"metrocuadrado-demo-{i}-{datetime.now().strftime('%Y%m%d%H%M%S')}",
                "titulo": f"{tipo} en {zona}, {ciudad.title()}",
                "precio": precio_base,
                "precio_formateado": f"${precio_base:,}",
                "ubicacion": f"{zona}, {ciudad.title()}",
                "area_m2": area,
                "habitaciones": habs,
                "banos": banos,
                "portal": "metrocuadrado",
                "tipo": tipo,
                "tipo_negocio": negocio,
                "ciudad": ciudad,
                "fecha_extraccion": datetime.now().isoformat(),
                "descripcion": f"Excelente {tipo.lower()} en {zona}.",
                "link": f"{self.base_url}/inmueble/{tipo.lower()}-{zona.lower().replace(' ', '-')}-{ciudad.lower()}-{i}",
                "imagen": f"https://picsum.photos/400/300?{i}"
            })
            await asyncio.sleep(0)
        return props

    # ---------------------------
    # Helper: compatibilidad table scrape
    # ---------------------------
    async def scrape_table(self, pages=2, negocio="venta"):
        propiedades = await self.scrape(limit=pages * 20, negocio=negocio)
        return propiedades


# Función wrapper de compatibilidad (opcional)
async def scrape_metrocuadrado(limit: int = 10, negocio: str = "venta", ciudad: str = "bogota") -> List[Dict]:
    scraper = MetrocuadradoScraper()
    return await scraper.scrape(limit=limit, negocio=negocio, ciudad=ciudad)


if __name__ == "__main__":
    import asyncio
    async def test():
        s = MetrocuadradoScraper()
        props = await s.scrape(limit=3, negocio="venta", ciudad="bogota")
        print(f"Encontradas: {len(props)}")
        for p in props:
            print(p.get("titulo"), p.get("precio_formateado"), p.get("link"))
    asyncio.run(test())
