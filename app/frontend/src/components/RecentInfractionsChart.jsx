import React from 'react';
import { ResponsiveContainer, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip } from 'recharts';
import { Typography, Box, useTheme } from '@mui/material';

const RecentInfractionsChart = ({ data }) => {
  const theme = useTheme();

  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', height: '100%', width: '100%'}}>
      <Typography variant="body2" sx={{ color: theme.palette.text.secondary, mb: 2, fontWeight: 600, textTransform: 'uppercase' }}>
        Last 7 Days
      </Typography>
      <ResponsiveContainer width="100%" height={250}>
        <BarChart
          data={data}
          margin={{ top: 10, right: 10, left: -20, bottom: 0 }}
        >
          <CartesianGrid strokeDasharray="3 3" stroke={theme.palette.divider} vertical={false} />
          <XAxis 
            dataKey="date" 
            stroke={theme.palette.text.secondary} 
            tick={{ fill: theme.palette.text.secondary, fontSize: 11 }} 
            axisLine={{ stroke: theme.palette.divider }}
            tickLine={false}
          />
          <YAxis 
            stroke={theme.palette.text.secondary}
            tick={{ fill: theme.palette.text.secondary, fontSize: 11 }} 
            axisLine={false}
            tickLine={false}
          />
          <Tooltip 
            cursor={{ fill: 'rgba(255, 255, 255, 0.05)' }}
            contentStyle={{ backgroundColor: theme.palette.background.paper, border: `1px solid ${theme.palette.divider}`, borderRadius: '4px', fontSize: '12px' }}
          />
          <Bar dataKey="count" fill={theme.palette.secondary.main} radius={[2, 2, 0, 0]} />
        </BarChart>
      </ResponsiveContainer>
    </Box>
  );
};

export default RecentInfractionsChart;
