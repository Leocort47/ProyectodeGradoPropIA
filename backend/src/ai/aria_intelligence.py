# ============================================================================
# backend/src/ai/aria_intelligence.py - MOTOR DE IA PARA ARIA
# ============================================================================

"""
ARIA - Asistente de Inteligencia Artificial para Búsqueda de Propiedades
Procesa lenguaje natural y extrae parámetros de búsqueda
"""

import re
from typing import Dict, List, Optional, Any
import logging

logger = logging.getLogger("ARIA_BACKEND")


class ARIAIntelligence:
    """
    Motor de IA para interpretar búsquedas en lenguaje natural
    """
    
    def __init__(self):
        # Diccionarios de mapeo
        self.tipos_propiedad_map = {
            'apartamento': ['apartamento', 'apto', 'apt', 'apartaestudio', 'estudio', 'flat'],
            'casa': ['casa', 'casas', 'vivienda', 'chalet'],
            'finca': ['finca', 'finca raíz', 'terreno', 'lote'],
            'local': ['local', 'locales', 'comercial'],
            'oficina': ['oficina', 'oficinas', 'consultorio'],
            'bodega': ['bodega', 'bodegas', 'almacén']
        }
        
        self.ciudades_map = {
            'bucaramanga': ['bucaramanga', 'buca', 'bmanga'],
            'bogota': ['bogotá', 'bogota', 'bta'],
            'medellin': ['medellín', 'medellin', 'mde'],
            'cali': ['cali'],
            'barranquilla': ['barranquilla', 'baq'],
            'cartagena': ['cartagena']
        }
        
        self.barrios_bucaramanga = [
            'cabecera', 'provenza', 'la victoria', 'álamos', 'alamos',
            'sotomayor', 'centro', 'garcía rovira', 'garcia rovira',
            'ciudadela', 'mutis', 'la floresta', 'san francisco',
            'conucos', 'morrorico', 'real de minas'
        ]
        
        self.negocio_map = {
            'venta': ['venta', 'vender', 'comprar', 'compra', 'adquirir', 'en venta'],
            'arriendo': ['arriendo', 'arrendar', 'alquilar', 'alquiler', 'renta', 'rentar']
        }
        
    def parse_query(self, query: str) -> Dict[str, Any]:
        """
        🧠 PARSEAR CONSULTA EN LENGUAJE NATURAL
        
        Ejemplos:
        - "apartamento en Cabecera con 3 habitaciones"
        - "casa para comprar en Bucaramanga de 2 pisos"
        - "arriendo apartaestudio en Provenza"
        """
        query_lower = query.lower().strip()
        
        logger.info(f"🧠 ARIA procesando: '{query}'")
        
        params = {
            'tipo_propiedad': self._extract_tipo_propiedad(query_lower),
            'ciudad': self._extract_ciudad(query_lower),
            'barrio': self._extract_barrio(query_lower),
            'habitaciones': self._extract_habitaciones(query_lower),
            'banos': self._extract_banos(query_lower),
            'negocio': self._extract_negocio(query_lower),
            'precio_min': self._extract_precio_min(query_lower),
            'precio_max': self._extract_precio_max(query_lower),
            'area_min': self._extract_area(query_lower),
            'garajes': self._extract_garajes(query_lower)
        }
        
        # Log de extracción
        logger.info(f"   📊 Parámetros extraídos:")
        for key, value in params.items():
            if value:
                logger.info(f"      - {key}: {value}")
        
        return params
    
    def _extract_tipo_propiedad(self, query: str) -> Optional[str]:
        """Extraer tipo de propiedad"""
        for tipo, keywords in self.tipos_propiedad_map.items():
            for keyword in keywords:
                if keyword in query:
                    return tipo
        return 'apartamento'  # Default
    
    def _extract_ciudad(self, query: str) -> Optional[str]:
        """Extraer ciudad"""
        for ciudad, keywords in self.ciudades_map.items():
            for keyword in keywords:
                if keyword in query:
                    return ciudad
        return 'bucaramanga'  # Default
    
    def _extract_barrio(self, query: str) -> Optional[str]:
        """Extraer barrio"""
        for barrio in self.barrios_bucaramanga:
            if barrio.lower() in query:
                return barrio.title()
        
        # Buscar después de "en" o "zona"
        patterns = [
            r'en\s+([a-záéíóúñ\s]+?)(?:\s+con|\s+de|\s*$)',
            r'zona\s+([a-záéíóúñ\s]+?)(?:\s+con|\s+de|\s*$)',
            r'barrio\s+([a-záéíóúñ\s]+?)(?:\s+con|\s+de|\s*$)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, query)
            if match:
                barrio_candidato = match.group(1).strip()
                if len(barrio_candidato) > 3 and len(barrio_candidato) < 30:
                    return barrio_candidato.title()
        
        return None
    
    def _extract_habitaciones(self, query: str) -> Optional[str]:
        """Extraer número de habitaciones"""
        # Patrones: "3 habitaciones", "3 hab", "3hab", "tres habitaciones"
        patterns = [
            r'(\d+)\s*(?:habitacion|hab|alcoba|dormitorio|cuarto)',
            r'(?:habitacion|hab|alcoba|dormitorio|cuarto)[es]*\s*[de:]*\s*(\d+)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, query)
            if match:
                num = match.group(1)
                return num
        
        # Números en letras
        numeros_texto = {
            'una': '1', 'un': '1',
            'dos': '2',
            'tres': '3',
            'cuatro': '4',
            'cinco': '5',
            'seis': '6'
        }
        
        for texto, numero in numeros_texto.items():
            if f'{texto} habitacion' in query or f'{texto} hab' in query:
                return numero
        
        return None
    
    def _extract_banos(self, query: str) -> Optional[int]:
        """Extraer número de baños"""
        patterns = [
            r'(\d+)\s*(?:baño|bano|bath)',
            r'(?:baño|bano|bath)[s]*\s*[de:]*\s*(\d+)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, query)
            if match:
                return int(match.group(1))
        
        return None
    
    def _extract_negocio(self, query: str) -> str:
        """Extraer tipo de negocio"""
        for negocio, keywords in self.negocio_map.items():
            for keyword in keywords:
                if keyword in query:
                    return negocio
        
        # Si no se especifica, inferir
        if 'precio' in query or 'valor' in query or 'cuesta' in query:
            return 'venta'
        
        return 'venta'  # Default
    
    def _extract_precio_min(self, query: str) -> Optional[int]:
        """Extraer precio mínimo"""
        patterns = [
            r'(?:desde|mínimo|minimo|min|mayor a)\s*\$?\s*(\d+(?:\.\d+)?)\s*(?:millones?|m)?',
            r'\$\s*(\d+(?:\.\d+)?)\s*(?:millones?|m)?\s*(?:a|hasta)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, query)
            if match:
                valor = float(match.group(1))
                # Convertir millones
                if 'millon' in query or 'm' in query:
                    return int(valor * 1_000_000)
                return int(valor)
        
        return None
    
    def _extract_precio_max(self, query: str) -> Optional[int]:
        """Extraer precio máximo"""
        patterns = [
            r'(?:hasta|máximo|maximo|max|menor a)\s*\$?\s*(\d+(?:\.\d+)?)\s*(?:millones?|m)?',
            r'\$\s*(\d+(?:\.\d+)?)\s*(?:millones?|m)?\s*$',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, query)
            if match:
                valor = float(match.group(1))
                if 'millon' in query or 'm' in query:
                    return int(valor * 1_000_000)
                return int(valor)
        
        return None
    
    def _extract_area(self, query: str) -> Optional[int]:
        """Extraer área mínima"""
        patterns = [
            r'(\d+)\s*m[²2]',
            r'(\d+)\s*metros',
            r'área\s*(?:de)?\s*(\d+)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, query)
            if match:
                return int(match.group(1))
        
        return None
    
    def _extract_garajes(self, query: str) -> Optional[int]:
        """Extraer número de garajes"""
        patterns = [
            r'(\d+)\s*(?:garaje|parqueadero|parking)',
            r'(?:garaje|parqueadero|parking)[s]*\s*[de:]*\s*(\d+)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, query)
            if match:
                return int(match.group(1))
        
        return None
    
    def generate_search_summary(self, params: Dict[str, Any]) -> str:
        """Generar resumen legible de la búsqueda"""
        parts = []
        
        if params.get('tipo_propiedad'):
            parts.append(f"{params['tipo_propiedad'].title()}")
        
        if params.get('negocio'):
            parts.append(f"en {params['negocio']}")
        
        if params.get('ciudad'):
            parts.append(f"en {params['ciudad'].title()}")
        
        if params.get('barrio'):
            parts.append(f"zona {params['barrio']}")
        
        if params.get('habitaciones'):
            parts.append(f"con {params['habitaciones']} habitaciones")
        
        if params.get('precio_min') or params.get('precio_max'):
            if params.get('precio_min') and params.get('precio_max'):
                parts.append(f"entre ${params['precio_min']:,} y ${params['precio_max']:,}")
            elif params.get('precio_min'):
                parts.append(f"desde ${params['precio_min']:,}")
            elif params.get('precio_max'):
                parts.append(f"hasta ${params['precio_max']:,}")
        
        if not parts:
            return "Propiedades en general"
        
        return " ".join(parts)


# ============================================================================
# FUNCIÓN PRINCIPAL DE BÚSQUEDA CON IA
# ============================================================================

async def buscar_con_ia(query: str, limit: int = 20) -> Dict[str, Any]:
    """
    Función principal que integra IA + Scraping
    """
    from src.scrapers.fincaraiz_scraper import FincaraizScraper
    
    logger.info("=" * 80)
    logger.info("🤖 ARIA IA ACTIVADA")
    logger.info(f"📝 Query: '{query}'")
    logger.info("=" * 80)
    
    # 1. Procesar con IA
    aria = ARIAIntelligence()
    params = aria.parse_query(query)
    summary = aria.generate_search_summary(params)
    
    logger.info(f"📊 Búsqueda interpretada: {summary}")
    
    # 2. Ejecutar scraping con parámetros extraídos
    scraper = FincaraizScraper()
    
    try:
        # 🔥 PASAR TODOS LOS PARÁMETROS AL SCRAPER
        propiedades = await scraper.scrape(
            limit=limit,
            negocio=params.get('negocio', 'venta'),
            ciudad=params.get('ciudad', 'bucaramanga'),
            tipo_propiedad=params.get('tipo_propiedad', 'apartamento'),
            habitaciones=int(params['habitaciones']) if params.get('habitaciones') else None,
            banos=params.get('banos'),
            precio_min=params.get('precio_min'),
            precio_max=params.get('precio_max'),
            area_min=params.get('area_min')
        )
        
        # 3. Filtrar post-scraping
        propiedades_filtradas = propiedades
        
        # Filtrar por barrio
        if params.get('barrio'):
            barrio_lower = params['barrio'].lower()
            propiedades_filtradas = [
                p for p in propiedades_filtradas
                if barrio_lower in p.get('ubicacion', '').lower() or 
                   barrio_lower in p.get('titulo', '').lower()
            ]
        
        # Filtrar por precio
        if params.get('precio_min'):
            propiedades_filtradas = [
                p for p in propiedades_filtradas 
                if p.get('precio', 0) >= params['precio_min']
            ]
        
        if params.get('precio_max'):
            propiedades_filtradas = [
                p for p in propiedades_filtradas 
                if p.get('precio', 0) <= params['precio_max']
            ]
        
        # Filtrar por área
        if params.get('area_min'):
            propiedades_filtradas = [
                p for p in propiedades_filtradas 
                if p.get('area_m2', 0) >= params['area_min']
            ]
        
        # Filtrar por baños
        if params.get('banos'):
            propiedades_filtradas = [
                p for p in propiedades_filtradas 
                if p.get('banos', 0) >= params['banos']
            ]
        
        # Filtrar por garajes
        if params.get('garajes'):
            propiedades_filtradas = [
                p for p in propiedades_filtradas 
                if p.get('garajes', 0) >= params['garajes']
            ]
        
        logger.info(f"✅ ARIA encontró {len(propiedades_filtradas)} propiedades")
        logger.info("=" * 80)
        
        return {
            "success": True,
            "query_original": query,
            "interpretacion": summary,
            "parametros_extraidos": params,
            "total_encontradas": len(propiedades_filtradas),
            "propiedades": propiedades_filtradas,
            "mensaje_aria": _generar_mensaje_aria(len(propiedades_filtradas), summary)
        }
    
    except Exception as e:
        logger.error(f"❌ Error en búsqueda IA: {e}", exc_info=True)
        return {
            "success": False,
            "query_original": query,
            "error": str(e),
            "mensaje_aria": "Lo siento, tuve un problema procesando tu búsqueda. ¿Podrías intentar de otra forma?"
        }


def _generar_mensaje_aria(total: int, summary: str) -> str:
    """Generar mensaje personalizado de ARIA"""
    if total == 0:
        return f"🤔 No encontré propiedades con esos criterios ({summary}). ¿Quieres que busque algo diferente?"
    elif total == 1:
        return f"✅ ¡Perfecto! Encontré 1 propiedad que coincide con tu búsqueda: {summary}"
    elif total <= 5:
        return f"✅ ¡Excelente! Encontré {total} propiedades para ti: {summary}"
    elif total <= 20:
        return f"🎯 ¡Muy bien! Encontré {total} opciones que podrían interesarte: {summary}"
    else:
        return f"🔥 ¡Wow! Encontré {total} propiedades. Aquí están las mejores opciones: {summary}"


# ============================================================================
# EJEMPLOS DE USO
# ============================================================================

if __name__ == "__main__":
    import asyncio
    
    async def test():
        logging.basicConfig(level=logging.INFO)
        
        queries_test = [
            "apartamento en Cabecera con 3 habitaciones",
            "casa para comprar en Bucaramanga de 2 pisos",
            "arriendo apartaestudio en Provenza",
            "busco casa en la victoria con garaje",
            "apartamento hasta 400 millones en cabecera"
        ]
        
        for query in queries_test:
            print(f"\n{'='*80}")
            print(f"TEST: {query}")
            print(f"{'='*80}")
            
            result = await buscar_con_ia(query, limit=5)
            
            print(f"\n📊 Interpretación: {result.get('interpretacion')}")
            print(f"💬 Mensaje ARIA: {result.get('mensaje_aria')}")
            print(f"🏠 Total: {result.get('total_encontradas', 0)} propiedades")
            
            if result.get('propiedades'):
                print(f"\nPrimeras 3 propiedades:")
                for i, p in enumerate(result['propiedades'][:3], 1):
                    print(f"  {i}. {p['titulo']} - {p['precio_formateado']}")
    
    asyncio.run(test())