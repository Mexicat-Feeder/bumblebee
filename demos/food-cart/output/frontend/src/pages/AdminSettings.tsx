/**
 * Admin Settings Page - Bumblebee Food Cart
 *
 * Configure cart name, operating hours, and admin PIN.
 * Integrates with the backend settings API.
 */

import { useState, useEffect, FormEvent } from 'react';
import { useNavigate } from 'react-router-dom';
import '../styles/design-tokens.css';

interface SettingsData {
  cartName: string;
  openTime: string;
  closeTime: string;
  hasAdminPin: boolean;
}

interface ApiSettingsResponse {
  cart_name: string;
  open_time: string;
  close_time: string;
  has_admin_pin: boolean;
}

export default function AdminSettings() {
  const navigate = useNavigate();

  const [cartName, setCartName] = useState('');
  const [openTime, setOpenTime] = useState('09:00');
  const [closeTime, setCloseTime] = useState('21:00');
  const [adminPin, setAdminPin] = useState('');
  const [hasAdminPin, setHasAdminPin] = useState(false);

  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  const [saveMessage, setSaveMessage] = useState<{
    type: 'success' | 'error';
    text: string;
  } | null>(null);

  // Load current settings on mount
  useEffect(() => {
    const loadSettings = async () => {
      try {
        const response = await fetch('/api/settings', {
          method: 'GET',
          headers: { 'Content-Type': 'application/json' },
        });

        if (!response.ok) {
          throw new Error('Failed to load settings');
        }

        const data: ApiSettingsResponse = await response.json();

        setCartName(data.cart_name);
        setOpenTime(data.open_time);
        setCloseTime(data.close_time);
        setHasAdminPin(data.has_admin_pin);
      } catch {
        setSaveMessage({
          type: 'error',
          text: 'Failed to load settings. Please try again.',
        });
      } finally {
        setIsLoading(false);
      }
    };

    loadSettings();
  }, []);

  // Clear save message after 4 seconds
  useEffect(() => {
    if (saveMessage) {
      const timer = setTimeout(() => {
        setSaveMessage(null);
      }, 4000);
      return () => clearTimeout(timer);
    }
  }, [saveMessage]);

  const handleSave = async (event: FormEvent) => {
    event.preventDefault();
    setIsSaving(true);
    setSaveMessage(null);

    try {
      // Update cart name
      await fetch('/api/settings/cart-name', {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ cart_name: cartName }),
      });

      // Update operating hours
      await fetch('/api/settings/operating-hours', {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          open_time: openTime,
          close_time: closeTime,
        }),
      });

      // Update admin PIN (only if provided)
      if (adminPin.length > 0) {
        await fetch('/api/settings/admin-pin', {
          method: 'PUT',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ admin_pin: adminPin }),
        });
        setHasAdminPin(true);
      }

      setSaveMessage({
        type: 'success',
        text: 'Settings saved successfully!',
      });
    } catch {
      setSaveMessage({
        type: 'error',
        text: 'Failed to save settings. Please try again.',
      });
    } finally {
      setIsSaving(false);
    }
  };

  const handleBack = () => {
    navigate('/admin');
  };

  if (isLoading) {
    return (
      <div style={{
        minHeight: '100vh',
        backgroundColor: 'var(--bg-page)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
      }}>
        <p style={{
          color: 'var(--text-secondary)',
          fontSize: '1rem',
        }}>
          Loading settings...
        </p>
      </div>
    );
  }

  return (
    <div style={{
      minHeight: '100vh',
      backgroundColor: 'var(--bg-page)',
      padding: '2rem 1rem',
    }}>
      <div style={{
        maxWidth: '600px',
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
              fontSize: '1.5rem',
              fontWeight: '700',
              color: 'var(--text-primary)',
              margin: 0,
            }}>
              Settings
            </h1>
            <p style={{
              fontSize: '0.875rem',
              color: 'var(--text-secondary)',
              margin: '0.25rem 0 0 0',
            }}>
              Configure your cart details and security.
            </p>
          </div>
          <button
            type="button"
            onClick={handleBack}
            style={{
              padding: '0.5rem 1rem',
              backgroundColor: 'var(--bg-card)',
              color: 'var(--text-primary)',
              border: '1px solid var(--border-color)',
              borderRadius: 'var(--radius-md, 8px)',
              cursor: 'pointer',
              fontSize: '0.875rem',
              fontWeight: '500',
            }}
          >
            ← Back
          </button>
        </header>

        {/* Save message */}
        {saveMessage && (
          <div style={{
            padding: '0.75rem 1rem',
            marginBottom: '1.5rem',
            borderRadius: 'var(--radius-md, 8px)',
            backgroundColor: saveMessage.type === 'success'
              ? 'var(--bg-success, #e6f9f0)'
              : 'var(--bg-error, #fde8e8)',
            color: saveMessage.type === 'success'
              ? 'var(--text-success, #1a7a4c)'
              : 'var(--text-error, #a94442)',
            fontSize: '0.875rem',
            fontWeight: '500',
          }}>
            {saveMessage.text}
          </div>
        )}

        {/* Settings Form */}
        <form onSubmit={handleSave}>
          {/* Cart Name */}
          <div style={{
            backgroundColor: 'var(--bg-card)',
            borderRadius: 'var(--radius-lg, 12px)',
            padding: '1.5rem',
            marginBottom: '1.5rem',
            border: '1px solid var(--border-color)',
          }}>
            <h2 style={{
              fontSize: '1.125rem',
              fontWeight: '600',
              color: 'var(--text-primary)',
              margin: '0 0 1rem 0',
            }}>
              Cart Name
            </h2>
            <input
              type="text"
              value={cartName}
              onChange={(e) => setCartName(e.target.value)}
              placeholder="Enter cart name"
              maxLength={100}
              required
              style={{
                width: '100%',
                padding: '0.75rem 1rem',
                fontSize: '1rem',
                border: '1px solid var(--border-color)',
                borderRadius: 'var(--radius-md, 8px)',
                backgroundColor: 'var(--bg-input, #fff)',
                color: 'var(--text-primary)',
                outline: 'none',
                boxSizing: 'border-box',
              }}
            />
            <p style={{
              fontSize: '0.75rem',
              color: 'var(--text-secondary)',
              margin: '0.5rem 0 0 0',
            }}>
              This name will be displayed to customers.
            </p>
          </div>

          {/* Operating Hours */}
          <div style={{
            backgroundColor: 'var(--bg-card)',
            borderRadius: 'var(--radius-lg, 12px)',
            padding: '1.5rem',
            marginBottom: '1.5rem',
            border: '1px solid var(--border-color)',
          }}>
            <h2 style={{
              fontSize: '1.125rem',
              fontWeight: '600',
              color: 'var(--text-primary)',
              margin: '0 0 1rem 0',
            }}>
              Operating Hours
            </h2>
            <div style={{
              display: 'flex',
              gap: '1rem',
              alignItems: 'center',
            }}>
              <div style={{ flex: 1 }}>
                <label style={{
                  display: 'block',
                  fontSize: '0.875rem',
                  fontWeight: '500',
                  color: 'var(--text-secondary)',
                  marginBottom: '0.375rem',
                }}>
                  Open
                </label>
                <input
                  type="time"
                  value={openTime}
                  onChange={(e) => setOpenTime(e.target.value)}
                  required
                  style={{
                    width: '100%',
                    padding: '0.75rem 1rem',
                    fontSize: '1rem',
                    border: '1px solid var(--border-color)',
                    borderRadius: 'var(--radius-md, 8px)',
                    backgroundColor: 'var(--bg-input, #fff)',
                    color: 'var(--text-primary)',
                    outline: 'none',
                    boxSizing: 'border-box',
                  }}
                />
              </div>
              <span style={{
                color: 'var(--text-secondary)',
                fontSize: '1.25rem',
                marginTop: '1.25rem',
              }}>
                to
              </span>
              <div style={{ flex: 1 }}>
                <label style={{
                  display: 'block',
                  fontSize: '0.875rem',
                  fontWeight: '500',
                  color: 'var(--text-secondary)',
                  marginBottom: '0.375rem',
                }}>
                  Close
                </label>
                <input
                  type="time"
                  value={closeTime}
                  onChange={(e) => setCloseTime(e.target.value)}
                  required
                  style={{
                    width: '100%',
                    padding: '0.75rem 1rem',
                    fontSize: '1rem',
                    border: '1px solid var(--border-color)',
                    borderRadius: 'var(--radius-md, 8px)',
                    backgroundColor: 'var(--bg-input, #fff)',
                    color: 'var(--text-primary)',
                    outline: 'none',
                    boxSizing: 'border-box',
                  }}
                />
              </div>
            </div>
            <p style={{
              fontSize: '0.75rem',
              color: 'var(--text-secondary)',
              margin: '0.5rem 0 0 0',
            }}>
              Format: HH:MM (24-hour).
            </p>
          </div>

          {/* Admin PIN */}
          <div style={{
            backgroundColor: 'var(--bg-card)',
            borderRadius: 'var(--radius-lg, 12px)',
            padding: '1.5rem',
            marginBottom: '1.5rem',
            border: '1px solid var(--border-color)',
          }}>
            <h2 style={{
              fontSize: '1.125rem',
              fontWeight: '600',
              color: 'var(--text-primary)',
              margin: '0 0 1rem 0',
            }}>
              Admin PIN
            </h2>
            <input
              type="password"
              value={adminPin}
              onChange={(e) => setAdminPin(e.target.value)}
              placeholder={hasAdminPin ? 'Enter new PIN (leave blank to keep current)' : 'Set admin PIN'}
              minLength={4}
              maxLength={20}
              style={{
                width: '100%',
                padding: '0.75rem 1rem',
                fontSize: '1rem',
                border: '1px solid var(--border-color)',
                borderRadius: 'var(--radius-md, 8px)',
                backgroundColor: 'var(--bg-input, #fff)',
                color: 'var(--text-primary)',
                outline: 'none',
                boxSizing: 'border-box',
              }}
            />
            <p style={{
              fontSize: '0.75rem',
              color: 'var(--text-secondary)',
              margin: '0.5rem 0 0 0',
            }}>
              {hasAdminPin
                ? 'A PIN is already set. Enter a new one to change it, or leave blank to keep the current PIN.'
                : 'Set a PIN of at least 4 characters to protect admin access.'}
            </p>
          </div>

          {/* Save Button */}
          <button
            type="submit"
            disabled={isSaving}
            style={{
              width: '100%',
              padding: '0.875rem 1.5rem',
              fontSize: '1rem',
              fontWeight: '600',
              color: '#fff',
              backgroundColor: 'var(--accent-primary, #f59e0b)',
              border: 'none',
              borderRadius: 'var(--radius-md, 8px)',
              cursor: isSaving ? 'not-allowed' : 'pointer',
              opacity: isSaving ? 0.7 : 1,
              transition: 'opacity 0.2s ease',
            }}
          >
            {isSaving ? 'Saving...' : 'Save Settings'}
          </button>
        </form>
      </div>
    </div>
  );
}
