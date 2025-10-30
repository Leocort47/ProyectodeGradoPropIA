// Simple cliente API con axios y baseURL configurable por variable de entorno
import axios from 'axios'

const baseURL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'

export const api = axios.create({
  baseURL,
  timeout: 180000, // 3 minutos para scraping largo
  headers: {
    'Content-Type': 'application/json'
  }
})

// ============================================================
// TIPOS
// ============================================================

export interface Property {
  id: number
  title: string
  price: number
  location: string
  area?: number
  bedrooms?: number
  bathrooms?: number
  property_type?: string
  source_url?: string
}

export interface CardItem {
  title: string
  price?: number
  price_text: string
  location?: string
  area_m2?: string
  bedrooms?: number
  bathrooms?: number
  admin?: string
  phone?: string
  contact?: string
  description?: string
  image_url?: string
  link?: string
  // NUEVOS CAMPOS AGREGADOS
  images?: string[]
  original_url?: string
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

// ============================================================
// API CALLS
// ============================================================

/**
 * Obtener propiedades (búsqueda general)
 */
export const getProperties = async (params: {
  q?: string
  city?: string
  min_price?: number
  max_price?: number
  type?: string
}) => {
  const { data } = await api.get<Property[]>('/api/properties', { params })
  return data
}

/**
 * Scraping raw de Finca Raíz (items crudos)
 */
export const runFincaRaizScrape = async (pages = 1, negocio = 'venta') => {
  const { data } = await api.post('/api/scrape/fincaraiz', null, {
    params: { pages, negocio },
  })
  return data as { success: boolean; count: number; items: any[] }
}

/**
 * Scraping de Finca Raíz en formato tabla
 */
export const getFincaRaizTable = async (pages = 5, negocio: 'venta' | 'arriendo' = 'arriendo') => {
  const { data } = await api.post<{
    success: boolean
    count: number
    rows: PropertyTableRow[]
    columns?: string[]
  }>('/api/scrape/fincaraiz/table', null, {
    params: { pages, negocio }
  })
  return data
}

/**
 * Scraping de Finca Raíz en formato cards (con imágenes y carrusel)
 */
export const getFincaRaizCards = async (limit = 10, negocio: 'venta' | 'arriendo' = 'arriendo') => {
  const { data } = await api.get<{
    cards: CardItem[]
    total: number
  }>('/scrape/fincaraiz', {
    params: { limit, negocio }
  })
  return data
}

/**
 * Obtener estadísticas de propiedades
 */
export const getFincaRaizStats = async (pages = 2, negocio: 'venta' | 'arriendo' = 'arriendo') => {
  const { data } = await api.get<{
    success: boolean
    stats: {
      total_propiedades: number
      precio_promedio: number
      precio_min: number
      precio_max: number
      area_promedio: number
    }
  }>('/api/scrape/fincaraiz/stats', {
    params: { pages, negocio }
  })
  return data
}
