import { Link } from 'react-router-dom';
import Layout from '../components/Layout';
import { formatMoney, useCart } from '../context/CartContext';

export default function CartPage() {
  const { lines, setQuantity, removeItem, clearCart, subtotal } = useCart();
  return (
    <Layout>
      <h1 className='mb-5 text-3xl font-black'>Your Cart</h1>
      {lines.length === 0 ? (
        <div className='rounded-2xl bg-white p-6 text-center shadow-sm'>
          <p className='text-slate-600'>Your cart is empty.</p>
          <Link to='/' className='mt-4 inline-block rounded-xl bg-orange-600 px-5 py-3 font-bold text-white'>Browse menu</Link>
        </div>
      ) : (
        <div className='space-y-4'>
          {lines.map(line => (
            <div key={line.item.id} className='flex gap-4 rounded-2xl bg-white p-4 shadow-sm'>
              <img src={line.item.photo_url} alt={line.item.name} className='h-20 w-20 rounded-xl object-cover' />
              <div className='flex-1'>
                <div className='flex justify-between gap-3'><h2 className='font-black'>{line.item.name}</h2><span className='font-bold'>{formatMoney(line.item.price * line.quantity)}</span></div>
                <div className='mt-3 flex items-center gap-3'>
                  <button onClick={() => setQuantity(line.item.id, line.quantity - 1)} className='rounded-lg bg-orange-100 px-3 py-1 font-black'>−</button>
                  <span className='font-bold'>{line.quantity}</span>
                  <button onClick={() => setQuantity(line.item.id, line.quantity + 1)} className='rounded-lg bg-orange-100 px-3 py-1 font-black'>+</button>
                  <button onClick={() => removeItem(line.item.id)} className='ml-auto text-sm font-bold text-red-600'>Remove</button>
                </div>
              </div>
            </div>
          ))}
          <div className='rounded-2xl bg-white p-5 shadow-sm'>
            <div className='flex justify-between text-xl font-black'><span>Subtotal</span><span>{formatMoney(subtotal)}</span></div>
            <div className='mt-5 flex gap-3'>
              <button onClick={clearCart} className='flex-1 rounded-xl bg-slate-200 px-4 py-3 font-bold'>Clear</button>
              <Link to='/checkout' className='flex-1 rounded-xl bg-orange-600 px-4 py-3 text-center font-bold text-white'>Checkout</Link>
            </div>
          </div>
        </div>
      )}
    </Layout>
  );
}
