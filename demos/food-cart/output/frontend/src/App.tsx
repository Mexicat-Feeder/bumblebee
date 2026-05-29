import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import HomePage from './pages/HomePage';
import CheckoutPage from './pages/CheckoutPage';
import TrackOrderPage from './pages/TrackOrderPage';
import AdminLoginPage from './pages/AdminLoginPage';
import AdminDashboardPage from './pages/AdminDashboardPage';
import AdminMenuPage from './pages/AdminMenuPage';
import AdminSettingsPage from './pages/AdminSettingsPage';
import AdminOrders from './pages/AdminOrders';
import AdminCategories from './pages/AdminCategories';
import AdminSalesSummary from './pages/AdminSalesSummary';
import OrderSubmit from './pages/OrderSubmit';
import OrderStatus from './pages/OrderStatus';

export default function App() {
  return <BrowserRouter>
    <Routes>
      <Route path="/" element={<HomePage />} />
      <Route path="/checkout" element={<CheckoutPage />} />
      <Route path="/track" element={<TrackOrderPage />} />
      <Route path="/order-submit" element={<OrderSubmit />} />
      <Route path="/order-status" element={<OrderStatus />} />
      <Route path="/admin/login" element={<AdminLoginPage />} />
      <Route path="/admin" element={<AdminDashboardPage />} />
      <Route path="/admin/menu" element={<AdminMenuPage />} />
      <Route path="/admin/settings" element={<AdminSettingsPage />} />
      <Route path="/admin/orders" element={<AdminOrders />} />
      <Route path="/admin/categories" element={<AdminCategories />} />
      <Route path="/admin/sales-summary" element={<AdminSalesSummary />} />
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  </BrowserRouter>;
}
