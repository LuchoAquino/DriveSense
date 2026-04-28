import React from 'react';
import { Typography, Box } from '@mui/material';
import AssignmentTurnedInIcon from '@mui/icons-material/AssignmentTurnedIn';

const WelcomeCard = () => {
  return (
    <Box sx={{ display: 'flex', alignItems: 'center', height: '100%' }}>
      <Box sx={{ flexGrow: 1 }}>
        <Typography variant="h6" color="text.secondary">
          Bienvenido de nuevo,
        </Typography>
        <Typography variant="h4" component="div" sx={{ fontWeight: 'bold', color: 'primary.main' }}>
          Luis Gonzales
        </Typography>
        <Typography variant="body2" color="text.secondary" display={'flex'} sx={{ mt: 1 }}>
          Revisa tus actividades pendientes por evaluar
        </Typography>
      </Box>
      <Box sx={{ color: 'primary.main', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
        <AssignmentTurnedInIcon sx={{ fontSize: 60 }} />
      </Box>
    </Box>
  );
};

export default WelcomeCard;