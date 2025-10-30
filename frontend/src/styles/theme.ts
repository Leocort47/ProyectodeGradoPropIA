import { createTheme } from '@mui/material/styles'

const theme = createTheme({
  palette: {
    mode: 'light',
    primary: { main: '#005BBB' },
    secondary: { main: '#00A86B' },
    background: { default: '#f7f9fc' },
  },
  shape: { borderRadius: 10 },
  typography: {
    fontFamily: `'Inter', system-ui, -apple-system, Segoe UI, Roboto, Arial, sans-serif`,
  },
  components: {
    MuiButton: {
      styleOverrides: { root: { textTransform: 'none', fontWeight: 600 } },
    },
    MuiCard: {
      styleOverrides: { root: { borderRadius: 12 } },
    },
  },
})

export default theme
