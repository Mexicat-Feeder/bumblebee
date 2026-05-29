import { useEffect, useState } from 'react';
import { DailySummary, Order } from '../types';
import '../styles/design-tokens.css';

export default function AdminDashboardPage() {
  const [orders, setOrders] = useState<Order[]>([]);
  const [summary, setSummary] = useState<DailySummary | null>(null);

  useEffect(() => {
    fetch('/api/orders').then(r => r.json()).then(setOrders);
    fetch(`/api/reports/daily-summary?date=${new Date().toISOString().slice(0, 10)}`).then(r => r.json()).then(setSummary);
  }, []);

  return <div style={{ padding: 16 }}>
    <h1>Admin Dashboard</h1>
    {summary && <div>Today: {summary.order_count} orders, ${summary.total_sales.toFixed(2)}</div>}
    <div style={{ marginTop: 16 }}>
      {orders.map(order => <div key={order.id}>{order.order_number} — {order.status}</div>)}
    </div>
  </div>;
}
