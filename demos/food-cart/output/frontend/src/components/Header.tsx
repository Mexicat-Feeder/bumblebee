import { Link } from 'react-router-dom';
import { useCart } from '../context/CartContext';

interface HeaderProps {
  title: string;
  subtitle?: string;
}

export default function Header({ title, subtitle }: HeaderProps) {
  const { itemCount } = useCart();

  return (
    <header style={{ background: 'var(--color-primary)', color: 'var(--color-white)', padding: 'var(--space-4)' }}>
      <div style={{ maxWidth: 'var(--max-width)', margin: '0 auto', display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: 'var(--space-3)' }}>
        <div>
          <Link to="/" style={{ color: 'var(--color-white)', textDecoration: 'none', fontSize: 'var(--font-size-2xl)', fontWeight: 700 }}>
            {title}
          </Link>
          {subtitle ? <div style={{ fontSize: 'var(--font-size-sm)', opacity: 0.9 }}>{subtitle}</div> : null}
        </div>
        <nav style={{ display: 'flex', gap: 'var(--space-3)', alignItems: 'center' }}>
          <Link to="/" style={{ color: 'var(--color-white)', textDecoration: 'none' }}>Menu</Link>
          <Link to="/cart" style={{ color: 'var(--color-white)', textDecoration: 'none' }}>
            Cart ({itemCount})
          </Link>
          <Link to="/admin" style={{ color: 'var(--color-white)', textDecoration: 'none' }}>Admin</Link>
        </nav>
      </div>
    </header>
  );
}
