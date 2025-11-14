import { useState, useEffect } from 'react'
import Grid from '@mui/material/Grid'
import { 
  Card, 
  CardMedia, 
  CardContent, 
  Typography, 
  Chip, 
  Button, 
  Stack, 
  Alert, 
  CircularProgress,
  Box,
  Divider,
  IconButton,
  Tooltip,
  Paper,
  Container
} from '@mui/material'
import FavoriteIcon from '@mui/icons-material/Favorite'
import ShareIcon from '@mui/icons-material/Share'
import TrendingUpIcon from '@mui/icons-material/TrendingUp'
import LocationCityIcon from '@mui/icons-material/LocationCity'
import { getFincaRaizCards, type CardItem } from '../services/api'

export default function PropertyGrid() {
  const [items, setItems] = useState<CardItem[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [lastSearch, setLastSearch] = useState<'venta' | 'arriendo'>('venta')

  // Imagen placeholder para propiedades sin imagen
  const PLACEHOLDER_IMAGE = 'https://via.placeholder.com/400x240/1a2332/6ae6ff?text=Imagen+no+disponible'

  const run = async (negocio: 'venta' | 'arriendo') => {
    try {
      setError(null)
      setLoading(true)
      setLastSearch(negocio)
      
      console.log(`🔄 Iniciando scraping para: ${negocio}`)
      
      const data = await getFincaRaizCards(10, negocio)
      
      console.log(`✅ Scraping completado: ${data.cards?.length || 0} propiedades encontradas`)
      
      setItems(data.cards || [])
      
      if (!data.cards || data.cards.length === 0) {
        setError('No se encontraron propiedades. Intenta con otros parámetros.')
      }
    } catch (e: any) {
      console.error('❌ Error en scraping:', e)
      
      const errorMessage = e?.response?.data?.detail || e?.message || 'Error cargando propiedades'
      
      // Mensajes de error más específicos
      if (errorMessage.includes('conectar')) {
        setError('⚠️ No se puede conectar al servidor. Verifica que el backend esté ejecutándose en http://127.0.0.1:8000')
      } else if (errorMessage.includes('tiempo')) {
        setError('⏱️ El scraping está tomando demasiado tiempo. El servidor puede estar ocupado. Intenta nuevamente.')
      } else if (errorMessage.includes('No se encontraron propiedades')) {
        setError('🏠 No se encontraron propiedades con los criterios actuales. Intenta con "Arriendo" u otras ciudades.')
      } else {
        setError(`❌ ${errorMessage}`)
      }
    } finally {
      setLoading(false)
    }
  }

  // Cargar propiedades en venta al iniciar
  useEffect(() => {
    run('venta')
  }, [])

  // Función para compartir propiedad
 const handleShare = async (property: CardItem) => {
  try {
    // Validar y proveer valores por defecto
    const shareTitle = property.title || 'Propiedad en Finca Raíz'
    const shareText = property.description?.substring(0, 100) || 'Propiedad disponible en el mercado inmobiliario'
    const shareUrl = property.link || window.location.href

    // Verificar si Web Share API está disponible
    if (navigator.share) {
      await navigator.share({
        title: shareTitle,
        text: shareText,
        url: shareUrl,
      })
      console.log('Propiedad compartida exitosamente')
    } else {
      // Fallback: copiar al portapapeles
      await navigator.clipboard.writeText(shareUrl)
      
      // Mostrar notificación más elegante
      const notification = document.createElement('div')
      notification.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        background: #22c55e;
        color: white;
        padding: 12px 20px;
        border-radius: 8px;
        font-weight: 600;
        z-index: 10000;
        box-shadow: 0 4px 12px rgba(0,0,0,0.3);
      `
      notification.textContent = '✅ Enlace copiado al portapapeles'
      document.body.appendChild(notification)
      
      // Auto-remover después de 3 segundos
      setTimeout(() => {
        if (document.body.contains(notification)) {
          document.body.removeChild(notification)
        }
      }, 3000)
    }
  } catch (error: any) {
    console.error('Error al compartir:', error)
    
    // No mostrar alerta si el usuario canceló el share
    if (error.name !== 'AbortError') {
      // Notificación de error elegante
      const errorNotification = document.createElement('div')
      errorNotification.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        background: #ef4444;
        color: white;
        padding: 12px 20px;
        border-radius: 8px;
        font-weight: 600;
        z-index: 10000;
        box-shadow: 0 4px 12px rgba(0,0,0,0.3);
      `
      errorNotification.textContent = '❌ Error al compartir la propiedad'
      document.body.appendChild(errorNotification)
      
      setTimeout(() => {
        if (document.body.contains(errorNotification)) {
          document.body.removeChild(errorNotification)
        }
      }, 3000)
    }
  }
}

  // Función para formatear precios
  const formatPrice = (price: number) => {
    if (price >= 1000000) {
      return `$${(price / 1000000).toFixed(1)}M`
    } else if (price >= 1000) {
      return `$${(price / 1000).toFixed(0)}K`
    }
    return `$${price}`
  }

  return (
    <Container maxWidth="xl" sx={{ py: 4 }}>
      {/* Hero Section con Estadísticas del Mercado Colombiano */}
      <Box sx={{ mb: 5 }}>
        <Typography 
          variant="h3" 
          sx={{ 
            color: '#ffffff',
            fontWeight: 800,
            mb: 2,
            textAlign: 'center',
            background: 'linear-gradient(135deg, #6ae6ff, #a78bfa)',
            WebkitBackgroundClip: 'text',
            WebkitTextFillColor: 'transparent'
          }}
        >
          Mercado Inmobiliario Colombia 2025
        </Typography>
        
        <Typography 
          variant="h6" 
          sx={{ 
            color: '#9cc3ff',
            mb: 4,
            textAlign: 'center',
            fontWeight: 400
          }}
        >
          Propiedades verificadas en tiempo real de Finca Raíz
        </Typography>

        {/* Estadísticas del Mercado en Cards */}
        <Grid container spacing={2} sx={{ mb: 4 }}>
          <Grid item xs={12} sm={6} md={3}>
            <Paper 
              elevation={0}
              sx={{ 
                p: 2.5, 
                background: 'linear-gradient(135deg, rgba(106, 230, 255, 0.15), rgba(106, 230, 255, 0.05))',
                border: '1px solid rgba(106, 230, 255, 0.3)',
                borderRadius: '12px',
                textAlign: 'center'
              }}
            >
              <TrendingUpIcon sx={{ color: '#6ae6ff', fontSize: 40, mb: 1 }} />
              <Typography variant="h5" sx={{ color: '#6ae6ff', fontWeight: 700 }}>
                +7.8%
              </Typography>
              <Typography variant="body2" sx={{ color: '#9cc3ff' }}>
                Crecimiento Medellín
              </Typography>
            </Paper>
          </Grid>

          <Grid item xs={12} sm={6} md={3}>
            <Paper 
              elevation={0}
              sx={{ 
                p: 2.5, 
                background: 'linear-gradient(135deg, rgba(167, 139, 250, 0.15), rgba(167, 139, 250, 0.05))',
                border: '1px solid rgba(167, 139, 250, 0.3)',
                borderRadius: '12px',
                textAlign: 'center'
              }}
            >
              <LocationCityIcon sx={{ color: '#a78bfa', fontSize: 40, mb: 1 }} />
              <Typography variant="h5" sx={{ color: '#a78bfa', fontWeight: 700 }}>
                180K
              </Typography>
              <Typography variant="body2" sx={{ color: '#b7aeff' }}>
                Unidades disponibles
              </Typography>
            </Paper>
          </Grid>

          <Grid item xs={12} sm={6} md={3}>
            <Paper 
              elevation={0}
              sx={{ 
                p: 2.5, 
                background: 'linear-gradient(135deg, rgba(244, 114, 182, 0.15), rgba(244, 114, 182, 0.05))',
                border: '1px solid rgba(244, 114, 182, 0.3)',
                borderRadius: '12px',
                textAlign: 'center'
              }}
            >
              <Typography variant="h5" sx={{ color: '#f472b6', fontWeight: 700 }}>
                $1,500
              </Typography>
              <Typography variant="body2" sx={{ color: '#ffb3e0' }}>
                USD/m² Bogotá
              </Typography>
            </Paper>
          </Grid>

          <Grid item xs={12} sm={6} md={3}>
            <Paper 
              elevation={0}
              sx={{ 
                p: 2.5, 
                background: 'linear-gradient(135deg, rgba(34, 197, 94, 0.15), rgba(34, 197, 94, 0.05))',
                border: '1px solid rgba(34, 197, 94, 0.3)',
                borderRadius: '12px',
                textAlign: 'center'
              }}
            >
              <Typography variant="h5" sx={{ color: '#22c55e', fontWeight: 700 }}>
                +10%
              </Typography>
              <Typography variant="body2" sx={{ color: '#86efac' }}>
                Crecimiento Cartagena
              </Typography>
            </Paper>
          </Grid>
        </Grid>

        {/* Botones de acción */}
        <Stack direction="row" spacing={2} justifyContent="center" sx={{ mb: 3 }}>
          <Button 
            variant="contained" 
            size="large"
            onClick={() => run('venta')}
            disabled={loading}
            sx={{
              background: lastSearch === 'venta' 
                ? 'linear-gradient(135deg, #6ae6ff, #a78bfa)' 
                : 'rgba(106, 230, 255, 0.2)',
              color: lastSearch === 'venta' ? '#0a0f1a' : '#6ae6ff',
              fontWeight: 700,
              px: 4,
              py: 1.5,
              fontSize: '1rem',
              borderRadius: '10px',
              boxShadow: lastSearch === 'venta' 
                ? '0 4px 14px rgba(106, 230, 255, 0.4)' 
                : 'none',
              border: lastSearch === 'venta' ? 'none' : '1px solid rgba(106, 230, 255, 0.5)',
              '&:hover': {
                background: 'linear-gradient(135deg, #5dd5ff, #9775fa)',
                transform: 'translateY(-2px)',
                boxShadow: '0 6px 20px rgba(106, 230, 255, 0.5)'
              },
              '&:disabled': {
                background: 'rgba(106, 230, 255, 0.1)',
                color: 'rgba(106, 230, 255, 0.5)'
              }
            }}
          >
            {loading && lastSearch === 'venta' ? '🔄 Cargando...' : '🏠 Propiedades en Venta'}
          </Button>
          <Button 
            variant="contained" 
            size="large"
            onClick={() => run('arriendo')}
            disabled={loading}
            sx={{
              background: lastSearch === 'arriendo' 
                ? 'linear-gradient(135deg, #a78bfa, #f472b6)' 
                : 'rgba(167, 139, 250, 0.2)',
              color: lastSearch === 'arriendo' ? '#0a0f1a' : '#a78bfa',
              fontWeight: 700,
              px: 4,
              py: 1.5,
              fontSize: '1rem',
              borderRadius: '10px',
              boxShadow: lastSearch === 'arriendo' 
                ? '0 4px 14px rgba(167, 139, 250, 0.4)' 
                : 'none',
              border: lastSearch === 'arriendo' ? 'none' : '1px solid rgba(167, 139, 250, 0.5)',
              '&:hover': {
                background: 'linear-gradient(135deg, #9775fa, #e85ba5)',
                transform: 'translateY(-2px)',
                boxShadow: '0 6px 20px rgba(167, 139, 250, 0.5)'
              },
              '&:disabled': {
                background: 'rgba(167, 139, 250, 0.1)',
                color: 'rgba(167, 139, 250, 0.5)'
              }
            }}
          >
            {loading && lastSearch === 'arriendo' ? '🔄 Cargando...' : '🔑 Propiedades en Arriendo'}
          </Button>
        </Stack>

        {/* Contador de resultados */}
        {items.length > 0 && !loading && (
          <Box sx={{ 
            display: 'flex',
            justifyContent: 'center'
          }}>
            <Paper
              elevation={0}
              sx={{ 
                px: 3,
                py: 1.5,
                borderRadius: '10px',
                background: 'rgba(106, 230, 255, 0.1)',
                border: '1px solid rgba(106, 230, 255, 0.3)'
              }}
            >
              <Typography sx={{ color: '#6ae6ff', fontWeight: 600, fontSize: '1.1rem' }}>
                📊 {items.length} propiedades encontradas
              </Typography>
            </Paper>
          </Box>
        )}
      </Box>

      {/* Loading State */}
      {loading && (
        <Box sx={{ 
          display: 'flex', 
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center', 
          my: 10
        }}>
          <CircularProgress 
            size={70} 
            thickness={4}
            sx={{ 
              mb: 3,
              color: '#6ae6ff'
            }} 
          />
          <Typography variant="h5" sx={{ color: '#d0eaff', mb: 1, fontWeight: 600 }}>
            Scrapeando propiedades en tiempo real...
          </Typography>
          <Typography variant="body1" sx={{ color: '#8fa9c8' }}>
            Esto puede tomar 1-2 minutos ⏱️
          </Typography>
          <Typography variant="body2" sx={{ color: '#6ae6ff', mt: 1, fontStyle: 'italic' }}>
            Extrayendo datos actualizados de Finca Raíz
          </Typography>
        </Box>
      )}
      
      {/* Error State */}
      {error && (
        <Alert 
          severity="error" 
          sx={{ 
            mb: 4,
            backgroundColor: 'rgba(244, 67, 54, 0.1)',
            border: '1px solid rgba(244, 67, 54, 0.3)',
            borderRadius: '10px',
            color: '#ff6b6b',
            fontSize: '1rem',
            '& .MuiAlert-message': {
              width: '100%'
            }
          }}
          action={
            <Button 
              color="inherit" 
              size="small" 
              onClick={() => run(lastSearch)}
              sx={{ color: '#ff6b6b', fontWeight: 600 }}
            >
              REINTENTAR
            </Button>
          }
        >
          {error}
        </Alert>
      )}

      {/* Empty State - Solo mostrar si no hay loading ni error */}
      {!loading && items.length === 0 && !error && (
        <Paper
          elevation={0}
          sx={{
            p: 6,
            textAlign: 'center',
            backgroundColor: 'rgba(106, 230, 255, 0.05)',
            border: '2px dashed rgba(106, 230, 255, 0.3)',
            borderRadius: '16px'
          }}
        >
          <Typography variant="h5" sx={{ color: '#6ae6ff', mb: 2, fontWeight: 600 }}>
            💡 ¡Comienza tu búsqueda!
          </Typography>
          <Typography variant="body1" sx={{ color: '#9cc3ff', mb: 3 }}>
            Haz clic en un botón para cargar propiedades verificadas de Finca Raíz
          </Typography>
          <Stack direction="row" spacing={2} justifyContent="center">
            <Button 
              variant="outlined"
              onClick={() => run('venta')}
              sx={{
                borderColor: '#6ae6ff',
                color: '#6ae6ff',
                '&:hover': {
                  backgroundColor: 'rgba(106, 230, 255, 0.1)'
                }
              }}
            >
              Buscar en Venta
            </Button>
            <Button 
              variant="outlined"
              onClick={() => run('arriendo')}
              sx={{
                borderColor: '#a78bfa',
                color: '#a78bfa',
                '&:hover': {
                  backgroundColor: 'rgba(167, 139, 250, 0.1)'
                }
              }}
            >
              Buscar en Arriendo
            </Button>
          </Stack>
        </Paper>
      )}

      {/* Property Cards Grid */}
      <Grid container spacing={3}>
        {items.map((property, index) => (
          <Grid item xs={12} sm={6} md={4} lg={3} key={index}>
            <Card 
              sx={{ 
                height: '100%',
                display: 'flex',
                flexDirection: 'column',
                background: 'linear-gradient(160deg, rgba(24,32,54,.98), rgba(15,21,36,.98))',
                border: '1px solid #1b2340',
                borderRadius: '16px',
                transition: 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
                position: 'relative',
                overflow: 'hidden',
                '&:hover': {
                  transform: 'translateY(-8px)',
                  boxShadow: '0 20px 40px rgba(106, 230, 255, 0.25)',
                  borderColor: '#6ae6ff',
                  '& .property-image': {
                    transform: 'scale(1.1)'
                  }
                }
              }}
            >
              {/* Badge de precio */}
              {property.price && (
                <Box
                  sx={{
                    position: 'absolute',
                    top: 12,
                    left: 12,
                    zIndex: 3,
                    background: 'linear-gradient(135deg, #6ae6ff, #a78bfa)',
                    color: '#0a0f1a',
                    px: 2,
                    py: 0.75,
                    borderRadius: '10px',
                    fontWeight: 800,
                    fontSize: '0.95rem',
                    boxShadow: '0 4px 12px rgba(0, 0, 0, 0.5)',
                    backdropFilter: 'blur(10px)'
                  }}
                >
                  {property.price_text || formatPrice(property.price)}
                </Box>
              )}

              {/* Botones de acción */}
              <Box
                sx={{
                  position: 'absolute',
                  top: 12,
                  right: 12,
                  zIndex: 3,
                  display: 'flex',
                  gap: 1
                }}
              >
                <Tooltip title="Guardar favorito" arrow>
                  <IconButton
                    size="small"
                    sx={{
                      backgroundColor: 'rgba(10, 15, 26, 0.8)',
                      backdropFilter: 'blur(10px)',
                      color: '#fff',
                      '&:hover': {
                        backgroundColor: '#6ae6ff',
                        color: '#0a0f1a'
                      }
                    }}
                  >
                    <FavoriteIcon fontSize="small" />
                  </IconButton>
                </Tooltip>
                <Tooltip title="Compartir propiedad" arrow>
                  <IconButton
                    size="small"
                    onClick={() => handleShare(property)}
                    sx={{
                      backgroundColor: 'rgba(10, 15, 26, 0.8)',
                      backdropFilter: 'blur(10px)',
                      color: '#fff',
                      '&:hover': {
                        backgroundColor: '#6ae6ff',
                        color: '#0a0f1a'
                      }
                    }}
                  >
                    <ShareIcon fontSize="small" />
                  </IconButton>
                </Tooltip>
              </Box>

              {/* Imagen de propiedad con fallback */}
              <Box sx={{ 
                position: 'relative',
                overflow: 'hidden',
                height: 220,
                backgroundColor: '#1a2332'
              }}>
                <CardMedia 
                  component="img"
                  className="property-image"
                  sx={{ 
                    height: '100%',
                    width: '100%',
                    objectFit: 'cover',
                    transition: 'transform 0.5s cubic-bezier(0.4, 0, 0.2, 1)'
                  }} 
                  image={property.image_url || PLACEHOLDER_IMAGE}
                  alt={property.title}
                  onError={(e: any) => {
                    e.target.src = PLACEHOLDER_IMAGE
                  }}
                />
                {/* Overlay gradient para mejor legibilidad */}
                <Box sx={{
                  position: 'absolute',
                  bottom: 0,
                  left: 0,
                  right: 0,
                  height: '50%',
                  background: 'linear-gradient(to top, rgba(10, 15, 26, 0.8), transparent)'
                }} />
              </Box>
              
              <CardContent sx={{ flexGrow: 1, p: 2.5 }}>
                {/* Título */}
                <Typography 
                  variant="h6" 
                  sx={{ 
                    color: '#ffffff',
                    fontWeight: 700,
                    mb: 1.5,
                    lineHeight: 1.4,
                    fontSize: '1.1rem',
                    display: '-webkit-box',
                    WebkitLineClamp: 2,
                    WebkitBoxOrient: 'vertical',
                    overflow: 'hidden',
                    minHeight: '2.8rem'
                  }}
                >
                  {property.title}
                </Typography>
                
                {/* Ubicación */}
                <Stack direction="row" spacing={0.5} alignItems="center" sx={{ mb: 2 }}>
                  <Typography sx={{ color: '#9cc3ff', fontSize: '0.9rem', fontWeight: 500 }}>
                    📍 {property.location || 'Bucaramanga, Colombia'}
                  </Typography>
                </Stack>

                <Divider sx={{ borderColor: '#1b2340', my: 2 }} />

                {/* Características */}
                <Stack 
                  direction="row" 
                  spacing={1} 
                  sx={{ mb: 2, flexWrap: 'wrap', gap: 1 }}
                >
                  {property.area_m2 && (
                    <Chip 
                      label={`${property.area_m2} m²`}
                      size="small"
                      sx={{
                        backgroundColor: 'rgba(106, 230, 255, 0.2)',
                        color: '#6ae6ff',
                        borderColor: 'rgba(106, 230, 255, 0.4)',
                        border: '1px solid',
                        fontWeight: 700,
                        fontSize: '0.8rem'
                      }}
                    />
                  )}
                  {property.bedrooms && (
                    <Chip 
                      label={`${property.bedrooms} hab`}
                      size="small"
                      sx={{
                        backgroundColor: 'rgba(167, 139, 250, 0.2)',
                        color: '#a78bfa',
                        borderColor: 'rgba(167, 139, 250, 0.4)',
                        border: '1px solid',
                        fontWeight: 700,
                        fontSize: '0.8rem'
                      }}
                    />
                  )}
                  {property.bathrooms && (
                    <Chip 
                      label={`${property.bathrooms} baños`}
                      size="small"
                      sx={{
                        backgroundColor: 'rgba(244, 114, 182, 0.2)',
                        color: '#f472b6',
                        borderColor: 'rgba(244, 114, 182, 0.4)',
                        border: '1px solid',
                        fontWeight: 700,
                        fontSize: '0.8rem'
                      }}
                    />
                  )}
                </Stack>

                {/* Administración */}
                {property.admin && (
                  <Typography 
                    variant="body2" 
                    sx={{ 
                      color: '#b7c9ff',
                      mb: 1.5,
                      fontSize: '0.875rem'
                    }}
                  >
                    💳 Admin: <Box component="span" sx={{ fontWeight: 600 }}>{property.admin}</Box>
                  </Typography>
                )}

                {/* Descripción */}
                {property.description && (
                  <Typography 
                    variant="body2" 
                    sx={{ 
                      color: '#8fa9c8',
                      mb: 2,
                      overflow: 'hidden',
                      textOverflow: 'ellipsis',
                      display: '-webkit-box',
                      WebkitLineClamp: 2,
                      WebkitBoxOrient: 'vertical',
                      lineHeight: 1.6,
                      fontSize: '0.875rem'
                    }}
                  >
                    {property.description}
                  </Typography>
                )}

                <Divider sx={{ borderColor: '#1b2340', my: 2 }} />

                {/* Contacto y acciones */}
                <Stack spacing={1.5}>
                  {property.phone && (
                    <Button
                      fullWidth
                      variant="outlined"
                      href={`tel:${property.phone}`}
                      sx={{
                        borderColor: 'rgba(34, 197, 94, 0.5)',
                        backgroundColor: 'rgba(34, 197, 94, 0.1)',
                        color: '#22c55e',
                        fontWeight: 600,
                        py: 1,
                        '&:hover': {
                          borderColor: '#22c55e',
                          backgroundColor: 'rgba(34, 197, 94, 0.2)'
                        }
                      }}
                    >
                      📞 {property.phone}
                    </Button>
                  )}
                  
                  {property.link && (
                    <Button 
                      fullWidth
                      variant="contained"
                      href={property.link} 
                      target="_blank" 
                      rel="noopener noreferrer"
                      sx={{
                        background: 'linear-gradient(135deg, #6ae6ff, #a78bfa)',
                        color: '#0a0f1a',
                        fontWeight: 700,
                        textTransform: 'none',
                        py: 1.2,
                        fontSize: '0.95rem',
                        '&:hover': {
                          background: 'linear-gradient(135deg, #5dd5ff, #9775fa)',
                          transform: 'scale(1.02)',
                          boxShadow: '0 4px 12px rgba(106, 230, 255, 0.4)'
                        }
                      }}
                    >
                      Ver detalles completos →
                    </Button>
                  )}
                </Stack>
              </CardContent>
            </Card>
          </Grid>
        ))}
      </Grid>
    </Container>
  )
}