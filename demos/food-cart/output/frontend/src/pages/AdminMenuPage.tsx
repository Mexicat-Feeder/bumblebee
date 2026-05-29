import { FormEvent, useEffect, useState } from 'react';
import AdminLayout from '../components/AdminLayout';
import { formatMoney } from '../context/CartContext';
import { Category, MenuItem } from '../types';

const blank = { name: '', description: '', price: 0, category_id: 1, photo_url: '', available: true, sort_order: 0 };

export default function AdminMenuPage() {
  const [items, setItems] = useState<MenuItem[]>([]);
  const [categories, setCategories] = useState<Category[]>([]);
  const [form, setForm] = useState(blank);
  const [editing, setEditing] = useState<number | null>(null);

  function load() {
    fetch('/api/items').then(r => r.json()).then(setItems);
    fetch('/api/categories').then(r => r.json()).then(c => {
      setCategories(c);
      if (c[0]) setForm(f => ({ ...f, category_id: c[0].id }));
    });
  }

  useEffect(load, []);

  async function submit(e: FormEvent) {
    e.preventDefault();
    const res = await fetch(editing ? `/api/items/${editing}` : '/api/items', {
      method: editing ? 'PUT' : 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(form),
    });
    await res.json();
    setForm(blank);
    setEditing(null);
    load();
  }

  function edit(item: MenuItem) {
    setEditing(item.id);
    setForm({
      name: item.name,
      description: item.description,
      price: item.price,
      category_id: item.category_id,
      photo_url: item.photo_url,
      available: item.available,
      sort_order: item.sort_order,
    });
  }

  async function remove(id: number) {
    await fetch(`/api/items/${id}`, { method: 'DELETE' });
    load();
  }

  async function toggle(id: number) {
    await fetch(`/api/items/${id}/availability`, { method: 'PATCH' });
    load();
  }

  return (
    <AdminLayout>
      <h1 className='mb-5 text-3xl font-black'>Menu Manager</h1>
      <form onSubmit={submit} className='mb-6 grid gap-3 rounded-2xl bg-white p-4 shadow-sm md:grid-cols-2'>
        <input
          required
          value={form.name}
          onChange={e => setForm({ ...form, name: e.target.value })}
          placeholder='Name'
          className='rounded-xl border px-3 py-2'
        />
        <input
          required
          type='number'
          value={form.price}
          onChange={e => setForm({ ...form, price: Number(e.target.value) })}
          placeholder='Price cents'
          className='rounded-xl border px-3 py-2'
        />
        <select
          value={form.category_id}
          onChange={e => setForm({ ...form, category_id: Number(e.target.value) })}
          className='rounded-xl border px-3 py-2'
        >
          {categories.map(c => (
            <option key={c.id} value={c.id}>
              {c.name}
            </option>
          ))}
        </select>
        <input
          value={form.photo_url}
          onChange={e => setForm({ ...form, photo_url: e.target.value })}
          placeholder='Photo URL'
          className='rounded-xl border px-3 py-2'
        />
        <textarea
          required
          value={form.description}
          onChange={e => setForm({ ...form, description: e.target.value })}
          placeholder='Description'
          className='rounded-xl border px-3 py-2 md:col-span-2'
        />
        <label className='flex items-center gap-2 font-bold'>
          <input
            type='checkbox'
            checked={form.available}
            onChange={e => setForm({ ...form, available: e.target.checked })}
          />{' '}
          Available
        </label>
        <button className='rounded-xl bg-orange-600 px-4 py-2 font-bold text-white'>
          {editing ? 'Update item' : 'Add item'}
        </button>
      </form>
      <div className='space-y-3'>
        {items.map(item => (
          <div key={item.id} className='flex flex-wrap items-center gap-3 rounded-2xl bg-white p-4 shadow-sm'>
            <img src={item.photo_url} className='h-16 w-16 rounded-xl object-cover' />
            <div className='flex-1'>
              <h2 className='font-black'>{item.name}</h2>
              <p className='text-sm text-slate-500'>
                {item.category_name} · {formatMoney(item.price)}
              </p>
            </div>
            <button onClick={() => toggle(item.id)} className='rounded-xl bg-yellow-100 px-3 py-2 font-bold'>
              {item.available ? 'Available' : 'Sold out'}
            </button>
            <button onClick={() => edit(item)} className='rounded-xl bg-slate-200 px-3 py-2 font-bold'>
              Edit
            </button>
            <button onClick={() => remove(item.id)} className='rounded-xl bg-red-600 px-3 py-2 font-bold text-white'>
              Delete
            </button>
          </div>
        ))}
      </div>
    </AdminLayout>
  );
}
