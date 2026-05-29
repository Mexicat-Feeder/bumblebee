import { useEffect, useState } from 'react';
import { Order } from '../types';

export default function TrackOrderPage() {
  const [orderId, setOrderId] = useState('');
  const [order, setOrder] = useState<Order | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!orderId) return;
    const timer = setInterval(async () => {
      try {
        const res = await fetch(`/api/orders/${orderId}`);
        if (res.ok) {
          const data = await res.json();
          setOrder(data);
          setError(null);
        } else {
          setError('Order not found');
          setOrder(null);
        }
      } catch {
        setError('Failed to fetch order');
      }
    }, 3000);
    return () => clearInterval(timer);
  }, [orderId]);

  return (
    <div style={{ padding: 16, background: 'var(--bg-page)', minHeight: '100vh' }}>
      <h1 style={{ color: 'var(--text-primary)' }}>Track Order</h1>
      <div style={{ display: 'flex', gap: 8, marginBottom: 16 }}>
        <input
          value={orderId}
          onChange={e => setOrderId(e.target.value)}
          placeholder="Order ID"
          style={{
            padding: '8px 12px',
            border: '1px solid var(--border-color)',
            borderRadius: 4,
            fontSize: 16,
            background: 'var(--bg-input)',
            color: 'var(--text-primary)',
          }}
        />
      </div>
      {error && (
        <div style={{ color: 'var(--text-error)', padding: 8, background: 'var(--bg-error)', borderRadius: 4 }}>
          {error}
        </div>
      )}
      {order && (
        <div
          style={{
            marginTop: 16,
            padding: 16,
            background: 'var(--bg-card)',
            borderRadius: 8,
            border: `1px solid var(--border-color)`,
          }}
        >
          <div style={{ color: 'var(--text-primary)', fontWeight: 'bold', marginBottom: 8 }}>
            Order #{order.order_number}
          </div>
          <div style={{ color: 'var(--text-secondary)' }}>
            Status: <span style={{ fontWeight: 'bold', color: 'var(--text-primary)' }}>{order.status}</span>
          </div>
          {order.customer_name && (
            <div style={{ color: 'var(--text-secondary)', marginTop: 4 }}>
              Customer: {order.customer_name}
            </div>
          )}
          {order.items.length > 0 && (
            <div style={{ marginTop: 12 }}>
              <div style={{ fontWeight: 'bold', color: 'var(--text-primary)', marginBottom: 4 }}>Items:</div>
              {order.items.map(item => (
                <div key={item.id} style={{ color: 'var(--text-secondary)', fontSize: 14 }}>
                  {item.quantity}x {item.menu_item_name} — ${item.line_total.toFixed(2)}
                </div>
              ))}
              <div style={{ marginTop: 8, fontWeight: 'bold', color: 'var(--text-primary)' }}>
                Subtotal: ${order.subtotal.toFixed(2)}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
