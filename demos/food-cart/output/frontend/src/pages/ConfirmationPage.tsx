import { useEffect, useState } from 'react';
import { Link, useParams } from 'react-router-dom';
import Layout from '../components/Layout';
import { formatMoney } from '../context/CartContext';
import { Order, Settings } from '../types';

export default function ConfirmationPage() {
  const { id } = useParams();
  const [order, setOrder] = useState<Order | null>(null);
  const [settings, setSettings] = useState<Settings | null>(null);
  const [error, setError] = useState('');

  useEffect(() => {
    Promise.all([fetch(`/api/orders/${id}`), fetch('/api/settings')]).then(async ([o, s]) => {
      if (!o.ok) throw new Error('Order not found');
      setOrder(await o.json());
      setSettings(await s.json());
    }).catch(err => setError(err.message));
  }, [id]);

  if (error) return <Layout><div className='rounded-xl bg-red-100 p-4 text-red-700'>{error}</div></Layout>;
  if (!order) return <Layout><p>Loading confirmation...</p></Layout>;

  return (
    <Layout>
      <div className='rounded-3xl bg-white p-6 text-center shadow-sm'>
        <div className='mx-auto mb-4 flex h-16 w-16 items-center justify-center rounded-full bg-green-100 text-3xl'>✓</div>
        <h1 className='text-3xl font-black'>Order {order.order_number}</h1>
        <p className='mt-2 text-slate-600'>Thanks, {order.customer_name}! We will call your name when it is ready.</p>
        <p className='mt-3 font-bold text-orange-600'>Estimated wait: {settings?.estimated_wait_minutes || 12} minutes</p>
        <div className='mt-6 space-y-2 text-left'>
          {order.items.map(item => (
            <div key={item.id} className='flex justify-between'>
              <span>{item.quantity} × {item.item_name}</span>
              <span>{formatMoney(item.item_price * item.quantity)}</span>
            </div>
          ))}
        </div>
        <div className='mt-4 flex justify-between border-t pt-4 text-xl font-black'>
          <span>Total</span>
          <span>{formatMoney(order.total)}</span>
        </div>
        <Link
          to={`/status/${order.id}`}
          className='mt-6 inline-block w-full rounded-xl bg-orange-600 px-4 py-3 font-bold text-white'
        >
          Track status
        </Link>
      </div>
    </Layout>
  );
}
