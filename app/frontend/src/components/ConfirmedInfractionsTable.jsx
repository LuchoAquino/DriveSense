import React, { useState, useMemo } from 'react';
import { Typography, Table, TableBody, TableCell, TableContainer, TableHead, TableRow, Box, Chip, TextField, FormControl, InputLabel, Select, MenuItem, TableSortLabel, useTheme } from '@mui/material';
import { visuallyHidden } from '@mui/utils';

const ConfirmedInfractionsTable = ({ data }) => {
  const theme = useTheme();
  const [searchText, setSearchText] = useState('');
  const [filterDecision, setFilterDecision] = useState('ALL');
  const [order, setOrder] = useState('desc');
  const [orderBy, setOrderBy] = useState('timestamp');

  const handleRequestSort = (property) => {
    const isAsc = orderBy === property && order === 'asc';
    setOrder(isAsc ? 'desc' : 'asc');
    setOrderBy(property);
  };

  const sortedAndFilteredData = useMemo(() => {
    let filtered = data.filter((infraction) => {
      const matchesSearchText =
        infraction.plate_number?.toLowerCase().includes(searchText.toLowerCase()) ||
        infraction.rule_name?.toLowerCase().includes(searchText.toLowerCase()) ||
        infraction.id?.toString().includes(searchText);

      const matchesDecision =
        filterDecision === 'ALL' || infraction.review_decision === filterDecision;

      return matchesSearchText && matchesDecision;
    });

    return filtered.sort((a, b) => {
      const isAsc = order === 'asc';
      let comparison = 0;

      if (orderBy === 'timestamp' || orderBy === 'reviewed_at') {
        const dateA = new Date(a[orderBy] || 0);
        const dateB = new Date(b[orderBy] || 0);
        comparison = dateA - dateB;
      } else if (orderBy === 'confidence') {
        comparison = (a[orderBy] || 0) - (b[orderBy] || 0);
      } else {
        if ((a[orderBy] || '') < (b[orderBy] || '')) comparison = -1;
        else if ((a[orderBy] || '') > (b[orderBy] || '')) comparison = 1;
      }

      return isAsc ? comparison : -comparison;
    });
  }, [data, searchText, filterDecision, order, orderBy]);

  const formatTimestamp = (timestamp) => {
    if (!timestamp) return '-';
    const date = new Date(timestamp);
    return date.toLocaleString('en-US', { 
      month: 'short', day: '2-digit', 
      hour: '2-digit', minute: '2-digit', second: '2-digit', hour12: false
    });
  };

  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', width: '100%'}}>
      <Box sx={{ p: 2, borderBottom: `1px solid ${theme.palette.divider}`, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <Typography variant="h6" sx={{ color: theme.palette.text.primary, fontWeight: 600 }}>
          Event Log
        </Typography>
        
        <Box sx={{ display: 'flex', gap: 2 }}>
          <TextField
            placeholder="Search plate or rule..."
            variant="outlined"
            size="small"
            value={searchText}
            onChange={(e) => setSearchText(e.target.value)}
            sx={{ width: '250px' }}
          />
          <FormControl size="small" sx={{ width: '150px' }}>
            <InputLabel>Status</InputLabel>
            <Select value={filterDecision} label="Status" onChange={(e) => setFilterDecision(e.target.value)}>
              <MenuItem value="ALL">All</MenuItem>
              <MenuItem value="CONFIRMED">Confirmed</MenuItem>
              <MenuItem value="REJECTED">Rejected</MenuItem>
            </Select>
          </FormControl>
        </Box>
      </Box>

      <TableContainer sx={{ maxHeight: 400 }}>
        <Table stickyHeader size="small">
          <TableHead>
            <TableRow>
              {['ID', 'RULE', 'PLATE', 'TIMESTAMP', 'CONFIDENCE', 'STATUS'].map(headCell => {
                const keyMap = {
                  'ID': 'id', 'RULE': 'rule_name', 'PLATE': 'plate_number',
                  'TIMESTAMP': 'timestamp', 'CONFIDENCE': 'confidence', 'STATUS': 'review_decision'
                };
                const sortKey = keyMap[headCell];
                return (
                  <TableCell key={headCell} sortDirection={orderBy === sortKey ? order : false}>
                    <TableSortLabel
                      active={orderBy === sortKey}
                      direction={orderBy === sortKey ? order : 'asc'}
                      onClick={() => handleRequestSort(sortKey)}
                    >
                      {headCell}
                      {orderBy === sortKey ? (
                        <Box component="span" sx={visuallyHidden}>
                          {order === 'desc' ? 'sorted descending' : 'sorted ascending'}
                        </Box>
                      ) : null}
                    </TableSortLabel>
                  </TableCell>
                );
              })}
            </TableRow>
          </TableHead>
          <TableBody>
            {sortedAndFilteredData.length === 0 ? (
              <TableRow>
                <TableCell colSpan={6} align="center" sx={{ py: 3, color: theme.palette.text.secondary }}>
                  No records found.
                </TableCell>
              </TableRow>
            ) : (
              sortedAndFilteredData.map((inf) => (
                <TableRow key={inf.id} hover>
                  <TableCell sx={{ color: theme.palette.text.secondary }}>#{inf.id}</TableCell>
                  <TableCell>{inf.rule_name}</TableCell>
                  <TableCell sx={{ fontFamily: '"JetBrains Mono", monospace', fontWeight: 600, fontSize: '0.9rem' }}>
                    {inf.plate_number}
                  </TableCell>
                  <TableCell sx={{ fontFamily: '"JetBrains Mono", monospace', fontSize: '0.8rem', color: theme.palette.text.secondary }}>
                    {formatTimestamp(inf.timestamp)}
                  </TableCell>
                  <TableCell>{`${(inf.confidence * 100).toFixed(0)}%`}</TableCell>
                  <TableCell>
                    <Chip 
                      label={inf.review_decision || 'PENDING'} 
                      size="small"
                      sx={{ 
                        borderRadius: '4px',
                        fontSize: '0.75rem',
                        fontWeight: 600,
                        backgroundColor: inf.review_decision === 'CONFIRMED' ? 'rgba(16, 185, 129, 0.1)' : 'rgba(239, 68, 68, 0.1)',
                        color: inf.review_decision === 'CONFIRMED' ? theme.palette.success.main : theme.palette.error.main,
                      }}
                    />
                  </TableCell>
                </TableRow>
              ))
            )}
          </TableBody>
        </Table>
      </TableContainer>
    </Box>
  );
};

export default ConfirmedInfractionsTable;