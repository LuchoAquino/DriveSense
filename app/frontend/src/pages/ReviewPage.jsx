
import React, { useState, useEffect } from 'react';
import { Box, CircularProgress, Typography } from '@mui/material';
import InfractionList from '../components/InfractionList';
import { fetchPendingInfractions } from '../api';

const ReviewPage = () => {
  const [pendingInfractions, setPendingInfractions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const loadPendingInfractions = async () => {
    try {
      setLoading(true);
      const data = await fetchPendingInfractions();
      setPendingInfractions(data);
    } catch (err) {
      setError(err);
      console.error("Error loading pending infractions:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadPendingInfractions();
  }, []);

  if (loading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: '100vh' }}>
        <CircularProgress />
        <Typography variant="h6" sx={{ ml: 2 }}>Cargando infracciones pendientes...</Typography>
      </Box>
    );
  }

  if (error) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: '100vh' }}>
        <Typography variant="h6" color="error">Error al cargar las infracciones: {error.message}</Typography>
      </Box>
    );
  }

  return (
    <Box>
      <InfractionList infractions={pendingInfractions} onReviewSuccess={loadPendingInfractions} />
    </Box>
  );
};

export default ReviewPage;
