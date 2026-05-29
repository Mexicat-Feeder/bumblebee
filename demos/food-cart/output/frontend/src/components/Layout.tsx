import { Link } from 'react-router-dom';
import { ReactNode } from 'react';
import { useCart } from '../context/CartContext';

export default function Layout({ children }: { children: ReactNode }) {
  const { itemCount } = useCart();
  return (
    <div className='min-h-screen bg-orange-50 text-slate-900'>
      <header className='sticky top-0 z-10 border-b border-orange-200 bg-white/95 backdrop-blur'>
        <div className='mx-auto flex max-w-5xl items-center justify-between px-4 py-3'>
          <Link to='/' className='text-xl font-black text-orange-600'>Food Cart</Link>
          <nav className='flex items-center gap-4 text-sm font-semibold'>
            <Link to='/' className='text-slate-700'>Menu</Link>
            <Link to='/cart' className='rounded-full bg-orange-600 px-4 py-2 text-white'>Cart ({itemCount})</Link>
          </nav>
        </div>
      </header>
      <main className='mx-auto max-w-5xl px-4 py-6'>{children}</main>
      <footer className='px-4 py-8 text-center text-sm text-slate-500'>Pay at the cart. We will call your name when ready.</footer>
    </div>
  );
}
