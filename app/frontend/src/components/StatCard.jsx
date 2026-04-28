import React from 'react';
import { Typography, Box, Paper, useTheme } from '@mui/material';

const StatCard = ({ title, value, color }) => {
  const theme = useTheme();

  return (
    <Paper sx={{ 
      p: 2.5, 
      display: 'flex', 
      flexDirection: 'column', 
      height: '100%',
      position: 'relative',
      borderRadius: '4px',
    }}>
      {/* Indicador de color discreto superior */}
      <Box sx={{
        position: 'absolute',
        top: 0,
        left: 0,
        right: 0,
        height: '3px',
        backgroundColor: color || theme.palette.primary.main,
      }} />

      <Typography variant="body2" sx={{ 
        color: 'text.secondary', 
        fontWeight: 600,
        mb: 1,
        textTransform: 'uppercase',
        letterSpacing: '0.5px'
      }}>
        {title}
      </Typography>
      
      <Typography variant="h3" sx={{ 
        color: 'text.primary', 
        fontWeight: 600,
        fontFamily: '"JetBrains Mono", monospace'
      }}>
        {value}
      </Typography>
    </Paper>
  );
};

export default StatCard;
