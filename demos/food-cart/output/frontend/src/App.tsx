import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom';
import { CartProvider } from './context/CartContext';
import MenuPage from './pages/MenuPage';
import ItemDetailPage from './pages/ItemDetailPage';
import CartPage from './pages/CartPage';
import CheckoutPage from './pages/CheckoutPage';
import ConfirmationPage from './pages/ConfirmationPage';
import OrderStatusPage from './pages/OrderStatusPage';
import AdminLoginPage from './pages/AdminLoginPage';
import AdminOrdersPage from './pages/AdminOrdersPage';
import AdminMenuPage from './pages/AdminMenuPage';
import AdminSettingsPage from './pages/AdminSettingsPage';

export default function App() {
  return (
    <CartProvider>
      <BrowserRouter>
        <Routes>
          <Route path='/' element={<MenuPage />} />
          <Route path='/items/:id' element={<ItemDetailPage />} />
          <Route path='/cart' element={<CartPage />} />
          <Route path='/checkout' element={<CheckoutPage />} />
          <Route path='/confirmation/:id' element={<ConfirmationPage />} />
          <Route path='/status/:id' element={<OrderStatusPage />} />
          <Route path='/admin/login' element={<AdminLoginPage />} />
          <Route path='/admin' element={<Navigate to='/admin/orders' replace />} />
          <Route path='/admin/orders' element={<AdminOrdersPage />} />
          <Route path='/admin/menu' element={<AdminMenuPage />} />
          <Route path='/admin/settings' element={<AdminSettingsPage />} />
          <Route path='*' element={<Navigate to='/' replace />} />
        </Routes>
      </BrowserRouter>
    </CartProvider>
  );
}
