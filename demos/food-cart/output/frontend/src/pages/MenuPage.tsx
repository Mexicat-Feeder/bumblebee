import { useEffect, useMemo, useState } from 'react';
import { Link } from 'react-router-dom';
import Header from '../components/Header';
import { useCart } from '../context/CartContext';
import { Category, MenuItem, Settings } from '../types';

function formatPrice(price: number) {
  return `$${(price / 100).toFixed(2)}`;
}

export default function MenuPage() {
  const { addItem } = useCart();
  const [categories, setCategories] = useState<Category[]>([]);
  const [items, setItems] = useState<MenuItem[]>([]);
  const [settings, setSettings] = useState<Settings | null>(null);
  const [activeCategory, setActiveCategory] = useState<number | null>(null);
  const [error, setError] = useState('');

  useEffect(() => {
    Promise.all([
      fetch('/api/categories').then((res) => res.json()),
      fetch('/api/menu-items').then((res) => res.json()),
      fetch('/api/settings').then((res) => res.json()),
    ])
      .then(([categoryData, itemData, settingsData]) => {
        setCategories(categoryData);
        setItems(itemData);
        setSettings(settingsData);
        if (categoryData.length > 0) {
          setActiveCategory(categoryData[0].id);
        }
      })
      .catch(() => setError('Unable to load menu right now.'));
  }, []);

  const filteredItems = useMemo(() => {
    return items.filter((item) => item.available && (activeCategory === null || item.category_id === activeCategory));
  }, [items, activeCategory]);

  return (
    <div>
      <Header title={settings?.cart_name || 'Food Cart'} subtitle={settings?.tagline || 'Fresh food made fast'} />
      <main style={{ maxWidth: 'var(--max-width)', margin: '0 auto', padding: 'var(--space-4)' }}>
        {settings && !settings.is_open ? (
          <div style={{ background: 'var(--color-danger-bg)', color: 'var(--color-danger)', padding: 'var(--space-3)', borderRadius: 'var(--radius-md)', marginBottom: 'var(--space-4)' }}>
            We are currently closed. Please check back later.
          </div>
        ) : null}
        {error ? <div style={{ color: 'var(--color-danger)', marginBottom: 'var(--space-4)' }}>{error}</div> : null}
        <div style={{ display: 'flex', gap: 'var(--space-2)', overflowX: 'auto', marginBottom: 'var(--space-4)' }}>
          {categories.map((category) => (
            <button
              key={category.id}
              onClick={() => setActiveCategory(category.id)}
              style={{
                border: 'none',
                borderRadius: 'var(--radius-full)',
                padding: 'var(--space-2) var(--space-3)',
                background: activeCategory === category.id ? 'var(--color-primary)' : 'var(--color-primary-light)',
                color: activeCategory === category.id ? 'var(--color-white)' : 'var(--color-primary-dark)',
                cursor: 'pointer',
              }}
            >
              {category.name}
            </button>
          ))}
        </div>
        {filteredItems.length === 0 ? <div>No menu items available.</div> : null}
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(260px, 1fr))', gap: 'var(--space-4)' }}>
          {filteredItems.map((item) => (
            <div key={item.id} style={{ background: 'var(--bg-card)', borderRadius: 'var(--radius-lg)', overflow: 'hidden', boxShadow: 'var(--shadow-md)' }}>
              <Link to={`/items/${item.id}`} style={{ color: 'inherit', textDecoration: 'none' }}>
                <img src={item.photo_url} alt={item.name} style={{ width: '100%', height: '180px', objectFit: 'cover' }} />
                <div style={{ padding: 'var(--space-3)' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', gap: 'var(--space-2)' }}>
                    <strong>{item.name}</strong>
                    <span>{formatPrice(item.price)}</span>
                  </div>
                  <p style={{ margin: 'var(--space-2) 0', color: 'var(--color-text-secondary)' }}>{item.description}</p>
                </div>
              </Link>
              <div style={{ padding: '0 var(--space-3) var(--space-3)' }}>
                <button
                  disabled={settings ? !settings.is_open : false}
                  onClick={() => addItem(item, 1)}
                  style={{ width: '100%', background: 'var(--color-primary)', color: 'var(--color-white)', border: 'none', borderRadius: 'var(--radius-md)', padding: 'var(--space-2) var(--space-3)', cursor: 'pointer' }}
                >
                  Add to Cart
                </button>
              </div>
            </div>
          ))}
        </div>
      </main>
    </div>
  );
}
