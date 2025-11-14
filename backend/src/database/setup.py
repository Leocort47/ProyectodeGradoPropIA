#!/usr/bin/env python3
"""
Script de configuración de la base de datos
Ejecutar: python database/setup.py
"""

import asyncio
import asyncpg
import os
from pathlib import Path

async def setup_database():
    """Configurar la base de datos desde cero"""
    
    # Leer el schema SQL
    schema_path = Path(__file__).parent / "schema.sql"
    with open(schema_path, 'r', encoding='utf-8') as f:
        schema_sql = f.read()
    
    # Conectar como superusuario para crear la base de datos
    super_conn = await asyncpg.connect(
        host='localhost',
        user='postgres',  # Cambiar según tu configuración
        password='password'  # Cambiar según tu configuración
    )
    
    try:
        # Crear base de datos si no existe
        await super_conn.execute("""
            SELECT 'CREATE DATABASE aria_real_estate'
            WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'aria_real_estate')
        """)
        
        print("✅ Base de datos creada o ya existe")
        
    except Exception as e:
        print(f"❌ Error creando base de datos: {e}")
        return
    
    finally:
        await super_conn.close()
    
    # Conectar a la nueva base de datos y ejecutar schema
    try:
        conn = await asyncpg.connect(
            host='localhost',
            database='aria_real_estate',
            user='postgres',
            password='password'
        )
        
        # Ejecutar el schema SQL
        await conn.execute(schema_sql)
        print("✅ Esquema de base de datos ejecutado correctamente")
        
        # Insertar datos de prueba
        await conn.execute("""
            INSERT INTO propiedades (
                titulo, descripcion, link, ciudad_id, portal_id,
                tipo_propiedad, area_m2, habitaciones, banos, precio,
                precio_formateado, tipo_negocio, estado
            ) VALUES (
                'Apartamento de prueba en Bogotá',
                'Hermoso apartamento en zona residencial',
                'https://fincaraiz.com.co/propiedad-test-1',
                1, 1, 'Apartamento', 85.5, 3, 2, 350000000,
                '$350,000,000', 'venta', 'disponible'
            )
        """)
        
        print("✅ Datos de prueba insertados")
        
    except Exception as e:
        print(f"❌ Error ejecutando schema: {e}")
        
    finally:
        await conn.close()

if __name__ == "__main__":
    print("🚀 Configurando base de datos ARIA Real Estate...")
    asyncio.run(setup_database())
    print("🎉 Configuración completada!")