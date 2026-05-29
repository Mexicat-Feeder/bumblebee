/**
 * Admin Orders Management Page - Bumblebee Food Cart
 *
 * Displays a live list of incoming orders with timestamps and one-click
 * status updates.  List is kept in sync via WebSocket.
 */

import { useState, useEffect, useCallback, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { useOrderStatusWebSocket } from '../hooks/useOrderStatusWebSocket';
import type { Order, OrderStatus } from '../types/shared';

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

const STATUS_FLOW: OrderStatus[] = [
  'pending',
  'confirmed',
  'preparing',
  'ready',
  'delivered',
  'cancelled',
];

function getNextStatus(current: OrderStatus): OrderStatus | null {
  const idx = STATUS_FLOW.indexOf(current);
  if (idx === -1 || idx === STATUS_FLOW.length - 1) return null;
  return STATUS_FLOW[idx + 1];
}

function formatTimestamp(iso: string): string {
  try {
    const d = new Date(iso);
    return d.toLocaleString(undefined, {
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  } catch {
    return iso;
  }
}

function timeAgo(iso: string): string {
  try {
    const diff = Date.now() - new Date(iso).getTime();
    const mins = Math.floor(diff / 60_000);
    if (mins < 1) return 'just now';
    if (mins < 60) return `${mins}m ago`;
    const hrs = Math.floor(mins / 60);
    return `${hrs}h ${mins % 60}m ago`;
  } catch {
    return '';
  }
}

// ---------------------------------------------------------------------------
// Sub-components
// ---------------------------------------------------------------------------

interface OrderCardProps {
  order: Order;
  onStatusChange: (orderId: string, newStatus: OrderStatus) => void;
}

function OrderCard({ order, onStatusChange }: OrderCardProps) {
  const nextStatus = getNextStatus(order.status);

  const statusColors: Record<OrderStatus, string> = {
    pending: 'var(--status-pending)',
    confirmed: 'var(--status-confirmed)',
    preparing: 'var(--status-preparing)',
    ready: 'var(--status-ready)',
    delivered: 'var(--status-delivered)',
    cancelled: 'var(--status-cancelled)',
  };

  const badgeColor = statusColors[order.status] ?? 'var(--text-secondary)';

  return (
    <div style={{
      backgroundColor: 'var(--bg-card)',
      borderRadius: 'var(--radius-md)',
      border: '1px solid var(--border-color)',
      padding: '1rem 1.25rem',
      marginBottom: '0.75rem',
      transition: 'box-shadow 0.2s ease',
    }}
      onMouseEnter={e => (e.currentTarget.style.boxShadow = '0 4px 12px rgba(0,0,0,0.08)')}
      onMouseLeave={e => (e.currentTarget.style.boxShadow = 'none')}
    >
      {/* Top row: order number + status badge + time */}
      <div style={{
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        marginBottom: '0.75rem',
        flexWrap: 'wrap',
        gap: '0.5rem',
      }}>
        <div>
          <span style={{
            fontWeight: '700',
            fontSize: '1.1rem',
            color: 'var(--text-primary)',
          }}>
            #{order.id}
          </span>
          {order.customerName && (
            <span style={{
              marginLeft: '0.75rem',
              fontSize: '0.875rem',
              color: 'var(--text-secondary)',
            }}>
              {order.customerName}
              {order.customerPhone && (
                <span style={{ marginLeft: '0.5rem' }}>
                  ({order.customerPhone})
                </span>
              )}
            </span>
          )}
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
          <span style={{
            fontSize: '0.75rem',
            color: 'var(--text-tertiary)',
          }}>
            {formatTimestamp(order.createdAt)} · {timeAgo(order.createdAt)}
          </span>
          <span style={{
            display: 'inline-block',
            padding: '0.2rem 0.6rem',
            borderRadius: 'var(--radius-full)',
            fontSize: '0.75rem',
            fontWeight: '600',
            textTransform: 'uppercase',
            backgroundColor: badgeColor,
            color: 'var(--text-on-accent)',
          }}>
            {order.status}
          </span>
        </div>
      </div>

      {/* Items list */}
      <div style={{
        fontSize: '0.875rem',
        color: 'var(--text-secondary)',
        marginBottom: '0.75rem',
        paddingLeft: '0.5rem',
        borderLeft: `2px solid var(--border-color)`,
      }}>
        {order.items.map((item, i) => (
          <div key={i} style={{ marginBottom: '0.25rem' }}>
            <strong>{item.quantity}×</strong> {item.name} —{' '}
            {(item.unitPrice * item.quantity).toFixed(2)}
            {item.specialInstructions && (
              <span style={{
                display: 'block',
                fontSize: '0.75rem',
                color: 'var(--text-tertiary)',
                fontStyle: 'italic',
              }}>
                Note: {item.specialInstructions}
              </span>
            )}
          </div>
        ))}
      </div>

      {/* Footer: total + action button */}
      <div style={{
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        paddingTop: '0.75rem',
        borderTop: '1px solid var(--border-color)',
      }}>
        <span style={{
          fontWeight: '700',
          fontSize: '1rem',
          color: 'var(--text-primary)',
        }}>
          Total: {order.totalAmount.toFixed(2)}
        </span>

        {nextStatus && order.status !== 'cancelled' && (
          <button
            onClick={() => onStatusChange(order.id, nextStatus)}
            style={{
              padding: '0.4rem 1rem',
              borderRadius: 'var(--radius-md)',
              border: 'none',
              backgroundColor: 'var(--accent-primary)',
              color: 'var(--text-on-accent)',
              fontWeight: '600',
              fontSize: '0.8rem',
              cursor: 'pointer',
              transition: 'opacity 0.15s ease',
            }}
            onMouseEnter={e => (e.currentTarget.style.opacity = '0.85')}
            onMouseLeave={e => (e.currentTarget.style.opacity = '1')}
          >
            Mark as {nextStatus}
          </button>
        )}

        {order.status === 'cancelled' && (
          <span style={{
            fontSize: '0.8rem',
            color: 'var(--status-cancelled)',
            fontStyle: 'italic',
          }}>
            Cancelled
          </span>
        )}
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Main component
// ---------------------------------------------------------------------------

export default function AdminOrders() {
  const navigate = useNavigate();

  // Local order state (mirrors what we receive from API / WebSocket)
  const [orders, setOrders] = useState<Order[]>([]);
  const [filter, setFilter] = useState<OrderStatus | 'all'>('all');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [lastRefresh, setLastRefresh] = useState<Date>(new Date());

  const abortRef = useRef<AbortController | null>(null);

  // -----------------------------------------------------------------------
  // Fetch orders from API
  // -----------------------------------------------------------------------

  const fetchOrders = useCallback(async (signal: AbortSignal) => {
    try {
      const res = await fetch('/api/orders', { signal });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();
      // The backend may return { orders: [...] } or a plain array
      const list: Order[] = Array.isArray(data) ? data : (data.orders ?? []);
      setOrders(list);
      setLastRefresh(new Date());
      setError(null);
    } catch (err: unknown) {
      if ((err as Error).name !== 'AbortError') {
        setError(err instanceof Error ? err.message : 'Failed to load orders');
      }
    } finally {
      setLoading(false);
    }
  }, []);

  // Initial fetch
  useEffect(() => {
    const controller = new AbortController();
    abortRef.current = controller;
    fetchOrders(controller.signal);
    return () => controller.abort();
  }, [fetchOrders]);

  // -----------------------------------------------------------------------
  // WebSocket for real-time updates
  // -----------------------------------------------------------------------

  const handleWsMessage = useCallback((msg: unknown) => {
    const m = msg as Record<string, unknown>;
    if (m.type === 'order_status_update') {
      const orderId = String(m.orderId ?? '');
      const newStatus = String(m.status ?? '') as OrderStatus;
      setOrders(prev =>
        prev.map(o =>
          o.id === orderId ? { ...o, status: newStatus, updatedAt: String(m.timestamp ?? new Date().toISOString()) } : o,
        ),
      );
    }
  }, []);

  useOrderStatusWebSocket({
    url: 'ws://localhost:8000/ws/orders',
    onMessage: handleWsMessage,
    autoReconnect: true,
  });

  // -----------------------------------------------------------------------
  // Status change handler
  // -----------------------------------------------------------------------

  const handleStatusChange = useCallback(async (orderId: string, newStatus: OrderStatus) => {
    try {
      await fetch(`/api/orders/${orderId}`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ status: newStatus }),
      });
      // Optimistic update
      setOrders(prev =>
        prev.map(o =>
          o.id === orderId ? { ...o, status: newStatus, updatedAt: new Date().toISOString() } : o,
        ),
      );
    } catch {
      // Re-fetch to stay in sync
      fetchOrders(new AbortController().signal);
    }
  }, [fetchOrders]);

  // -----------------------------------------------------------------------
  // Derived data
  // -----------------------------------------------------------------------

  const filteredOrders = filter === 'all'
    ? orders
    : orders.filter(o => o.status === filter);

  const activeOrders = orders.filter(o => !['delivered', 'cancelled'].includes(o.status));
  const pendingCount = orders.filter(o => o.status === 'pending').length;

  // -----------------------------------------------------------------------
  // Render
  // -----------------------------------------------------------------------

  if (loading) {
    return (
      <div style={{
        minHeight: '100vh',
        backgroundColor: 'var(--bg-page)',
        display: 'flex',
        justifyContent: 'center',
        alignItems: 'center',
        color: 'var(--text-secondary)',
      }}>
        Loading orders…
      </div>
    );
  }

  return (
    <div style={{
      minHeight: '100vh',
      backgroundColor: 'var(--bg-page)',
      padding: '2rem 1rem',
    }}>
      <div style={{ maxWidth: '900px', margin: '0 auto' }}>
        {/* Header */}
        <header style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          marginBottom: '1.5rem',
          flexWrap: 'wrap',
          gap: '1rem',
        }}>
          <div>
            <h1 style={{
              fontSize: '1.5rem',
              fontWeight: '700',
              color: 'var(--text-primary)',
              margin: 0,
            }}>
              Order Management
            </h1>
            <p style={{
              fontSize: '0.8rem',
              color: 'var(--text-tertiary)',
              margin: '0.25rem 0 0 0',
            }}>
              {activeOrders.length} active · {pendingCount} pending · Updated{' '}
              {lastRefresh.toLocaleTimeString()}
            </p>
          </div>

          <button
            onClick={() => navigate('/admin')}
            style={{
              padding: '0.4rem 1rem',
              borderRadius: 'var(--radius-md)',
              border: '1px solid var(--border-color)',
              backgroundColor: 'var(--bg-card)',
              color: 'var(--text-secondary)',
              cursor: 'pointer',
              fontSize: '0.8rem',
            }}
          >
            ← Back to Admin
          </button>
        </header>

        {/* Error banner */}
        {error && (
          <div style={{
            backgroundColor: 'var(--status-cancelled)',
            color: 'var(--text-on-accent)',
            padding: '0.75rem 1rem',
            borderRadius: 'var(--radius-md)',
            marginBottom: '1rem',
            fontSize: '0.85rem',
          }}>
            ⚠ {error}
            <button
              onClick={() => {
                setError(null);
                setLoading(true);
                fetchOrders(new AbortController().signal);
              }}
              style={{
                marginLeft: '1rem',
                padding: '0.2rem 0.6rem',
                borderRadius: 'var(--radius-sm)',
                border: 'none',
                backgroundColor: 'rgba(255,255,255,0.2)',
                color: 'inherit',
                cursor: 'pointer',
                fontSize: '0.8rem',
              }}
            >
              Retry
            </button>
          </div>
        )}

        {/* Filter tabs */}
        <div style={{
          display: 'flex',
          gap: '0.5rem',
          marginBottom: '1.25rem',
          flexWrap: 'wrap',
        }}>
          {(['all', 'pending', 'confirmed', 'preparing', 'ready', 'delivered', 'cancelled'] as const).map(f => (
            <button
              key={f}
              onClick={() => setFilter(f)}
              style={{
                padding: '0.35rem 0.85rem',
                borderRadius: 'var(--radius-full)',
                border: 'none',
                backgroundColor: filter === f ? 'var(--accent-primary)' : 'var(--bg-card)',
                color: filter === f ? 'var(--text-on-accent)' : 'var(--text-secondary)',
                fontWeight: filter === f ? '600' : '400',
                fontSize: '0.8rem',
                cursor: 'pointer',
                textTransform: 'capitalize',
                transition: 'background-color 0.15s ease',
              }}
            >
              {f}
              {f !== 'all' && (
                <span style={{ marginLeft: '0.35rem', opacity: 0.7 }}>
                  ({orders.filter(o => o.status === f).length})
                </span>
              )}
            </button>
          ))}
        </div>

        {/* Orders list */}
        {filteredOrders.length === 0 ? (
          <div style={{
            textAlign: 'center',
            padding: '3rem 1rem',
            color: 'var(--text-tertiary)',
            fontSize: '0.9rem',
          }}>
            {filter !== 'all'
              ? `No ${filter} orders at this time.`
              : 'No orders yet. New orders will appear here in real time.'}
          </div>
        ) : (
          filteredOrders.map(order => (
            <OrderCard
              key={order.id}
              order={order}
              onStatusChange={handleStatusChange}
            />
          ))
        )}
      </div>
    </div>
  );
}
