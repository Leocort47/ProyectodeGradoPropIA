import { useState } from 'react'
import { Box, Typography, TextField, Button, Stack, Chip } from '@mui/material'

export default function AriaChat() {
  const [query, setQuery] = useState('')

  const handleSearch = () => {
    // Aquí irá la lógica de búsqueda con IA
    console.log('Buscando:', query)
  }

  return (
    <Box sx={{ 
      background: 'linear-gradient(160deg, rgba(24,32,54,.9), rgba(15,21,36,.9))',
      border: '1px solid #1c2740',
      borderRadius: '14px',
      padding: '16px',
      color: '#ffffff'  // ← Texto blanco por defecto
    }}>
      {/* Encabezado con logo y título */}
      <Stack direction="row" spacing={2} alignItems="center" sx={{ mb: 2 }}>
        <Box
          sx={{
            width: 48,
            height: 48,
            borderRadius: '12px',
            background: 'linear-gradient(135deg, #a78bfa, #6ae6ff)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center'
          }}
        >
          <Typography sx={{ fontSize: '24px' }}>🏠</Typography>
        </Box>
        
        <Box>
          <Typography variant="h6" sx={{ 
            color: '#ffffff',
            fontWeight: 700,
            lineHeight: 1.2
          }}>
            ARIA - Asistente IA
          </Typography>
          <Typography sx={{ 
            color: '#d0eaff',
            fontSize: '0.875rem'
          }}>
            Listo para ayudarte
          </Typography>
        </Box>
      </Stack>

      {/* Mensaje de bienvenida */}
      <Box sx={{ 
        backgroundColor: 'rgba(106, 230, 255, 0.05)',
        borderLeft: '3px solid #6ae6ff',
        borderRadius: '8px',
        padding: '12px',
        mb: 2
      }}>
        <Typography sx={{ 
          color: '#ffffff',
          mb: 1,
          fontSize: '0.95rem'
        }}>
          👋 ¡Hola! Soy ARIA, tu asistente inmobiliario. ¿Qué buscas hoy? Ej:
        </Typography>
        
        <Typography sx={{ 
          color: '#e6f0ff',
          fontStyle: 'italic',
          fontSize: '0.9rem',
          pl: 2
        }}>
          "apartamento en Cabecera con 3 habitaciones"
        </Typography>
      </Box>

      {/* Campo de búsqueda */}
      <TextField
        fullWidth
        value={query}
        onChange={(e) => setQuery(e.target.value)}
        placeholder="Ej: apartaestudio en Cabecera con 2 hab"
        sx={{
          mb: 2,
          '& .MuiInputBase-input': {
            color: '#ffffff',
          },
          '& .MuiInputBase-input::placeholder': {
            color: '#8fa9c8',
            opacity: 1
          },
          '& .MuiOutlinedInput-root': {
            backgroundColor: 'rgba(0,0,0,0.2)',
            '& fieldset': {
              borderColor: '#1b2340'
            },
            '&:hover fieldset': {
              borderColor: '#6ae6ff'
            },
            '&.Mui-focused fieldset': {
              borderColor: '#6ae6ff'
            }
          }
        }}
      />

      {/* Chips de sugerencias */}
      <Stack direction="row" spacing={1} sx={{ mb: 2, flexWrap: 'wrap', gap: 1 }}>
        <Chip 
          label="3 hab" 
          size="small"
          sx={{ 
            color: '#ffffff',
            borderColor: '#1b2340',
            backgroundColor: 'rgba(106, 230, 255, 0.1)',
            '&:hover': {
              backgroundColor: 'rgba(106, 230, 255, 0.2)'
            }
          }}
        />
        <Chip 
          label="Cabecera" 
          size="small"
          sx={{ 
            color: '#ffffff',
            borderColor: '#1b2340',
            backgroundColor: 'rgba(106, 230, 255, 0.1)',
            '&:hover': {
              backgroundColor: 'rgba(106, 230, 255, 0.2)'
            }
          }}
        />
        <Chip 
          label="casa" 
          size="small"
          sx={{ 
            color: '#ffffff',
            borderColor: '#1b2340',
            backgroundColor: 'rgba(106, 230, 255, 0.1)',
            '&:hover': {
              backgroundColor: 'rgba(106, 230, 255, 0.2)'
            }
          }}
        />
      </Stack>

      {/* Botón de enviar */}
      <Button
        fullWidth
        variant="contained"
        onClick={handleSearch}
        disabled={!query.trim()}
        sx={{
          background: 'linear-gradient(135deg, #6ae6ff, #a78bfa)',
          color: '#0a0f1a',
          fontWeight: 700,
          textTransform: 'none',
          py: 1.5,
          '&:hover': {
            background: 'linear-gradient(135deg, #5dd5ff, #9775fa)',
          },
          '&:disabled': {
            background: 'rgba(106, 230, 255, 0.1)',
            color: '#4a5568'
          }
        }}
        endIcon={
          <Box sx={{ fontSize: '20px' }}>▶</Box>
        }
      >
        Buscar propiedades
      </Button>
    </Box>
  )
}
