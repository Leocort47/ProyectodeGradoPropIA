-- =============================================
-- BASE DE DATOS: ARIA REAL ESTATE COLOMBIA
-- =============================================

CREATE DATABASE aria_real_estate;
\c aria_real_estate;

-- =============================================
-- TABLAS PRINCIPALES
-- =============================================

-- Tabla de portales inmobiliarios
CREATE TABLE portales (
    id SERIAL PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL UNIQUE,
    url_base VARCHAR(255) NOT NULL,
    activo BOOLEAN DEFAULT TRUE,
    fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Tabla de ciudades
CREATE TABLE ciudades (
    id SERIAL PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL UNIQUE,
    departamento VARCHAR(100),
    pais VARCHAR(50) DEFAULT 'Colombia',
    activo BOOLEAN DEFAULT TRUE
);

-- Tabla principal de propiedades
CREATE TABLE propiedades (
    id SERIAL PRIMARY KEY,
    -- Identificación única
    id_externo VARCHAR(255) UNIQUE,
    portal_id INTEGER REFERENCES portales(id),
    
    -- Información básica
    titulo VARCHAR(500) NOT NULL,
    descripcion TEXT,
    link VARCHAR(500) UNIQUE NOT NULL,
    
    -- Ubicación
    ciudad_id INTEGER REFERENCES ciudades(id),
    ubicacion_detallada VARCHAR(300),
    barrio VARCHAR(100),
    direccion TEXT,
    latitud DECIMAL(10, 8),
    longitud DECIMAL(11, 8),
    
    -- Características físicas
    tipo_propiedad VARCHAR(50), -- Apartamento, Casa, Finca, etc.
    area_m2 DECIMAL(8, 2),
    habitaciones INTEGER,
    banos INTEGER,
    parqueaderos INTEGER,
    estrato INTEGER,
    antiguedad INTEGER, -- En años
    piso INTEGER,
    
    -- Precios y costos
    precio DECIMAL(15, 2),
    precio_formateado VARCHAR(100),
    administracion DECIMAL(10, 2),
    moneda VARCHAR(10) DEFAULT 'COP',
    
    -- Información de contacto
    contacto_nombre VARCHAR(200),
    contacto_telefono VARCHAR(100),
    contacto_email VARCHAR(200),
    inmobiliaria VARCHAR(200),
    
    -- Información de extracción
    tipo_negocio VARCHAR(20) CHECK (tipo_negocio IN ('venta', 'arriendo')),
    estado VARCHAR(50) DEFAULT 'disponible',
    fecha_extraccion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    fecha_actualizacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    fuente_original VARCHAR(100),
    
    -- Metadatos
    verificada BOOLEAN DEFAULT FALSE,
    prioridad INTEGER DEFAULT 1,
    etiquetas TEXT[], -- Array de etiquetas
    
    -- Índices para búsqueda rápida
    CONSTRAINT chk_precio_positivo CHECK (precio > 0),
    CONSTRAINT chk_area_positiva CHECK (area_m2 > 0)
);

-- Tabla de imágenes de propiedades
CREATE TABLE imagenes_propiedades (
    id SERIAL PRIMARY KEY,
    propiedad_id INTEGER REFERENCES propiedades(id) ON DELETE CASCADE,
    url_imagen VARCHAR(500) NOT NULL,
    orden INTEGER DEFAULT 1,
    descripcion_imagen VARCHAR(200),
    es_principal BOOLEAN DEFAULT FALSE,
    fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Tabla de características adicionales
CREATE TABLE caracteristicas_propiedades (
    id SERIAL PRIMARY KEY,
    propiedad_id INTEGER REFERENCES propiedades(id) ON DELETE CASCADE,
    caracteristica VARCHAR(100) NOT NULL,
    valor VARCHAR(200),
    categoria VARCHAR(50),
    UNIQUE(propiedad_id, caracteristica)
);

-- Tabla de búsquedas de usuarios (para analytics)
CREATE TABLE busquedas_usuarios (
    id SERIAL PRIMARY KEY,
    -- Parámetros de búsqueda
    ciudad VARCHAR(100),
    tipo_negocio VARCHAR(20),
    tipo_propiedad VARCHAR(50),
    precio_min DECIMAL(15, 2),
    precio_max DECIMAL(15, 2),
    habitaciones_min INTEGER,
    area_min DECIMAL(8, 2),
    
    -- Resultados
    total_resultados INTEGER,
    portales_buscados TEXT[], -- Array de portales
    
    -- Metadatos de la búsqueda
    ip_usuario VARCHAR(45),
    user_agent TEXT,
    fecha_busqueda TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    duracion_ms INTEGER -- Tiempo que tomó la búsqueda
);

-- Tabla de logs de scraping
CREATE TABLE logs_scraping (
    id SERIAL PRIMARY KEY,
    portal_id INTEGER REFERENCES portales(id),
    fecha_inicio TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    fecha_fin TIMESTAMP,
    estado VARCHAR(20) CHECK (estado IN ('exitoso', 'fallido', 'parcial')),
    propiedades_encontradas INTEGER DEFAULT 0,
    propiedades_guardadas INTEGER DEFAULT 0,
    duracion_segundos INTEGER,
    error_message TEXT,
    parametros_busqueda JSONB
);

-- =============================================
-- ÍNDICES PARA OPTIMIZACIÓN
-- =============================================

-- Índices para propiedades
CREATE INDEX idx_propiedades_ciudad ON propiedades(ciudad_id);
CREATE INDEX idx_propiedades_tipo_negocio ON propiedades(tipo_negocio);
CREATE INDEX idx_propiedades_precio ON propiedades(precio);
CREATE INDEX idx_propiedades_area ON propiedades(area_m2);
CREATE INDEX idx_propiedades_habitaciones ON propiedades(habitaciones);
CREATE INDEX idx_propiedades_fecha_actualizacion ON propiedades(fecha_actualizacion);
CREATE INDEX idx_propiedades_estado ON propiedades(estado);
CREATE INDEX idx_propiedades_tipo ON propiedades(tipo_propiedad);

-- Índices compuestos para búsquedas frecuentes
CREATE INDEX idx_propiedades_busqueda_avanzada ON propiedades(ciudad_id, tipo_negocio, precio, area_m2);
CREATE INDEX idx_propiedades_ubicacion ON propiedades(ciudad_id, barrio);

-- Índices para imágenes
CREATE INDEX idx_imagenes_propiedad ON imagenes_propiedades(propiedad_id);
CREATE INDEX idx_imagenes_principal ON imagenes_propiedades(es_principal) WHERE es_principal = true;

-- Índices para características
CREATE INDEX idx_caracteristicas_propiedad ON caracteristicas_propiedades(propiedad_id);
CREATE INDEX idx_caracteristicas_nombre ON caracteristicas_propiedades(caracteristica);

-- Índices para logs
CREATE INDEX idx_logs_fecha ON logs_scraping(fecha_inicio);
CREATE INDEX idx_logs_estado ON logs_scraping(estado);

-- =============================================
-- DATOS INICIALES
-- =============================================

-- Insertar portales principales
INSERT INTO portales (nombre, url_base) VALUES
('fincaraiz', 'https://fincaraiz.com.co'),
('metrocuadrado', 'https://www.metrocuadrado.com'),
('lahaus', 'https://www.lahaus.com'),
('vivanuncios', 'https://www.vivanuncios.com.co'),
('compreoalquile', 'https://compreoalquile.com');

-- Insertar ciudades principales de Colombia
INSERT INTO ciudades (nombre, departamento) VALUES
('Bogotá', 'Bogotá D.C.'),
('Medellín', 'Antioquia'),
('Cali', 'Valle del Cauca'),
('Barranquilla', 'Atlántico'),
('Cartagena', 'Bolívar'),
('Bucaramanga', 'Santander'),
('Cúcuta', 'Norte de Santander'),
('Pereira', 'Risaralda'),
('Manizales', 'Caldas'),
('Armenia', 'Quindío'),
('Ibagué', 'Tolima'),
('Villavicencio', 'Meta'),
('Pasto', 'Nariño'),
('Neiva', 'Huila'),
('Santa Marta', 'Magdalena');

-- =============================================
-- VISTAS ÚTILES
-- =============================================

-- Vista para propiedades con información completa
CREATE VIEW vista_propiedades_completas AS
SELECT 
    p.id,
    p.titulo,
    p.descripcion,
    p.link,
    p.precio,
    p.precio_formateado,
    p.area_m2,
    p.habitaciones,
    p.banos,
    p.administracion,
    p.contacto_nombre,
    p.contacto_telefono,
    p.inmobiliaria,
    p.tipo_propiedad,
    p.tipo_negocio,
    p.estado,
    p.fecha_actualizacion,
    c.nombre as ciudad,
    c.departamento,
    port.nombre as portal,
    port.url_base,
    (SELECT url_imagen FROM imagenes_propiedades WHERE propiedad_id = p.id AND es_principal = TRUE LIMIT 1) as imagen_principal
FROM propiedades p
JOIN ciudades c ON p.ciudad_id = c.id
JOIN portales port ON p.portal_id = port.id
WHERE p.estado = 'disponible';

-- Vista para estadísticas de portales
CREATE VIEW vista_estadisticas_portales AS
SELECT 
    port.nombre as portal,
    COUNT(p.id) as total_propiedades,
    COUNT(DISTINCT p.ciudad_id) as ciudades_cubiertas,
    AVG(p.precio) as precio_promedio,
    MIN(p.precio) as precio_minimo,
    MAX(p.precio) as precio_maximo,
    MAX(p.fecha_actualizacion) as ultima_actualizacion
FROM propiedades p
JOIN portales port ON p.portal_id = port.id
GROUP BY port.id, port.nombre;

-- =============================================
-- FUNCIONES Y TRIGGERS
-- =============================================

-- Función para actualizar automáticamente fecha_actualizacion
CREATE OR REPLACE FUNCTION actualizar_fecha_actualizacion()
RETURNS TRIGGER AS $$
BEGIN
    NEW.fecha_actualizacion = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger para actualizar fecha_actualizacion
CREATE TRIGGER trigger_actualizar_fecha
    BEFORE UPDATE ON propiedades
    FOR EACH ROW
    EXECUTE FUNCTION actualizar_fecha_actualizacion();

-- Función para calcular estadísticas de búsqueda
CREATE OR REPLACE FUNCTION calcular_estadisticas_busqueda()
RETURNS TABLE(
    total_propiedades BIGINT,
    propiedades_hoy BIGINT,
    precio_promedio DECIMAL,
    ciudad_mas_propiedades VARCHAR
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        COUNT(*) as total_propiedades,
        COUNT(CASE WHEN DATE(fecha_actualizacion) = CURRENT_DATE THEN 1 END) as propiedades_hoy,
        AVG(precio) as precio_promedio,
        (SELECT nombre FROM ciudades WHERE id = (
            SELECT ciudad_id FROM propiedades GROUP BY ciudad_id ORDER BY COUNT(*) DESC LIMIT 1
        )) as ciudad_mas_propiedades
    FROM propiedades
    WHERE estado = 'disponible';
END;
$$ LANGUAGE plpgsql;

-- =============================================
-- CONFIGURACIÓN DE PERMISOS
-- =============================================

-- Crear usuario para la aplicación
CREATE USER aria_user WITH PASSWORD 'aria_password_2024';
GRANT CONNECT ON DATABASE aria_real_estate TO aria_user;
GRANT USAGE ON SCHEMA public TO aria_user;
GRANT SELECT, INSERT, UPDATE ON ALL TABLES IN SCHEMA public TO aria_user;
GRANT USAGE ON ALL SEQUENCES IN SCHEMA public TO aria_user;

COMMENT ON DATABASE aria_real_estate IS 'Base de datos para propiedades inmobiliarias en Colombia - ARIA System';