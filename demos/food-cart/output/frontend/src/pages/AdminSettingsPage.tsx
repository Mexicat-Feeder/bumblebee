import { useEffect, useState } from 'react';
import { UpdateSettingsInput } from '../types';
import '../styles/design-tokens.css';

export default function AdminSettingsPage() {
  const [settings, setSettings] = useState<UpdateSettingsInput | null>(null);
  const [editing, setEditing] = useState(false);
  const [pin, setPin] = useState('');
  const [error, setError] = useState('');
  const [formData, setFormData] = useState<UpdateSettingsInput>({
    cart_name: '',
    opening_time: '',
    closing_time: '',
    admin_pin: '',
  });

  useEffect(() => {
    fetch('/api/settings')
      .then((r) => r.json())
      .then((data) => {
        setSettings(data);
        setFormData({
          cart_name: data.cart_name,
          opening_time: data.opening_time,
          closing_time: data.closing_time,
          admin_pin: '',
        });
      });
  }, []);

  const handleStartEdit = () => {
    setError('');
    setPin('');
    setEditing(true);
  };

  const handleCancelEdit = () => {
    setEditing(false);
    setError('');
    setPin('');
    if (settings) {
      setFormData({
        cart_name: settings.cart_name,
        opening_time: settings.opening_time,
        closing_time: settings.closing_time,
        admin_pin: '',
      });
    }
  };

  const handleVerifyAndSave = async () => {
    setError('');

    // Verify PIN first
    const verifyRes = await fetch('/api/settings/verify', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ admin_pin: pin }),
    });
    const verifyData = await verifyRes.json();

    if (!verifyData.valid) {
      setError('Invalid PIN');
      return;
    }

    // Save settings
    const saveRes = await fetch('/api/settings', {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        cart_name: formData.cart_name,
        opening_time: formData.opening_time,
        closing_time: formData.closing_time,
        admin_pin: pin,
      }),
    });
    const updated = await saveRes.json();
    setSettings(updated);
    setEditing(false);
  };

  const handleChange = (
    e: React.ChangeEvent<HTMLInputElement>
  ) => {
    setFormData((prev) => ({ ...prev, [e.target.name]: e.target.value }));
  };

  return (
    <div style={{ padding: '16px', maxWidth: '600px', margin: '0 auto' }}>
      <h1 style={{ marginBottom: '16px' }}>Settings</h1>

      {settings && (
        <div
          style={{
            background: 'var(--bg-card)',
            borderRadius: '8px',
            padding: '16px',
            boxShadow: '0 1px 3px rgba(0,0,0,0.1)',
          }}
        >
          {!editing ? (
            <>
              <div style={{ marginBottom: '12px' }}>
                <label
                  style={{
                    display: 'block',
                    fontSize: '12px',
                    color: 'var(--text-muted)',
                    marginBottom: '4px',
                  }}
                >
                  Cart Name
                </label>
                <div
                  style={{
                    fontSize: '18px',
                    fontWeight: 600,
                    color: 'var(--text-primary)',
                  }}
                >
                  {settings.cart_name}
                </div>
              </div>

              <div style={{ marginBottom: '12px' }}>
                <label
                  style={{
                    display: 'block',
                    fontSize: '12px',
                    color: 'var(--text-muted)',
                    marginBottom: '4px',
                  }}
                >
                  Hours
                </label>
                <div
                  style={{
                    fontSize: '18px',
                    fontWeight: 600,
                    color: 'var(--text-primary)',
                  }}
                >
                  {settings.opening_time} - {settings.closing_time}
                </div>
              </div>

              <div style={{ marginBottom: '12px' }}>
                <label
                  style={{
                    display: 'block',
                    fontSize: '12px',
                    color: 'var(--text-muted)',
                    marginBottom: '4px',
                  }}
                >
                  Admin PIN
                </label>
                <div
                  style={{
                    fontSize: '18px',
                    fontWeight: 600,
                    color: 'var(--text-primary)',
                  }}
                >
                  3333
                </div>
              </div>

              <button
                onClick={handleStartEdit}
                style={{
                  background: 'var(--accent)',
                  color: 'var(--bg-primary)',
                  border: 'none',
                  borderRadius: '6px',
                  padding: '8px 16px',
                  fontSize: '14px',
                  fontWeight: 600,
                  cursor: 'pointer',
                }}
              >
                Edit Settings
              </button>
            </>
          ) : (
            <>
              <div style={{ marginBottom: '12px' }}>
                <label
                  style={{
                    display: 'block',
                    fontSize: '12px',
                    color: 'var(--text-muted)',
                    marginBottom: '4px',
                  }}
                >
                  Cart Name
                </label>
                <input
                  name="cart_name"
                  value={formData.cart_name}
                  onChange={handleChange}
                  style={{
                    width: '100%',
                    padding: '8px',
                    borderRadius: '6px',
                    border: '1px solid var(--border)',
                    background: 'var(--bg-input)',
                    color: 'var(--text-primary)',
                    fontSize: '14px',
                    boxSizing: 'border-box',
                  }}
                />
              </div>

              <div style={{ marginBottom: '12px' }}>
                <label
                  style={{
                    display: 'block',
                    fontSize: '12px',
                    color: 'var(--text-muted)',
                    marginBottom: '4px',
                  }}
                >
                  Opening Time
                </label>
                <input
                  name="opening_time"
                  type="time"
                  value={formData.opening_time}
                  onChange={handleChange}
                  style={{
                    width: '100%',
                    padding: '8px',
                    borderRadius: '6px',
                    border: '1px solid var(--border)',
                    background: 'var(--bg-input)',
                    color: 'var(--text-primary)',
                    fontSize: '14px',
                    boxSizing: 'border-box',
                  }}
                />
              </div>

              <div style={{ marginBottom: '12px' }}>
                <label
                  style={{
                    display: 'block',
                    fontSize: '12px',
                    color: 'var(--text-muted)',
                    marginBottom: '4px',
                  }}
                >
                  Closing Time
                </label>
                <input
                  name="closing_time"
                  type="time"
                  value={formData.closing_time}
                  onChange={handleChange}
                  style={{
                    width: '100%',
                    padding: '8px',
                    borderRadius: '6px',
                    border: '1px solid var(--border)',
                    background: 'var(--bg-input)',
                    color: 'var(--text-primary)',
                    fontSize: '14px',
                    boxSizing: 'border-box',
                  }}
                />
              </div>

              <div style={{ marginBottom: '12px' }}>
                <label
                  style={{
                    display: 'block',
                    fontSize: '12px',
                    color: 'var(--text-muted)',
                    marginBottom: '4px',
                  }}
                >
                  Admin PIN (to confirm changes)
                </label>
                <input
                  type="password"
                  value={pin}
                  onChange={(e) => setPin(e.target.value)}
                  placeholder="Enter PIN"
                  style={{
                    width: '100%',
                    padding: '8px',
                    borderRadius: '6px',
                    border: '1px solid var(--border)',
                    background: 'var(--bg-input)',
                    color: 'var(--text-primary)',
                    fontSize: '14px',
                    boxSizing: 'border-box',
                  }}
                />
              </div>

              {error && (
                <div
                  style={{
                    color: 'var(--error)',
                    fontSize: '13px',
                    marginBottom: '8px',
                  }}
                >
                  {error}
                </div>
              )}

              <div style={{ display: 'flex', gap: '8px' }}>
                <button
                  onClick={handleVerifyAndSave}
                  style={{
                    background: 'var(--accent)',
                    color: 'var(--bg-primary)',
                    border: 'none',
                    borderRadius: '6px',
                    padding: '8px 16px',
                    fontSize: '14px',
                    fontWeight: 600,
                    cursor: 'pointer',
                  }}
                >
                  Save
                </button>
                <button
                  onClick={handleCancelEdit}
                  style={{
                    background: 'var(--bg-input)',
                    color: 'var(--text-primary)',
                    border: `1px solid var(--border)`,
                    borderRadius: '6px',
                    padding: '8px 16px',
                    fontSize: '14px',
                    fontWeight: 600,
                    cursor: 'pointer',
                  }}
                >
                  Cancel
                </button>
              </div>
            </>
          )}
        </div>
      )}
    </div>
  );
}
