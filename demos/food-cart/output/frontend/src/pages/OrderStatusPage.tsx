import { useEffect, useState } from 'react';
import { useParams } from 'react-router-dom';
import Header from '../components/Header';
import { Order } from '../types';
import './design-tokens.css';

const LABELS: Record<string, string> = {
  received: 'Received',
  in_progress: 'In Progress',
  ready: 'Ready',
  picked_up: 'Picked Up',
};

export default function OrderStatusPage() {
  const { orderId } = useParams();
  const [order, setOrder] = useState<Order | null>(null);
  const [error, setError] = useState('');

  useEffect(() => {
    let active = true;
    const load = () => {
      fetch(`/api/orders/${orderId}`)
        .then((res) => {
          if (!res.ok) {
            throw new Error('not found');
          }
          return res.json();
        })
        .then((data) => {
          if (active) {
            setOrder(data);
            setError('');
          }
        })
        .catch(() => {
          if (active) {
            setError('Order not found.');
          }
        });
    };
    load();
    const interval = window.setInterval(load, 5000);
    return () => {
      active = false;
      window.clearInterval(interval);
    };
  }, [orderId]);

  return (
    <div>
      <Header title="Food Cart" subtitle="Order status" />
      <main style={{ maxWidth: 'var(--max-width)', margin: '0 auto', padding: 'var(--space-4)' }}>
        {error ? <div style={{ color: 'var(--color-danger)' }}>{error}</div> : null}
        {order ? (
          <div style={{ background: 'var(--bg-card)', borderRadius: 'var(--radius-lg)', padding: 'var(--space-5)' }}>
            <div style={{ fontSize: 'var(--font-size-3xl)', fontWeight: 700, color: 'var(--color-primary)', marginBottom: 'var(--space-2)' }}>{order.order_number}</div>
            <div style={{ marginBottom: 'var(--space-4)' }}>Pickup for {order.customer_name}</div>
            <div style={{ display: 'grid', gap: 'var(--space-3)' }}>
              {['received', 'in_progress', 'ready'].map((status) => {
                const active = order.status === status || (status === 'received' && ['in_progress', 'ready', 'picked_up'].includes(order.status)) || (status === 'in_progress' && ['ready', 'picked_up'].includes(order.status));
                return (
                  <div key={status} style={{ padding: 'var(--space-3)', borderRadius: 'var(--radius-md)', background: active ? 'var(--color-primary-light)' : 'var(--bg-muted)', color: 'var(--text-primary)' }}>
                    {LABELS[status]}
                  </div>
                );
              })}
            </div>
          </div>
        ) : null}
      </main>
    </div>
  );
}
