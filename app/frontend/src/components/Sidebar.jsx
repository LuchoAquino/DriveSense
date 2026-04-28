import React from 'react';
import { NavLink } from 'react-router-dom';
import { Box, Drawer, List, ListItem, ListItemIcon, ListItemText, Typography, useTheme } from '@mui/material';
import DashboardIcon from '@mui/icons-material/Dashboard';
import ChecklistIcon from '@mui/icons-material/Checklist';
import BarChartIcon from '@mui/icons-material/BarChart';
import ShieldIcon from '@mui/icons-material/Shield';

const drawerWidth = 240;

const navItems = [
  { text: 'Overview', icon: <DashboardIcon />, path: '/' },
  { text: 'Pending Review', icon: <ChecklistIcon />, path: '/revision' },
  { text: 'Reports', icon: <BarChartIcon />, path: '/reportes' },
];

const Sidebar = () => {
  const theme = useTheme();

  return (
    <Drawer
      variant="permanent"
      sx={{
        width: drawerWidth,
        flexShrink: 0,
        [`& .MuiDrawer-paper`]: {
          width: drawerWidth,
          boxSizing: 'border-box',
        },
      }}
    >
      <Box sx={{ p: 2, display: 'flex', alignItems: 'center', gap: 1.5, borderBottom: `1px solid ${theme.palette.divider}`, height: '64px' }}>
        <ShieldIcon sx={{ color: theme.palette.text.primary, fontSize: 24 }} />
        <Typography variant="h6" sx={{ color: theme.palette.text.primary, m: 0, textTransform: 'none', letterSpacing: 'normal' }}>
          DriveSense
        </Typography>
      </Box>

      <Box sx={{ p: 1 }}>
        <List sx={{ display: 'flex', flexDirection: 'column', gap: 0.5 }}>
          {navItems.map((item) => (
            <ListItem key={item.text} disablePadding>
              <NavLink 
                to={item.path} 
                end
                style={({ isActive }) => ({
                  display: 'flex',
                  alignItems: 'center',
                  width: '100%',
                  padding: '8px 16px',
                  textDecoration: 'none',
                  borderRadius: '4px',
                  color: isActive ? theme.palette.text.primary : theme.palette.text.secondary,
                  backgroundColor: isActive ? 'rgba(255, 255, 255, 0.05)' : 'transparent',
                })}
              >
                {({ isActive }) => (
                  <>
                    <ListItemIcon sx={{ 
                      minWidth: '36px', 
                      color: isActive ? theme.palette.text.primary : theme.palette.text.secondary,
                    }}>
                      {React.cloneElement(item.icon, { sx: { fontSize: 20 } })}
                    </ListItemIcon>
                    <ListItemText 
                      primary={item.text} 
                      primaryTypographyProps={{ 
                        fontWeight: isActive ? 600 : 500,
                        fontSize: '0.875rem'
                      }} 
                    />
                  </>
                )}
              </NavLink>
            </ListItem>
          ))}
        </List>
      </Box>
    </Drawer>
  );
};

export default Sidebar;
