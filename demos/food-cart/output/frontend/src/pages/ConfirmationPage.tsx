import { useEffect, useState } from 'react';
import { Link, useParams } from 'react-router-dom';
import Header from '../components/Header';
import { Order, Settings } from '../types';
import './styles/design-tokens.css';

export default function ConfirmationPage() {
  const { orderId } = useParams();
  const [order, setOrder] = useState<Order | null>(null);
  const [settings, setSettings] = useState<Settings | null>(null);
  const [error, setError] = useState('');

  useEffect(() => {
    fetch(`/api/orders/${orderId}`)
      .then((res) => {
        if (!res.ok) {
          throw new Error('not found');
        }
        return res.json();
      })
      .then(setOrder)
      .catch(() => setError('Order not found.'));
    fetch('/api/settings').then((res) => res.json()).then(setSettings);
  }, [orderId]);

  return (
    <div>
      <Header title={settings?.cart_name || 'Food Cart'} subtitle="Order received" />
      <main style={{ maxWidth: 'var(--max-width)', margin: '0 auto', padding: 'var(--space-4)' }}>
        {error ? <div style={{ color: 'var(--color-error)' }}>{error}</div> : null}
        {order ? (
          <div style={{ background: 'var(--bg-card)', borderRadius: 'var(--radius-lg)', padding: 'var(--space-5)' }}>
            <h1 style={{ marginTop: 0 }}>Thanks, {order.customer_name}!</h1>
            <div style={{ fontSize: 'var(--font-size-3xl)', fontWeight: 700, color: 'var(--color-primary)', marginBottom: 'var(--space-3)' }}>{order.order_number}</div>
            <div style={{ marginBottom: 'var(--space-3)' }}>We'll call your name when it's ready.</div>
            <div style={{ marginBottom: 'var(--space-3)' }}>Estimated wait: {settings?.estimated_wait_minutes ?? 10} minutes</div>
            <div style={{ marginBottom: 'var(--space-3)', fontWeight: 700 }}>Items</div>
            <div style={{ display: 'grid', gap: 'var(--space-2)', marginBottom: 'var(--space-4)' }}>
              {order.items.map((item) => (
                <div key={item.id} style={{ display: 'flex', justifyContent: 'space-between' }}>
                  <span>{item.item_name} x {item.quantity}</span>
                  <span>${((item.item_price * item.quantity) / 100).toFixed(2)}</span>
                </div>
              ))}
            </div>
            <Link to={`/status/${order.id}`} style={{ display: 'inline-block', textDecoration: 'none', background: 'var(--color-primary)', color: 'var(--color-white)', borderRadius: 'var(--radius-md)', padding: 'var(--space-3) var(--space-4)' }}>
              Track Order Status
            </Link>
          </div>
        ) : null}
      </main>
    </div>
  );
}
