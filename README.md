# phoenix-backend
Backend et interface web du projet PHOENIX (ESIEE Paris E3 2025-2026). Reçoit les alertes LoRa des nœuds terrain via MQTT, les persiste dans InfluxDB, et les pousse en temps réel vers un dashboard cartographique React/Leaflet avec simulation de propagation du feu par automate cellulaire.

# 🔥 PHOENIX — LOT 6 : Système d'Information & Web UI

Projet technique de fin d'E3 — ESIEE Paris 2025-2026  
Surveillance temps réel d'un réseau de capteurs incendie LoRa par Edge AI

---

## Vue d'ensemble

Ce dépôt contient le **LOT 6** du projet PHOENIX : la couche système d'information et l'interface web de visualisation. Il reçoit les alertes incendie émises par des nœuds terrain LoRa, les persiste en base de données, et les affiche en temps réel sur une carte interactive avec simulation de propagation du feu.

### Architecture générale

```
[Nœuds terrain DFR1195 + BME688]
        │ LoRa 868 MHz
        ▼
[DFR1195 Gateway — USB]
        │ Port série (JSON)
        ▼
[Script Python — serial_reader.py]     ← LOT 3 (dépendance hardware)
        │ MQTT
        ▼
[Broker Mosquitto]  ──────────────────────────────────┐
        │ MQTT                                         │
        ▼                                             │
[Serveur Node.js / Express]                           │
        │ InfluxDB Write API          WebSocket Push  │
        ▼                                             ▼
[Base de données InfluxDB]         [Frontend React / Leaflet.js]
                                           │
                                           │ HTTP POST /simulate
                                           ▼
                                   [API FastAPI — LOT 5]
                                   (Simulation propagation feu)
```

### Stack technique

| Composant | Technologie | Port |
|---|---|---|
| Broker MQTT | Eclipse Mosquitto 2 | 1883 |
| Base de données | InfluxDB 2.7 | 8086 |
| Serveur backend | Node.js / Express / WebSocket | 3000 |
| API simulation | Python / FastAPI (LOT 5) | 8000 |
| Interface web | React / Leaflet.js | 3001 |

---

## Prérequis

Avant de commencer, installe les outils suivants sur ta machine :

- [Docker Desktop](https://www.docker.com/products/docker-desktop) (Windows/Mac/Linux)
- [Node.js 20 LTS](https://nodejs.org)
- [Python 3.11+](https://www.python.org)
- [Git](https://git-scm.com)

Vérifie les installations dans un terminal :

```bash
docker --version    # Docker version 24.x ou supérieur
node --version      # v20.x.x
npm --version       # 10.x.x
python --version    # Python 3.11.x ou supérieur
```

---

## Installation

### 1. Cloner le dépôt

```bash
git clone https://github.com/ton-compte/phoenix-backend.git
cd phoenix-backend
```

### 2. Configurer les variables d'environnement

Crée un fichier `.env` à la racine du dossier `phoenix-backend/` en copiant le fichier exemple :

```bash
cp .env.example .env
```

Ouvre `.env` et renseigne tes valeurs :

```env
# Token InfluxDB — ne pas modifier si tu utilises la config Docker par défaut
INFLUX_TOKEN=phoenix-token-initial

# Clé API OpenWeatherMap — crée un compte gratuit sur openweathermap.org
OPENWEATHER_API_KEY=ta_clé_openweathermap_ici
```

> **Note :** La clé OpenWeatherMap est optionnelle pour les tests. Si elle est absente ou invalide, la simulation utilisera automatiquement un vent par défaut (3 m/s, direction 0°).

### 3. Installer les dépendances du frontend

```bash
cd phoenix-frontend
npm install
cd ..
```

---

## Lancement

Le projet se lance en deux étapes dans deux terminaux séparés.

### Terminal 1 — Démarrer le backend (Docker)

Depuis le dossier `phoenix-backend/` :

```bash
docker-compose up --build
```

> Le flag `--build` est nécessaire uniquement au premier lancement ou après une modification du code backend. Pour les lancements suivants, utilise simplement `docker-compose up`.

Attends que les quatre services soient démarrés. Tu dois voir dans les logs :

```
mosquitto     | mosquitto version 2.x starting
influxdb      | ts=... msg="Listening" log_level=info
node-backend  | ✅ Connecté au broker MQTT
node-backend  | 🚀 Serveur HTTP + WebSocket démarré sur le port 3000
fastapi-sim   | INFO: Application startup complete.
fastapi-sim   | INFO: Uvicorn running on http://0.0.0.0:8000
```

### Terminal 2 — Démarrer le frontend (React)

Depuis le dossier `phoenix-frontend/` :

```bash
npm start
```

L'interface s'ouvre automatiquement dans ton navigateur sur :

```
http://localhost:3001
```

---

## Vérification du bon fonctionnement

### Vérifier les services Docker

```bash
docker ps
```

Tu dois voir 4 conteneurs avec le statut `Up` : `mosquitto`, `influxdb`, `node-backend`, `fastapi-sim`.

### Vérifier les endpoints

| URL | Résultat attendu |
|---|---|
| `http://localhost:3000/health` | `{"status":"ok","service":"phoenix-backend"}` |
| `http://localhost:8000/health` | `{"status":"ok","service":"PHOENIX Simulation API"}` |
| `http://localhost:8000/test` | Résultats de simulation de test |
| `http://localhost:8086` | Interface web InfluxDB (login: `admin` / `phoenix123`) |
| `http://localhost:3001` | Interface cartographique React |

### Tester manuellement une alerte

Pour simuler une alerte sans avoir le matériel physique, publie un message MQTT de test.

**Sous Windows (cmd.exe) :**

```cmd
docker exec -it mosquitto mosquitto_pub -h localhost -t phoenix/alerts -m "{""node"":1,""alert"":2,""hops"":1,""batt"":3.85}"
```

**Sous Linux / Mac :**

```bash
docker exec -it mosquitto mosquitto_pub -h localhost -t phoenix/alerts -m '{"node":1,"alert":2,"hops":1,"batt":3.85}'
```

**Résultat attendu dans les logs Node.js :**

```
node-backend  | 📨 Alerte reçue : {"node":1,"alert":2,"hops":1,"batt":3.85}
node-backend  | 💾 Alerte du nœud 1 sauvegardée dans InfluxDB
node-backend  | 📡 Alerte diffusée à 1 client(s) WebSocket
```

**Résultat attendu dans l'interface :**
- Le marqueur du nœud 1 passe au **rouge**
- L'alerte apparaît dans le **dashboard** à gauche
- **3 polygones colorés** de propagation apparaissent sur la carte (rouge t+5min, orange t+15min, jaune t+30min)

---

## Structure du projet

```
phoenix-backend/                  ← Backend et infrastructure Docker
├── mosquitto/
│   └── mosquitto.conf            ← Configuration du broker MQTT
├── backend/
│   ├── Dockerfile                ← Image Docker Node.js
│   ├── package.json              ← Dépendances Node.js
│   └── index.js                  ← Serveur Express + WebSocket + MQTT + InfluxDB
├── simulation/                   ← API FastAPI de simulation (LOT 5)
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── main.py                   ← Point d'entrée FastAPI
│   ├── API_Météo.py              ← Appel OpenWeatherMap
│   ├── grid.py                   ← Modélisation grille campus
│   ├── propagation.py            ← Algorithme propagation feu
│   ├── simulation.py             ← Automate cellulaire
│   ├── geojson_export.py         ← Export isochrones GeoJSON
│   └── test_geojson.py           ← Tests de cohérence géospatiale
├── docker-compose.yml            ← Orchestration des 4 services Docker
├── .env                          ← Variables d'environnement (non versionné)
├── .env.example                  ← Modèle de configuration
└── .gitignore

phoenix-frontend/                 ← Interface web React
├── src/
│   ├── components/
│   │   ├── PhoenixMap.js         ← Carte Leaflet principale
│   │   ├── NodeMarkers.js        ← Marqueurs dynamiques des nœuds
│   │   ├── FireLayers.js         ← Affichage polygones GeoJSON
│   │   └── Dashboard.js          ← Panneau latéral alertes
│   ├── hooks/
│   │   └── useAlerts.js          ← Hook WebSocket + état des alertes
│   ├── App.js                    ← Composant racine
│   └── index.js                  ← Point d'entrée React
└── .env                          ← PORT=3001
```

---

## Configuration avancée

### Modifier la position des nœuds sur la carte

Dans `phoenix-frontend/src/hooks/useAlerts.js`, modifie le tableau `NODES` :

```javascript
export const NODES = [
  { id: 1, lat: 48.8395, lng: 2.5872, label: 'Nœud 1' },
  { id: 2, lat: 48.8391, lng: 2.5878, label: 'Nœud 2' },
  { id: 3, lat: 48.8388, lng: 2.5874, label: 'Nœud 3' },
];
```

Les coordonnées GPS s'obtiennent par clic droit sur Google Maps.

### Modifier la zone de simulation

Dans `phoenix-backend/simulation/grid.py` :

```python
ORIGIN_LAT = 48.84013163789159   # Coin haut-gauche de la grille
ORIGIN_LON = 2.5837427716557353
GRID_SIZE   = 50                 # Nombre de cases (50 = zone 500m × 500m)
CELL_SIZE_M = 10                 # Taille d'une case en mètres
```

Pour visualiser la grille dans le terminal :

```bash
docker exec -it fastapi-sim python grid.py
```

---

## Commandes utiles

```bash
# Démarrer tous les services
docker-compose up

# Arrêter tous les services
docker-compose down

# Voir les logs en temps réel
docker-compose logs -f

# Voir les logs d'un service spécifique
docker-compose logs -f node-backend
docker-compose logs -f fastapi-sim

# Rebuilder après modification du code backend
docker-compose up --build

# Lister les conteneurs actifs
docker ps

# Accéder au terminal d'un conteneur
docker exec -it fastapi-sim bash
docker exec -it node-backend sh
```

---

## Dépannage

**Docker Desktop n'est pas lancé**
```
unable to get image: failed to connect to the docker API
```
Lance Docker Desktop et attends que l'icône en bas à gauche indique "Engine running".

**Port déjà utilisé**
```
Error: bind: address already in use
```
Un autre service utilise le port 3000 ou 8086. Arrête les autres conteneurs avec `docker-compose down` ou redémarre Docker Desktop.

**React démarre sur le port 3000 au lieu de 3001**  
Vérifie que le fichier `phoenix-frontend/.env` contient bien `PORT=3001`.

**Les polygones GeoJSON n'apparaissent pas**  
Vérifie que le conteneur `fastapi-sim` est bien démarré avec `docker ps` et que `http://localhost:8000/health` répond correctement.

**Erreur 401 sur l'API météo**  
Ta clé OpenWeatherMap est invalide ou non activée. Les clés peuvent mettre jusqu'à 2h à être activées après la création du compte. La simulation fonctionne quand même avec un vent par défaut.

---

## Auteur

LOT 6 développé par **[Marius VELLUET et Valentin POCLET]** — ESIEE Paris, promotion E3 2025-2026  
Projet PHOENIX — Réseau Maillé LoRa de Détection Ultra-Précoce d'Incendie par Edge AI
