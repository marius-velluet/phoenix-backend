import { useState, useEffect } from 'react';

// Positions GPS provisoires des 3 nœuds terrain sur le campus
// À mettre à jour avec les vraies positions quand le LOT 1/3 les fournira
export const NODES = [
  { id: 1, lat: 48.8395, lng: 2.5872, label: 'Nœud 1' },
  { id: 2, lat: 48.8391, lng: 2.5878, label: 'Nœud 2' },
  { id: 3, lat: 48.8388, lng: 2.5874, label: 'Nœud 3' },
];

function useAlerts() {
  // État des alertes par nœud : { 1: {alert: 0, batt: 0, hops: 0}, ... }
  const [nodeStates, setNodeStates] = useState(
    Object.fromEntries(NODES.map(n => [n.id, { alert: 0, batt: 0, hops: 0 }]))
  );

  // Historique des 10 dernières alertes pour le dashboard
  const [alertHistory, setAlertHistory] = useState([]);

  // Statut de la connexion WebSocket
  const [wsStatus, setWsStatus] = useState('Déconnecté');

  useEffect(() => {
    // Chargement initial de l'historique via l'API REST
    fetch('http://localhost:3000/api/alerts')
      .then(r => r.json())
      .then(data => {
        if (data.alerts) setAlertHistory(data.alerts.slice(0, 10));
      })
      .catch(err => console.error('Erreur chargement historique :', err));

    // Connexion WebSocket au backend Node.js
    const ws = new WebSocket('ws://localhost:3000');

    ws.onopen = () => {
      console.log('✅ WebSocket connecté');
      setWsStatus('Connecté');
    };

    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      console.log('📨 Alerte WebSocket reçue :', data);

      // Mise à jour de l'état du nœud concerné
      setNodeStates(prev => ({
        ...prev,
        [data.node]: { alert: data.alert, batt: data.batt, hops: data.hops }
      }));

      // Ajout en tête de l'historique (max 10 entrées)
      setAlertHistory(prev => [data, ...prev].slice(0, 10));
    };

    ws.onclose = () => {
      console.log('🔌 WebSocket déconnecté');
      setWsStatus('Déconnecté');
    };

    ws.onerror = (err) => {
      console.error('❌ Erreur WebSocket :', err);
      setWsStatus('Erreur');
    };

    // Nettoyage à la destruction du composant
    return () => ws.close();
  }, []);

  return { nodeStates, alertHistory, wsStatus };
}

export default useAlerts;