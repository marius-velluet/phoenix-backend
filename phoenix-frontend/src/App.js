import React from 'react';
import PhoenixMap from './components/PhoenixMap';
import Dashboard  from './components/Dashboard';
import useAlerts, { NODES } from './hooks/useAlerts';
import './App.css';

function App() {
  const { nodeStates, alertHistory, wsStatus, geoJsonLayers, fetchSimulation } = useAlerts();

  // Fonction appelée quand l'utilisateur clique sur une alerte du dashboard
  function handleAlertClick(alert) {
    const nodeId = alert.node || alert.node_id;
    const node   = NODES.find(n => n.id === parseInt(nodeId));
    if (node) {
      fetchSimulation(node.id, node.lat, node.lng, alert.timestamp);
    }
  }

  return (
    <div style={{ display: 'flex', height: '100vh' }}>
      <Dashboard
        alertHistory={alertHistory}
        wsStatus={wsStatus}
        onAlertClick={handleAlertClick}
      />
      <PhoenixMap
        nodeStates={nodeStates}
        geoJsonLayers={geoJsonLayers}
      />
    </div>
  );
}

export default App;