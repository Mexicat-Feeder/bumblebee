import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import '../styles/design-tokens.css';

export default function AdminLoginPage() {
  const navigate = useNavigate();
  const [pin, setPin] = useState('');
  const [error, setError] = useState('');

  async function login() {
    const res = await fetch('/api/settings/verify', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ admin_pin: pin }),
    });
    const data = await res.json();
    if (data.valid) {
      navigate('/admin');
    } else {
      setError('Invalid PIN');
    }
  }

  return (
    <div style={{ padding: 16, backgroundColor: 'var(--bg-page)', minHeight: '100vh', display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center' }}>
      <div style={{ backgroundColor: 'var(--bg-card)', padding: 24, borderRadius: 8, boxShadow: 'var(--shadow-card)', minWidth: 300 }}>
        <h1 style={{ color: 'var(--text-primary)', marginBottom: 16 }}>Admin Login</h1>
        <input
          value={pin}
          onChange={(e) => setPin(e.target.value)}
          placeholder="PIN"
          type="password"
          onKeyDown={(e) => {
            if (e.key === 'Enter') login();
          }}
          style={{
            width: '100%',
            padding: 8,
            marginBottom: 12,
            borderRadius: 4,
            border: '1px solid var(--border-color)',
            backgroundColor: 'var(--bg-input)',
            color: 'var(--text-primary)',
            boxSizing: 'border-box',
          }}
        />
        <button
          onClick={login}
          style={{
            width: '100%',
            padding: 8,
            borderRadius: 4,
            border: 'none',
            backgroundColor: 'var(--color-primary)',
            color: 'var(--text-on-primary)',
            cursor: 'pointer',
            fontWeight: 'bold',
          }}
        >
          Enter
        </button>
        {error && <div style={{ color: 'var(--color-error)', marginTop: 12, textAlign: 'center' }}>{error}</div>}
      </div>
    </div>
  );
}
