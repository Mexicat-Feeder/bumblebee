/**
 * Admin Sales Summary Page - Bumblebee Food Cart
 *
 * Displays total sales amount and number of orders for the current day.
 */

import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import '../styles/design-tokens.css';

interface DailySalesSummary {
  totalSales: number;
  orderCount: number;
  date: string;
}

export default function AdminSalesSummary() {
  const navigate = useNavigate();
  const [summary, setSummary] = useState<DailySalesSummary | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchSalesSummary = async () => {
      try {
        setLoading(true);
        const response = await fetch('/api/admin/sales-summary');
        if (!response.ok) {
          throw new Error('Failed to fetch sales summary');
        }
        const data: DailySalesSummary = await response.json();
        setSummary(data);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'An error occurred');
      } finally {
        setLoading(false);
      }
    };

    fetchSalesSummary();
  }, []);

  const handleBack = () => {
    navigate('/admin/orders');
  };

  if (loading) {
    return (
      <div style={{
        minHeight: '100vh',
        backgroundColor: 'var(--bg-page)',
        display: 'flex',
        justifyContent: 'center',
        alignItems: 'center',
      }}>
        <p style={{
          color: 'var(--text-secondary)',
          fontSize: '1rem',
        }}>
          Loading sales data...
        </p>
      </div>
    );
  }

  if (error) {
    return (
      <div style={{
        minHeight: '100vh',
        backgroundColor: 'var(--bg-page)',
        display: 'flex',
        justifyContent: 'center',
        alignItems: 'center',
      }}>
        <div style={{
          backgroundColor: 'var(--bg-card)',
          padding: '2rem',
          borderRadius: 'var(--radius-md)',
          textAlign: 'center',
          maxWidth: '400px',
        }}>
          <p style={{
            color: 'var(--text-danger)',
            marginBottom: '1rem',
          }}>
            {error}
          </p>
          <button
            onClick={handleBack}
            style={{
              backgroundColor: 'var(--accent-primary)',
              color: 'var(--text-on-accent)',
              border: 'none',
              padding: '0.5rem 1.5rem',
              borderRadius: 'var(--radius-sm)',
              cursor: 'pointer',
              fontSize: '0.875rem',
              fontWeight: '600',
            }}
          >
            Go Back
          </button>
        </div>
      </div>
    );
  }

  const formattedDate = summary?.date
    ? new Date(summary.date).toLocaleDateString('en-US', {
        weekday: 'long',
        year: 'numeric',
        month: 'long',
        day: 'numeric',
      })
    : '';

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
              Daily Sales Summary
            </h1>
            <p style={{
              fontSize: '0.875rem',
              color: 'var(--text-secondary)',
              margin: '0.25rem 0 0 0',
            }}>
              {formattedDate}
            </p>
          </div>
          <button
            onClick={handleBack}
            style={{
              backgroundColor: 'var(--bg-card)',
              color: 'var(--text-primary)',
              border: '1px solid var(--border-color)',
              padding: '0.5rem 1rem',
              borderRadius: 'var(--radius-sm)',
              cursor: 'pointer',
              fontSize: '0.875rem',
              fontWeight: '500',
            }}
          >
            ← Back to Orders
          </button>
        </header>

        {/* Summary Cards */}
        <div style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))',
          gap: '1.5rem',
          marginBottom: '2rem',
        }}>
          {/* Total Sales Card */}
          <div style={{
            backgroundColor: 'var(--bg-card)',
            borderRadius: 'var(--radius-md)',
            padding: '1.5rem',
            boxShadow: 'var(--shadow-sm)',
          }}>
            <div style={{
              display: 'flex',
              alignItems: 'center',
              marginBottom: '0.75rem',
            }}>
              <span style={{
                fontSize: '1.5rem',
                marginRight: '0.75rem',
              }}>
                💰
              </span>
              <h2 style={{
                fontSize: '1rem',
                fontWeight: '600',
                color: 'var(--text-secondary)',
                margin: 0,
              }}>
                Total Sales
              </h2>
            </div>
            <p style={{
              fontSize: '2rem',
              fontWeight: '700',
              color: 'var(--text-primary)',
              margin: 0,
            }}>
              {summary ? summary.totalSales.toFixed(2) : '0.00'}
            </p>
            <p style={{
              fontSize: '0.75rem',
              color: 'var(--text-secondary)',
              margin: '0.5rem 0 0 0',
            }}>
              Today&apos;s revenue
            </p>
          </div>

          {/* Order Count Card */}
          <div style={{
            backgroundColor: 'var(--bg-card)',
            borderRadius: 'var(--radius-md)',
            padding: '1.5rem',
            boxShadow: 'var(--shadow-sm)',
          }}>
            <div style={{
              display: 'flex',
              alignItems: 'center',
              marginBottom: '0.75rem',
            }}>
              <span style={{
                fontSize: '1.5rem',
                marginRight: '0.75rem',
              }}>
                📦
              </span>
              <h2 style={{
                fontSize: '1rem',
                fontWeight: '600',
                color: 'var(--text-secondary)',
                margin: 0,
              }}>
                Orders Today
              </h2>
            </div>
            <p style={{
              fontSize: '2rem',
              fontWeight: '700',
              color: 'var(--text-primary)',
              margin: 0,
            }}>
              {summary ? summary.orderCount : 0}
            </p>
            <p style={{
              fontSize: '0.75rem',
              color: 'var(--text-secondary)',
              margin: '0.5rem 0 0 0',
            }}>
              Total orders placed
            </p>
          </div>
        </div>

        {/* Quick Actions */}
        <div style={{
          backgroundColor: 'var(--bg-card)',
          borderRadius: 'var(--radius-md)',
          padding: '1.5rem',
          boxShadow: 'var(--shadow-sm)',
        }}>
          <h2 style={{
            fontSize: '1.125rem',
            fontWeight: '600',
            color: 'var(--text-primary)',
            margin: '0 0 1rem 0',
          }}>
            Quick Actions
          </h2>
          <div style={{
            display: 'flex',
            gap: '1rem',
            flexWrap: 'wrap',
          }}>
            <button
              onClick={() => navigate('/admin/orders')}
              style={{
                backgroundColor: 'var(--accent-primary)',
                color: 'var(--text-on-accent)',
                border: 'none',
                padding: '0.625rem 1.25rem',
                borderRadius: 'var(--radius-sm)',
                cursor: 'pointer',
                fontSize: '0.875rem',
                fontWeight: '600',
              }}
            >
              View All Orders
            </button>
            <button
              onClick={() => navigate('/admin/menu')}
              style={{
                backgroundColor: 'var(--bg-page)',
                color: 'var(--text-primary)',
                border: '1px solid var(--border-color)',
                padding: '0.625rem 1.25rem',
                borderRadius: 'var(--radius-sm)',
                cursor: 'pointer',
                fontSize: '0.875rem',
                fontWeight: '600',
              }}
            >
              Manage Menu
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
