import React, { useState } from 'react';
import { Box, Typography, Table, TableBody, TableCell, TableContainer, TableHead, TableRow, Button, useTheme } from '@mui/material';
import ReviewInfractionModal from './ReviewInfractionModal';

const InfractionList = ({ infractions, onReviewSuccess }) => {
  const theme = useTheme();
  const [openModal, setOpenModal] = useState(false);
  const [selectedInfraction, setSelectedInfraction] = useState(null);

  const handleReviewClick = (infraction) => {
    setSelectedInfraction(infraction);
    setOpenModal(true);
  };

  const handleCloseModal = () => {
    setOpenModal(false);
    setSelectedInfraction(null);
  };

  const formatTimestamp = (timestamp) => {
    if (!timestamp) return '-';
    const date = new Date(timestamp);
    return date.toLocaleString('en-US', { 
      month: 'short', day: '2-digit', 
      hour: '2-digit', minute: '2-digit', second: '2-digit', hour12: false
    });
  };

  return (
    <Box sx={{ width: '100%' }}>
      <Box sx={{ mb: 3, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <Typography variant="h5" sx={{ fontWeight: 600 }}>
          Pending Review Queue
        </Typography>
        <Typography variant="body2" color="text.secondary">
          {infractions.length} event(s) awaiting operator action
        </Typography>
      </Box>

      <TableContainer sx={{ border: `1px solid ${theme.palette.divider}`, borderRadius: '4px', bgcolor: theme.palette.background.paper }}>
        <Table size="small">
          <TableHead>
            <TableRow>
              <TableCell>ID</TableCell>
              <TableCell>RULE</TableCell>
              <TableCell>PLATE</TableCell>
              <TableCell>TIMESTAMP</TableCell>
              <TableCell>NODE ID</TableCell>
              <TableCell>CONFIDENCE</TableCell>
              <TableCell align="right">ACTION</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {infractions.length === 0 ? (
              <TableRow>
                <TableCell colSpan={7} align="center" sx={{ py: 6, color: theme.palette.text.secondary }}>
                  No pending events in the queue.
                </TableCell>
              </TableRow>
            ) : (
              infractions.map((infraction) => (
                <TableRow key={infraction.id} hover>
                  <TableCell sx={{ color: theme.palette.text.secondary }}>#{infraction.id}</TableCell>
                  <TableCell sx={{ fontWeight: 500 }}>{infraction.rule_name}</TableCell>
                  <TableCell sx={{ fontFamily: '"JetBrains Mono", monospace', fontWeight: 600, fontSize: '0.9rem' }}>
                    {infraction.plate_number || 'UNKNOWN'}
                  </TableCell>
                  <TableCell sx={{ fontFamily: '"JetBrains Mono", monospace', fontSize: '0.8rem', color: theme.palette.text.secondary }}>
                    {formatTimestamp(infraction.timestamp)}
                  </TableCell>
                  <TableCell sx={{ fontFamily: '"JetBrains Mono", monospace', fontSize: '0.8rem' }}>
                    {infraction.camera_id}
                  </TableCell>
                  <TableCell>{`${(infraction.confidence * 100).toFixed(0)}%`}</TableCell>
                  <TableCell align="right">
                    <Button
                      variant="contained"
                      color="primary"
                      size="small"
                      onClick={() => handleReviewClick(infraction)}
                    >
                      Review Evidence
                    </Button>
                  </TableCell>
                </TableRow>
              ))
            )}
          </TableBody>
        </Table>
      </TableContainer>

      <ReviewInfractionModal
        open={openModal}
        onClose={handleCloseModal}
        infraction={selectedInfraction}
        onReviewSuccess={onReviewSuccess}
      />
    </Box>
  );
};

export default InfractionList;
