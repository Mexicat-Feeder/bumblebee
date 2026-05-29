import { useEffect, useState } from 'react';
import { Link, useNavigate, useParams } from 'react-router-dom';
import Layout from '../components/Layout';
import { formatMoney, useCart } from '../context/CartContext';
import { MenuItem } from '../types';

export default function ItemDetailPage() {
  const { id } = useParams();
  const navigate = useNavigate();
  const { addItem } = useCart();
  const [item, setItem] = useState<MenuItem | null>(null);
  const [quantity, setQuantity] = useState(1);
  const [error, setError] = useState('');

  useEffect(() => {
    fetch(`/api/items/${id}`).then(async res => {
      if (!res.ok) throw new Error('Item not found');
      setItem(await res.json());
    }).catch(err => setError(err.message));
  }, [id]);

  if (error) return <Layout><div className='rounded-xl bg-red-100 p-4 text-red-700'>{error}</div></Layout>;
  if (!item) return <Layout><p>Loading...</p></Layout>;

  return (
    <Layout>
      <Link to='/' className='font-semibold text-orange-700'>← Back to menu</Link>
      <article className='mt-4 overflow-hidden rounded-3xl bg-white shadow'>
        <img src={item.photo_url} alt={item.name} className='h-72 w-full object-cover' />
        <div className='p-5'>
          <p className='text-sm font-bold text-orange-600'>{item.category_name}</p>
          <h1 className='mt-1 text-3xl font-black'>{item.name}</h1>
          <p className='mt-3 text-slate-600'>{item.description}</p>
          <p className='mt-4 text-2xl font-black text-orange-600'>{formatMoney(item.price)}</p>
          <div className='mt-6 flex items-center gap-3'>
            <button onClick={() => setQuantity(Math.max(1, quantity - 1))} className='h-11 w-11 rounded-full bg-orange-100 text-xl font-black'>−</button>
            <span className='w-10 text-center text-xl font-black'>{quantity}</span>
            <button onClick={() => setQuantity(quantity + 1)} className='h-11 w-11 rounded-full bg-orange-100 text-xl font-black'>+</button>
          </div>
          <button disabled={!item.available} onClick={() => { addItem(item, quantity); navigate('/cart'); }} className='mt-6 w-full rounded-xl bg-orange-600 px-4 py-3 font-bold text-white'>Add {quantity} to cart</button>
        </div>
      </article>
    </Layout>
  );
}
