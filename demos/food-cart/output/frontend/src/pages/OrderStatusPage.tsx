import { useCallback, useEffect, useState } from 'react';
import { useParams } from 'react-router-dom';
import Layout from '../components/Layout';
import { useWebSocket } from '../hooks/useWebSocket';
import { Order, OrderStatus } from '../types';

const steps: OrderStatus[] = ['received', 'in_progress', 'ready'];
const labels: Record<OrderStatus, string> = { received: 'Received', in_progress: 'In Progress', ready: 'Ready', picked_up: 'Picked Up' };

export default function OrderStatusPage() {
  const { id } = useParams();
  const [order, setOrder] = useState<Order | null>(null);
  const [error, setError] = useState('');

  useEffect(() => {
    fetch(`/api/orders/${id}`).then(async res => {
      if (!res.ok) throw new Error('Order not found');
      setOrder(await res.json());
    }).catch(err => setError(err.message));
  }, [id]);

  const onMessage = useCallback((data: any) => {
    if (data.type === 'order_updated') setOrder(data.order);
  }, []);
  useWebSocket(`/api/ws/orders/${id}`, onMessage);

  if (error) return <Layout><div className='rounded-xl bg-red-100 p-4 text-red-700'>{error}</div></Layout>;
  if (!order) return <Layout><p>Loading status...</p></Layout>;
  const activeIndex = order.status === 'picked_up' ? 2 : steps.indexOf(order.status);

  return (
    <Layout>
      <div className='rounded-3xl bg-white p-6 shadow-sm'>
        <h1 className='text-3xl font-black'>Order {order.order_number}</h1>
        <p className='mt-1 text-slate-600'>Hi {order.customer_name}, your order is {labels[order.status]}.</p>
        <div className='mt-8 space-y-5'>
          {steps.map((step, idx) => (
            <div key={step} className='flex items-center gap-4'>
              <div className={`flex h-10 w-10 items-center justify-center rounded-full font-black ${idx <= activeIndex ? 'bg-orange-600 text-white' : 'bg-slate-200'}`}>{idx + 1}</div>
              <div><p className='font-black'>{labels[step]}</p><p className='text-sm text-slate-500'>{step === 'ready' ? 'Come grab it at the cart.' : 'We are on it.'}</p></div>
            </div>
          ))}
        </div>
        {order.status === 'ready' && <div className='mt-6 rounded-xl bg-green-100 p-4 font-black text-green-800'>Your order is ready!</div>}
      </div>
    </Layout>
  );
}
