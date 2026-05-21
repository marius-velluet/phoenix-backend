const express = require('express')
const mqtt = require('mqtt')

const app = express()

// Connexion au broker MQTT
const mqttClient = mqtt.connect(`mqtt://${process.env.MQTT_HOST}:1883`)

mqttClient.on('connect', () => {
  console.log('✅ Connecté au broker MQTT')
  mqttClient.subscribe('phoenix/alerts')
})

mqttClient.on('message', (topic, message) => {
  console.log('📨 Alerte reçue :', message.toString())
  // La suite viendra ici : InfluxDB + WebSocket
})

// Route de test
app.get('/health', (req, res) => {
  res.json({ status: 'ok', service: 'phoenix-backend' })
})

app.listen(3000, () => {
  console.log('🚀 Serveur démarré sur le port 3000')
})