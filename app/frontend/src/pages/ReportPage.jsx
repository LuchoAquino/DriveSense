import React, { useState, useEffect } from 'react';
import {
  Box,
  Typography,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Checkbox,
  Button,
  CircularProgress,
  Alert,
  Modal,
  TextField,
  IconButton,
} from '@mui/material';
import CloseIcon from '@mui/icons-material/Close';
import { fetchConfirmedInfractions, generatePdfReport, sendReportEmail } from '../api';

const ReportPage = () => {
  const [infractions, setInfractions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [selectedInfractions, setSelectedInfractions] = useState([]);
  const [emailModalOpen, setEmailModalOpen] = useState(false);
  const [emailRecipient, setEmailRecipient] = useState('');
  const [emailSubject, setEmailSubject] = useState('Reporte de Infracciones');
  const [emailBody, setEmailBody] = useState('Adjunto el reporte de infracciones seleccionadas.');
  const [sendingEmail, setSendingEmail] = useState(false);
  const [emailError, setEmailError] = useState(null);
  const [emailSuccess, setEmailSuccess] = useState(false);

  useEffect(() => {
    const getConfirmedInfractions = async () => {
      try {
        const data = await fetchConfirmedInfractions();
        setInfractions(data);
      } catch (err) {
        setError(err.message || 'Error al cargar las infracciones confirmadas');
        console.error('Error fetching confirmed infractions:', err);
      } finally {
        setLoading(false);
      }
    };

    getConfirmedInfractions();
  }, []);

  const handleSelectAllClick = (event) => {
    if (event.target.checked) {
      const newSelecteds = infractions.map((n) => n.id);
      setSelectedInfractions(newSelecteds);
      return;
    }
    setSelectedInfractions([]);
  };

  const handleClick = (event, id) => {
    const selectedIndex = selectedInfractions.indexOf(id);
    let newSelected = [];

    if (selectedIndex === -1) {
      newSelected = newSelected.concat(selectedInfractions, id);
    } else if (selectedIndex === 0) {
      newSelected = newSelected.concat(selectedInfractions.slice(1));
    } else if (selectedIndex === selectedInfractions.length - 1) {
      newSelected = newSelected.concat(selectedInfractions.slice(0, -1));
    } else if (selectedIndex > 0) {
      newSelected = newSelected.concat(
        selectedInfractions.slice(0, selectedIndex),
        selectedInfractions.slice(selectedIndex + 1),
      );
    }
    setSelectedInfractions(newSelected);
  };

  const isSelected = (id) => selectedInfractions.indexOf(id) !== -1;

  const handleGenerateReport = async () => {
    try {
      const pdfBlob = await generatePdfReport(selectedInfractions);
      const url = window.URL.createObjectURL(pdfBlob);
      const a = document.createElement('a');
      a.href = url;
      a.download = 'reporte_infracciones.pdf';
      document.body.appendChild(a);
      a.click();
      a.remove();
      window.URL.revokeObjectURL(url);
    } catch (err) {
      setError(err.message || 'Error al generar el reporte PDF');
      console.error('Error generating PDF report:', err);
    }
  };

  const handleOpenEmailModal = () => {
    setEmailModalOpen(true);
    setEmailError(null);
    setEmailSuccess(false);
  };

  const handleCloseEmailModal = () => {
    setEmailModalOpen(false);
    setEmailRecipient('');
    setEmailSubject('Reporte de Infracciones');
    setEmailBody('Adjunto el reporte de infracciones seleccionadas.');
  };

  const handleSendEmailConfirm = async () => {
    setSendingEmail(true);
    setEmailError(null);
    setEmailSuccess(false);
    try {
      await sendReportEmail({
        recipient_email: emailRecipient,
        subject: emailSubject,
        body: emailBody,
        infraction_ids: selectedInfractions,
      });
      setEmailSuccess(true);
      // Optionally close modal after a short delay or user action
      // setTimeout(() => handleCloseEmailModal(), 2000);
    } catch (err) {
      setEmailError(err.message || 'Error al enviar el correo');
      console.error('Error sending email:', err);
    } finally {
      setSendingEmail(false);
    }
  };

  if (loading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '80vh' }}>
        <CircularProgress />
        <Typography sx={{ ml: 2 }}>Cargando infracciones confirmadas...</Typography>
      </Box>
    );
  }

  if (error) {
    return (
      <Box sx={{ p: 3 }}>
        <Alert severity="error">{error}</Alert>
      </Box>
    );
  }

  return (
    <Box sx={{ p: 3 }}>
      <Typography variant="h4" component="h1" gutterBottom>
        Reporte de Infracciones Confirmadas
      </Typography>

      <Box sx={{ mb: 2, display: 'flex', gap: 2 }}>
        <Button
          variant="contained"
          color="primary"
          onClick={handleGenerateReport}
          disabled={selectedInfractions.length === 0}
        >
          Generar Informe PDF
        </Button>
        <Button
          variant="contained"
          color="secondary"
          onClick={handleOpenEmailModal}
          disabled={selectedInfractions.length === 0}
        >
          Enviar por Correo
        </Button>
      </Box>

      <TableContainer component={Paper}>
        <Table sx={{ minWidth: 650 }} aria-label="confirmed infractions table">
          <TableHead>
            <TableRow>
              <TableCell padding="checkbox">
                <Checkbox
                  indeterminate={selectedInfractions.length > 0 && selectedInfractions.length < infractions.length}
                  checked={infractions.length > 0 && selectedInfractions.length === infractions.length}
                  onChange={handleSelectAllClick}
                  inputProps={{ 'aria-label': 'select all desserts' }}
                />
              </TableCell>
              <TableCell>ID</TableCell>
              <TableCell>Placa</TableCell>
              <TableCell>Tipo de Infracción</TableCell>
              <TableCell>Fecha/Hora</TableCell>
              <TableCell>Cámara ID</TableCell>
              <TableCell>Confianza</TableCell>
              <TableCell>Comentarios de Revisión</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {infractions.map((infraction) => {
              const isItemSelected = isSelected(infraction.id);

              return (
                <TableRow
                  hover
                  onClick={(event) => handleClick(event, infraction.id)}
                  role="checkbox"
                  aria-checked={isItemSelected}
                  tabIndex={-1}
                  key={infraction.id}
                  selected={isItemSelected}
                  sx={{ cursor: 'pointer' }}
                >
                  <TableCell padding="checkbox">
                    <Checkbox
                      checked={isItemSelected}
                      inputProps={{ 'aria-labelledby': `infraction-checkbox-${infraction.id}` }}
                    />
                  </TableCell>
                  <TableCell>{infraction.id}</TableCell>
                  <TableCell>{infraction.plate_number}</TableCell>
                  <TableCell>{infraction.rule_name}</TableCell>
                  <TableCell>{new Date(infraction.timestamp).toLocaleString()}</TableCell>
                  <TableCell>{infraction.camera_id}</TableCell>
                  <TableCell>{`${(infraction.confidence * 100).toFixed(0)}%`}</TableCell>
                  <TableCell>{infraction.review_comments || 'N/A'}</TableCell>
                </TableRow>
              );
            })}
          </TableBody>
        </Table>
      </TableContainer>

      <Modal
        open={emailModalOpen}
        onClose={handleCloseEmailModal}
        aria-labelledby="email-modal-title"
        aria-describedby="email-modal-description"
      >
        <Box sx={{
          position: 'absolute',
          top: '50%',
          left: '50%',
          transform: 'translate(-50%, -50%)',
          width: { xs: '90%', md: 500 },
          bgcolor: 'background.paper',
          borderRadius: 2,
          boxShadow: 24,
          p: 4,
          maxHeight: '90vh',
          overflowY: 'auto',
        }}>
          <IconButton
            aria-label="close"
            onClick={handleCloseEmailModal}
            sx={{
              position: 'absolute',
              right: 8,
              top: 8,
              color: (theme) => theme.palette.grey[500],
            }}
          >
            <CloseIcon />
          </IconButton>
          <Typography id="email-modal-title" variant="h6" component="h2" sx={{ mb: 2 }}>
            Enviar Reporte por Correo Electrónico
          </Typography>

          {emailError && (
            <Alert severity="error" sx={{ my: 2 }}>
              Error: {emailError}
            </Alert>
          )}
          {emailSuccess && (
            <Alert severity="success" sx={{ my: 2 }}>
              Correo enviado exitosamente!
            </Alert>
          )}

          <TextField
            label="Destinatario"
            fullWidth
            margin="normal"
            value={emailRecipient}
            onChange={(e) => setEmailRecipient(e.target.value)}
            required
          />
          <TextField
            label="Asunto"
            fullWidth
            margin="normal"
            value={emailSubject}
            onChange={(e) => setEmailSubject(e.target.value)}
          />
          <TextField
            label="Cuerpo del Mensaje"
            multiline
            rows={4}
            fullWidth
            margin="normal"
            value={emailBody}
            onChange={(e) => setEmailBody(e.target.value)}
          />

          <Box sx={{ display: 'flex', justifyContent: 'flex-end', gap: 2, mt: 3 }}>
            <Button
              variant="contained"
              onClick={handleSendEmailConfirm}
              disabled={sendingEmail || !emailRecipient}
            >
              {sendingEmail ? <CircularProgress size={24} /> : 'Enviar'}
            </Button>
            <Button variant="outlined" onClick={handleCloseEmailModal} disabled={sendingEmail}>
              Cancelar
            </Button>
          </Box>
        </Box>
      </Modal>
    </Box>
  );
};

export default ReportPage;