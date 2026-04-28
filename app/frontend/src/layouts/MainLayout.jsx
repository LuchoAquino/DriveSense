import React from 'react';
import { Box, CssBaseline, Toolbar, Container } from '@mui/material';
import { Outlet } from 'react-router-dom';
import Sidebar from '../components/Sidebar';
import Topbar from '../components/Topbar';

const drawerWidth = 240;

const MainLayout = () => {
  return (
    <Box sx={{ display: 'flex', minHeight: '100vh', width: '100vw', overflowX: 'hidden' }}>
      <CssBaseline />
      <Topbar />
      <Sidebar />
      <Box
        component="main"
        sx={{
          flexGrow: 1,
          width: `calc(100% - ${drawerWidth}px)`,
          position: 'relative',
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center', // Center the Container
        }}
      >
        <Toolbar sx={{ height: '64px', width: '100%' }} /> {/* Spacer for Topbar */}
        <Container maxWidth="xl" sx={{ p: 4, flexGrow: 1, display: 'flex', flexDirection: 'column' }}>
          <Outlet />
        </Container>
      </Box>
    </Box>
  );
};

export default MainLayout;
