import React, { useState, useEffect } from 'react';
import { AppBar, Toolbar, Typography, Box, IconButton, useTheme } from '@mui/material';
import AccountCircleIcon from '@mui/icons-material/AccountCircle';
import CircleIcon from '@mui/icons-material/Circle';

const drawerWidth = 240;

const Topbar = () => {
  const theme = useTheme();
  const [time, setTime] = useState(new Date().toLocaleTimeString('en-US', { hour12: false }) + ' UTC-5');

  useEffect(() => {
    const interval = setInterval(() => {
      setTime(new Date().toLocaleTimeString('en-US', { hour12: false }) + ' UTC-5');
    }, 1000);
    return () => clearInterval(interval);
  }, []);

  return (
    <AppBar
      position="fixed"
      sx={{
        width: `calc(100% - ${drawerWidth}px)`,
        ml: `${drawerWidth}px`,
      }}
    >
      <Toolbar sx={{ height: '64px', display: 'flex', justifyContent: 'space-between' }}>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
          <Typography variant="h6" sx={{ color: theme.palette.text.primary, fontWeight: 500, letterSpacing: 'normal', textTransform: 'none' }}>
            System Dashboard
          </Typography>
        </Box>
        
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 3 }}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <CircleIcon sx={{ fontSize: 10, color: theme.palette.success.main }} />
            <Typography variant="body2" sx={{ fontFamily: '"JetBrains Mono", monospace' }}>
              LIVE FEED
            </Typography>
          </Box>

          <Typography variant="body2" sx={{ fontFamily: '"JetBrains Mono", monospace', color: theme.palette.text.secondary }}>
            {time}
          </Typography>

          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, pl: 2, borderLeft: `1px solid ${theme.palette.divider}` }}>
            <AccountCircleIcon sx={{ color: theme.palette.text.secondary }} />
            <Typography variant="body2" sx={{ color: theme.palette.text.primary, fontWeight: 500 }}>
              Operator: Luis
            </Typography>
          </Box>
        </Box>
      </Toolbar>
    </AppBar>
  );
};

export default Topbar;
