import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { CreateOrderInput } from '../types';
import '../styles/design-tokens.css';

export default function CheckoutPage() {
  const navigate = useNavigate();
  const [customerName, setCustomerName] = useState('');
  const [customerPhone, setCustomerPhone] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [orderNumber, setOrderNumber] = useState('');

  async function submitOrder() {
    setSubmitting(true);
    const payload: CreateOrderInput = { customer_name: customerName || null, customer_phone: customerPhone || null, items: [] };
    const res = await fetch('/api/orders', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(payload) });
    const data = await res.json();
    setOrderNumber(data.order_number);
    setSubmitting(false);
  }

  if (orderNumber) return <div style={{ padding: 16 }}><h1>Order confirmed</h1><p>Your order number is {orderNumber}</p><button onClick={() => navigate('/track')}>Track status</button></div>;

  return <div style={{ padding: 16 }}>
    <h1>Checkout</h1>
    <input value={customerName} onChange={e => setCustomerName(e.target.value)} placeholder="Name" />
    <input value={customerPhone} onChange={e => setCustomerPhone(e.target.value)} placeholder="Phone" />
    <button disabled={submitting} onClick={submitOrder}>{submitting ? 'Submitting...' : 'Submit order'}</button>
  </div>;
}
