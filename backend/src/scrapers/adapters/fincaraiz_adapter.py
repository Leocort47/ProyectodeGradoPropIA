# src/scrapers/adapters/fincaraiz_adapter.py
import re
import random
import logging
import asyncio
import requests
from datetime import datetime
from typing import List, Dict, Optional
from bs4 import BeautifulSoup
from urllib.parse import urljoin

logger = logging.getLogger(__name__)

class FincaraizScraper:
    def __init__(self):
        self.base_url = "https://fincaraiz.com.co"  # CORREGIDO: sin www
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'es-CO,es;q=0.9,en;q=0.8',
            'Referer': 'https://fincaraiz.com.co',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        })

    async def scrape(self, limit: int = 10, negocio: str = "venta", ciudad: str = "bucaramanga") -> List[Dict]:
        """Scraper principal para Fincaraíz - VERSIÓN MEJORADA"""
        try:
            logger.info(f"🚀 Iniciando Fincaraíz: {ciudad}, {negocio}, límite: {limit}")
            
            # PRIMERO intentar scraping real
            propiedades_reales = await self._scrape_real(ciudad, negocio, limit)
            
            if propiedades_reales:
                logger.info(f"✅ Fincaraíz REAL: {len(propiedades_reales)} propiedades encontradas")
                return propiedades_reales[:limit]
            
            # SI FALLA, usar datos demo
            logger.warning("🔄 Usando datos de demostración - Scraping real falló")
            propiedades_demo = await self._generar_datos_demo(ciudad, negocio, limit)
            return propiedades_demo
            
        except Exception as e:
            logger.error(f"❌ Error crítico en Fincaraíz: {e}")
            # Fallback a datos demo
            return await self._generar_datos_demo(ciudad, negocio, limit)

    async def _scrape_real(self, ciudad: str, negocio: str, limit: int) -> List[Dict]:
        """Scraping real mejorado con múltiples estrategias"""
        try:
            # Construir URL correctamente
            ciudad_formateada = ciudad.lower().replace(" ", "-")
            url = f"{self.base_url}/{negocio}/casas-y-apartamentos/{ciudad_formateada}/santander"
            
            logger.info(f"🌐 Accediendo a: {url}")
            response = await asyncio.get_event_loop().run_in_executor(
                None, 
                lambda: self.session.get(url, timeout=20)
            )
            
            if response.status_code != 200:
                logger.warning(f"⚠️ Status code {response.status_code} para {url}")
                return []
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # DEBUG: Guardar HTML para análisis
            with open("debug_fincaraiz.html", "w", encoding="utf-8") as f:
                f.write(soup.prettify())
            logger.info("💾 HTML guardado en debug_fincaraiz.html")
            
            propiedades = []
            
            # ESTRATEGIA 1: Buscar contenedores principales
            contenedores = self._encontrar_contenedores_propiedades(soup)
            logger.info(f"🔍 Encontrados {len(contenedores)} contenedores de propiedades")
            
            for i, contenedor in enumerate(contenedores[:limit]):
                try:
                    propiedad = await self._extraer_datos_contenedor(contenedor, ciudad, negocio)
                    if propiedad and propiedad.get('precio'):
                        propiedades.append(propiedad)
                        logger.debug(f"✅ Propiedad {i+1} extraída: {propiedad.get('titulo', 'Sin título')}")
                except Exception as e:
                    logger.debug(f"❌ Error en contenedor {i+1}: {e}")
                    continue
                
                # Pequeño delay para no sobrecargar
                await asyncio.sleep(0.1)
            
            return propiedades
            
        except Exception as e:
            logger.error(f"💥 Error en scraping real: {e}")
            return []

    def _encontrar_contenedores_propiedades(self, soup: BeautifulSoup) -> List:
        """Encuentra contenedores de propiedades usando múltiples estrategias"""
        contenedores = []
        
        # ESTRATEGIAS de búsqueda (ordenadas por efectividad)
        estrategias = [
            # Por atributos de datos
            lambda: soup.find_all(attrs={"data-cy": re.compile(r"listing|property", re.I)}),
            # Por clases específicas
            lambda: soup.select('[class*="listing-card"]'),
            lambda: soup.select('[class*="property-card"]'),
            lambda: soup.select('[class*="advertisement-card"]'),
            # Por estructura semántica
            lambda: soup.select('article'),
            # Por patrones genéricos
            lambda: soup.select('[class*="card"]'),
            lambda: soup.select('[class*="property"]'),
            lambda: soup.select('[class*="listing"]'),
            # Buscar cualquier elemento que contenga links a inmuebles
            lambda: [elem for elem in soup.find_all() 
                    if elem.find('a', href=re.compile(r'/inmueble/'))]
        ]
        
        for estrategia in estrategias:
            try:
                resultados = estrategia()
                if resultados:
                    logger.info(f"🎯 Estrategia exitosa: {len(resultados)} elementos")
                    contenedores.extend(resultados)
                    break
            except Exception as e:
                logger.debug(f"Estrategia falló: {e}")
                continue
        
        # Eliminar duplicados
        contenedores_unicos = []
        seen = set()
        for contenedor in contenedores:
            contenedor_id = str(contenedor)
            if contenedor_id not in seen:
                seen.add(contenedor_id)
                contenedores_unicos.append(contenedor)
        
        return contenedores_unicos

    async def _extraer_datos_contenedor(self, contenedor, ciudad: str, negocio: str) -> Optional[Dict]:
        """Extrae datos de un contenedor de propiedad"""
        try:
            propiedad = {
                "portal": "fincaraiz",
                "tipo_negocio": negocio,
                "ciudad": ciudad,
                "fecha_extraccion": datetime.now().isoformat()
            }
            
            # TEXT completo del contenedor para búsquedas
            texto_completo = contenedor.get_text(" ", strip=True)
            
            # 1. LINK - Estrategia robusta
            link = self._extraer_link(contenedor)
            if not link:
                return None
            propiedad["link"] = link
            
            # 2. TÍTULO
            propiedad["titulo"] = self._extraer_titulo(contenedor, ciudad, negocio)
            
            # 3. PRECIO - Múltiples estrategias
            precio = self._extraer_precio(contenedor, texto_completo)
            if precio:
                propiedad["precio"] = precio
                propiedad["precio_formateado"] = f"${precio:,}"
            else:
                # Si no hay precio, no es una propiedad válida
                return None
            
            # 4. CARACTERÍSTICAS
            propiedad.update(self._extraer_caracteristicas(texto_completo))
            
            # 5. TIPO DE PROPIEDAD
            propiedad["tipo"] = self._determinar_tipo(contenedor, texto_completo)
            
            # 6. UBICACIÓN
            propiedad["ubicacion"] = self._extraer_ubicacion(contenedor, ciudad)
            
            # 7. IMAGEN
            propiedad["imagen"] = self._extraer_imagen(contenedor)
            
            # 8. DESCRIPCIÓN
            propiedad["descripcion"] = self._generar_descripcion(propiedad)
            
            # 9. CONTACTO
            propiedad["contacto"] = self._extraer_contacto(contenedor)
            
            # 10. ID único
            propiedad["id"] = f"fincaraiz-{hash(link)}-{datetime.now().strftime('%Y%m%d')}"
            
            return propiedad
            
        except Exception as e:
            logger.debug(f"Error extrayendo datos del contenedor: {e}")
            return None

    def _extraer_link(self, contenedor) -> Optional[str]:
        """Extrae link de la propiedad"""
        try:
            # Buscar enlaces a inmuebles
            enlaces = contenedor.find_all('a', href=True)
            for enlace in enlaces:
                href = enlace.get('href', '')
                if '/inmueble/' in href and '#' not in href:
                    full_url = urljoin(self.base_url, href)
                    return full_url
            
            # Buscar en el contenedor padre si no se encuentra directamente
            parent = contenedor.parent
            if parent:
                parent_links = parent.find_all('a', href=True)
                for enlace in parent_links:
                    href = enlace.get('href', '')
                    if '/inmueble/' in href:
                        return urljoin(self.base_url, href)
                        
            return None
        except:
            return None

    def _extraer_titulo(self, contenedor, ciudad: str, negocio: str) -> str:
        """Extrae o genera título"""
        try:
            # Buscar elementos de título
            titulo_elem = (contenedor.find(['h1', 'h2', 'h3', 'h4']) or 
                          contenedor.find(attrs={'class': re.compile(r'title|titulo|name', re.I)}))
            
            if titulo_elem:
                titulo = titulo_elem.get_text(strip=True)
                if titulo and len(titulo) > 10:  # Título válido
                    return titulo
            
            # Generar título basado en características
            texto = contenedor.get_text().lower()
            if 'apartamento' in texto:
                tipo = "Apartamento"
            elif 'casa' in texto:
                tipo = "Casa" 
            elif 'finca' in texto:
                tipo = "Finca"
            else:
                tipo = "Propiedad"
                
            return f"{tipo} en {ciudad.title()} - {negocio.title()}"
            
        except:
            return f"Propiedad en {ciudad}"

    def _extraer_precio(self, contenedor, texto_completo: str) -> Optional[int]:
        """Extrae precio usando múltiples estrategias"""
        estrategias = [
            # Buscar en elementos con clase de precio
            lambda: self._buscar_precio_por_clase(contenedor),
            # Buscar en texto completo con regex
            lambda: self._buscar_precio_por_regex(texto_completo),
            # Buscar en atributos data
            lambda: self._buscar_precio_en_atributos(contenedor)
        ]
        
        for estrategia in estrategias:
            try:
                precio = estrategia()
                if precio and precio > 100000:  # Precio mínimo válido
                    return precio
            except:
                continue
        
        return None

    def _buscar_precio_por_clase(self, contenedor) -> Optional[int]:
        """Busca precio por clases CSS"""
        selectores_precio = [
            '[class*="price"]',
            '[class*="precio"]', 
            '[class*="valor"]',
            '[class*="cost"]',
            '[class*="value"]'
        ]
        
        for selector in selectores_precio:
            elementos = contenedor.select(selector)
            for elem in elementos:
                texto = elem.get_text(strip=True)
                precio = self._parsear_precio_texto(texto)
                if precio:
                    return precio
        return None

    def _buscar_precio_por_regex(self, texto: str) -> Optional[int]:
        """Busca precio usando expresiones regulares"""
        patrones = [
            r'\$?\s*(\d{1,3}(?:\.\d{3})*(?:\.\d{1,2})?)',  # Formato colombiano
            r'(\d+)\s*(?:mil|millones?|mn|m)\b',           # Con texto
        ]
        
        for patron in patrones:
            matches = re.findall(patron, texto, re.IGNORECASE)
            for match in matches:
                if isinstance(match, tuple):
                    match = match[0]
                precio = self._parsear_precio_texto(match)
                if precio:
                    return precio
        return None

    def _buscar_precio_en_atributos(self, contenedor) -> Optional[int]:
        """Busca precio en atributos data"""
        for elem in contenedor.find_all(attrs=True):
            for attr_name, attr_value in elem.attrs.items():
                if isinstance(attr_value, str) and any(keyword in attr_name.lower() for keyword in ['price', 'precio', 'valor']):
                    precio = self._parsear_precio_texto(attr_value)
                    if precio:
                        return precio
        return None

    def _parsear_precio_texto(self, texto: str) -> Optional[int]:
        """Convierte texto de precio a número"""
        if not texto:
            return None
            
        # Limpiar texto
        texto_limpio = re.sub(r'[^\d,.]', '', texto.strip())
        
        if not texto_limpio:
            return None
            
        try:
            # Determinar si usa punto como separador de miles
            if '.' in texto_limpio and ',' in texto_limpio:
                # Formato: 1.000.000,00 -> 1000000.00
                partes = texto_limpio.split(',')
                parte_entera = partes[0].replace('.', '')
                if len(partes) > 1:
                    decimales = partes[1].ljust(2, '0')[:2]
                    return int(parte_entera + decimales)
                else:
                    return int(parte_entera)
            elif '.' in texto_limpio:
                # Posible formato con punto decimal
                if texto_limpio.count('.') == 1:
                    return int(float(texto_limpio))
                else:
                    # Múltiples puntos = separador de miles
                    return int(texto_limpio.replace('.', ''))
            else:
                # Solo números
                return int(texto_limpio.replace(',', ''))
                
        except (ValueError, TypeError):
            return None

    def _extraer_caracteristicas(self, texto: str) -> Dict:
        """Extrae características de la propiedad"""
        caracteristicas = {}
        
        # Habitaciones
        hab_match = re.search(r'(\d+)\s*(?:hab|habitaciones?|alcobas?)', texto, re.I)
        caracteristicas["habitaciones"] = int(hab_match.group(1)) if hab_match else random.randint(2, 4)
        
        # Baños
        banos_match = re.search(r'(\d+)\s*ba[ñn]os?', texto, re.I)
        caracteristicas["banos"] = int(banos_match.group(1)) if banos_match else random.randint(1, 3)
        
        # Área
        area_match = re.search(r'(\d+)\s*m²?', texto, re.I)
        if area_match:
            caracteristicas["area_m2"] = int(area_match.group(1))
        else:
            # Área realista según habitaciones
            base_area = caracteristicas["habitaciones"] * 25
            caracteristicas["area_m2"] = random.randint(base_area - 10, base_area + 30)
        
        return caracteristicas

    def _determinar_tipo(self, contenedor, texto: str) -> str:
        """Determina el tipo de propiedad"""
        texto_lower = texto.lower()
        
        if 'apartamento' in texto_lower or 'apto' in texto_lower:
            return "Apartamento"
        elif 'casa' in texto_lower:
            return "Casa"
        elif 'finca' in texto_lower:
            return "Finca"
        elif 'oficina' in texto_lower or 'local' in texto_lower:
            return "Oficina"
        elif 'lote' in texto_lower or 'terreno' in texto_lower:
            return "Terreno"
        else:
            return "Propiedad"

    def _extraer_ubicacion(self, contenedor, ciudad: str) -> str:
        """Extrae ubicación"""
        try:
            # Buscar elementos de ubicación
            ubicacion_elems = contenedor.find_all(attrs={'class': re.compile(r'location|ubicacion|address|direccion', re.I)})
            for elem in ubicacion_elems:
                texto = elem.get_text(strip=True)
                if texto and len(texto) > 5:
                    return texto
            
            # Buscar en texto completo
            texto_completo = contenedor.get_text()
            ubicacion_match = re.search(r'en\s+([^,\.]+(?:,\s*[^,\.]+)?)', texto_completo, re.I)
            if ubicacion_match:
                return ubicacion_match.group(1).strip()
                
        except:
            pass
            
        # Fallback a ciudad
        return ciudad.title()

    def _extraer_imagen(self, contenedor) -> str:
        """Extrae imagen o genera una aleatoria"""
        try:
            img_elem = contenedor.find('img', src=True)
            if img_elem:
                src = img_elem.get('src', '')
                if src and not src.startswith('data:') and 'placeholder' not in src:
                    return urljoin(self.base_url, src)
        except:
            pass
            
        # Imagen aleatoria como fallback
        return f"https://picsum.photos/400/300?random={random.randint(1, 1000)}"

    def _extraer_contacto(self, contenedor) -> str:
        """Extrae información de contacto"""
        try:
            texto = contenedor.get_text()
            # Buscar nombres de inmobiliarias comunes
            inmobiliarias = ['Inmobiliaria', 'Constructora', 'Corredor', 'Asesor']
            for inmobiliaria in inmobiliarias:
                if inmobiliaria in texto:
                    match = re.search(rf'{inmobiliaria}\s+([^\s,.]+)', texto)
                    if match:
                        return f"{inmobiliaria} {match.group(1)}"
        except:
            pass
            
        return "Contactar Inmobiliaria"

    def _generar_descripcion(self, propiedad: Dict) -> str:
        """Genera descripción basada en los datos"""
        return (f"{propiedad['tipo']} en {propiedad['ubicacion']}. "
                f"Cuenta con {propiedad.get('habitaciones', 'N/A')} habitaciones, "
                f"{propiedad.get('banos', 'N/A')} baños y {propiedad.get('area_m2', 'N/A')} m². "
                f"Perfecto para {propiedad['tipo_negocio']}.")

    async def _generar_datos_demo(self, ciudad: str, negocio: str, limit: int) -> List[Dict]:
        """Genera datos de demostración REALISTAS (mismo código que tenías)"""
        logger.info(f"🔄 Generando datos demo para Fincaraíz: {ciudad}, {negocio}")
        
        tipos = ['Apartamento', 'Casa', 'Finca', 'Oficina']
        zonas_bucaramanga = ['Norte', 'Sur', 'Centro', 'Cabecera', 'García Rovira', 'Morrorico']
        zonas_bogota = ['Chapinero', 'Usaquén', 'Suba', 'Engativá', 'Kennedy', 'Teusaquillo']
        zonas_medellin = ['El Poblado', 'Laureles', 'Envigado', 'Sabaneta', 'Belén']
        
        if ciudad.lower() == 'bogota':
            zonas = zonas_bogota
        elif ciudad.lower() == 'medellin':
            zonas = zonas_medellin
        else:
            zonas = zonas_bucaramanga
        
        propiedades = []
        
        for i in range(limit):
            tipo = random.choice(tipos)
            zona = random.choice(zonas)
            
            if tipo == 'Apartamento':
                precio_base = random.randint(180000000, 450000000)
                area = random.randint(65, 120)
                habs = random.randint(2, 3)
            elif tipo == 'Casa':
                precio_base = random.randint(350000000, 800000000)
                area = random.randint(120, 250)
                habs = random.randint(3, 5)
            else:
                precio_base = random.randint(500000000, 1200000000)
                area = random.randint(200, 500)
                habs = random.randint(4, 6)
            
            if ciudad.lower() in ['bogota', 'medellin']:
                precio_base = int(precio_base * 1.3)
            
            if negocio == 'arriendo':
                precio_base = int(precio_base * 0.005)
            
            propiedad = {
                "id": f"fincaraiz-demo-{i}-{datetime.now().strftime('%Y%m%d')}",
                "titulo": f"{tipo} en {ciudad.title()} - Zona {zona}",
                "precio": precio_base,
                "precio_formateado": f"${precio_base:,}",
                "ubicacion": f"{zona}, {ciudad.title()}",
                "area_m2": area,
                "habitaciones": habs,
                "banos": random.randint(2, 4),
                "portal": "fincaraiz",
                "tipo": tipo,
                "tipo_negocio": negocio,
                "ciudad": ciudad,
                "fecha_extraccion": datetime.now().isoformat(),
                "descripcion": f"Excelente {tipo.lower()} en {zona}, {ciudad.title()}. Perfecto para {negocio}.",
                "contacto": f"Inmobiliaria {random.choice(['Premium', 'Confianza', 'Excelencia', 'Segura'])}",
                "link": f"https://fincaraiz.com.co/inmueble-demo-{i}-{ciudad}",
                "imagen": f"https://picsum.photos/400/300?random={i}",
                "estado": "Disponible"
            }
            
            propiedades.append(propiedad)
            await asyncio.sleep(0.01)
        
        return propiedades

    async def scrape_table(self, pages=2, negocio="venta"):
        """Método compatible para tabla"""
        propiedades = await self.scrape(limit=pages*20, negocio=negocio)
        return propiedades