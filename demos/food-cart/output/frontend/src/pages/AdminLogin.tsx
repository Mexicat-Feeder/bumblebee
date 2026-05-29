/**
 * Admin Login Page - Bumblebee Food Cart
 *
 * Allows the admin to enter a PIN to authenticate and access the admin panel.
 * Validates the PIN against the backend settings API.
 */

import { useState, FormEvent, ChangeEvent } from 'react';

interface AdminLoginProps {
  onLoginSuccess: () => void;
  onLoginError?: (message: string) => void;
}

export default function AdminLogin({ onLoginSuccess, onLoginError }: AdminLoginProps) {
  const [pin, setPin] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [errorMessage, setErrorMessage] = useState('');

  const handleChange = (e: ChangeEvent<HTMLInputElement>) => {
    const value = e.target.value.replace(/\D/g, '').slice(0, 20);
    setPin(value);
    setErrorMessage('');
  };

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();

    if (pin.length < 4) {
      setErrorMessage('PIN must be at least 4 digits.');
      return;
    }

    setIsLoading(true);
    setErrorMessage('');

    try {
      const response = await fetch('/api/settings/verify', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ admin_pin: pin }),
      });

      if (!response.ok) {
        const data = await response.json().catch(() => ({}));
        const message = data.detail || 'Invalid PIN. Please try again.';
        setErrorMessage(message);
        if (onLoginError) {
          onLoginError(message);
        }
        return;
      }

      const data = await response.json();
      if (!data.valid) {
        setErrorMessage('Invalid PIN. Please try again.');
        if (onLoginError) {
          onLoginError('Invalid PIN. Please try again.');
        }
        return;
      }

      // Success — redirect to admin panel
      onLoginSuccess();
    } catch (err) {
      const message = 'Connection error. Please try again.';
      setErrorMessage(message);
      if (onLoginError) {
        onLoginError(message);
      }
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div style={{
      display: 'flex',
      justifyContent: 'center',
      alignItems: 'center',
      minHeight: '100vh',
      backgroundColor: 'var(--bg-page)',
    }}>
      <div style={{
        backgroundColor: 'var(--bg-card)',
        borderRadius: 'var(--radius-lg)',
        padding: 'var(--space-2xl)',
        width: '100%',
        maxWidth: '400px',
        boxShadow: 'var(--shadow-md)',
        textAlign: 'center',
      }}>
        <h1 style={{
          fontSize: 'var(--text-2xl)',
          fontWeight: 'var(--font-bold)',
          color: 'var(--text-primary)',
          marginBottom: 'var(--space-md)',
        }}>
          Admin Login
        </h1>
        <p style={{
          fontSize: 'var(--text-sm)',
          color: 'var(--text-secondary)',
          marginBottom: 'var(--space-xl)',
        }}>
          Enter your admin PIN to continue
        </p>

        <form onSubmit={handleSubmit}>
          <div style={{ marginBottom: 'var(--space-lg)' }}>
            <label
              htmlFor="admin-pin"
              style={{
                display: 'block',
                textAlign: 'left',
                fontSize: 'var(--text-sm)',
                fontWeight: 'var(--font-medium)',
                color: 'var(--text-primary)',
                marginBottom: 'var(--space-xs)',
              }}
            >
              Admin PIN
            </label>
            <input
              id="admin-pin"
              type="password"
              inputMode="numeric"
              pattern="[0-9]*"
              value={pin}
              onChange={handleChange}
              placeholder="Enter PIN"
              autoFocus
              disabled={isLoading}
              style={{
                width: '100%',
                padding: 'var(--space-md)',
                fontSize: 'var(--text-lg)',
                textAlign: 'center',
                letterSpacing: 'var(--space-md)',
                borderRadius: 'var(--radius-md)',
                border: `1px solid ${errorMessage ? 'var(--color-error)' : 'var(--border-subtle)'}`,
                backgroundColor: 'var(--bg-input)',
                color: 'var(--text-primary)',
                outline: 'none',
                boxSizing: 'border-box',
                transition: 'border-color 0.2s ease',
              }}
              onFocus={(e) => {
                if (!errorMessage) {
                  e.target.style.borderColor = 'var(--color-primary)';
                }
              }}
              onBlur={(e) => {
                if (!errorMessage) {
                  e.target.style.borderColor = 'var(--border-subtle)';
                }
              }}
            />
          </div>

          {errorMessage && (
            <div style={{
              backgroundColor: 'var(--bg-error)',
              color: 'var(--color-error)',
              padding: 'var(--space-md)',
              borderRadius: 'var(--radius-md)',
              fontSize: 'var(--text-sm)',
              marginBottom: 'var(--space-lg)',
              border: `1px solid var(--color-error)`,
            }}>
              {errorMessage}
            </div>
          )}

          <button
            type="submit"
            disabled={isLoading || pin.length === 0}
            style={{
              width: '100%',
              padding: 'var(--space-md)',
              fontSize: 'var(--text-base)',
              fontWeight: 'var(--font-semibold)',
              color: 'var(--text-on-primary)',
              backgroundColor: isLoading || pin.length === 0
                ? 'var(--color-disabled)'
                : 'var(--color-primary)',
              border: 'none',
              borderRadius: 'var(--radius-md)',
              cursor: isLoading || pin.length === 0 ? 'not-allowed' : 'pointer',
              transition: 'background-color 0.2s ease',
            }}
          >
            {isLoading ? 'Verifying...' : 'Submit'}
          </button>
        </form>
      </div>
    </div>
  );
}
