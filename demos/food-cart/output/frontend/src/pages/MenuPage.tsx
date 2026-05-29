import { useEffect, useMemo, useState } from 'react';
import { Link } from 'react-router-dom';
import Layout from '../components/Layout';
import { useCart, formatMoney } from '../context/CartContext';
import { Category, MenuItem, Settings } from '../types';

export default function MenuPage() {
  const [items, setItems] = useState<MenuItem[]>([]);
  const [categories, setCategories] = useState<Category[]>([]);
  const [settings, setSettings] = useState<Settings | null>(null);
  const [active, setActive] = useState<number | 'all'>('all');
  const [error, setError] = useState('');
  const { addItem } = useCart();

  useEffect(() => {
    Promise.all([fetch('/api/items'), fetch('/api/categories'), fetch('/api/settings')])
      .then(async ([i, c, s]) => {
        if (!i.ok || !c.ok || !s.ok) throw new Error('Could not load menu');
        setItems(await i.json()); setCategories(await c.json()); setSettings(await s.json());
      })
      .catch(err => setError(err.message));
  }, []);

  const shown = useMemo(() => items.filter(item => active === 'all' || item.category_id === active), [items, active]);

  return (
    <Layout>
      <section className='mb-6 rounded-3xl bg-gradient-to-br from-orange-500 to-yellow-400 p-6 text-white shadow'>
        <p className='text-sm font-bold uppercase tracking-wide'>{settings?.is_open ? 'Open now' : 'Closed'}</p>
        <h1 className='mt-2 text-4xl font-black'>{settings?.cart_name || 'Food Cart'}</h1>
        <p className='mt-2 text-lg'>{settings?.tagline || 'Fresh food made fast'}</p>
        {settings && <p className='mt-3 text-sm font-semibold'>Estimated wait: {settings.estimated_wait_minutes} minutes</p>}
      </section>
      {error && <div className='mb-4 rounded-xl bg-red-100 p-3 text-red-700'>{error}</div>}
      {settings && !settings.is_open && <div className='mb-4 rounded-xl bg-yellow-100 p-4 font-semibold text-yellow-800'>We are closed right now. Please check back soon.</div>}
      <div className='mb-5 flex gap-2 overflow-x-auto pb-2'>
        <button onClick={() => setActive('all')} className={`rounded-full px-4 py-2 font-bold ${active === 'all' ? 'bg-orange-600 text-white' : 'bg-white'}`}>All</button>
        {categories.map(cat => <button key={cat.id} onClick={() => setActive(cat.id)} className={`rounded-full px-4 py-2 font-bold ${active === cat.id ? 'bg-orange-600 text-white' : 'bg-white'}`}>{cat.name}</button>)}
      </div>
      <div className='grid gap-4 sm:grid-cols-2 lg:grid-cols-3'>
        {shown.map(item => (
          <article key={item.id} className='overflow-hidden rounded-2xl bg-white shadow-sm'>
            <Link to={`/items/${item.id}`}><img src={item.photo_url} alt={item.name} className='h-44 w-full object-cover' /></Link>
            <div className='p-4'>
              <div className='flex items-start justify-between gap-3'><h2 className='text-lg font-black'>{item.name}</h2><span className='font-bold text-orange-600'>{formatMoney(item.price)}</span></div>
              <p className='mt-2 line-clamp-2 text-sm text-slate-600'>{item.description}</p>
              <button disabled={!settings?.is_open || !item.available} onClick={() => addItem(item, 1)} className='mt-4 w-full rounded-xl bg-orange-600 px-4 py-3 font-bold text-white'>{item.available ? 'Add to cart' : 'Sold out'}</button>
            </div>
          </article>
        ))}
      </div>
    </Layout>
  );
}
