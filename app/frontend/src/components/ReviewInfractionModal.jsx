import React, { useState, useEffect, useRef } from 'react';
import { Modal, Box, Typography, Button, TextField, IconButton, Grid, CircularProgress, Alert, useTheme } from '@mui/material';
import CloseIcon from '@mui/icons-material/Close';
import { reviewInfraction } from '../api';

const ReviewInfractionModal = ({ open, onClose, infraction, onReviewSuccess }) => {
  const theme = useTheme();
  const [reviewComments, setReviewComments] = useState('');
  const [editedPlateNumber, setEditedPlateNumber] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [videoError, setVideoError] = useState(false);
  const [videoLoading, setVideoLoading] = useState(true);
  const videoRef = useRef(null);

  useEffect(() => {
    if (open) {
      setReviewComments('');
      setEditedPlateNumber(infraction?.plate_number || '');
      setError(null);
      setVideoError(false);
      setVideoLoading(true);
    }
  }, [open, infraction]);

  if (!infraction) return null;

  const handleReview = async (decision) => {
    setLoading(true);
    setError(null);
    try {
      await reviewInfraction(infraction.id, {
        review_decision: decision,
        review_comments: reviewComments,
        plate_number: editedPlateNumber,
      });
      onReviewSuccess();
      onClose();
    } catch (err) {
      setError(err.message || 'Error en revisión');
    } finally {
      setLoading(false);
    }
  };

  const formatTimestamp = (timestamp) => {
    if (!timestamp) return 'N/A';
    const date = new Date(timestamp);
    return date.toLocaleString('en-US', { day: '2-digit', month: '2-digit', year: 'numeric', hour: '2-digit', minute: '2-digit', second: '2-digit', hour12: false });
  };

  const modalStyle = {
    position: 'absolute',
    top: '50%',
    left: '50%',
    transform: 'translate(-50%, -50%)',
    width: { xs: '95%', md: 900 },
    bgcolor: theme.palette.background.paper,
    border: `1px solid ${theme.palette.divider}`,
    borderRadius: '8px',
    boxShadow: 24,
    p: 3,
    maxHeight: '95vh',
    overflowY: 'auto',
  };

  return (
    <Modal open={open} onClose={onClose}>
      <Box sx={modalStyle}>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3, borderBottom: `1px solid ${theme.palette.divider}`, pb: 1.5 }}>
          <Typography variant="h6" sx={{ fontWeight: 600 }}>
            Review Incident #{infraction.id}
          </Typography>
          <IconButton onClick={onClose} size="small">
            <CloseIcon />
          </IconButton>
        </Box>

        {loading && (
          <Box sx={{ display: 'flex', justifyContent: 'center', my: 2 }}>
            <CircularProgress size={24} sx={{ mr: 2 }} />
            <Typography>Processing...</Typography>
          </Box>
        )}
        
        {error && (
          <Alert severity="error" sx={{ my: 2 }}>
            {error}
          </Alert>
        )}

        <Grid container spacing={3}>
          <Grid item xs={12} md={7}>
            <Box sx={{
                width: '100%', height: 400, bgcolor: '#000', display: 'flex', alignItems: 'center', justifyContent: 'center',
                position: 'relative', borderRadius: '4px', overflow: 'hidden'
              }}>
              {videoLoading && <CircularProgress sx={{ position: 'absolute', zIndex: 1 }} />}
              {videoError ? (
                <Box sx={{ textAlign: 'center', p: 2 }}>
                  <Typography variant="body2" color="error">Evidence video unavailable</Typography>
                  <Button variant="text" sx={{ mt: 1 }} onClick={() => window.open(`http://127.0.0.1:8000/evidence/${infraction.video_path}`, '_blank')}>
                    Try Direct Link
                  </Button>
                </Box>
              ) : (
                <video ref={videoRef} controls width="100%" height="100%" src={`http://127.0.0.1:8000/evidence/${infraction.video_path}`}
                  onError={() => { setVideoError(true); setVideoLoading(false); }} onLoadedData={() => { setVideoError(false); setVideoLoading(false); }} onCanPlay={() => setVideoLoading(false)}
                  preload="metadata" style={{ objectFit: 'contain' }}
                />
              )}
            </Box>
          </Grid>

          <Grid item xs={12} md={5}>
            <Box sx={{ mb: 3 }}>
              <TextField 
                label="Plate Number" 
                variant="outlined" 
                value={editedPlateNumber} 
                onChange={(e) => setEditedPlateNumber(e.target.value)} 
                fullWidth 
                size="small"
                sx={{ 
                  mb: 2, 
                  '& .MuiInputBase-input': { 
                    fontFamily: '"JetBrains Mono", monospace', 
                    fontSize: '1.25rem', 
                    fontWeight: 600 
                  } 
                }} 
              />
              
              <Grid container spacing={1} sx={{ mb: 2 }}>
                <Grid item xs={4}>
                  <Typography variant="caption" color="text.secondary">TIMESTAMP</Typography>
                </Grid>
                <Grid item xs={8}>
                  <Typography variant="body2" sx={{ fontFamily: '"JetBrains Mono", monospace' }}>{formatTimestamp(infraction.timestamp)}</Typography>
                </Grid>
                
                <Grid item xs={4}>
                  <Typography variant="caption" color="text.secondary">CAMERA ID</Typography>
                </Grid>
                <Grid item xs={8}>
                  <Typography variant="body2" sx={{ fontFamily: '"JetBrains Mono", monospace' }}>{infraction.camera_id}</Typography>
                </Grid>

                <Grid item xs={4}>
                  <Typography variant="caption" color="text.secondary">VIOLATION</Typography>
                </Grid>
                <Grid item xs={8}>
                  <Typography variant="body2" sx={{ fontWeight: 600, color: theme.palette.error.main }}>{infraction.rule_name}</Typography>
                </Grid>

                <Grid item xs={4}>
                  <Typography variant="caption" color="text.secondary">CONFIDENCE</Typography>
                </Grid>
                <Grid item xs={8}>
                  <Typography variant="body2">{(infraction.confidence * 100).toFixed(0)}%</Typography>
                </Grid>
              </Grid>
            </Box>

            <TextField 
              label="Review Comments" 
              variant="outlined" 
              multiline 
              rows={3} 
              fullWidth 
              size="small"
              value={reviewComments} 
              onChange={(e) => setReviewComments(e.target.value)} 
              sx={{ mb: 3 }} 
            />

            <Box sx={{ display: 'flex', gap: 2 }}>
              <Button 
                variant="contained" 
                color="success" 
                onClick={() => handleReview('CONFIRMED')} 
                disabled={loading} 
                fullWidth
              >
                Confirm
              </Button>
              <Button 
                variant="contained" 
                color="error" 
                onClick={() => handleReview('REJECTED')} 
                disabled={loading} 
                fullWidth
              >
                Reject
              </Button>
            </Box>
          </Grid>
        </Grid>
      </Box>
    </Modal>
  );
};

export default ReviewInfractionModal;