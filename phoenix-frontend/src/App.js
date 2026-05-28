import React from 'react';
import PhoenixMap from './components/PhoenixMap';
import Dashboard  from './components/Dashboard';
import useAlerts  from './hooks/useAlerts';
import './App.css';

function App() {
  const { nodeStates, alertHistory, wsStatus, geoJsonLayers } = useAlerts();

  return (
    <div style={{ display: 'flex', height: '100vh' }}>
      <Dashboard
        alertHistory={alertHistory}
        wsStatus={wsStatus}
      />
      <PhoenixMap
        nodeStates={nodeStates}
        geoJsonLayers={geoJsonLayers}
      />
    </div>
  );
}

export default App;