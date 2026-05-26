const express = require('express');
const mqtt = require('mqtt');
const { InfluxDB, Point } = require('@influxdata/influxdb-client');
const { WebSocketServer } = require('ws');
const http = require('http');

const app = express();
app.use(express.json());

// ── Configuration InfluxDB ─────────────────────────────────
const influxUrl    = process.env.INFLUXDB_URL    || 'http://influxdb:8086';
const influxToken  = process.env.INFLUXDB_TOKEN  || 'phoenix-token-initial';
const influxOrg    = process.env.INFLUXDB_ORG    || 'phoenix-org';
const influxBucket = process.env.INFLUXDB_BUCKET || 'phoenix-alerts';

const influxClient = new InfluxDB({ url: influxUrl, token: influxToken });
const writeApi     = influxClient.getWriteApi(influxOrg, influxBucket, 'ms');
const queryApi     = influxClient.getQueryApi(influxOrg);

// ── Serveur HTTP (Express) + WebSocket sur le même port ───
// On crée un serveur HTTP manuellement pour y attacher
// à la fois Express et le WebSocket sur le port 3000
const server = http.createServer(app);
const wss = new WebSocketServer({ server });

// Fonction utilitaire pour diffuser à TOUS les clients connectés
function broadcast(data) {
  const payload = JSON.stringify(data);
  wss.clients.forEach(client => {
    // readyState 1 = OPEN = client bien connecté
    if (client.readyState === 1) {
      client.send(payload);
    }
  });
}

// Gestion des connexions WebSocket entrantes
wss.on('connection', (ws) => {
  console.log('🔌 Nouveau client WebSocket connecté');

  // Heartbeat : répond aux pings pour garder la connexion active
  ws.on('pong', () => { ws.isAlive = true; });

  ws.on('close', () => {
    console.log('🔌 Client WebSocket déconnecté');
  });
});

// Heartbeat toutes les 30s pour détecter les clients fantômes
const heartbeatInterval = setInterval(() => {
  wss.clients.forEach(client => {
    if (client.isAlive === false) {
      client.terminate();
      return;
    }
    client.isAlive = false;
    client.ping();
  });
}, 30000);

wss.on('close', () => clearInterval(heartbeatInterval));

// ── Connexion MQTT ─────────────────────────────────────────
const mqttClient = mqtt.connect(
  `mqtt://${process.env.MQTT_HOST || 'mosquitto'}:1883`
);

mqttClient.on('connect', () => {
  console.log('✅ Connecté au broker MQTT');
  mqttClient.subscribe('phoenix/alerts');
});

mqttClient.on('message', (topic, message) => {
  if (topic === 'phoenix/alerts') {
    console.log('📨 Alerte reçue :', message.toString());

    try {
      const data = JSON.parse(message.toString());

      // ── Persistance InfluxDB ───────────────────────────
      const point = new Point('fire_alerts')
        .tag('node_id', data.node.toString())
        .intField('alert_level', data.alert)
        .intField('hop_count', data.hops)
        .floatField('battery_voltage', data.batt)
        .timestamp(data.timestamp ? new Date(data.timestamp) : new Date());

      writeApi.writePoint(point);
      console.log(`💾 Alerte du nœud ${data.node} sauvegardée dans InfluxDB`);

      // ── Diffusion WebSocket temps réel ─────────────────
      // On enrichit le payload avec un timestamp ISO pour le frontend
      const alertPayload = {
        node:      data.node,
        alert:     data.alert,
        hops:      data.hops,
        batt:      data.batt,
        timestamp: new Date().toISOString()
      };
      broadcast(alertPayload);
      console.log(`📡 Alerte diffusée à ${wss.clients.size} client(s) WebSocket`);

    } catch (error) {
      console.error('❌ Erreur traitement :', error);
    }
  }
});

// ── API REST ───────────────────────────────────────────────

// GET /health — test de vie du serveur
app.get('/health', (req, res) => {
  res.json({
    status: 'ok',
    service: 'phoenix-backend',
    websocket_clients: wss.clients.size
  });
});

// GET /api/alerts — historique des 10 dernières alertes
// Paramètres optionnels : ?node=1 pour filtrer par nœud
app.get('/api/alerts', async (req, res) => {
  const nodeFilter = req.query.node;

  // Requête Flux : 24 dernières heures, triées par date décroissante
  let query = `
    from(bucket: "${influxBucket}")
      |> range(start: -24h)
      |> filter(fn: (r) => r._measurement == "fire_alerts")
  `;

  // Filtre optionnel par nœud
  if (nodeFilter) {
    query += `|> filter(fn: (r) => r.node_id == "${nodeFilter}")`;
  }

  query += `
      |> pivot(rowKey: ["_time"], columnKey: ["_field"], valueColumn: "_value")
      |> sort(columns: ["_time"], desc: true)
      |> limit(n: 10)
  `;

  try {
    const results = [];
    await queryApi.collectRows(query, {
      next(row, tableMeta) {
        results.push({
          timestamp:       row._time,
          node_id:         row.node_id,
          alert_level:     row.alert_level,
          hop_count:       row.hop_count,
          battery_voltage: row.battery_voltage
        });
      },
      error(error) {
        throw error;
      },
      complete() {}
    });

    res.json({ count: results.length, alerts: results });

  } catch (error) {
    console.error('❌ Erreur requête InfluxDB :', error);
    res.status(500).json({ error: 'Erreur lors de la récupération des alertes' });
  }
});

// ── Démarrage du serveur ───────────────────────────────────
// Important : on démarre `server` (HTTP) et non `app` (Express)
// pour que WebSocket et Express partagent le même port 3000
server.listen(3000, () => {
  console.log('🚀 Serveur HTTP + WebSocket démarré sur le port 3000');
});

// ── Arrêt propre ───────────────────────────────────────────
const gracefulShutdown = () => {
  console.log('\n🛑 Arrêt détecté. Fermeture des connexions...');
  writeApi.close()
    .then(() => {
      console.log('✨ Buffer InfluxDB vidé proprement.');
      process.exit(0);
    })
    .catch(err => {
      console.error('❌ Erreur fermeture InfluxDB :', err);
      process.exit(1);
    });
};

process.on('SIGINT', gracefulShutdown);
process.on('SIGTERM', gracefulShutdown);