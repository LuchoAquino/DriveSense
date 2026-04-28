
import React from 'react';
import { Routes, Route } from 'react-router-dom';
import MainLayout from './layouts/MainLayout';
import DashboardPage from './pages/DashboardPage';
import ReviewPage from './pages/ReviewPage';
import ReportPage from './pages/ReportPage';

const NotFoundPage = () => <div><h2>404 - Página no encontrada</h2></div>;

function App() {
  return (
    <Routes>
      <Route path="/" element={<MainLayout />}>
        <Route index element={<DashboardPage />} />
        <Route path="revision" element={<ReviewPage />} />
        <Route path="reportes" element={<ReportPage />} />
        <Route path="*" element={<NotFoundPage />} />
      </Route>
    </Routes>
  );
}

export default App;
