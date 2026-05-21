import React from 'react';

export default function App() {
  return (
    <div style={{
      background: '#0D1117',
      color: '#E6EDF3',
      minHeight: '100vh',
      display: 'flex',
      gap: '16px',
      padding: '16px',
      fontFamily: 'system-ui, sans-serif',
    }}>
      <div className="panel library-panel" style={{
        background: '#161B22',
        borderRadius: '12px',
        padding: '16px',
        width: '250px',
        border: '1px solid #21262D',
      }}>
        <h2 style={{ fontSize: '12px', textTransform: 'uppercase', letterSpacing: '0.05em', color: '#8B949E' }}>Library</h2>
        <ul style={{ listStyle: 'none', padding: 0 }}>
          <li>photo_001.png</li>
          <li>video_002.mp4</li>
          <li>song_003.wav</li>
        </ul>
      </div>
      <div className="panel preview-panel" style={{
        background: '#161B22',
        borderRadius: '12px',
        padding: '16px',
        flex: 1,
        border: '1px solid #21262D',
      }}>
        <h2 style={{ fontSize: '12px', textTransform: 'uppercase', letterSpacing: '0.05em', color: '#8B949E' }}>Now Viewing</h2>
        <div style={{ background: '#0D1117', borderRadius: '8px', height: '300px', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
          <span style={{ color: '#484F58' }}>No file selected</span>
        </div>
      </div>
      <div className="panel remy-panel" style={{
        background: '#161B22',
        borderRadius: '12px',
        padding: '16px',
        width: '300px',
        border: '1px solid #21262D',
      }}>
        <h2 style={{ fontSize: '12px', textTransform: 'uppercase', letterSpacing: '0.05em', color: '#8B949E' }}>Remy</h2>
        <button style={{
          background: '#1F6FEB',
          color: 'white',
          border: 'none',
          borderRadius: '9999px',
          padding: '10px 24px',
          cursor: 'pointer',
          width: '100%',
          marginTop: '12px',
        }}>Generate</button>
      </div>
    </div>
  );
}
