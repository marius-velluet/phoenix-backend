const express = require('express');
const mqtt = require('mqtt');
// 1. Import du client officiel InfluxDB
const { InfluxDB, Point } = require('@influxdata/influxdb-client');

const app = express();

// 2. Configuration d'InfluxDB via les variables d'environnement de la stack Docker
const influxUrl = process.env.INFLUXDB_URL || 'http://influxdb:8086';
const influxToken = process.env.INFLUXDB_TOKEN || 'votre_token_secret';
const influxOrg = process.env.INFLUXDB_ORG || 'phoenix-org';
const influxBucket = process.env.INFLUXDB_BUCKET || 'phoenix-alerts';

const influxClient = new InfluxDB({ url: influxUrl, token: influxToken });
// Option 'ms' car les paquets du script Python incluront un timestamp Unix en millisecondes
const writeApi = influxClient.getWriteApi(influxOrg, influxBucket, 'ms'); 

// Connexion au broker MQTT
const mqttClient = mqtt.connect(`mqtt://${process.env.MQTT_HOST || 'mosquitto'}:1883`);

mqttClient.on('connect', () => {
  console.log('✅ Connecté au broker MQTT');
  mqttClient.subscribe('phoenix/alerts');
});

// 3. Modification du callback de réception pour la persistance
mqttClient.on('message', (topic, message) => {
  if (topic === 'phoenix/alerts') {
    console.log('📨 Alerte reçue :', message.toString());

    try {
      // Parsing du payload JSON envoyé par le script de conversion (8.2.3)
      const data = JSON.parse(message.toString());

      // Création du point avec la structure définie dans les critères d'acceptation (8.3.1)
      const point = new Point('fire_alerts')
        .tag('node_id', data.node.toString()) // Tag pour indexer et filtrer par nœud
        .intField('alert_level', data.alert)  // Intensité de l'alerte
        .intField('hop_count', data.hops)     // Nombre de sauts réseau LoRa
        .floatField('battery_voltage', data.batt) // Tension de la batterie LiPo
        // Si le script Python fournit un timestamp, on l'utilise, sinon heure du serveur
        .timestamp(data.timestamp ? new Date(data.timestamp) : new Date());

      // Écriture du point dans le buffer InfluxDB
      writeApi.writePoint(point);
      console.log(`💾 Alerte du nœud ${data.node} sauvegardée dans InfluxDB`);

      // TODO 8.3.2 : Diffusion WebSocket (wss.broadcast...) viendra s'insérer ici !

    } catch (error) {
      console.error('❌ Erreur lors du traitement ou de l écriture InfluxDB :', error);
    }
  }
});

// Route de test
app.get('/health', (req, res) => {
  res.json({ status: 'ok', service: 'phoenix-backend' });
});

app.listen(3000, () => {
  console.log('🚀 Serveur démarré sur le port 3000');
});

// 4. Sécurité : Vidage propre du buffer InfluxDB en cas d'arrêt du conteneur (SIGINT/SIGTERM)
const gracefulShutdown = () => {
  console.log('\n🛑 Arrêt du serveur détecté. Fermeture des connexions...');
  writeApi.close()
    .then(() => {
      console.log('✨ Buffer InfluxDB vidé et API fermée proprement.');
      process.exit(0);
    })
    .catch((err) => {
      console.error('Erreur lors de la fermeture d InfluxDB :', err);
      process.exit(1);
    });
};

process.on('SIGINT', gracefulShutdown);
process.on('SIGTERM', gracefulShutdown);