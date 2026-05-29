import { Link } from 'react-router-dom';
import Header from '../components/Header';
import { useCart } from '../context/CartContext';
import './styles/design-tokens.css';

export default function CartPage() {
  const { items, updateQuantity, removeItem, clearCart, subtotal } = useCart();

  return (
    <div>
      <Header title="Food Cart" subtitle="Review your order" />
      <main style={{ maxWidth: 'var(--max-width)', margin: '0 auto', padding: 'var(--space-4)' }}>
        <h1 style={{ color: 'var(--color-text)' }}>Cart</h1>
        {items.length === 0 ? (
          <div>
            <p style={{ color: 'var(--color-text-secondary)' }}>Your cart is empty.</p>
            <Link to="/" style={{ color: 'var(--color-primary)' }}>Browse menu</Link>
          </div>
        ) : (
          <div style={{ display: 'grid', gap: 'var(--space-3)' }}>
            {items.map((entry) => (
              <div key={entry.item.id} style={{ background: 'var(--bg-card)', borderRadius: 'var(--radius-lg)', padding: 'var(--space-3)', display: 'flex', justifyContent: 'space-between', gap: 'var(--space-3)' }}>
                <div>
                  <div style={{ fontWeight: 700, color: 'var(--color-text)' }}>{entry.item.name}</div>
                  <div style={{ color: 'var(--color-text-secondary)' }}>${(entry.item.price / 100).toFixed(2)} each</div>
                </div>
                <div style={{ display: 'flex', gap: 'var(--space-2)', alignItems: 'center' }}>
                  <button onClick={() => updateQuantity(entry.item.id, entry.quantity - 1)} style={{ border: 'none', borderRadius: 'var(--radius-md)', padding: 'var(--space-2) var(--space-2)', background: 'var(--color-primary-light)' }}>-</button>
                  <span>{entry.quantity}</span>
                  <button onClick={() => updateQuantity(entry.item.id, entry.quantity + 1)} style={{ border: 'none', borderRadius: 'var(--radius-md)', padding: 'var(--space-2) var(--space-2)', background: 'var(--color-primary-light)' }}>+</button>
                  <button onClick={() => removeItem(entry.item.id)} style={{ border: 'none', borderRadius: 'var(--radius-md)', padding: 'var(--space-2) var(--space-2)', background: 'var(--color-danger-light)', color: 'var(--color-danger)' }}>Remove</button>
                </div>
              </div>
            ))}
            <div style={{ background: 'var(--bg-card)', borderRadius: 'var(--radius-lg)', padding: 'var(--space-4)' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 'var(--space-3)' }}>
                <strong style={{ color: 'var(--color-text)' }}>Subtotal</strong>
                <strong style={{ color: 'var(--color-text)' }}>${(subtotal / 100).toFixed(2)}</strong>
              </div>
              <div style={{ display: 'flex', gap: 'var(--space-3)' }}>
                <button onClick={clearCart} style={{ flex: 1, border: 'none', borderRadius: 'var(--radius-md)', padding: 'var(--space-3)', background: 'var(--color-neutral-light)' }}>Clear Cart</button>
                <Link to="/checkout" style={{ flex: 1, textAlign: 'center', textDecoration: 'none', borderRadius: 'var(--radius-md)', padding: 'var(--space-3)', background: 'var(--color-primary)', color: 'var(--color-white)' }}>Checkout</Link>
              </div>
            </div>
          </div>
        )}
      </main>
    </div>
  );
}
