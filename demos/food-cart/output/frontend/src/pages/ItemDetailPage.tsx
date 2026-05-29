import { useEffect, useState } from 'react';
import { Link, useParams } from 'react-router-dom';
import Header from '../components/Header';
import { useCart } from '../context/CartContext';
import { MenuItem, Settings } from '../types';

export default function ItemDetailPage() {
  const { itemId } = useParams();
  const { addItem } = useCart();
  const [item, setItem] = useState<MenuItem | null>(null);
  const [settings, setSettings] = useState<Settings | null>(null);
  const [quantity, setQuantity] = useState(1);
  const [error, setError] = useState('');

  useEffect(() => {
    fetch(`/api/menu-items/${itemId}`)
      .then((res) => {
        if (!res.ok) {
          throw new Error('not found');
        }
        return res.json();
      })
      .then(setItem)
      .catch(() => setError('Menu item not found.'));
    fetch('/api/settings').then((res) => res.json()).then(setSettings);
  }, [itemId]);

  return (
    <div>
      <Header title={settings?.cart_name || 'Food Cart'} subtitle={settings?.tagline || 'Fresh food made fast'} />
      <main style={{ maxWidth: 'var(--max-width)', margin: '0 auto', padding: 'var(--space-4)' }}>
        <Link to="/" style={{ color: 'var(--color-primary)', textDecoration: 'none' }}>← Back to menu</Link>
        {error ? <div style={{ marginTop: 'var(--space-4)', color: 'var(--color-danger)' }}>{error}</div> : null}
        {item ? (
          <div style={{ background: 'var(--bg-card)', borderRadius: 'var(--radius-lg)', overflow: 'hidden', marginTop: 'var(--space-4)', boxShadow: 'var(--shadow-md)' }}>
            <img src={item.photo_url} alt={item.name} style={{ width: '100%', height: '280px', objectFit: 'cover' }} />
            <div style={{ padding: 'var(--space-4)' }}>
              <h1 style={{ margin: '0 0 var(--space-2)' }}>{item.name}</h1>
              <div style={{ color: 'var(--color-text-secondary)', marginBottom: 'var(--space-2)' }}>{item.category_name}</div>
              <div style={{ fontWeight: 700, marginBottom: 'var(--space-3)' }}>${(item.price / 100).toFixed(2)}</div>
              <p style={{ color: 'var(--color-text)' }}>{item.description}</p>
              <div style={{ display: 'flex', gap: 'var(--space-3)', alignItems: 'center', marginTop: 'var(--space-4)' }}>
                <input
                  type="number"
                  min={1}
                  value={quantity}
                  onChange={(e) => setQuantity(Number(e.target.value) || 1)}
                  style={{ width: '80px', padding: 'var(--space-2)', borderRadius: 'var(--radius-md)', border: '1px solid var(--color-border)' }}
                />
                <button
                  disabled={settings ? !settings.is_open : false}
                  onClick={() => addItem(item, quantity)}
                  style={{ background: 'var(--color-primary)', color: 'var(--color-white)', border: 'none', borderRadius: 'var(--radius-md)', padding: 'var(--space-2) var(--space-4)', cursor: 'pointer' }}
                >
                  Add to Cart
                </button>
              </div>
            </div>
          </div>
        ) : null}
      </main>
    </div>
  );
}
