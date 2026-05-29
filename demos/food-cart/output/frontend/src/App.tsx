import { BrowserRouter, Route, Routes } from 'react-router-dom';
import { CartProvider } from './context/CartContext';
import AdminItemFormPage from './pages/AdminItemFormPage';
import AdminLoginPage from './pages/AdminLoginPage';
import AdminMenuPage from './pages/AdminMenuPage';
import AdminOrdersPage from './pages/AdminOrdersPage';
import AdminSettingsPage from './pages/AdminSettingsPage';
import CartPage from './pages/CartPage';
import CheckoutPage from './pages/CheckoutPage';
import ConfirmationPage from './pages/ConfirmationPage';
import ItemDetailPage from './pages/ItemDetailPage';
import MenuPage from './pages/MenuPage';
import OrderStatusPage from './pages/OrderStatusPage';

export default function App() {
  return (
    <BrowserRouter>
      <CartProvider>
      <Routes>
        <Route path="/" element={<MenuPage />} />
        <Route path="/items/:itemId" element={<ItemDetailPage />} />
        <Route path="/cart" element={<CartPage />} />
        <Route path="/checkout" element={<CheckoutPage />} />
        <Route path="/confirmation/:orderId" element={<ConfirmationPage />} />
        <Route path="/status/:orderId" element={<OrderStatusPage />} />
        <Route path="/admin" element={<AdminLoginPage />} />
        <Route path="/admin/orders" element={<AdminOrdersPage />} />
        <Route path="/admin/menu" element={<AdminMenuPage />} />
        <Route path="/admin/menu/:itemId" element={<AdminItemFormPage />} />
        <Route path="/admin/settings" element={<AdminSettingsPage />} />
      </Routes>
      </CartProvider>
    </BrowserRouter>
  );
}
