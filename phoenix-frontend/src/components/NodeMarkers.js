import React from 'react';
import { Marker, Popup } from 'react-leaflet';
import L from 'leaflet';
import { NODES } from '../hooks/useAlerts';

// Couleur selon le niveau d'alerte
function getColor(alertLevel) {
  if (alertLevel >= 2) return '#e74c3c'; // Rouge — Feu avéré
  if (alertLevel === 1) return '#f39c12'; // Orange — Suspicion
  return '#2ecc71';                        // Vert — RAS
}

// Création d'une icône circulaire colorée avec l'API Leaflet
function createIcon(color) {
  return L.divIcon({
    className: '',
    html: `
      <div style="
        width: 20px; height: 20px;
        background: ${color};
        border: 3px solid white;
        border-radius: 50%;
        box-shadow: 0 0 8px ${color};
      "></div>
    `,
    iconSize:   [20, 20],
    iconAnchor: [10, 10],
  });
}

function NodeMarkers({ nodeStates }) {
  // Sécurité : si nodeStates n'est pas encore prêt, on n'affiche rien
  if (!nodeStates) return null;

  return NODES.map(node => {
    const state = nodeStates[node.id] || { alert: 0, batt: 0, hops: 0 };
    const color     = getColor(state.alert);
    const alertText = state.alert >= 2 ? '🔴 Feu avéré'
                    : state.alert === 1 ? '🟠 Suspicion'
                    : '🟢 RAS';

    return (
      <Marker
        key={node.id}
        position={[node.lat, node.lng]}
        icon={createIcon(color)}
      >
        <Popup>
          <strong>{node.label}</strong><br />
          État : {alertText}<br />
          Batterie : {state.batt}V<br />
          Sauts LoRa : {state.hops}
        </Popup>
      </Marker>
    );
  });
}

export default NodeMarkers;