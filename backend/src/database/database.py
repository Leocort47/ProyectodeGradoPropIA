#!/usr/bin/env python3
"""
Módulo de Base de Datos para ARIA Real Estate
Maneja todas las operaciones de base de datos para propiedades
"""

import logging
import asyncpg
import asyncio
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any
import json
import os
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class DatabaseConfig:
    """Configuración de base de datos"""
    host: str = os.getenv('DB_HOST', 'localhost')
    port: int = int(os.getenv('DB_PORT', '5432'))
    database: str = os.getenv('DB_NAME', 'aria_real_estate')
    user: str = os.getenv('DB_USER', 'aria_user')
    password: str = os.getenv('DB_PASSWORD', 'aria_password_2024')
    min_connections: int = 1
    max_connections: int = 10

class PropertyDatabase:
    """Clase principal para operaciones de base de datos"""
    
    def __init__(self, config: DatabaseConfig = None):
        self.config = config or DatabaseConfig()
        self.pool = None
        self._connected = False
    
    async def connect(self):
        """Conectar a la base de datos"""
        try:
            self.pool = await asyncpg.create_pool(
                host=self.config.host,
                port=self.config.port,
                database=self.config.database,
                user=self.config.user,
                password=self.config.password,
                min_size=self.config.min_connections,
                max_size=self.config.max_connections
            )
            self._connected = True
            logger.info("✅ Conectado a la base de datos PostgreSQL")
            return True
        except Exception as e:
            logger.error(f"❌ Error conectando a la base de datos: {e}")
            return False
    
    async def disconnect(self):
        """Desconectar de la base de datos"""
        if self.pool:
            await self.pool.close()
            self._connected = False
            logger.info("🔌 Desconectado de la base de datos")
    
    async def save_properties(self, properties: List[Dict]) -> Dict[str, Any]:
        """
        Guarda o actualiza propiedades en la base de datos
        
        Args:
            properties: Lista de diccionarios con datos de propiedades
            
        Returns:
            Dict con estadísticas de la operación
        """
        if not self._connected:
            await self.connect()
        
        stats = {
            'total_recibidas': len(properties),
            'guardadas': 0,
            'actualizadas': 0,
            'errores': 0,
            'errores_detalle': []
        }
        
        async with self.pool.acquire() as connection:
            for prop in properties:
                try:
                    # Verificar si la propiedad ya existe
                    existing = await connection.fetchrow(
                        "SELECT id FROM propiedades WHERE link = $1",
                        prop.get('link')
                    )
                    
                    if existing:
                        # Actualizar propiedad existente
                        await self._update_property(connection, prop, existing['id'])
                        stats['actualizadas'] += 1
                    else:
                        # Insertar nueva propiedad
                        await self._insert_property(connection, prop)
                        stats['guardadas'] += 1
                        
                except Exception as e:
                    stats['errores'] += 1
                    stats['errores_detalle'].append({
                        'propiedad': prop.get('titulo', 'Sin título'),
                        'error': str(e)
                    })
                    logger.error(f"Error guardando propiedad {prop.get('link')}: {e}")
        
        logger.info(f"💾 Base de datos: {stats['guardadas']} nuevas, {stats['actualizadas']} actualizadas, {stats['errores']} errores")
        return stats
    
    async def _insert_property(self, connection, prop: Dict):
        """Insertar una nueva propiedad"""
        # Obtener IDs de ciudad y portal
        ciudad_id = await self._get_or_create_ciudad(connection, prop.get('ciudad', ''))
        portal_id = await self._get_or_create_portal(connection, prop.get('portal', ''))
        
        query = """
        INSERT INTO propiedades (
            id_externo, portal_id, titulo, descripcion, link, ciudad_id,
            ubicacion_detallada, barrio, tipo_propiedad, area_m2, habitaciones,
            banos, precio, precio_formateado, administracion, contacto_nombre,
            contacto_telefono, inmobiliaria, tipo_negocio, estado, fuente_original
        ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16, $17, $18, $19, $20, $21)
        RETURNING id
        """
        
        prop_id = await connection.fetchval(
            query,
            prop.get('id'),
            portal_id,
            prop.get('titulo'),
            prop.get('descripcion'),
            prop.get('link'),
            ciudad_id,
            prop.get('ubicacion'),
            prop.get('barrio'),
            prop.get('tipo'),
            prop.get('area_m2'),
            prop.get('habitaciones'),
            prop.get('banos'),
            prop.get('precio'),
            prop.get('precio_formateado'),
            prop.get('administracion'),
            prop.get('contacto'),
            prop.get('telefonos'),
            prop.get('inmobiliaria'),
            prop.get('tipo_negocio', 'venta'),
            prop.get('estado', 'disponible'),
            prop.get('portal')
        )
        
        # Guardar imagen principal si existe
        if prop.get('imagen'):
            await self._save_property_image(connection, prop_id, prop['imagen'], True)
        
        # Guardar características adicionales
        await self._save_property_features(connection, prop_id, prop)
        
        return prop_id
    
    async def _update_property(self, connection, prop: Dict, prop_id: int):
        """Actualizar una propiedad existente"""
        query = """
        UPDATE propiedades SET
            titulo = $1,
            descripcion = $2,
            precio = $3,
            precio_formateado = $4,
            administracion = $5,
            contacto_nombre = $6,
            contacto_telefono = $7,
            estado = $8,
            fecha_actualizacion = CURRENT_TIMESTAMP
        WHERE id = $9
        """
        
        await connection.execute(
            query,
            prop.get('titulo'),
            prop.get('descripcion'),
            prop.get('precio'),
            prop.get('precio_formateado'),
            prop.get('administracion'),
            prop.get('contacto'),
            prop.get('telefonos'),
            prop.get('estado', 'disponible'),
            prop_id
        )
    
    async def _get_or_create_ciudad(self, connection, ciudad_nombre: str) -> int:
        """Obtener o crear ciudad en la base de datos"""
        if not ciudad_nombre:
            return None
        
        # Buscar ciudad
        ciudad = await connection.fetchrow(
            "SELECT id FROM ciudades WHERE nombre ILIKE $1",
            ciudad_nombre.strip()
        )
        
        if ciudad:
            return ciudad['id']
        
        # Crear nueva ciudad
        return await connection.fetchval(
            "INSERT INTO ciudades (nombre) VALUES ($1) RETURNING id",
            ciudad_nombre.strip()
        )
    
    async def _get_or_create_portal(self, connection, portal_nombre: str) -> int:
        """Obtener o crear portal en la base de datos"""
        if not portal_nombre:
            return None
        
        portal = await connection.fetchrow(
            "SELECT id FROM portales WHERE nombre ILIKE $1",
            portal_nombre.strip()
        )
        
        if portal:
            return portal['id']
        
        return await connection.fetchval(
            "INSERT INTO portales (nombre, url_base) VALUES ($1, $2) RETURNING id",
            portal_nombre.strip(),
            f"https://{portal_nombre.strip().lower().replace(' ', '')}.com.co"
        )
    
    async def _save_property_image(self, connection, prop_id: int, image_url: str, es_principal: bool = False):
        """Guardar imagen de propiedad"""
        await connection.execute(
            "INSERT INTO imagenes_propiedades (propiedad_id, url_imagen, es_principal) VALUES ($1, $2, $3)",
            prop_id, image_url, es_principal
        )
    
    async def _save_property_features(self, connection, prop_id: int, prop: Dict):
        """Guardar características adicionales de la propiedad"""
        features = [
            ('parqueaderos', prop.get('parqueaderos')),
            ('estrato', prop.get('estrato')),
            ('antiguedad', prop.get('antiguedad')),
            ('piso', prop.get('piso')),
            ('area_privada', prop.get('area_privada')),
            ('area_construida', prop.get('area_construida'))
        ]
        
        for feature, value in features:
            if value is not None:
                await connection.execute(
                    "INSERT INTO caracteristicas_propiedades (propiedad_id, caracteristica, valor) VALUES ($1, $2, $3)",
                    prop_id, feature, str(value)
                )
    
    async def search_properties(self, filters: Dict) -> List[Dict]:
        """
        Buscar propiedades con filtros avanzados
        
        Args:
            filters: Diccionario con filtros de búsqueda
            
        Returns:
            Lista de propiedades que coinciden con los filtros
        """
        if not self._connected:
            await self.connect()
        
        # Construir query dinámica
        query_parts = ["SELECT * FROM vista_propiedades_completas WHERE 1=1"]
        params = []
        param_count = 0
        
        # Aplicar filtros
        if filters.get('ciudad'):
            param_count += 1
            query_parts.append(f"AND ciudad ILIKE ${param_count}")
            params.append(f"%{filters['ciudad']}%")
        
        if filters.get('tipo_negocio'):
            param_count += 1
            query_parts.append(f"AND tipo_negocio = ${param_count}")
            params.append(filters['tipo_negocio'])
        
        if filters.get('tipo_propiedad'):
            param_count += 1
            query_parts.append(f"AND tipo_propiedad ILIKE ${param_count}")
            params.append(f"%{filters['tipo_propiedad']}%")
        
        if filters.get('precio_min'):
            param_count += 1
            query_parts.append(f"AND precio >= ${param_count}")
            params.append(filters['precio_min'])
        
        if filters.get('precio_max'):
            param_count += 1
            query_parts.append(f"AND precio <= ${param_count}")
            params.append(filters['precio_max'])
        
        if filters.get('habitaciones_min'):
            param_count += 1
            query_parts.append(f"AND habitaciones >= ${param_count}")
            params.append(filters['habitaciones_min'])
        
        if filters.get('area_min'):
            param_count += 1
            query_parts.append(f"AND area_m2 >= ${param_count}")
            params.append(filters['area_min'])
        
        if filters.get('portal'):
            param_count += 1
            query_parts.append(f"AND portal = ${param_count}")
            params.append(filters['portal'])
        
        # Ordenamiento
        order_by = filters.get('ordenar_por', 'fecha_actualizacion')
        order_dir = 'DESC' if filters.get('orden_desc', True) else 'ASC'
        query_parts.append(f"ORDER BY {order_by} {order_dir}")
        
        # Límite
        if filters.get('limite'):
            param_count += 1
            query_parts.append(f"LIMIT ${param_count}")
            params.append(filters['limite'])
        
        final_query = " ".join(query_parts)
        
        async with self.pool.acquire() as connection:
            results = await connection.fetch(final_query, *params)
            
            # Convertir a lista de diccionarios
            properties = []
            for row in results:
                properties.append(dict(row))
            
            return properties
    
    async def get_property_stats(self) -> Dict[str, Any]:
        """Obtener estadísticas generales de propiedades"""
        if not self._connected:
            await self.connect()
        
        async with self.pool.acquire() as connection:
            stats = await connection.fetchrow("""
                SELECT 
                    COUNT(*) as total_propiedades,
                    COUNT(DISTINCT ciudad_id) as total_ciudades,
                    COUNT(DISTINCT portal_id) as total_portales,
                    AVG(precio) as precio_promedio,
                    MAX(fecha_actualizacion) as ultima_actualizacion
                FROM propiedades 
                WHERE estado = 'disponible'
            """)
            
            return dict(stats) if stats else {}
    
    async def log_scraping_session(self, portal: str, properties_found: int, 
                                 properties_saved: int, duration: float, 
                                 status: str, error: str = None, search_params: Dict = None):
        """Registrar sesión de scraping en logs"""
        if not self._connected:
            await self.connect()
        
        portal_id = await self._get_portal_id(portal)
        
        async with self.pool.acquire() as connection:
            await connection.execute("""
                INSERT INTO logs_scraping 
                (portal_id, fecha_fin, estado, propiedades_encontradas, 
                 propiedades_guardadas, duracion_segundos, error_message, parametros_busqueda)
                VALUES ($1, CURRENT_TIMESTAMP, $2, $3, $4, $5, $6, $7)
            """, portal_id, status, properties_found, properties_saved, duration, error, json.dumps(search_params))
    
    async def _get_portal_id(self, portal_nombre: str) -> int:
        """Obtener ID de portal por nombre"""
        if not self._connected:
            await self.connect()
        
        async with self.pool.acquire() as connection:
            portal = await connection.fetchrow(
                "SELECT id FROM portales WHERE nombre ILIKE $1",
                portal_nombre.strip()
            )
            return portal['id'] if portal else None
    
    async def cleanup_old_properties(self, days_old: int = 30):
        """
        Limpiar propiedades antiguas no actualizadas
        
        Args:
            days_old: Número de días para considerar una propiedad como antigua
        """
        if not self._connected:
            await self.connect()
        
        cutoff_date = datetime.now() - timedelta(days=days_old)
        
        async with self.pool.acquire() as connection:
            deleted_count = await connection.fetchval("""
                UPDATE propiedades 
                SET estado = 'expirada' 
                WHERE fecha_actualizacion < $1 AND estado = 'disponible'
                RETURNING COUNT(*)
            """, cutoff_date)
            
            logger.info(f"🧹 Limpieza: {deleted_count} propiedades marcadas como expiradas")
            return deleted_count

# Instancia global de la base de datos
db = PropertyDatabase()

async def init_database():
    """Inicializar la conexión a la base de datos"""
    return await db.connect()

async def close_database():
    """Cerrar conexión a la base de datos"""
    await db.disconnect()