import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import Header from '../components/Header';
import { useCart } from '../context/CartContext';
import { CreateOrderInput, Order } from '../types';

export default function CheckoutPage() {
  const navigate = useNavigate();
  const { items, subtotal, clearCart } = useCart();
  const [customerName, setCustomerName] = useState('');
  const [error, setError] = useState('');
  const [submitting, setSubmitting] = useState(false);

  const placeOrder = async () => {
    if (!customerName.trim()) {
      setError('Please enter your name.');
      return;
    }
    if (items.length === 0) {
      setError('Your cart is empty.');
      return;
    }
    setSubmitting(true);
    setError('');
    const payload: CreateOrderInput = {
      customer_name: customerName.trim(),
      items: items.map((entry) => ({ item_id: entry.item.id, quantity: entry.quantity })),
    };
    try {
      const res = await fetch('/api/orders', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });
      const data: Order | { detail: string } = await res.json();
      if (!res.ok) {
        setError('detail' in data ? data.detail : 'Unable to place order.');
        setSubmitting(false);
        return;
      }
      clearCart();
      navigate(`/confirmation/${data.id}`);
    } catch {
      setError('Unable to place order. Please try again.');
      setSubmitting(false);
    }
  };

  return (
    <div>
      <Header title="Food Cart" subtitle="Checkout" />
      <main style={{ maxWidth: 'var(--max-width)', margin: '0 auto', padding: 'var(--space-4)' }}>
        <h1 style={{ color: 'var(--color-text)' }}>Checkout</h1>
        {items.length === 0 ? <div style={{ color: 'var(--color-text)' }}>Your cart is empty.</div> : null}
        <div style={{ background: 'var(--bg-card)', borderRadius: 'var(--radius-lg)', padding: 'var(--space-4)', marginTop: 'var(--space-3)' }}>
          <label style={{ display: 'block', marginBottom: 'var(--space-2)', fontWeight: 700, color: 'var(--color-text)' }}>Name for pickup</label>
          <input
            value={customerName}
            onChange={(e) => setCustomerName(e.target.value)}
            placeholder="Your name"
            style={{ width: '100%', padding: 'var(--space-3)', borderRadius: 'var(--radius-md)', border: `1px solid var(--color-border)`, marginBottom: 'var(--space-4)', fontSize: 'var(--font-size-base)' }}
          />
          <div style={{ marginBottom: 'var(--space-3)', fontWeight: 700, color: 'var(--color-text)' }}>Order Summary</div>
          <div style={{ display: 'grid', gap: 'var(--space-2)', marginBottom: 'var(--space-3)' }}>
            {items.map((entry) => (
              <div key={entry.item.id} style={{ display: 'flex', justifyContent: 'space-between', color: 'var(--color-text)' }}>
                <span>{entry.item.name} x {entry.quantity}</span>
                <span>${((entry.item.price * entry.quantity) / 100).toFixed(2)}</span>
              </div>
            ))}
          </div>
          <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 'var(--space-4)', color: 'var(--color-text)' }}>
            <strong>Total</strong>
            <strong>${(subtotal / 100).toFixed(2)}</strong>
          </div>
          {error ? <div style={{ color: 'var(--color-error)', marginBottom: 'var(--space-3)' }}>{error}</div> : null}
          <button
            disabled={submitting || items.length === 0}
            onClick={placeOrder}
            style={{ width: '100%', background: 'var(--color-primary)', color: 'var(--color-white)', border: 'none', borderRadius: 'var(--radius-md)', padding: 'var(--space-3)', cursor: submitting || items.length === 0 ? 'not-allowed' : 'pointer', opacity: submitting || items.length === 0 ? 0.7 : 1, fontSize: 'var(--font-size-base)' }}
          >
            {submitting ? 'Placing Order...' : 'Place Order'}
          </button>
        </div>
      </main>
    </div>
  );
}
