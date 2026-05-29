import { FormEvent, useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { setAdminAuthed } from '../components/AdminLayout';
import { Settings } from '../types';

export default function AdminLoginPage() {
  const [settings, setSettings] = useState<Settings | null>(null);
  const [pin, setPin] = useState('');
  const [error, setError] = useState('');
  const navigate = useNavigate();

  useEffect(() => { fetch('/api/settings').then(res => res.json()).then(setSettings); }, []);

  function submit(e: FormEvent) {
    e.preventDefault();
    if (pin === (settings?.admin_pin || '1234')) {
      setAdminAuthed(true);
      navigate('/admin/orders');
    } else {
      setError('Invalid PIN');
    }
  }

  return (
    <div className='flex min-h-screen items-center justify-center bg-orange-50 p-4'>
      <form onSubmit={submit} className='w-full max-w-sm rounded-3xl bg-white p-6 shadow'>
        <h1 className='text-3xl font-black'>Admin Login</h1>
        <p className='mt-2 text-slate-600'>Enter the operator PIN.</p>
        {error && <div className='mt-4 rounded-xl bg-red-100 p-3 text-red-700'>{error}</div>}
        <input value={pin} onChange={e => setPin(e.target.value)} className='mt-5 w-full rounded-xl border px-4 py-3 text-center text-2xl tracking-widest' placeholder='1234' />
        <button className='mt-4 w-full rounded-xl bg-orange-600 px-4 py-3 font-bold text-white'>Enter</button>
      </form>
    </div>
  );
}
