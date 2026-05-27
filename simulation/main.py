# main.py
import time
import numpy as np
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from API_Météo import get_wind_data
from grid import gps_to_grid
from simulation import run_simulation
from geojson_export import snapshots_to_geojson

# ── INITIALISATION FASTAPI ───────────────────────────────────────────────
app = FastAPI(
    title="PHOENIX — API Simulation de Propagation",
    description="Reçoit une alerte feu et retourne les isochrones GeoJSON",
    version="1.0.0"
)

# ── CORS : autorise le frontend React à appeler cette API ────────────────
# Sans ça, le navigateur bloque les requêtes venant de React
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── MODÈLE DE LA REQUÊTE ENTRANTE ───────────────────────────────────────
# C'est ce que React envoie quand une alerte est détectée
class SimulationRequest(BaseModel):
    node_id:   int      # ID du nœud qui a détecté le feu (1, 2 ou 3)
    lat:       float    # latitude GPS du nœud
    lon:       float    # longitude GPS du nœud
    timestamp: str      # horodatage de l'alerte

# ── ENDPOINT PRINCIPAL ───────────────────────────────────────────────────
@app.post("/simulate")
def simulate(req: SimulationRequest):
    """
    Reçoit une alerte feu et retourne les isochrones GeoJSON.
    Appelé automatiquement par le frontend React à chaque alerte.
    """
    start = time.time()
    print(f"\n🚨 Alerte reçue — Nœud {req.node_id} à ({req.lat}, {req.lon})")

    # ── ÉTAPE 1 : Récupération météo ─────────────────────────────────────
    print("📡 Récupération météo...")
    wind = get_wind_data(req.lat, req.lon)
    print(f"💨 Vent : {wind['vitesse_ms']} m/s, direction {wind['direction']}°")

    # ── ÉTAPE 2 : Conversion GPS → case grille ───────────────────────────
    row, col = gps_to_grid(req.lat, req.lon)
    print(f"🗺️  Case grille : ({row}, {col})")

    # ── ÉTAPE 3 : Simulation ─────────────────────────────────────────────
    print("🔥 Lancement simulation...")
    try:
        np.random.seed(42)
        snapshots = run_simulation(
            origin_row     = row,
            origin_col     = col,
            wind_speed     = wind["vitesse_ms"],
            wind_direction = wind["direction"],
            n_steps        = 30
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    # ── ÉTAPE 4 : Export GeoJSON ─────────────────────────────────────────
    print("🗺️  Génération GeoJSON...")
    geojson = snapshots_to_geojson(snapshots)

    elapsed = round(time.time() - start, 2)
    print(f"✅ Réponse prête en {elapsed}s")

    return {
        "status":            "alert",
        "node_id":           req.node_id,
        "timestamp":         req.timestamp,
        "geojson_polygons":  geojson,
        "simulation_time_s": elapsed,
        "wind_used":         wind,
        "origin_grid":       {"row": row, "col": col},
        "isochrones_summary": [
            {
                "horizon":   f["properties"]["time_horizon"],
                "nb_cases":  f["properties"]["nb_cases"],
                "surface_m2": f["properties"]["surface_m2"],
                "color":     f["properties"]["color"]
            }
            for f in geojson["features"]
        ]
    }


# ── ENDPOINT DE SANTÉ ────────────────────────────────────────────────────
# Permet à LOT 6 de vérifier que l'API est bien démarrée
@app.get("/health")
def health():
    return {"status": "ok", "service": "PHOENIX Simulation API"}


# ── ENDPOINT DE TEST SANS HARDWARE ──────────────────────────────────────
# Simule une alerte depuis le campus ESIEE — utile pour tester sans nœuds
@app.get("/test")
def test_simulation():
    """
    Lance une simulation de test avec les coordonnées du campus ESIEE.
    Accessible directement depuis le navigateur.
    """
    from API_Météo import get_wind_data
    wind = get_wind_data(48.8399, 2.5878)
    np.random.seed(42)
    snapshots = run_simulation(
        origin_row     = 38,
        origin_col     = 3,
        wind_speed     = wind["vitesse_ms"],
        wind_direction = wind["direction"],
        n_steps        = 30
    )
    geojson = snapshots_to_geojson(snapshots)
    return {
        "status":  "test_ok",
        "message": "Simulation de test réussie",
        "wind":    wind,
        "isochrones": [
            {
                "horizon":    f["properties"]["time_horizon"],
                "nb_cases":   f["properties"]["nb_cases"],
                "surface_m2": f["properties"]["surface_m2"]
            }
            for f in geojson["features"]
        ]
    }