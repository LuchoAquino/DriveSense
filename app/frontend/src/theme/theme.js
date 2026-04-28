import { createTheme } from '@mui/material/styles';

const darkBg = '#121212';
const paperBg = '#1E1E1E';
const primaryGray = '#3A3A3C';
const textPrimary = '#F3F4F6';
const textSecondary = '#9CA3AF';
const colorGreen = '#10B981'; // Allowed / Confirmed
const colorRed = '#EF4444';   // Alert / Rejected
const colorAmber = '#F59E0B'; // Pending

const theme = createTheme({
  palette: {
    mode: 'dark',
    primary: {
      main: '#4B5563',
      light: '#6B7280',
    },
    secondary: {
      main: colorAmber,
    },
    success: {
      main: colorGreen,
    },
    error: {
      main: colorRed,
    },
    background: {
      default: darkBg,
      paper: paperBg,
    },
    text: {
      primary: textPrimary,
      secondary: textSecondary,
    },
    divider: '#333333',
  },
  typography: {
    fontFamily: '"Inter", "Roboto", "Helvetica", "Arial", sans-serif',
    h1: { fontWeight: 600, letterSpacing: '-0.5px' },
    h2: { fontWeight: 600, letterSpacing: '-0.5px' },
    h3: { fontWeight: 600, letterSpacing: '-0.5px' },
    h4: { fontWeight: 600, fontSize: '1.5rem', letterSpacing: '-0.25px' },
    h5: { fontWeight: 600, fontSize: '1.25rem' },
    h6: { fontWeight: 600, fontSize: '1rem', color: textSecondary, textTransform: 'uppercase', letterSpacing: '0.5px' },
    button: {
      textTransform: 'none',
      fontWeight: 500,
    },
    body1: {
      fontSize: '0.875rem',
    },
    body2: {
      fontSize: '0.875rem',
      color: textSecondary,
    },
  },
  shape: {
    borderRadius: 4, // Very subtle rounding
  },
  components: {
    MuiCssBaseline: {
      styleOverrides: {
        body: {
          backgroundColor: darkBg,
          color: textPrimary,
        },
      },
    },
    MuiPaper: {
      styleOverrides: {
        root: {
          backgroundImage: 'none',
          boxShadow: 'none',
          border: '1px solid #333333',
        },
      },
    },
    MuiButton: {
      styleOverrides: {
        root: {
          boxShadow: 'none',
          '&:hover': {
            boxShadow: 'none',
          },
        },
      },
    },
    MuiAppBar: {
      styleOverrides: {
        root: {
          backgroundColor: paperBg,
          borderBottom: '1px solid #333333',
          boxShadow: 'none',
        },
      },
    },
    MuiDrawer: {
      styleOverrides: {
        paper: {
          backgroundColor: paperBg,
          borderRight: '1px solid #333333',
        },
      },
    },
    MuiTableCell: {
      styleOverrides: {
        root: {
          borderBottom: '1px solid #333333',
          padding: '12px 16px',
        },
        head: {
          backgroundColor: '#18181B',
          color: textSecondary,
          fontWeight: 600,
          textTransform: 'uppercase',
          fontSize: '0.75rem',
          letterSpacing: '0.5px',
        },
      },
    },
    MuiChip: {
      styleOverrides: {
        root: {
          fontWeight: 600,
          borderRadius: '4px',
        },
      },
    },
  },
});

export default theme;
