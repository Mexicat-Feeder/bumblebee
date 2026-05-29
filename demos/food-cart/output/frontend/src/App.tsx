import React, { useState } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';

import MenuBrowse from './pages/MenuBrowse';
import OrderSubmit from './pages/OrderSubmit';
import OrderStatus from './pages/OrderStatus';
import AdminLogin from './pages/AdminLogin';
import AdminPanel from './pages/AdminPanel';
import AdminCategories from './pages/AdminCategories';
import AdminOrders from './pages/AdminOrders';
import AdminSettings from './pages/AdminSettings';
import AdminSalesSummary from './pages/AdminSalesSummary';

/**
 * Main App component with routing.
 * Handles public and admin routes with simple auth state.
 */

export default function App() {
  // Simple auth state for admin panel
  const [isAdminAuthenticated, setIsAdminAuthenticated] = useState(false);

  // Handler for successful admin login
  const handleLoginSuccess = () => {
    setIsAdminAuthenticated(true);
  };

  // Handler for admin logout
  const handleLogout = () => {
    setIsAdminAuthenticated(false);
  };

  return (
    <Router>
      <Routes>
        {/* Public routes */}
        <Route path="/" element={<MenuBrowse />} />
        <Route path="/order" element={<OrderSubmit />} />
        <Route path="/order-status" element={<OrderStatus />} />

        {/* Admin login route */}
        <Route
          path="/admin/login"
          element={<AdminLogin onLoginSuccess={handleLoginSuccess} />}
        />

        {/* Admin protected routes */}
        <Route
          path="/admin"
          element={
            isAdminAuthenticated ? (
              <AdminPanel onLogout={handleLogout} />
            ) : (
              <Navigate to="/admin/login" replace />
            )
          }
        />

        <Route
          path="/admin/categories"
          element={
            isAdminAuthenticated ? <AdminCategories /> : <Navigate to="/admin/login" replace />
          }
        />

        <Route
          path="/admin/orders"
          element={
            isAdminAuthenticated ? <AdminOrders /> : <Navigate to="/admin/login" replace />
          }
        />

        <Route
          path="/admin/settings"
          element={
            isAdminAuthenticated ? <AdminSettings /> : <Navigate to="/admin/login" replace />
          }
        />

        <Route
          path="/admin/sales-summary"
          element={
            isAdminAuthenticated ? <AdminSalesSummary /> : <Navigate to="/admin/login" replace />
          }
        />

        {/* Fallback route */}
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </Router>
  );
}
