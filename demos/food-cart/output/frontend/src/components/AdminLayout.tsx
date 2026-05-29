import { ReactNode } from 'react';
import { Link, Navigate } from 'react-router-dom';

export function isAdminAuthed() {
  return localStorage.getItem('foodcart.admin') === 'yes';
}

export function setAdminAuthed(value: boolean) {
  if (value) localStorage.setItem('foodcart.admin', 'yes');
  else localStorage.removeItem('foodcart.admin');
}

export default function AdminLayout({ children }: { children: ReactNode }) {
  if (!isAdminAuthed()) return <Navigate to='/admin/login' replace />;
  return (
    <div className='min-h-screen bg-slate-100 text-slate-900 md:flex'>
      <aside className='bg-slate-900 p-4 text-white md:min-h-screen md:w-56'>
        <h1 className='text-xl font-black text-orange-300'>Food Cart Admin</h1>
        <nav className='mt-6 flex gap-2 md:flex-col'>
          <Link className='rounded-lg px-3 py-2 font-bold hover:bg-slate-800' to='/admin/orders'>Orders</Link>
          <Link className='rounded-lg px-3 py-2 font-bold hover:bg-slate-800' to='/admin/menu'>Menu</Link>
          <Link className='rounded-lg px-3 py-2 font-bold hover:bg-slate-800' to='/admin/settings'>Settings</Link>
        </nav>
      </aside>
      <main className='flex-1 p-4 md:p-6'>{children}</main>
    </div>
  );
}
