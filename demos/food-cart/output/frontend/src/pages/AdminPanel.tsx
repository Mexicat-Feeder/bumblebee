/**
 * Admin Panel Main Page - Bumblebee Food Cart
 *
 * Displays navigation links to the various admin sections:
 * - Menu Management
 * - Order Management
 * - Settings
 */

import { useNavigate } from 'react-router-dom';

interface AdminPanelProps {
  onLogout: () => void;
}

export default function AdminPanel({ onLogout }: AdminPanelProps) {
  const navigate = useNavigate();

  const handleNavigate = (path: string) => {
    navigate(path);
  };

  const handleLogout = () => {
    onLogout();
    navigate('/admin/login');
  };

  const menuItems = [
    {
      title: 'Menu Management',
      description: 'Add, edit, and remove menu items, categories, and pricing.',
      path: '/admin/menu',
      icon: '🍽️',
    },
    {
      title: 'Order Management',
      description: 'View and manage incoming and completed orders.',
      path: '/admin/orders',
      icon: '📋',
    },
    {
      title: 'Settings',
      description: 'Configure store settings, PIN, and operational preferences.',
      path: '/admin/settings',
      icon: '⚙️',
    },
  ];

  return (
    <div style={{
      minHeight: '100vh',
      backgroundColor: 'var(--bg-page)',
      padding: '2rem 1rem',
    }}>
      <div style={{
        maxWidth: '800px',
        margin: '0 auto',
      }}>
        {/* Header */}
        <header style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          marginBottom: '2rem',
          paddingBottom: '1rem',
          borderBottom: '1px solid var(--border-color)',
        }}>
          <div>
            <h1 style={{
              fontSize: '1.75rem',
              fontWeight: '700',
              color: 'var(--text-primary)',
              margin: 0,
            }}>
              Admin Panel
            </h1>
            <p style={{
              fontSize: '0.875rem',
              color: 'var(--text-secondary)',
              margin: '0.25rem 0 0 0',
            }}>
              Manage your food cart operations
            </p>
          </div>
          <button
            onClick={handleLogout}
            style={{
              padding: '0.5rem 1rem',
              backgroundColor: 'var(--bg-card)',
              color: 'var(--text-primary)',
              border: '1px solid var(--border-color)',
              borderRadius: 'var(--radius-md)',
              cursor: 'pointer',
              fontSize: '0.875rem',
              fontWeight: '500',
              transition: 'background-color 0.2s, border-color 0.2s',
            }}
            onMouseEnter={(e) => {
              e.currentTarget.style.backgroundColor = 'var(--bg-hover)';
              e.currentTarget.style.borderColor = 'var(--border-hover)';
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.backgroundColor = 'var(--bg-card)';
              e.currentTarget.style.borderColor = 'var(--border-color)';
            }}
          >
            Logout
          </button>
        </header>

        {/* Navigation Cards */}
        <nav style={{
          display: 'flex',
          flexDirection: 'column',
          gap: '1rem',
        }}>
          {menuItems.map((item) => (
            <button
              key={item.path}
              onClick={() => handleNavigate(item.path)}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '1rem',
                padding: '1.25rem 1.5rem',
                backgroundColor: 'var(--bg-card)',
                border: '1px solid var(--border-color)',
                borderRadius: 'var(--radius-lg)',
                cursor: 'pointer',
                textAlign: 'left',
                width: '100%',
                transition: 'transform 0.15s, box-shadow 0.15s, border-color 0.15s',
              }}
              onMouseEnter={(e) => {
                e.currentTarget.style.transform = 'translateY(-2px)';
                e.currentTarget.style.boxShadow = '0 4px 12px rgba(0, 0, 0, 0.1)';
                e.currentTarget.style.borderColor = 'var(--border-hover)';
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.transform = 'translateY(0)';
                e.currentTarget.style.boxShadow = 'none';
                e.currentTarget.style.borderColor = 'var(--border-color)';
              }}
            >
              <span style={{
                fontSize: '2rem',
                lineHeight: 1,
              }}>
                {item.icon}
              </span>
              <div style={{
                flex: 1,
              }}>
                <h2 style={{
                  fontSize: '1.125rem',
                  fontWeight: '600',
                  color: 'var(--text-primary)',
                  margin: 0,
                }}>
                  {item.title}
                </h2>
                <p style={{
                  fontSize: '0.875rem',
                  color: 'var(--text-secondary)',
                  margin: '0.25rem 0 0 0',
                  lineHeight: 1.4,
                }}>
                  {item.description}
                </p>
              </div>
              <span style={{
                color: 'var(--text-muted)',
                fontSize: '1.25rem',
              }}>
                ›
              </span>
            </button>
          ))}
        </nav>

        {/* Footer info */}
        <footer style={{
          marginTop: '2rem',
          textAlign: 'center',
          fontSize: '0.75rem',
          color: 'var(--text-muted)',
        }}>
          Bumblebee Food Cart &mdash; Admin Dashboard
        </footer>
      </div>
    </div>
  );
}
