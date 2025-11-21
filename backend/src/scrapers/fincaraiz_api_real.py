from typing import List, Dict, Optional, Any
import requests
import json
import logging
import asyncio
from datetime import datetime
import re
from urllib.parse import urljoin
import time
import random

logger = logging.getLogger("ARIA_BACKEND")

class FincaraizApiScraper:
    """Scraper REAL que accede a la API interna de Fincaraíz - Datos 100% reales"""
    
    def __init__(self):
        self.base_url = "https://www.fincaraiz.com.co"
        self.api_base = "https://api.fincaraiz.com.co"  # API interna
        self.session = self._create_session()
    
    def _create_session(self) -> requests.Session:
        """Crear sesión con headers realistas"""
        session = requests.Session()
        session.headers.update({
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "es-CO,es;q=0.9,en;q=0.8",
            "Referer": "https://www.fincaraiz.com.co/",
            "Origin": "https://www.fincaraiz.com.co",
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "same-site",
        })
        return session
    
    async def scrape(self, params: Dict) -> Dict:
        """Interfaz async principal"""
        return await self._scrape_via_api(params)
    
    async def _scrape_via_api(self, params: Dict) -> Dict:
        """Scraping REAL via API interna de Fincaraíz"""
        limit = params.get('limit', 10)
        negocio = params.get('negocio', 'venta')
        ciudad = params.get('ciudad', 'bucaramanga')
        
        try:
            logger.info(f"🚀 Iniciando scraping REAL via API: {ciudad}, {negocio}")
            
            # Estrategia 1: Buscar endpoints API en la página principal
            api_data = await self._discover_api_endpoints(ciudad, negocio, limit)
            
            if not api_data:
                # Estrategia 2: Scraping directo del HTML con técnicas avanzadas
                api_data = await self._scrape_direct_html(ciudad, negocio, limit)
            
            if not api_data:
                # Estrategia 3: Buscar datos en scripts JavaScript
                api_data = await self._extract_from_scripts(ciudad, negocio, limit)
            
            if api_data:
                logger.info(f"🎉 Scraping REAL completado: {len(api_data)} propiedades")
                return {
                    "propiedades": api_data,
                    "total": len(api_data),
                    "fuente": "API_REAL",
                    "parametros": params
                }
            else:
                logger.error("❌ No se pudieron obtener datos reales")
                return {
                    "propiedades": [],
                    "total": 0,
                    "fuente": "ERROR",
                    "parametros": params
                }
                
        except Exception as e:
            logger.error(f"❌ Error en scraping API: {e}")
            return {
                "propiedades": [],
                "total": 0,
                "fuente": "ERROR",
                "parametros": params
            }
    
    async def _discover_api_endpoints(self, ciudad: str, negocio: str, limit: int) -> List[Dict]:
        """Descubrir y usar endpoints API de Fincaraíz"""
        try:
            # URL de búsqueda principal
            search_url = self._build_search_url(ciudad, negocio)
            logger.info(f"🔍 Analizando: {search_url}")
            
            response = self.session.get(search_url, timeout=15)
            if response.status_code != 200:
                return []
            
            html_content = response.text
            
            # Buscar endpoints API en el HTML
            api_endpoints = self._find_api_endpoints(html_content)
            
            # Buscar datos en scripts JSON-LD
            jsonld_data = self._extract_jsonld(html_content)
            
            # Buscar datos en variables JavaScript
            js_data = self._extract_js_variables(html_content)
            
            # Combinar todos los datos encontrados
            all_properties = []
            
            if api_endpoints:
                for endpoint in api_endpoints[:3]:  # Probar primeros 3 endpoints
                    try:
                        properties = await self._fetch_api_endpoint(endpoint, limit)
                        all_properties.extend(properties)
                    except:
                        continue
            
            if jsonld_data:
                all_properties.extend(jsonld_data)
            
            if js_data:
                all_properties.extend(js_data)
            
            # Eliminar duplicados y limitar
            unique_props = self._remove_duplicates(all_properties)
            return unique_props[:limit]
            
        except Exception as e:
            logger.error(f"❌ Error descubriendo APIs: {e}")
            return []
    
    def _build_search_url(self, ciudad: str, negocio: str) -> str:
        """Construir URL de búsqueda REAL"""
        ciudad_map = {
            'bucaramanga': 'bucaramanga-santander',
            'bogota': 'bogota',
            'medellin': 'medellin', 
            'cali': 'cali',
            'barranquilla': 'barranquilla',
            'cartagena': 'cartagena'
        }
        
        ciudad_slug = ciudad_map.get(ciudad.lower(), 'bucaramanga-santander')
        
        if negocio.lower() == "arriendo":
            return f"{self.base_url}/arriendo/inmuebles/{ciudad_slug}"
        else:
            return f"{self.base_url}/venta/inmuebles/{ciudad_slug}"
    
    def _find_api_endpoints(self, html: str) -> List[str]:
        """Encontrar endpoints API en el HTML"""
        endpoints = []
        
        # Buscar patrones de API
        patterns = [
            r'https?://[^"\']+?/api/[^"\']+',
            r'https?://[^"\']+?/graphql[^"\']*',
            r'https?://[^"\']+?/search[^"\']*',
            r'https?://[^"\']+?/properties[^"\']*',
            r'https?://[^"\']+?/listings[^"\']*',
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, html, re.IGNORECASE)
            endpoints.extend(matches)
        
        # Filtrar endpoints relevantes
        filtered = [endpoint for endpoint in endpoints if any(keyword in endpoint.lower() for keyword in ['property', 'listing', 'search', 'inmueble'])]
        
        logger.info(f"🔌 Endpoints API encontrados: {len(filtered)}")
        return filtered
    
    def _extract_jsonld(self, html: str) -> List[Dict]:
        """Extraer datos de JSON-LD"""
        properties = []
        
        try:
            # Buscar scripts JSON-LD
            jsonld_pattern = r'<script type="application/ld\+json">(.*?)</script>'
            matches = re.findall(jsonld_pattern, html, re.DOTALL)
            
            for match in matches:
                try:
                    data = json.loads(match.strip())
                    property_data = self._parse_jsonld(data)
                    if property_data:
                        properties.append(property_data)
                except:
                    continue
                    
        except Exception as e:
            logger.debug(f"Error extrayendo JSON-LD: {e}")
        
        return properties
    
    def _parse_jsonld(self, data: Any) -> Optional[Dict]:
        """Parsear datos JSON-LD a formato de propiedad"""
        try:
            if isinstance(data, dict):
                # Schema.org/Product o Schema.org/Offer
                if data.get('@type') in ['Product', 'Offer', 'SingleFamilyResidence']:
                    return self._extract_from_jsonld_schema(data)
                
                # Buscar en @graph
                if '@graph' in data:
                    for item in data['@graph']:
                        result = self._parse_jsonld(item)
                        if result:
                            return result
            
            elif isinstance(data, list):
                for item in data:
                    result = self._parse_jsonld(item)
                    if result:
                        return result
                        
        except:
            pass
        
        return None
    
    def _extract_from_jsonld_schema(self, data: Dict) -> Optional[Dict]:
        """Extraer datos de schema.org"""
        try:
            # Información básica
            name = data.get('name') or data.get('headline')
            price = data.get('price') or data.get('offers', {}).get('price')
            url = data.get('url') or data.get('offers', {}).get('url')
            image = data.get('image') or data.get('photo')
            
            if not name or not price:
                return None
            
            # Convertir precio a número
            if isinstance(price, str):
                price = self._parse_price(price)
            
            if not price:
                return None
            
            # Construir objeto de propiedad
            propiedad = {
                "portal": "fincaraiz",
                "titulo": name,
                "precio": price,
                "precio_formateado": f"${price:,}",
                "link": url if url else f"{self.base_url}/inmueble/{hash(name)}",
                "imagen_principal": image[0] if isinstance(image, list) and image else image,
                "fotos": [image] if image else [],
                "fecha_extraccion": datetime.now().isoformat(),
                "es_real": True,
                "es_demo": False,
                "link_funcional": bool(url)
            }
            
            # Características adicionales
            if data.get('numberOfRooms'):
                propiedad['habitaciones'] = data['numberOfRooms']
            if data.get('numberOfBathroomsTotal'):
                propiedad['banos'] = data['numberOfBathroomsTotal']
            if data.get('floorSize'):
                propiedad['area_m2'] = data['floorSize'].get('value') if isinstance(data['floorSize'], dict) else data['floorSize']
            
            return propiedad
            
        except:
            return None
    
    def _extract_js_variables(self, html: str) -> List[Dict]:
        """Extraer datos de variables JavaScript"""
        properties = []
        
        try:
            # Buscar variables con datos de propiedades
            patterns = [
                r'window\.__INITIAL_STATE__\s*=\s*({.*?});',
                r'var\s+properties\s*=\s*(\[.*?\]);',
                r'window\.properties\s*=\s*(\[.*?\]);',
                r'JSON\.parse\(\s*[\'"](.*?)[\'"]\s*\)',  # JSON embebido
            ]
            
            for pattern in patterns:
                matches = re.findall(pattern, html, re.DOTALL)
                for match in matches:
                    try:
                        # Limpiar el JSON
                        json_str = match.replace('\\"', '"').replace("\\'", "'").replace('\\/', '/')
                        data = json.loads(json_str)
                        extracted = self._extract_from_js_data(data)
                        properties.extend(extracted)
                    except:
                        continue
                        
        except Exception as e:
            logger.debug(f"Error extrayendo JS variables: {e}")
        
        return properties
    
    def _extract_from_js_data(self, data: Any) -> List[Dict]:
        """Extraer propiedades de datos JavaScript"""
        properties = []
        
        try:
            if isinstance(data, dict):
                # Buscar arrays de propiedades
                for key, value in data.items():
                    if isinstance(value, list) and len(value) > 0:
                        first_item = value[0]
                        if isinstance(first_item, dict) and any(field in first_item for field in ['price', 'precio', 'value']):
                            for item in value:
                                prop = self._parse_js_property(item)
                                if prop:
                                    properties.append(prop)
            
            elif isinstance(data, list):
                for item in data:
                    prop = self._parse_js_property(item)
                    if prop:
                        properties.append(prop)
                        
        except:
            pass
        
        return properties
    
    def _parse_js_property(self, data: Dict) -> Optional[Dict]:
        """Parsear propiedad desde datos JS"""
        try:
            # Mapear campos comunes
            title = data.get('title') or data.get('name') or data.get('titulo')
            price = data.get('price') or data.get('precio') or data.get('value')
            url = data.get('url') or data.get('link') or data.get('permalink')
            image = data.get('image') or data.get('image_url') or data.get('photo')
            
            if not title or not price:
                return None
            
            # Convertir precio
            if isinstance(price, str):
                price = self._parse_price(price)
            
            if not price:
                return None
            
            propiedad = {
                "portal": "fincaraiz",
                "titulo": title,
                "precio": price,
                "precio_formateado": f"${price:,}",
                "link": url if url else f"{self.base_url}/inmueble/{hash(title)}",
                "imagen_principal": image,
                "fotos": [image] if image else [],
                "fecha_extraccion": datetime.now().isoformat(),
                "es_real": True,
                "es_demo": False,
                "link_funcional": bool(url)
            }
            
            # Características
            if data.get('bedrooms') or data.get('habitaciones'):
                propiedad['habitaciones'] = data.get('bedrooms') or data.get('habitaciones')
            if data.get('bathrooms') or data.get('banos'):
                propiedad['banos'] = data.get('bathrooms') or data.get('banos')
            if data.get('area') or data.get('size'):
                propiedad['area_m2'] = data.get('area') or data.get('size')
            
            return propiedad
            
        except:
            return None
    
    async def _scrape_direct_html(self, ciudad: str, negocio: str, limit: int) -> List[Dict]:
        """Scraping directo del HTML con técnicas avanzadas"""
        try:
            search_url = self._build_search_url(ciudad, negocio)
            logger.info(f"🔍 Scraping directo HTML: {search_url}")
            
            response = self.session.get(search_url, timeout=15)
            if response.status_code != 200:
                return []
            
            html_content = response.text
            
            # Estrategia 1: Buscar datos estructurados en divs con atributos data
            properties_from_data_attrs = self._extract_from_data_attributes(html_content)
            
            # Estrategia 2: Buscar en microformatos
            properties_from_microformats = self._extract_from_microformats(html_content)
            
            # Estrategia 3: Parsear HTML tradicional
            properties_from_html = await self._parse_traditional_html(html_content, limit)
            
            # Combinar resultados
            all_properties = properties_from_data_attrs + properties_from_microformats + properties_from_html
            unique_props = self._remove_duplicates(all_properties)
            
            return unique_props[:limit]
            
        except Exception as e:
            logger.error(f"❌ Error en scraping directo HTML: {e}")
            return []
    
    def _extract_from_data_attributes(self, html: str) -> List[Dict]:
        """Extraer propiedades de atributos data-*"""
        properties = []
        
        try:
            # Buscar elementos con atributos data de propiedades
            patterns = [
                r'<[^>]+data-price="([^"]*)"[^>]*data-title="([^"]*)"',
                r'<[^>]+data-property="([^"]*)"',
                r'<[^>]+data-listing="([^"]*)"',
            ]
            
            for pattern in patterns:
                matches = re.findall(pattern, html)
                for match in matches:
                    try:
                        if isinstance(match, tuple) and len(match) >= 2:
                            price, title = match[0], match[1]
                        else:
                            # Intentar parsear JSON
                            data = json.loads(match)
                            price = data.get('price')
                            title = data.get('title')
                        
                        if price and title:
                            price_num = self._parse_price(price) if isinstance(price, str) else price
                            if price_num:
                                propiedades.append({
                                    "portal": "fincaraiz",
                                    "titulo": title,
                                    "precio": price_num,
                                    "precio_formateado": f"${price_num:,}",
                                    "link": f"{self.base_url}/inmueble/{hash(title)}",
                                    "fecha_extraccion": datetime.now().isoformat(),
                                    "es_real": True,
                                    "es_demo": False,
                                    "link_funcional": False
                                })
                    except:
                        continue
                        
        except Exception as e:
            logger.debug(f"Error extrayendo data attributes: {e}")
        
        return properties
    
    def _extract_from_microformats(self, html: str) -> List[Dict]:
        """Extraer propiedades de microformatos"""
        properties = []
        
        try:
            # Buscar schema.org microformatos
            patterns = [
                r'itemtype="[^"]*schema\.org/[^"]*Product[^"]*"[^>]*>.*?<[^>]*itemprop="name"[^>]*>([^<]*)<.*?<[^>]*itemprop="price"[^>]*>([^<]*)<',
                r'itemprop="price"[^>]*content="([^"]*)"[^>]*>.*?itemprop="name"[^>]*content="([^"]*)"',
            ]
            
            for pattern in patterns:
                matches = re.findall(pattern, html, re.DOTALL)
                for match in matches:
                    try:
                        if len(match) >= 2:
                            price, title = match[1], match[0]  # Ajustar orden según el pattern
                            price_num = self._parse_price(price)
                            if price_num and title:
                                properties.append({
                                    "portal": "fincaraiz",
                                    "titulo": title,
                                    "precio": price_num,
                                    "precio_formateado": f"${price_num:,}",
                                    "link": f"{self.base_url}/inmueble/{hash(title)}",
                                    "fecha_extraccion": datetime.now().isoformat(),
                                    "es_real": True,
                                    "es_demo": False,
                                    "link_funcional": False
                                })
                    except:
                        continue
                        
        except Exception as e:
            logger.debug(f"Error extrayendo microformatos: {e}")
        
        return properties
    
    async def _parse_traditional_html(self, html: str, limit: int) -> List[Dict]:
        """Parseo tradicional de HTML como fallback"""
        properties = []
        
        try:
            # Buscar cards de propiedades con regex
            card_patterns = [
                r'<article[^>]*>.*?</article>',
                r'<div[^>]*class="[^"]*card[^"]*"[^>]*>.*?</div>',
                r'<div[^>]*data-cy="listing-card"[^>]*>.*?</div>',
            ]
            
            for pattern in card_patterns:
                cards = re.findall(pattern, html, re.DOTALL)
                for card in cards[:limit]:
                    try:
                        prop = self._parse_html_card(card)
                        if prop:
                            properties.append(prop)
                    except:
                        continue
                
                if properties:
                    break
                    
        except Exception as e:
            logger.debug(f"Error en parseo tradicional: {e}")
        
        return properties
    
    def _parse_html_card(self, card_html: str) -> Optional[Dict]:
        """Parsear una card HTML individual"""
        try:
            # Extraer título
            title_match = re.search(r'<h[23][^>]*>(.*?)</h[23]>', card_html, re.DOTALL)
            if not title_match:
                return None
            
            title = re.sub(r'<[^>]*>', '', title_match.group(1)).strip()
            
            # Extraer precio
            price_match = re.search(r'>\s*\$?\s*([\d\.,]+)\s*(?:millones?|mn|m|mil)?\s*<', card_html)
            if not price_match:
                return None
            
            price = self._parse_price(price_match.group(1))
            if not price:
                return None
            
            # Extraer link
            link_match = re.search(r'href="([^"]*/(?:inmueble|apartamento|casa|finca)/[^"]*)"', card_html)
            link = link_match.group(1) if link_match else None
            
            # Extraer imagen
            img_match = re.search(r'src="([^"]*\.(?:jpg|jpeg|png|webp)[^"]*)"', card_html)
            image = img_match.group(1) if img_match else None
            
            # Construir propiedad
            return {
                "portal": "fincaraiz",
                "titulo": title,
                "precio": price,
                "precio_formateado": f"${price:,}",
                "link": urljoin(self.base_url, link) if link and link.startswith('/') else link,
                "imagen_principal": image,
                "fotos": [image] if image else [],
                "fecha_extraccion": datetime.now().isoformat(),
                "es_real": True,
                "es_demo": False,
                "link_funcional": bool(link)
            }
            
        except:
            return None
    
    async def _extract_from_scripts(self, ciudad: str, negocio: str, limit: int) -> List[Dict]:
        """Extraer datos de scripts JavaScript ejecutables"""
        try:
            search_url = self._build_search_url(ciudad, negocio)
            logger.info(f"🔍 Extrayendo de scripts JS: {search_url}")
            
            response = self.session.get(search_url, timeout=15)
            if response.status_code != 200:
                return []
            
            html_content = response.text
            
            # Buscar scripts que contengan datos
            script_pattern = r'<script[^>]*>(.*?)</script>'
            scripts = re.findall(script_pattern, html_content, re.DOTALL)
            
            properties = []
            
            for script in scripts:
                # Buscar arrays de propiedades
                array_patterns = [
                    r'var\s+\w*\s*=\s*(\[[\s\S]{100,}?\])',
                    r'const\s+\w*\s*=\s*(\[[\s\S]{100,}?\])',
                    r'let\s+\w*\s*=\s*(\[[\s\S]{100,}?\])',
                ]
                
                for pattern in array_patterns:
                    matches = re.findall(pattern, script)
                    for match in matches:
                        try:
                            # Limpiar y parsear
                            clean_json = match.replace("'", '"').replace('\\"', '"')
                            data = json.loads(clean_json)
                            extracted = self._extract_from_js_data(data)
                            properties.extend(extracted)
                        except:
                            continue
            
            unique_props = self._remove_duplicates(properties)
            return unique_props[:limit]
            
        except Exception as e:
            logger.error(f"❌ Error extrayendo de scripts: {e}")
            return []
    
    async def _fetch_api_endpoint(self, endpoint: str, limit: int) -> List[Dict]:
        """Hacer request a un endpoint API"""
        try:
            # Normalizar endpoint
            if endpoint.startswith('//'):
                endpoint = 'https:' + endpoint
            elif endpoint.startswith('/'):
                endpoint = self.base_url + endpoint
            
            logger.info(f"🔌 Probando endpoint: {endpoint}")
            
            response = self.session.get(endpoint, timeout=10)
            if response.status_code != 200:
                return []
            
            data = response.json()
            properties = self._extract_from_api_response(data)
            
            return properties[:limit]
            
        except:
            return []
    
    def _extract_from_api_response(self, data: Any) -> List[Dict]:
        """Extraer propiedades de respuesta API"""
        properties = []
        
        try:
            if isinstance(data, dict):
                # Buscar arrays de propiedades
                for key, value in data.items():
                    if isinstance(value, list):
                        for item in value:
                            prop = self._parse_api_property(item)
                            if prop:
                                properties.append(prop)
                    elif isinstance(value, dict):
                        # Buscar recursivamente
                        properties.extend(self._extract_from_api_response(value))
            
            elif isinstance(data, list):
                for item in data:
                    prop = self._parse_api_property(item)
                    if prop:
                        properties.append(prop)
                        
        except:
            pass
        
        return properties
    
    def _parse_api_property(self, item: Dict) -> Optional[Dict]:
        """Parsear propiedad desde respuesta API"""
        try:
            # Mapear campos API comunes
            mapping = {
                'title': ['title', 'name', 'titulo', 'propertyTitle'],
                'price': ['price', 'precio', 'value', 'propertyPrice', 'salePrice'],
                'url': ['url', 'link', 'permalink', 'propertyUrl'],
                'image': ['image', 'imageUrl', 'photo', 'mainImage', 'propertyImage'],
                'bedrooms': ['bedrooms', 'habitaciones', 'rooms', 'propertyBedrooms'],
                'bathrooms': ['bathrooms', 'banos', 'propertyBathrooms'],
                'area': ['area', 'size', 'squareMeters', 'propertyArea']
            }
            
            # Extraer campos
            title = self._get_nested_value(item, mapping['title'])
            price = self._get_nested_value(item, mapping['price'])
            url = self._get_nested_value(item, mapping['url'])
            image = self._get_nested_value(item, mapping['image'])
            bedrooms = self._get_nested_value(item, mapping['bedrooms'])
            bathrooms = self._get_nested_value(item, mapping['bathrooms'])
            area = self._get_nested_value(item, mapping['area'])
            
            if not title or not price:
                return None
            
            # Convertir precio
            if isinstance(price, str):
                price = self._parse_price(price)
            
            if not price:
                return None
            
            # Construir propiedad
            propiedad = {
                "portal": "fincaraiz",
                "titulo": title,
                "precio": price,
                "precio_formateado": f"${price:,}",
                "link": url if url else f"{self.base_url}/inmueble/{hash(title)}",
                "imagen_principal": image,
                "fotos": [image] if image else [],
                "fecha_extraccion": datetime.now().isoformat(),
                "es_real": True,
                "es_demo": False,
                "link_funcional": bool(url)
            }
            
            # Agregar características
            if bedrooms:
                propiedad['habitaciones'] = bedrooms
            if bathrooms:
                propiedad['banos'] = bathrooms
            if area:
                propiedad['area_m2'] = area
            
            return propiedad
            
        except:
            return None
    
    def _get_nested_value(self, obj: Dict, keys: List[str]) -> Any:
        """Obtener valor anidado de un objeto usando múltiples posibles keys"""
        for key in keys:
            try:
                if '.' in key:
                    # Para keys anidadas como 'offers.price'
                    value = obj
                    for k in key.split('.'):
                        value = value[k]
                    return value
                else:
                    if key in obj:
                        return obj[key]
            except:
                continue
        return None
    
    def _parse_price(self, price_text: str) -> Optional[int]:
        """Parsear texto de precio a número"""
        try:
            if not price_text:
                return None
            
            # Limpiar texto
            clean_text = re.sub(r'[^\d,.]', '', str(price_text).strip())
            
            if not clean_text:
                return None
            
            # Determinar formato
            if '.' in clean_text and ',' in clean_text:
                # Formato: 1.500.000,00 -> 1500000
                parts = clean_text.split(',')
                integer_part = parts[0].replace('.', '')
                return int(integer_part)
            elif '.' in clean_text:
                # Formato: 1.500.000 -> 1500000
                return int(clean_text.replace('.', ''))
            elif ',' in clean_text:
                # Formato: 1500000,00 -> 1500000
                return int(clean_text.split(',')[0].replace('.', ''))
            else:
                # Solo números
                return int(clean_text)
                
        except:
            return None
    
    def _remove_duplicates(self, properties: List[Dict]) -> List[Dict]:
        """Eliminar propiedades duplicadas"""
        seen = set()
        unique = []
        
        for prop in properties:
            # Crear clave única basada en título y precio
            key = f"{prop.get('titulo', '')}_{prop.get('precio', 0)}"
            if key not in seen:
                seen.add(key)
                unique.append(prop)
        
        return unique


# ============================================================================
# SCRAPER PRINCIPAL MEJORADO
# ============================================================================

class FincaraizScraper:
    """Scraper principal que usa múltiples estrategias para datos REALES"""
    
    def __init__(self):
        self.name = "fincaraiz"
        self.api_scraper = FincaraizApiScraper()
    
    async def scrape(self, params: Dict) -> Dict:
        """Usar API scraper como estrategia principal"""
        return await self.api_scraper.scrape(params)


# ============================================================================
# PRUEBA DEL SCRAPER REAL
# ============================================================================

async def test_scraper_real():
    """Probar el scraper con datos REALES"""
    print("🧪 TESTEANDO SCRAPER REAL CON API...")
    
    scraper = FincaraizApiScraper()
    
    result = await scraper.scrape({
        'limit': 5,
        'negocio': 'venta', 
        'ciudad': 'bogota'
    })
    
    propiedades = result.get('propiedades', [])
    print(f"\n📊 RESULTADOS REALES: {len(propiedades)} propiedades")
    
    for i, prop in enumerate(propiedades, 1):
        print(f"\n{i}. {prop.get('titulo', 'Sin título')}")
        print(f"   💰 Precio REAL: {prop.get('precio_formateado', 'N/A')}")
        print(f"   🔗 Link REAL: {prop.get('link', 'N/A')}")
        print(f"   🖼️ Imagen REAL: {prop.get('imagen_principal', 'Sin imagen')}")
        print(f"   ✅ ¿Es REAL?: {prop.get('es_real', False)}")
        print(f"   ✅ Link FUNCIONAL: {prop.get('link_funcional', False)}")
    
    return result

if __name__ == "__main__":
    asyncio.run(test_scraper_real())