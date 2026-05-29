import { FormEvent, useEffect, useState } from 'react';
import AdminLayout, { setAdminAuthed } from '../components/AdminLayout';
import { Settings } from '../types';

export default function AdminSettingsPage() {
  const [settings, setSettings] = useState<Settings | null>(null);
  const [saved, setSaved] = useState(false);

  useEffect(() => { fetch('/api/settings').then(res => res.json()).then(setSettings); }, []);

  async function submit(e: FormEvent) {
    e.preventDefault();
    if (!settings) return;
    const res = await fetch('/api/settings', { method: 'PUT', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(settings) });
    setSettings(await res.json()); setSaved(true); setTimeout(() => setSaved(false), 1500);
  }

  if (!settings) return <AdminLayout><p>Loading...</p></AdminLayout>;

  return (
    <AdminLayout>
      <h1 className='mb-5 text-3xl font-black'>Settings</h1>
      <form onSubmit={submit} className='max-w-xl space-y-4 rounded-2xl bg-white p-5 shadow-sm'>
        {saved && <div className='rounded-xl bg-green-100 p-3 font-bold text-green-700'>Saved</div>}
        <label className='block'><span className='font-bold'>Cart name</span><input value={settings.cart_name} onChange={e => setSettings({ ...settings, cart_name: e.target.value })} className='mt-1 w-full rounded-xl border px-3 py-2' /></label>
        <label className='block'><span className='font-bold'>Tagline</span><input value={settings.tagline} onChange={e => setSettings({ ...settings, tagline: e.target.value })} className='mt-1 w-full rounded-xl border px-3 py-2' /></label>
        <label className='block'><span className='font-bold'>Estimated wait minutes</span><input type='number' value={settings.estimated_wait_minutes} onChange={e => setSettings({ ...settings, estimated_wait_minutes: Number(e.target.value) })} className='mt-1 w-full rounded-xl border px-3 py-2' /></label>
        <label className='block'><span className='font-bold'>Admin PIN</span><input value={settings.admin_pin} onChange={e => setSettings({ ...settings, admin_pin: e.target.value })} className='mt-1 w-full rounded-xl border px-3 py-2' /></label>
        <label className='flex items-center gap-3 font-bold'><input type='checkbox' checked={settings.is_open} onChange={e => setSettings({ ...settings, is_open: e.target.checked })} /> Ordering is open</label>
        <button className='w-full rounded-xl bg-orange-600 px-4 py-3 font-bold text-white'>Save settings</button>
        <button type='button' onClick={() => { setAdminAuthed(false); location.href = '/admin/login'; }} className='w-full rounded-xl bg-slate-200 px-4 py-3 font-bold'>Log out</button>
      </form>
    </AdminLayout>
  );
}
