import { useEffect, useMemo, useState } from 'react';
import { Link } from 'react-router-dom';
import { Category, MenuItem } from '../types';

export default function HomePage() {
  const [categories, setCategories] = useState<Category[]>([]);
  const [items, setItems] = useState<MenuItem[]>([]);
  const [selectedCategoryId, setSelectedCategoryId] = useState<number | null>(null);
  const [cart, setCart] = useState<Record<number, number>>({});

  useEffect(() => {
    Promise.all([fetch('/api/categories').then(r => r.json()), fetch('/api/menu-items').then(r => r.json())])
      .then(([cats, menu]) => {
        setCategories(cats);
        setItems(menu);
        setSelectedCategoryId(cats[0]?.id ?? null);
      });
  }, []);

  const visibleItems = useMemo(() => items.filter(i => selectedCategoryId === null || i.category_id === selectedCategoryId), [items, selectedCategoryId]);
  const cartCount = Object.values(cart).reduce((a, b) => a + b, 0);

  return <div style={{ padding: 16, fontFamily: 'system-ui', background: 'var(--bg-page)', minHeight: '100vh' }}>
    <h1 style={{ margin: 0 }}>Pop-Up Food Cart</h1>
    <div style={{ display: 'flex', gap: 8, overflowX: 'auto', margin: '16px 0' }}>
      {categories.map(c => <button key={c.id} onClick={() => setSelectedCategoryId(c.id)} style={{ padding: '8px 12px', borderRadius: 999, border: `1px solid var(--color-accent)`, background: selectedCategoryId === c.id ? 'var(--color-accent)' : 'var(--bg-card)' }}>{c.name}</button>)}
    </div>
    <div style={{ display: 'grid', gap: 12 }}>
      {visibleItems.map(item => <div key={item.id} style={{ background: 'var(--bg-card)', borderRadius: 16, padding: 12, boxShadow: '0 1px 6px rgba(0,0,0,0.08)' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', gap: 12 }}>
          <div>
            <div style={{ fontWeight: 700 }}>{item.name}</div>
            <div style={{ fontSize: 14, color: 'var(--color-text-secondary)' }}>{item.description}</div>
            <div style={{ marginTop: 8 }}>${item.price.toFixed(2)}</div>
          </div>
          <button onClick={() => setCart(prev => ({ ...prev, [item.id]: (prev[item.id] ?? 0) + 1 }))} style={{ alignSelf: 'center', padding: '8px 12px', borderRadius: 12, background: 'var(--color-accent)', color: 'var(--color-on-accent)', border: 0 }}>Add</button>
        </div>
      </div>)}
    </div>
    <div style={{ position: 'sticky', bottom: 16, marginTop: 16, background: 'var(--bg-dark)', color: 'var(--color-on-dark)', padding: 12, borderRadius: 16, display: 'flex', justifyContent: 'space-between' }}>
      <span>{cartCount} in cart</span>
      <Link to="/checkout" style={{ color: 'var(--color-on-dark)' }}>Checkout</Link>
    </div>
    <div style={{ marginTop: 12 }}><Link to="/track" style={{ color: 'var(--color-accent-dark)' }}>Track order</Link></div>
  </div>;
}
