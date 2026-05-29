import { useEffect, useState } from 'react';
import { Category, MenuItem } from '../types';
import '../styles/design-tokens.css';

export default function AdminMenuPage() {
  const [categories, setCategories] = useState<Category[]>([]);
  const [items, setItems] = useState<MenuItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Form state for adding/editing
  const [showForm, setShowForm] = useState(false);
  const [editingItem, setEditingItem] = useState<MenuItem | null>(null);
  const [formName, setFormName] = useState('');
  const [formDescription, setFormDescription] = useState('');
  const [formPrice, setFormPrice] = useState('');
  const [formCategoryId, setFormCategoryId] = useState<number | ''>('');
  const [formSortOrder, setFormSortOrder] = useState('');
  const [formIsAvailable, setFormIsAvailable] = useState(true);
  const [formPhotoUrl, setFormPhotoUrl] = useState('');

  const [showCategoryForm, setShowCategoryForm] = useState(false);
  const [categoryName, setCategoryName] = useState('');
  const [categorySortOrder, setCategorySortOrder] = useState('');

  useEffect(() => {
    Promise.all([
      fetch('/api/categories').then(r => r.json()),
      fetch('/api/menu-items').then(r => r.json()),
    ])
      .then(([cats, itms]) => {
        setCategories(cats);
        setItems(itms);
        setLoading(false);
      })
      .catch(() => {
        setError('Failed to load data');
        setLoading(false);
      });
  }, []);

  const resetForm = () => {
    setEditingItem(null);
    setFormName('');
    setFormDescription('');
    setFormPrice('');
    setFormCategoryId('');
    setFormSortOrder('');
    setFormIsAvailable(true);
    setFormPhotoUrl('');
    setShowForm(false);
  };

  const openAddForm = () => {
    resetForm();
    setShowForm(true);
  };

  const openEditForm = (item: MenuItem) => {
    setEditingItem(item);
    setFormName(item.name);
    setFormDescription(item.description);
    setFormPrice(String(item.price));
    setFormCategoryId(item.category_id);
    setFormSortOrder(String(item.sort_order));
    setFormIsAvailable(item.is_available);
    setFormPhotoUrl(item.photo_url || '');
    setShowForm(true);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    const payload = {
      name: formName,
      description: formDescription,
      price: parseFloat(formPrice),
      category_id: Number(formCategoryId),
      photo_url: formPhotoUrl || null,
      is_available: formIsAvailable,
      sort_order: Number(formSortOrder),
    };

    try {
      if (editingItem) {
        const res = await fetch(`/api/menu-items/${editingItem.id}`, {
          method: 'PUT',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(payload),
        });
        if (!res.ok) throw new Error('Failed to update item');
        const updated = await res.json();
        setItems(prev => prev.map(i => (i.id === updated.id ? updated : i)));
      } else {
        const res = await fetch('/api/menu-items', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(payload),
        });
        if (!res.ok) throw new Error('Failed to create item');
        const created = await res.json();
        setItems(prev => [...prev, created]);
      }
      resetForm();
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'An error occurred');
    }
  };

  const handleDelete = async (id: number) => {
    if (!confirm('Are you sure you want to delete this menu item?')) return;
    try {
      const res = await fetch(`/api/menu-items/${id}`, { method: 'DELETE' });
      if (!res.ok) throw new Error('Failed to delete item');
      setItems(prev => prev.filter(i => i.id !== id));
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'An error occurred');
    }
  };

  const handleToggleAvailability = async (item: MenuItem) => {
    const newAvailability = !item.is_available;
    try {
      const res = await fetch(`/api/menu-items/${item.id}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ ...item, is_available: newAvailability }),
      });
      if (!res.ok) throw new Error('Failed to update availability');
      const updated = await res.json();
      setItems(prev => prev.map(i => (i.id === updated.id ? updated : i)));
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'An error occurred');
    }
  };

  const handleCategorySubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    const payload = {
      name: categoryName,
      sort_order: Number(categorySortOrder),
    };

    try {
      const res = await fetch('/api/categories', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });
      if (!res.ok) throw new Error('Failed to create category');
      const created = await res.json();
      setCategories(prev => [...prev, created]);
      setCategoryName('');
      setCategorySortOrder('');
      setShowCategoryForm(false);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'An error occurred');
    }
  };

  const handleDeleteCategory = async (id: number) => {
    if (!confirm('Are you sure you want to delete this category?')) return;
    try {
      const res = await fetch(`/api/categories/${id}`, { method: 'DELETE' });
      if (!res.ok) throw new Error('Failed to delete category');
      setCategories(prev => prev.filter(c => c.id !== id));
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'An error occurred');
    }
  };

  if (loading) {
    return (
      <div style={{ padding: 16, textAlign: 'center' }}>
        <p>Loading...</p>
      </div>
    );
  }

  // Group items by category
  const groupedItems = categories.map(cat => ({
    category: cat,
    items: items.filter(i => i.category_id === cat.id),
  }));

  return (
    <div style={{ padding: 16, maxWidth: 1200, margin: '0 auto' }}>
      <h1 style={{ marginBottom: 16 }}>Menu Management</h1>

      {error && (
        <div
          style={{
            background: 'var(--bg-error, #fee)',
            color: 'var(--text-error, #c00)',
            padding: 12,
            borderRadius: 8,
            marginBottom: 16,
          }}
        >
          {error}
        </div>
      )}

      {/* Categories Section */}
      <section style={{ marginBottom: 32 }}>
        <div
          style={{
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            marginBottom: 12,
          }}
        >
          <h2 style={{ margin: 0 }}>Categories</h2>
          <button
            onClick={() => setShowCategoryForm(!showCategoryForm)}
            style={{
              background: 'var(--bg-primary, #4a90d9)',
              color: 'var(--text-inverse, #fff)',
              border: 'none',
              padding: '8px 16px',
              borderRadius: 6,
              cursor: 'pointer',
            }}
          >
            {showCategoryForm ? 'Cancel' : '+ Add Category'}
          </button>
        </div>

        {showCategoryForm && (
          <form
            onSubmit={handleCategorySubmit}
            style={{
              background: 'var(--bg-card, #fff)',
              padding: 16,
              borderRadius: 8,
              marginBottom: 12,
              border: '1px solid var(--border-color, #ddd)',
            }}
          >
            <div style={{ display: 'flex', gap: 12, flexWrap: 'wrap' }}>
              <div>
                <label style={{ display: 'block', marginBottom: 4, fontWeight: 500 }}>
                  Name
                </label>
                <input
                  type="text"
                  value={categoryName}
                  onChange={e => setCategoryName(e.target.value)}
                  required
                  style={{
                    padding: '8px 12px',
                    borderRadius: 6,
                    border: '1px solid var(--border-color, #ddd)',
                    minWidth: 200,
                  }}
                />
              </div>
              <div>
                <label style={{ display: 'block', marginBottom: 4, fontWeight: 500 }}>
                  Sort Order
                </label>
                <input
                  type="number"
                  value={categorySortOrder}
                  onChange={e => setCategorySortOrder(e.target.value)}
                  required
                  min={0}
                  style={{
                    padding: '8px 12px',
                    borderRadius: 6,
                    border: '1px solid var(--border-color, #ddd)',
                    width: 80,
                  }}
                />
              </div>
              <div style={{ display: 'flex', alignItems: 'flex-end' }}>
                <button
                  type="submit"
                  style={{
                    background: 'var(--bg-primary, #4a90d9)',
                    color: 'var(--text-inverse, #fff)',
                    border: 'none',
                    padding: '8px 16px',
                    borderRadius: 6,
                    cursor: 'pointer',
                  }}
                >
                  Save
                </button>
              </div>
            </div>
          </form>
        )}

        <div
          style={{
            display: 'flex',
            flexWrap: 'wrap',
            gap: 8,
          }}
        >
          {categories.map(cat => (
            <div
              key={cat.id}
              style={{
                background: 'var(--bg-card, #fff)',
                padding: '8px 16px',
                borderRadius: 8,
                border: '1px solid var(--border-color, #ddd)',
                display: 'flex',
                alignItems: 'center',
                gap: 8,
              }}
            >
              <span>{cat.name}</span>
              <span style={{ color: 'var(--text-muted, #888)', fontSize: 12 }}>
                (#{cat.sort_order})
              </span>
              <button
                onClick={() => handleDeleteCategory(cat.id)}
                style={{
                  background: 'none',
                  border: 'none',
                  color: 'var(--text-error, #c00)',
                  cursor: 'pointer',
                  fontSize: 14,
                  padding: 0,
                }}
                title="Delete category"
              >
                ✕
              </button>
            </div>
          ))}
          {categories.length === 0 && (
            <p style={{ color: 'var(--text-muted, #888)' }}>No categories yet.</p>
          )}
        </div>
      </section>

      {/* Menu Items Section */}
      <section>
        <div
          style={{
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            marginBottom: 12,
          }}
        >
          <h2 style={{ margin: 0 }}>Menu Items</h2>
          <button
            onClick={openAddForm}
            style={{
              background: 'var(--bg-primary, #4a90d9)',
              color: 'var(--text-inverse, #fff)',
              border: 'none',
              padding: '8px 16px',
              borderRadius: 6,
              cursor: 'pointer',
            }}
          >
            + Add Menu Item
          </button>
        </div>

        {/* Add/Edit Form */}
        {showForm && (
          <form
            onSubmit={handleSubmit}
            style={{
              background: 'var(--bg-card, #fff)',
              padding: 16,
              borderRadius: 8,
              marginBottom: 16,
              border: '1px solid var(--border-color, #ddd)',
            }}
          >
            <h3 style={{ marginTop: 0 }}>
              {editingItem ? 'Edit Menu Item' : 'Add Menu Item'}
            </h3>
            <div
              style={{
                display: 'grid',
                gridTemplateColumns: 'repeat(auto-fill, minmax(200px, 1fr))',
                gap: 12,
              }}
            >
              <div>
                <label style={{ display: 'block', marginBottom: 4, fontWeight: 500 }}>
                  Name *
                </label>
                <input
                  type="text"
                  value={formName}
                  onChange={e => setFormName(e.target.value)}
                  required
                  style={{
                    width: '100%',
                    padding: '8px 12px',
                    borderRadius: 6,
                    border: '1px solid var(--border-color, #ddd)',
                    boxSizing: 'border-box',
                  }}
                />
              </div>
              <div>
                <label style={{ display: 'block', marginBottom: 4, fontWeight: 500 }}>
                  Description
                </label>
                <input
                  type="text"
                  value={formDescription}
                  onChange={e => setFormDescription(e.target.value)}
                  style={{
                    width: '100%',
                    padding: '8px 12px',
                    borderRadius: 6,
                    border: '1px solid var(--border-color, #ddd)',
                    boxSizing: 'border-box',
                  }}
                />
              </div>
              <div>
                <label style={{ display: 'block', marginBottom: 4, fontWeight: 500 }}>
                  Price *
                </label>
                <input
                  type="number"
                  value={formPrice}
                  onChange={e => setFormPrice(e.target.value)}
                  required
                  min="0"
                  step="0.01"
                  style={{
                    width: '100%',
                    padding: '8px 12px',
                    borderRadius: 6,
                    border: '1px solid var(--border-color, #ddd)',
                    boxSizing: 'border-box',
                  }}
                />
              </div>
              <div>
                <label style={{ display: 'block', marginBottom: 4, fontWeight: 500 }}>
                  Category *
                </label>
                <select
                  value={formCategoryId}
                  onChange={e => setFormCategoryId(Number(e.target.value) || '')}
                  required
                  style={{
                    width: '100%',
                    padding: '8px 12px',
                    borderRadius: 6,
                    border: '1px solid var(--border-color, #ddd)',
                    boxSizing: 'border-box',
                  }}
                >
                  <option value="">Select category...</option>
                  {categories.map(cat => (
                    <option key={cat.id} value={cat.id}>
                      {cat.name}
                    </option>
                  ))}
                </select>
              </div>
              <div>
                <label style={{ display: 'block', marginBottom: 4, fontWeight: 500 }}>
                  Sort Order
                </label>
                <input
                  type="number"
                  value={formSortOrder}
                  onChange={e => setFormSortOrder(e.target.value)}
                  required
                  min={0}
                  style={{
                    width: '100%',
                    padding: '8px 12px',
                    borderRadius: 6,
                    border: '1px solid var(--border-color, #ddd)',
                    boxSizing: 'border-box',
                  }}
                />
              </div>
              <div>
                <label style={{ display: 'block', marginBottom: 4, fontWeight: 500 }}>
                  Photo URL
                </label>
                <input
                  type="text"
                  value={formPhotoUrl}
                  onChange={e => setFormPhotoUrl(e.target.value)}
                  placeholder="https://..."
                  style={{
                    width: '100%',
                    padding: '8px 12px',
                    borderRadius: 6,
                    border: '1px solid var(--border-color, #ddd)',
                    boxSizing: 'border-box',
                  }}
                />
              </div>
              <div
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  paddingTop: 24,
                }}
              >
                <label style={{ display: 'flex', alignItems: 'center', gap: 8, cursor: 'pointer' }}>
                  <input
                    type="checkbox"
                    checked={formIsAvailable}
                    onChange={e => setFormIsAvailable(e.target.checked)}
                  />
                  <span>Available</span>
                </label>
              </div>
            </div>
            <div style={{ marginTop: 12, display: 'flex', gap: 8 }}>
              <button
                type="submit"
                style={{
                  background: 'var(--bg-primary, #4a90d9)',
                  color: 'var(--text-inverse, #fff)',
                  border: 'none',
                  padding: '8px 16px',
                  borderRadius: 6,
                  cursor: 'pointer',
                }}
              >
                {editingItem ? 'Update' : 'Create'}
              </button>
              <button
                type="button"
                onClick={resetForm}
                style={{
                  background: 'var(--bg-secondary, #eee)',
                  color: 'var(--text-primary, #333)',
                  border: '1px solid var(--border-color, #ddd)',
                  padding: '8px 16px',
                  borderRadius: 6,
                  cursor: 'pointer',
                }}
              >
                Cancel
              </button>
            </div>
          </form>
        )}

        {/* Grouped Items */}
        {groupedItems.map(({ category, items: catItems }) => (
          <div key={category.id} style={{ marginBottom: 24 }}>
            <h3 style={{ marginBottom: 8, color: 'var(--text-primary, #333)' }}>
              {category.name}
            </h3>
            {catItems.length === 0 ? (
              <p style={{ color: 'var(--text-muted, #888)', margin: 0 }}>
                No items in this category.
              </p>
            ) : (
              <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                {catItems.map(item => (
                  <div
                    key={item.id}
                    style={{
                      background: 'var(--bg-card, #fff)',
                      padding: 12,
                      borderRadius: 8,
                      border: `1px solid ${item.is_available ? 'var(--border-color, #ddd)' : 'var(--border-error, #f99)'}`,
                      display: 'flex',
                      justifyContent: 'space-between',
                      alignItems: 'center',
                      opacity: item.is_available ? 1 : 0.6,
                    }}
                  >
                    <div style={{ flex: 1 }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                        <strong>{item.name}</strong>
                        <span
                          style={{
                            fontSize: 12,
                            padding: '2px 8px',
                            borderRadius: 12,
                            background: item.is_available
                              ? 'var(--bg-success, #e6ffe6)'
                              : 'var(--bg-error, #fee)',
                            color: item.is_available
                              ? 'var(--text-success, #060)'
                              : 'var(--text-error, #c00)',
                          }}
                        >
                          {item.is_available ? 'Available' : 'Sold out'}
                        </span>
                      </div>
                      {item.description && (
                        <p style={{ margin: '4px 0 0', color: 'var(--text-muted, #888)', fontSize: 14 }}>
                          {item.description}
                        </p>
                      )}
                      <p style={{ margin: '4px 0 0', fontWeight: 500 }}>
                        ${item.price.toFixed(2)}
                      </p>
                    </div>
                    <div style={{ display: 'flex', gap: 8, marginLeft: 16 }}>
                      <button
                        onClick={() => handleToggleAvailability(item)}
                        style={{
                          background: item.is_available
                            ? 'var(--bg-warning, #fff3cd)'
                            : 'var(--bg-success, #d4edda)',
                          color: item.is_available
                            ? 'var(--text-warning, #856404)'
                            : 'var(--text-success, #155724)',
                          border: 'none',
                          padding: '6px 12px',
                          borderRadius: 6,
                          cursor: 'pointer',
                          fontSize: 13,
                        }}
                      >
                        {item.is_available ? 'Mark Sold Out' : 'Mark Available'}
                      </button>
                      <button
                        onClick={() => openEditForm(item)}
                        style={{
                          background: 'var(--bg-secondary, #eee)',
                          color: 'var(--text-primary, #333)',
                          border: '1px solid var(--border-color, #ddd)',
                          padding: '6px 12px',
                          borderRadius: 6,
                          cursor: 'pointer',
                          fontSize: 13,
                        }}
                      >
                        Edit
                      </button>
                      <button
                        onClick={() => handleDelete(item.id)}
                        style={{
                          background: 'var(--bg-error, #fee)',
                          color: 'var(--text-error, #c00)',
                          border: 'none',
                          padding: '6px 12px',
                          borderRadius: 6,
                          cursor: 'pointer',
                          fontSize: 13,
                        }}
                      >
                        Delete
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        ))}

        {items.length === 0 && categories.length === 0 && (
          <p style={{ color: 'var(--text-muted, #888)', textAlign: 'center' }}>
            No menu items or categories yet. Add a category to get started.
          </p>
        )}
      </section>
    </div>
  );
}
