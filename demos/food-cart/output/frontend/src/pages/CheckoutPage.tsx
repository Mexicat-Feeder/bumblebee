import { FormEvent, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import Layout from '../components/Layout';
import { formatMoney, useCart } from '../context/CartContext';
import { Order } from '../types';

export default function CheckoutPage() {
  const { lines, subtotal, clearCart } = useCart();
  const [customerName, setCustomerName] = useState('');
  const [error, setError] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const navigate = useNavigate();

  async function submit(e: FormEvent) {
    e.preventDefault();
    setError(''); setSubmitting(true);
    try {
      const res = await fetch('/api/orders', {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ customer_name: customerName, items: lines.map(line => ({ item_id: line.item.id, quantity: line.quantity })) })
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || 'Could not place order');
      const order = data as Order;
      clearCart();
      navigate(`/confirmation/${order.id}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Network error');
    } finally {
      setSubmitting(false);
    }
  }

  if (lines.length === 0) return <Layout><div className='rounded-2xl bg-white p-6 text-center'><p>Your cart is empty.</p><Link to='/' className='mt-4 inline-block text-orange-700 font-bold'>Back to menu</Link></div></Layout>;

  return (
    <Layout>
      <h1 className='mb-5 text-3xl font-black'>Checkout</h1>
      <form onSubmit={submit} className='space-y-5 rounded-2xl bg-white p-5 shadow-sm'>
        {error && <div className='rounded-xl bg-red-100 p-3 text-red-700'>{error}</div>}
        <label className='block'>
          <span className='font-bold'>Name for pickup</span>
          <input value={customerName} onChange={e => setCustomerName(e.target.value)} required className='mt-2 w-full rounded-xl border border-orange-200 px-4 py-3' placeholder='Your name' />
        </label>
        <div className='space-y-2'>
          {lines.map(line => <div key={line.item.id} className='flex justify-between text-sm'><span>{line.quantity} × {line.item.name}</span><span>{formatMoney(line.item.price * line.quantity)}</span></div>)}
        </div>
        <div className='flex justify-between border-t pt-4 text-xl font-black'><span>Total</span><span>{formatMoney(subtotal)}</span></div>
        <button disabled={submitting} className='w-full rounded-xl bg-orange-600 px-4 py-3 font-bold text-white'>{submitting ? 'Placing order...' : 'Place order'}</button>
      </form>
    </Layout>
  );
}
