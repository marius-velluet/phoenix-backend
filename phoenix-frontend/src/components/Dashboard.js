import React from 'react';

function alertLabel(level) {
  if (level >= 2) return { text: 'Feu avéré', color: '#e74c3c' };
  if (level === 1) return { text: 'Suspicion', color: '#f39c12' };
  return { text: 'RAS', color: '#2ecc71' };
}

function Dashboard({ alertHistory, wsStatus }) {
  return (
    <div style={{
      width: '320px',
      minWidth: '320px',
      background: '#16213e',
      padding: '16px',
      overflowY: 'auto',
      display: 'flex',
      flexDirection: 'column',
      gap: '12px'
    }}>
      {/* Titre */}
      <h2 style={{ color: '#e94560', textAlign: 'center' }}>
        🔥 PHOENIX
      </h2>

      {/* Statut WebSocket */}
      <div style={{
        background: '#0f3460',
        borderRadius: '8px',
        padding: '10px',
        textAlign: 'center'
      }}>
        <span style={{
          color: wsStatus === 'Connecté' ? '#2ecc71' : '#e74c3c'
        }}>
          ● {wsStatus}
        </span>
        <span style={{ color: '#aaa', marginLeft: '8px', fontSize: '12px' }}>
          WebSocket
        </span>
      </div>

      {/* Historique des alertes */}
      <h3 style={{ color: '#aaa', fontSize: '13px' }}>
        DERNIÈRES ALERTES
      </h3>

      {alertHistory.length === 0 ? (
        <p style={{ color: '#555', fontSize: '12px', textAlign: 'center' }}>
          Aucune alerte reçue
        </p>
      ) : (
        alertHistory.map((alert, index) => {
          const label = alertLabel(alert.alert || alert.alert_level);
          return (
            <div key={index} style={{
              background: '#0f3460',
              borderRadius: '8px',
              padding: '10px',
              borderLeft: `4px solid ${label.color}`
            }}>
              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <strong>Nœud {alert.node || alert.node_id}</strong>
                <span style={{ color: label.color, fontSize: '12px' }}>
                  {label.text}
                </span>
              </div>
              <div style={{ color: '#aaa', fontSize: '11px', marginTop: '4px' }}>
                🔋 {alert.batt || alert.battery_voltage}V
                &nbsp;·&nbsp;
                📡 {alert.hops || alert.hop_count} saut(s)
              </div>
              <div style={{ color: '#555', fontSize: '10px', marginTop: '2px' }}>
                {new Date(alert.timestamp).toLocaleTimeString()}
              </div>
            </div>
          );
        })
      )}

      {/* Bouton reset */}
      <button
        onClick={() => window.location.reload()}
        style={{
          marginTop: 'auto',
          background: '#e94560',
          color: 'white',
          border: 'none',
          borderRadius: '8px',
          padding: '10px',
          cursor: 'pointer'
        }}
      >
        Réinitialiser la vue
      </button>
    </div>
  );
}

export default Dashboard;