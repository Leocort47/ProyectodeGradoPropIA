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

  // Imagen placeholder para propiedades sin imagen
  const PLACEHOLDER_IMAGE = 'https://via.placeholder.com/400x240/1a2332/6ae6ff?text=Imagen+no+disponible'

  const run = async (negocio: 'venta' | 'arriendo') => {
    try {
      setError(null)
      setLoading(true)
      const data = await getFincaRaizCards(10, negocio)
      setItems(data.cards || [])
    } catch (e: any) {
      setError(e?.response?.data?.detail || e?.message || 'Error cargando propiedades')
    } finally {
      setLoading(false)
    }
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
          Descubre propiedades con información verificada y fotos reales
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
              background: 'linear-gradient(135deg, #6ae6ff, #a78bfa)',
              color: '#0a0f1a',
              fontWeight: 700,
              px: 4,
              py: 1.5,
              fontSize: '1rem',
              borderRadius: '10px',
              boxShadow: '0 4px 14px rgba(106, 230, 255, 0.4)',
              '&:hover': {
                background: 'linear-gradient(135deg, #5dd5ff, #9775fa)',
                transform: 'translateY(-2px)',
                boxShadow: '0 6px 20px rgba(106, 230, 255, 0.5)'
              },
              '&:disabled': {
                background: 'rgba(106, 230, 255, 0.3)'
              }
            }}
          >
            🏠 Cargar en Venta
          </Button>
          <Button 
            variant="contained" 
            size="large"
            onClick={() => run('arriendo')}
            disabled={loading}
            sx={{
              background: 'linear-gradient(135deg, #a78bfa, #f472b6)',
              color: '#0a0f1a',
              fontWeight: 700,
              px: 4,
              py: 1.5,
              fontSize: '1rem',
              borderRadius: '10px',
              boxShadow: '0 4px 14px rgba(167, 139, 250, 0.4)',
              '&:hover': {
                background: 'linear-gradient(135deg, #9775fa, #e85ba5)',
                transform: 'translateY(-2px)',
                boxShadow: '0 6px 20px rgba(167, 139, 250, 0.5)'
              },
              '&:disabled': {
                background: 'rgba(167, 139, 250, 0.3)'
              }
            }}
          >
            🔑 Cargar en Arriendo
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
            Scrapeando propiedades...
          </Typography>
          <Typography variant="body1" sx={{ color: '#8fa9c8' }}>
            Esto puede tomar 1-2 minutos ⏱️
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
            fontSize: '1rem'
          }}
        >
          ⚠️ {error}
        </Alert>
      )}

      {/* Empty State */}
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
          <Typography variant="body1" sx={{ color: '#9cc3ff' }}>
            Haz clic en un botón para cargar propiedades verificadas de Finca Raíz
          </Typography>
        </Paper>
      )}

      {/* Property Cards Grid */}
      <Grid container spacing={3}>
        {items.map((p, i) => (
          <Grid item xs={12} sm={6} md={4} lg={3} key={i}>
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
              {p.price && (
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
                  {p.price_text}
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
                <Tooltip title="Compartir" arrow>
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
                  image={p.image_url || PLACEHOLDER_IMAGE}
                  alt={p.title}
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
                  {p.title}
                </Typography>
                
                {/* Ubicación */}
                <Stack direction="row" spacing={0.5} alignItems="center" sx={{ mb: 2 }}>
                  <Typography sx={{ color: '#9cc3ff', fontSize: '0.9rem', fontWeight: 500 }}>
                    📍 {p.location || 'Bucaramanga, Colombia'}
                  </Typography>
                </Stack>

                <Divider sx={{ borderColor: '#1b2340', my: 2 }} />

                {/* Características */}
                <Stack 
                  direction="row" 
                  spacing={1} 
                  sx={{ mb: 2, flexWrap: 'wrap', gap: 1 }}
                >
                  {p.area_m2 && (
                    <Chip 
                      label={`${p.area_m2} m²`}
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
                  {p.bedrooms && (
                    <Chip 
                      label={`${p.bedrooms} hab`}
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
                  {p.bathrooms && (
                    <Chip 
                      label={`${p.bathrooms} baños`}
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
                {p.admin && (
                  <Typography 
                    variant="body2" 
                    sx={{ 
                      color: '#b7c9ff',
                      mb: 1.5,
                      fontSize: '0.875rem'
                    }}
                  >
                    💳 Admin: <Box component="span" sx={{ fontWeight: 600 }}>{p.admin}</Box>
                  </Typography>
                )}

                {/* Descripción */}
                {p.description && (
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
                    {p.description}
                  </Typography>
                )}

                <Divider sx={{ borderColor: '#1b2340', my: 2 }} />

                {/* Contacto y acciones */}
                <Stack spacing={1.5}>
                  {p.phone && (
                    <Button
                      fullWidth
                      variant="outlined"
                      href={`tel:${p.phone}`}
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
                      📞 {p.phone}
                    </Button>
                  )}
                  
                  {p.link && (
                    <Button 
                      fullWidth
                      variant="contained"
                      href={p.link} 
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
