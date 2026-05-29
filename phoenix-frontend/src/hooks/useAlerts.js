import { useState, useEffect } from 'react';

export const NODES = [
  { id: 1, lat: 48.835417, lng: 2.578168, label: 'Nœud 1' },
  { id: 2, lat: 48.837918, lng: 2.581005, label: 'Nœud 2' },
  { id: 3, lat: 48.840029, lng: 2.580233, label: 'Nœud 3' },
];

function useAlerts() {
  const [nodeStates, setNodeStates] = useState(
    Object.fromEntries(NODES.map(n => [n.id, { alert: 0, batt: 0, hops: 0 }]))
  );
  const [alertHistory, setAlertHistory]   = useState([]);
  const [wsStatus, setWsStatus]           = useState('Déconnecté');
  const [geoJsonLayers, setGeoJsonLayers] = useState([]);

  // Appel FastAPI pour récupérer les polygones GeoJSON
  async function fetchSimulation(nodeId, lat, lon, timestamp) {
    try {
      console.log(`🔥 Appel simulation pour nœud ${nodeId}...`);
      const response = await fetch('http://localhost:8000/simulate', {
        method:  'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          node_id:   nodeId,
          lat:       lat,
          lon:       lon,
          timestamp: timestamp || new Date().toISOString()
        })
      });

      if (!response.ok) throw new Error(`HTTP ${response.status}`);

      const data = await response.json();
      console.log(`✅ GeoJSON reçu — ${data.geojson_polygons.features.length} isochrones`);
      setGeoJsonLayers(data.geojson_polygons.features);

    } catch (error) {
      console.error('❌ Erreur simulation FastAPI :', error);
    }
  }

  useEffect(() => {

    // Chargement initial de l'historique via l'API REST
    fetch('http://localhost:3000/api/alerts')
      .then(r => r.json())
      .then(data => {
        if (data.alerts) setAlertHistory(data.alerts.slice(0, 10));
      })
      .catch(err => console.error('Erreur historique :', err));

    // Connexion WebSocket avec reconnexion automatique
    let ws;
    let reconnectTimeout;

    function connectWebSocket() {
      ws = new WebSocket('ws://localhost:3000');

      ws.onopen = () => {
        console.log('✅ WebSocket connecté');
        setWsStatus('Connecté');
      };

      ws.onclose = () => {
        console.log('🔌 WebSocket déconnecté — reconnexion dans 3s...');
        setWsStatus('Déconnecté');
        // Reconnexion automatique après 3 secondes
        reconnectTimeout = setTimeout(connectWebSocket, 3000);
      };

      ws.onerror = () => {
        setWsStatus('Erreur');
        ws.close();
      };

      ws.onmessage = (event) => {
        const data = JSON.parse(event.data);
        console.log('📨 Alerte WebSocket :', data);

        // Mise à jour de l'état du nœud concerné
        setNodeStates(prev => ({
          ...prev,
          [data.node]: { alert: data.alert, batt: data.batt, hops: data.hops }
        }));

        // Ajout en tête de l'historique (max 10 entrées)
        setAlertHistory(prev => [data, ...prev].slice(0, 10));

        // Appel simulation seulement si alerte réelle (niveau ≥ 1)
        if (data.alert >= 1) {
          const node = NODES.find(n => n.id === data.node);
          if (node) {
            fetchSimulation(node.id, node.lat, node.lng, data.timestamp);
          }
        }
      };
    }

    connectWebSocket();

    // Nettoyage à la destruction du composant
    return () => {
      clearTimeout(reconnectTimeout);
      if (ws) ws.close();
    };

  }, []);

  return { nodeStates, alertHistory, wsStatus, geoJsonLayers, fetchSimulation };
}

export default useAlerts;