import { useCallback, useEffect, useState } from 'react';
import AdminLayout from '../components/AdminLayout';
import { formatMoney } from '../context/CartContext';
import { useWebSocket } from '../hooks/useWebSocket';
import { Order, OrderStatus } from '../types';

const labels: Record<OrderStatus, string> = { received: 'Received', in_progress: 'In Progress', ready: 'Ready', picked_up: 'Picked Up' };

export default function AdminOrdersPage() {
  const [orders, setOrders] = useState<Order[]>([]);
  const [expanded, setExpanded] = useState<number | null>(null);

  function load() { fetch('/api/orders').then(res => res.json()).then(setOrders); }
  useEffect(load, []);

  const onMessage = useCallback((data: any) => {
    if (data.order) setOrders(prev => [data.order, ...prev.filter(o => o.id !== data.order.id)].sort((a, b) => b.id - a.id));
  }, []);
  useWebSocket('/api/ws/orders', onMessage);

  async function setStatus(order: Order, status: OrderStatus) {
    const res = await fetch(`/api/orders/${order.id}/status`, { method: 'PATCH', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ status }) });
    const updated = await res.json();
    setOrders(prev => prev.map(o => o.id === updated.id ? updated : o));
  }

  return (
    <AdminLayout>
      <div className='mb-5 flex items-center justify-between'><h1 className='text-3xl font-black'>Orders</h1><button onClick={load} className='rounded-xl bg-white px-4 py-2 font-bold'>Refresh</button></div>
      <div className='space-y-3'>
        {orders.map(order => (
          <article key={order.id} className='rounded-2xl bg-white p-4 shadow-sm'>
            <button onClick={() => setExpanded(expanded === order.id ? null : order.id)} className='flex w-full items-center justify-between text-left'>
              <div><h2 className='text-xl font-black'>{order.order_number} · {order.customer_name}</h2><p className='text-sm text-slate-500'>{new Date(order.created_at).toLocaleTimeString()}</p></div>
              <span className='rounded-full bg-orange-100 px-3 py-1 text-sm font-bold text-orange-700'>{labels[order.status]}</span>
            </button>
            {expanded === order.id && <div className='mt-4 border-t pt-4'>
              {order.items.map(item => <div key={item.id} className='flex justify-between'><span>{item.quantity} × {item.item_name}</span><span>{formatMoney(item.item_price * item.quantity)}</span></div>)}
              <div className='mt-3 flex justify-between font-black'><span>Total</span><span>{formatMoney(order.total)}</span></div>
              <div className='mt-4 flex flex-wrap gap-2'>
                <button onClick={() => setStatus(order, 'in_progress')} className='rounded-xl bg-yellow-400 px-4 py-2 font-bold'>In Progress</button>
                <button onClick={() => setStatus(order, 'ready')} className='rounded-xl bg-green-600 px-4 py-2 font-bold text-white'>Ready</button>
                <button onClick={() => setStatus(order, 'picked_up')} className='rounded-xl bg-slate-800 px-4 py-2 font-bold text-white'>Picked Up</button>
              </div>
            </div>}
          </article>
        ))}
        {orders.length === 0 && <div className='rounded-2xl bg-white p-6 text-center text-slate-500'>No orders yet.</div>}
      </div>
    </AdminLayout>
  );
}
