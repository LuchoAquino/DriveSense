import React from 'react';
import ReactDOM from 'react-dom/client';
import { BrowserRouter } from 'react-router-dom';
import { ThemeProvider, CssBaseline } from '@mui/material';
import App from './App.jsx';
import theme from './theme/theme.js'; // Importamos nuestro tema personalizado
import './index.css';

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    {/* El ThemeProvider aplica el tema a todos los componentes hijos */}
    <ThemeProvider theme={theme}>
      {/* CssBaseline normaliza los estilos a través de los navegadores */}
      <CssBaseline />
      {/* BrowserRouter habilita el enrutamiento en la aplicación */}
      <BrowserRouter>
        <App />
      </BrowserRouter>
    </ThemeProvider>
  </React.StrictMode>,
);