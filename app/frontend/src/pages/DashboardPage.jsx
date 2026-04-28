import React, { useState, useEffect } from 'react';
import { Box, CircularProgress, Typography, Paper, useTheme } from '@mui/material';
import StatCard from '../components/StatCard';
import InfractionsChart from '../components/InfractionsChart';
import RecentInfractionsChart from '../components/RecentInfractionsChart';
import ConfirmedInfractionsTable from '../components/ConfirmedInfractionsTable';

import { fetchDashboardStats, fetchInfractionsByRule, fetchInfractionsByDay, fetchAllInfractions } from '../api';

const cardBoxStyle = {
  p: 3,
  height: '100%',
  display: 'flex',
  flexDirection: 'column',
  width: '100%', 
};

const DashboardPage = () => {
  const theme = useTheme();
  const [stats, setStats] = useState(null);
  const [infractionsByRule, setInfractionsByRule] = useState([]);
  const [infractionsByDay, setInfractionsByDay] = useState([]);
  const [allInfractions, setAllInfractions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const loadDashboardData = async () => {
      try {
        const [dashboardStats, ruleData, dayData, allInfData] = await Promise.all([
          fetchDashboardStats(),
          fetchInfractionsByRule(),
          fetchInfractionsByDay(),
          fetchAllInfractions()
        ]);

        setStats(dashboardStats);
        setInfractionsByRule(ruleData);
        setInfractionsByDay(dayData);
        setAllInfractions(allInfData);
      } catch (err) {
        setError(err);
      } finally {
        setLoading(false);
      }
    };

    loadDashboardData();
  }, []);

  if (loading) {
    return (
      <Box sx={{ display: 'flex', flexDirection: 'column', justifyContent: 'center', alignItems: 'center', minHeight: '80vh' }}>
        <CircularProgress size={40} thickness={4} sx={{ color: theme.palette.text.secondary, mb: 2 }} />
        <Typography variant="body2" sx={{ fontFamily: '"JetBrains Mono", monospace', color: theme.palette.text.secondary }}>
          Loading System Data...
        </Typography>
      </Box>
    );
  }

  if (error) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: '80vh' }}>
        <Typography variant="body1" color="error">System Error: {error.message}</Typography>
      </Box>
    );
  }

  return (
    <Box sx={{ width: '100%' }}>
      <Typography variant="h5" sx={{ mb: 3, fontWeight: 600 }}>
        Dashboard Overview
      </Typography>

      {/* FILA 1: 4 Tarjetas Numéricas usando CSS Grid */}
      <Box 
        sx={{ 
          display: 'grid', 
          gridTemplateColumns: { xs: '1fr', sm: 'repeat(2, 1fr)', md: 'repeat(4, 1fr)' }, 
          gap: 3, 
          mb: 3 
        }}
      >
        <StatCard 
          title="Total Events" 
          value={stats.total_infractions} 
          color={theme.palette.text.secondary}
        />
        <StatCard 
          title="Pending Review" 
          value={stats.pending_review} 
          color={theme.palette.secondary.main}
        />
        <StatCard 
          title="Confirmed Valid" 
          value={stats.confirmed} 
          color={theme.palette.success.main}
        />
        <StatCard 
          title="Rejected (False Pos)" 
          value={stats.rejected} 
          color={theme.palette.error.main}
        />
      </Box>

      {/* FILA 2: Gráficos (2 columnas) usando CSS Grid */}
      <Box 
        sx={{ 
          display: 'grid', 
          gridTemplateColumns: { xs: '1fr', md: 'repeat(2, 1fr)' }, 
          gap: 3, 
          mb: 3 
        }}
      >
        <Paper sx={{ ...cardBoxStyle }}>
          <InfractionsChart data={infractionsByRule} />
        </Paper>
        <Paper sx={{ ...cardBoxStyle }}>
          <RecentInfractionsChart data={infractionsByDay} />
        </Paper>
      </Box>

      {/* FILA 3: Tabla (1 columna) usando CSS Grid */}
      <Box 
        sx={{ 
          display: 'grid', 
          gridTemplateColumns: '1fr', 
          gap: 3 
        }}
      >
        <Paper sx={{ ...cardBoxStyle, p: 0, overflow: 'hidden' }}>
          <ConfirmedInfractionsTable data={allInfractions.filter(inf => inf.status === 'CONFIRMED' || inf.status === 'REJECTED')} />
        </Paper>
      </Box>

    </Box>
  );
};

export default DashboardPage;