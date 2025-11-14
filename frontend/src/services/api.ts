// frontend/src/services/api.ts
// Cliente API completo y corregido para Fincaraíz Scraper
import axios from 'axios'

const baseURL = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000'

export const api = axios.create({
  baseURL,
  timeout: 180000, // 3 minutos para scraping largo
  headers: {
    'Content-Type': 'application/json'
  }
})

// Interceptor para manejar errores globalmente
api.interceptors.response.use(
  (response) => response,
  (error) => {
    console.error('API Error:', error.response?.data || error.message)
    
    if (error.code === 'ECONNREFUSED') {
      throw new Error('No se puede conectar al servidor. Verifica que el backend esté ejecutándose en http://127.0.0.1:8000')
    }
    
    if (error.response?.status === 404) {
      throw new Error('Endpoint no encontrado. Verifica las rutas del backend.')
    }
    
    if (error.response?.status >= 500) {
      throw new Error('Error interno del servidor. Intenta nuevamente.')
    }
    
    throw error
  }
)

// ============================================================
// TIPOS COMPLETOS Y CORREGIDOS
// ============================================================

export interface Property {
  id?: number
  title: string
  price: number
  location: string
  area?: number
  bedrooms?: number
  bathrooms?: number
  property_type?: string
  source_url?: string
}

// Interface principal para propiedades de Fincaraíz
export interface FincaRaizProperty {
  link: string
  nombre: string
  tipo: string
  ubicacion: string
  area_m2?: number
  habitaciones?: number
  banos?: number
  precio?: number
  telefonos?: string
  contacto?: string
  descripcion?: string
  image_url?: string
  administracion?: string
  es_nuevo?: boolean
  fr_id?: string
  demo?: boolean
}

// Response del endpoint de scraping
export interface ScrapingResponse {
  success: boolean
  count: number
  properties: FincaRaizProperty[]
  timestamp: string
  demo?: boolean
  error?: string
}

// CardItem para compatibilidad con el componente existente
export interface CardItem {
  title: string
  price?: number
  price_text: string
  location?: string
  area_m2?: number
  bedrooms?: number
  bathrooms?: number
  admin?: string
  phone?: string
  contact?: string
  description?: string
  image_url?: string
  link?: string
  images?: string[]
  original_url?: string
  // Campos adicionales para mejor UX
  tipo?: string
  habitaciones?: number
  banos?: number
  telefonos?: string
  demo?: boolean
}

export interface PropertyTableRow {
  Link: string
  Nombre: string
  Tipo: string
  Ubicación: string
  'Área (m²)': number | string
  Habitaciones: number | string
  Baños: number | string
  Precio: string
  Administración: string
  Teléfonos: string
  Contacto: string
  Descripción: string
  Imagen?: string
}

export interface StatsResponse {
  success: boolean
  stats: {
    total_propiedades: number
    precio_promedio: number
    precio_min: number
    precio_max: number
    area_promedio: number
    propiedades_con_telefono: number
    propiedades_con_imagen: number
  }
  timestamp: string
}

export interface TableResponse {
  success: boolean
  count: number
  data: PropertyTableRow[]
  columns?: string[]
}

// ============================================================
// API CALLS COMPLETAMENTE CORREGIDAS
// ============================================================

/**
 * SCRAPING PRINCIPAL - Endpoint corregido
 * Obtiene propiedades de Fincaraíz en tiempo real (25 propiedades = 5 páginas)
 */
export const scrapeFincaRaiz = async (
  limit: number = 25, 
  negocio: 'venta' | 'arriendo' = 'venta',
  ciudad: string = 'bucaramanga'
): Promise<ScrapingResponse> => {
  try {
    console.log(`🔄 Iniciando scraping: ${limit} propiedades, ${negocio}, ${ciudad}`)
    
    const { data } = await api.get<ScrapingResponse>('/scrape/fincaraiz', {
      params: { limit, negocio, ciudad }
    })
    
    if (!data.success) {
      throw new Error('El servidor no pudo completar el scraping')
    }
    
    console.log(`✅ Scraping exitoso: ${data.count} propiedades encontradas`)
    return data
  } catch (error: any) {
    console.error('❌ Error en scraping:', error)
    
    // Proporcionar mensajes de error más específicos
    let errorMessage = error.response?.data?.detail || error.message || 'Error desconocido en scraping'
    
    if (errorMessage.includes('conectar')) {
      errorMessage = 'No se puede conectar al servidor backend. Verifica que esté ejecutándose en http://127.0.0.1:8000'
    } else if (errorMessage.includes('tiempo')) {
      errorMessage = 'El scraping está tomando demasiado tiempo. El servidor puede estar sobrecargado.'
    } else if (errorMessage.includes('404')) {
      errorMessage = 'Endpoint no encontrado. El servidor puede estar usando rutas diferentes.'
    }
    
    throw new Error(errorMessage)
  }
}

/**
 * Scraping de Finca Raíz en formato cards (PRINCIPAL)
 * Compatible con PropertyGrid existente - 25 propiedades por defecto
 */
export const getFincaRaizCards = async (
  limit: number = 25, 
  negocio: 'venta' | 'arriendo' = 'venta'
): Promise<{ cards: CardItem[]; demo?: boolean }> => {
  try {
    console.log(`🔄 Solicitando ${limit} propiedades en ${negocio}...`)
    
    const response = await scrapeFincaRaiz(limit, negocio, 'bucaramanga')
    
    // Mapear propiedades al formato CardItem esperado por el frontend
    const cards: CardItem[] = response.properties.map((prop, index) => {
      // Determinar precio formateado
      let price_text = 'Consultar'
      if (prop.precio) {
        if (prop.precio >= 1000000) {
          price_text = `$${(prop.precio / 1000000).toFixed(1)}M`
        } else if (prop.precio >= 1000) {
          price_text = `$${(prop.precio / 1000).toFixed(0)}K`
        } else {
          price_text = `$${prop.precio.toLocaleString()}`
        }
      }
      
      return {
        title: prop.nombre || `${prop.tipo} en ${prop.ubicacion}`,
        price: prop.precio,
        price_text: price_text,
        location: prop.ubicacion,
        area_m2: prop.area_m2,
        bedrooms: prop.habitaciones,
        bathrooms: prop.banos,
        admin: prop.administracion,
        phone: prop.telefonos,
        contact: prop.contacto,
        description: prop.descripcion,
        image_url: prop.image_url,
        link: prop.link,
        // Campos adicionales para compatibilidad
        tipo: prop.tipo,
        habitaciones: prop.habitaciones,
        banos: prop.banos,
        telefonos: prop.telefonos,
        images: prop.image_url ? [prop.image_url] : [],
        demo: response.demo || false
      }
    })
    
    console.log(`✅ ${cards.length} propiedades mapeadas correctamente`)
    
    return { 
      cards,
      demo: response.demo
    }
  } catch (error: any) {
    console.error('❌ Error en getFincaRaizCards:', error)
    throw error
  }
}

/**
 * Scraping de Finca Raíz en formato tabla - ENDPOINT CORREGIDO
 * 5 páginas = 25 propiedades
 */
export const getFincaRaizTable = async (
  pages: number = 5, 
  negocio: 'venta' | 'arriendo' = 'venta'
): Promise<TableResponse> => {
  try {
    console.log(`📊 Solicitando tabla: ${pages} páginas, ${negocio}`)
    
    const { data } = await api.post<TableResponse>('/api/scrape/fincaraiz/table', null, {
      params: { pages, negocio }
    })
    
    console.log(`✅ Tabla recibida: ${data.count} filas, éxito: ${data.success}`)
    return data
    
  } catch (error: any) {
    console.error('❌ Error en getFincaRaizTable:', error)
    
    // Fallback robusto: usar el endpoint principal y convertir a tabla
    console.log('🔄 Usando fallback para tabla...')
    try {
      const scrapingResponse = await scrapeFincaRaiz(pages * 5, negocio)
      
      const tableData: PropertyTableRow[] = scrapingResponse.properties.map(prop => ({
        Link: prop.link || '#',
        Nombre: prop.nombre || 'Sin nombre',
        Tipo: prop.tipo || 'Inmueble',
        Ubicación: prop.ubicacion || 'Bucaramanga, Santander',
        'Área (m²)': prop.area_m2 || 'N/A',
        Habitaciones: prop.habitaciones || 'N/A',
        Baños: prop.banos || 'N/A',
        Precio: prop.precio ? `$${prop.precio.toLocaleString()}` : 'Consultar',
        Administración: prop.administracion || 'No incluye',
        Teléfonos: prop.telefonos || 'N/A',
        Contacto: prop.contacto || 'N/A',
        Descripción: prop.descripcion || 'Descripción no disponible',
        Imagen: prop.image_url || ''
      }))
      
      const result = {
        success: true,
        count: tableData.length,
        data: tableData,
        columns: tableData.length > 0 ? Object.keys(tableData[0]) : []
      }
      
      console.log(`✅ Fallback exitoso: ${result.count} filas generadas`)
      return result
      
    } catch (fallbackError) {
      console.error('❌ Fallback también falló:', fallbackError)
      throw new Error('No se pudo obtener datos para la tabla. Verifica la conexión con el servidor.')
    }
  }
}

/**
 * Obtener estadísticas de propiedades
 */
export const getFincaRaizStats = async (
  pages: number = 5, 
  negocio: 'venta' | 'arriendo' = 'venta'
): Promise<StatsResponse> => {
  try {
    const { data } = await api.get<StatsResponse>('/api/scrape/fincaraiz/stats', {
      params: { pages, negocio }
    })
    
    return data
  } catch (error: any) {
    console.warn('⚠️ Endpoint de stats no disponible, calculando localmente...')
    
    // Fallback: calcular stats localmente desde los datos
    try {
      const scrapingResponse = await scrapeFincaRaiz(pages * 5, negocio)
      const properties = scrapingResponse.properties
      
      const precios = properties.filter(p => p.precio && p.precio > 0).map(p => p.precio!)
      const areas = properties.filter(p => p.area_m2 && p.area_m2 > 0).map(p => p.area_m2!)
      
      const stats = {
        total_propiedades: properties.length,
        precio_promedio: precios.length > 0 ? Math.round(precios.reduce((a, b) => a + b, 0) / precios.length) : 0,
        precio_min: precios.length > 0 ? Math.min(...precios) : 0,
        precio_max: precios.length > 0 ? Math.max(...precios) : 0,
        area_promedio: areas.length > 0 ? Math.round(areas.reduce((a, b) => a + b, 0) / areas.length) : 0,
        propiedades_con_telefono: properties.filter(p => p.telefonos && p.telefonos.length > 0).length,
        propiedades_con_imagen: properties.filter(p => p.image_url && p.image_url.length > 0).length
      }
      
      return {
        success: true,
        stats,
        timestamp: new Date().toISOString()
      }
    } catch (calcError) {
      console.error('❌ Error calculando stats:', calcError)
      throw new Error('No se pudieron calcular las estadísticas')
    }
  }
}

/**
 * Health check del servidor
 */
export const healthCheck = async (): Promise<{ status: string; timestamp: string }> => {
  try {
    const { data } = await api.get('/health')
    console.log('✅ Health check exitoso:', data.status)
    return data
  } catch (error) {
    console.error('❌ Health check falló:', error)
    throw new Error('Servidor no disponible')
  }
}

/**
 * Obtener propiedades (búsqueda general) - ENDPOINT LEGACY
 */
export const getProperties = async (params: {
  q?: string
  city?: string
  min_price?: number
  max_price?: number
  type?: string
} = {}) => {
  try {
    const { data } = await api.get<Property[]>('/api/properties', { params })
    return data
  } catch (error: any) {
    console.warn('⚠️ Endpoint /api/properties no disponible:', error.message)
    return [] // Retorna array vacío para compatibilidad
  }
}

/**
 * Scraping raw de Finca Raíz (LEGACY - mantener compatibilidad)
 */
export const runFincaRaizScrape = async (pages = 1, negocio = 'venta') => {
  try {
    const response = await scrapeFincaRaiz(pages * 5, negocio as 'venta' | 'arriendo')
    return {
      success: response.success,
      count: response.count,
      items: response.properties
    }
  } catch (error) {
    console.error('❌ Error en runFincaRaizScrape:', error)
    return {
      success: false,
      count: 0,
      items: []
    }
  }
}

/**
 * Obtener datos de demostración
 */
export const getDemoData = async (): Promise<ScrapingResponse> => {
  try {
    const { data } = await api.get<ScrapingResponse>('/scrape/fincaraiz/demo')
    return data
  } catch (error: any) {
    console.error('❌ Error obteniendo datos demo:', error)
    throw new Error('No se pudieron cargar los datos de demostración')
  }
}

// ============================================================
// UTILIDADES
// ============================================================

/**
 * Formatear precio para display
 */
export const formatPrice = (price: number): string => {
  if (!price || price <= 0) return 'Consultar'
  
  if (price >= 1000000) {
    return `$${(price / 1000000).toFixed(1)}M`
  } else if (price >= 1000) {
    return `$${(price / 1000).toFixed(0)}K`
  }
  return `$${price.toLocaleString()}`
}

/**
 * Validar si una propiedad tiene datos mínimos
 */
export const isValidProperty = (property: FincaRaizProperty): boolean => {
  return !!(property.nombre && (property.precio || property.area_m2 || property.habitaciones))
}

/**
 * Filtrar propiedades duplicadas por link
 */
export const removeDuplicateProperties = (properties: FincaRaizProperty[]): FincaRaizProperty[] => {
  const seen = new Set()
  return properties.filter(prop => {
    const key = prop.link || prop.nombre
    if (!key || seen.has(key)) {
      return false
    }
    seen.add(key)
    return true
  })
}

/**
 * Generar datos de demostración localmente (fallback ultimate)
 */
export const generateLocalDemoData = (count: number = 25, negocio: 'venta' | 'arriendo' = 'venta'): CardItem[] => {
  const locations = [
    "Bucaramanga, Santander",
    "Floridablanca, Santander", 
    "Girón, Santander",
    "Piedecuesta, Santander",
    "Cabecera, Bucaramanga"
  ]
  
  const types = ["Apartamento", "Casa", "Apartaestudio"]
  
  return Array.from({ length: count }, (_, i) => {
    const basePrice = negocio === 'venta' ? 450000000 + (i * 10000000) : 1200000 + (i * 100000)
    const area = 60 + (i * 5)
    const bedrooms = 2 + (i % 3)
    
    return {
      title: `${types[i % types.length]} moderno en ${locations[i % locations.length]}`,
      price: basePrice,
      price_text: formatPrice(basePrice),
      location: locations[i % locations.length],
      area_m2: area,
      bedrooms: bedrooms,
      bathrooms: 1 + (i % 2),
      admin: 'No incluye',
      phone: `315${1000000 + i}`,
      contact: i % 2 === 0 ? 'Inmobiliaria Finca Raíz' : 'Propietario Directo',
      description: `Excelente propiedad en ${locations[i % locations.length]} con ${bedrooms} habitaciones y ${area} m². Perfecta para ${negocio}.`,
      image_url: `https://images.unsplash.com/photo-${1560448204 + i}-e02f11c3d0e2?w=400&h=300&fit=crop`,
      link: `https://www.fincaraiz.com.co/inmueble/demo-${i + 1}`,
      tipo: types[i % types.length],
      habitaciones: bedrooms,
      banos: 1 + (i % 2),
      telefonos: `315${1000000 + i}`,
      demo: true
    }
  })
}

export default api