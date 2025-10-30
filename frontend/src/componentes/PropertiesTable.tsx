import { useState } from 'react'

import {
  Box,
  Button,
  Stack,
  Alert,
  CircularProgress,
  Paper,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Chip,
  Link,
  Typography
} from '@mui/material'
import { getFincaRaizTable, type PropertyTableRow } from '../services/api'

export default function PropertyTable() {
  const [rows, setRows] = useState<PropertyTableRow[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const run = async (negocio: 'venta' | 'arriendo') => {
    try {
      setError(null)
      setLoading(true)
      const data = await getFincaRaizTable(2, negocio)
      setRows(data.rows || [])
    } catch (e: any) {
      setError(e?.response?.data?.detail || e?.message || 'Error cargando propiedades')
    } finally {
      setLoading(false)
    }
  }

  return (
    <Box sx={{ p: 3 }}>
      <Stack direction="row" spacing={2} sx={{ mb: 3 }}>
        <Button
          variant="contained"
          onClick={() => run('venta')}
          disabled={loading}
        >
          Cargar Venta
        </Button>
        <Button
          variant="contained"
          color="secondary"
          onClick={() => run('arriendo')}
          disabled={loading}
        >
          Cargar Arriendo
        </Button>
      </Stack>

      {loading && (
        <Box sx={{ display: 'flex', justifyContent: 'center', my: 4 }}>
          <CircularProgress />
          <Typography sx={{ ml: 2, alignSelf: 'center' }}>
            Scrapeando propiedades... Esto puede tardar unos minutos
          </Typography>
        </Box>
      )}

      {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}

      {!loading && rows.length === 0 && (
        <Alert severity="info">
          Haz clic en un botón para cargar propiedades en formato tabla
        </Alert>
      )}

      {rows.length > 0 && (
        <>
          <Alert severity="success" sx={{ mb: 2 }}>
            {rows.length} propiedades encontradas
          </Alert>

          <TableContainer component={Paper} sx={{ maxHeight: 600 }}>
            <Table stickyHeader>
              <TableHead>
                <TableRow>
                  <TableCell><strong>Nombre</strong></TableCell>
                  <TableCell><strong>Tipo</strong></TableCell>
                  <TableCell><strong>Ubicación</strong></TableCell>
                  <TableCell align="right"><strong>Precio</strong></TableCell>
                  <TableCell align="right"><strong>Área</strong></TableCell>
                  <TableCell align="center"><strong>Hab</strong></TableCell>
                  <TableCell align="center"><strong>Baños</strong></TableCell>
                  <TableCell><strong>Teléfonos</strong></TableCell>
                  <TableCell><strong>Link</strong></TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {rows.map((row, index) => (
                  <TableRow
                    key={index}
                    sx={{ '&:hover': { backgroundColor: 'rgba(144, 202, 249, 0.08)' } }}
                  >
                    <TableCell>
                      <Typography variant="body2" sx={{ maxWidth: 200 }}>
                        {row.Nombre || 'Sin nombre'}
                      </Typography>
                    </TableCell>

                    <TableCell>
                      <Chip
                        label={row.Tipo || 'N/D'}
                        size="small"
                        color={
                          row.Tipo === 'Apartamento' ? 'primary' :
                          row.Tipo === 'Casa' ? 'secondary' :
                          'default'
                        }
                      />
                    </TableCell>

                    <TableCell>{row.Ubicación || 'Bucaramanga'}</TableCell>

                    <TableCell align="right">
                      <Typography variant="body2" color="primary" fontWeight="bold">
                        {row.Precio || 'Consultar'}
                      </Typography>
                    </TableCell>

                    <TableCell align="right">
                      {row['Área (m²)'] ? `${row['Área (m²)']} m²` : '-'}
                    </TableCell>

                    <TableCell align="center">{row.Habitaciones || '-'}</TableCell>
                    <TableCell align="center">{row.Baños || '-'}</TableCell>

                    <TableCell>
                      {row.Teléfonos ? (
                        <Chip
                          label={row.Teléfonos}
                          size="small"
                          color="success"
                          variant="outlined"
                        />
                      ) : (
                        '-'
                      )}
                    </TableCell>

                    <TableCell>
                      {row.Link && (
                        <Link
                          href={row.Link}
                          target="_blank"
                          rel="noopener noreferrer"
                          underline="hover"
                        >
                          Ver
                        </Link>
                      )}
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </TableContainer>
        </>
      )}
    </Box>
  )
}