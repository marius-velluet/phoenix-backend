# geojson_export.py
import numpy as np
import json
from grid import grid_to_gps
from simulation import BURNING, BURNT

# ── CONFIGURATION DES ISOCHRONES ────────────────────────────────────────
# On génère 3 "photos" de la propagation du feu dans le temps
ISOCHRONES = {
    5:  {"label": "t+5min",  "color": "#FF0000"},  # rouge  → danger immédiat
    15: {"label": "t+15min", "color": "#FF8C00"},  # orange → danger proche
    30: {"label": "t+30min", "color": "#FFD700"},  # jaune  → zone à risque
}

def snapshots_to_geojson(snapshots: list[np.ndarray]) -> dict:
    """
    Convertit les snapshots de simulation en FeatureCollection GeoJSON.
    Chaque isochrone = un polygone sur la carte Leaflet.

    Un fichier GeoJSON c'est juste un format standard pour
    représenter des formes géographiques — c'est ce que
    Leaflet.js sait lire et afficher sur une carte web.
    """

    features = []

    for minutes, config in ISOCHRONES.items():

        # ── ÉTAPE 1 : Récupérer le bon snapshot ─────────────────────────
        # On prend la photo de la grille au bon moment
        idx  = min(minutes, len(snapshots) - 1)
        snap = snapshots[idx]

        # ── ÉTAPE 2 : Trouver toutes les cases touchées par le feu ──────
        # On prend les cases EN FEU et les cases déjà BRÛLÉES
        fire_cells = np.argwhere((snap == BURNING) | (snap == BURNT))

        if len(fire_cells) == 0:
            continue  # pas de feu à ce moment → on saute

        # ── ÉTAPE 3 : Convertir chaque case en carré GPS ─────────────────
        # Chaque case de la grille devient un petit carré
        # de 10m × 10m en coordonnées GPS réelles
        polygons = []
        for (r, c) in fire_cells:

            # Centre de la case en GPS
            lat, lon = grid_to_gps(r, c)

            # On crée un carré de ~10m autour du centre
            # 0.00005 degrés ≈ 5 mètres → carré de 10m
            d = 0.00005

            # Les 4 coins du carré + fermeture (1er point = dernier point)
            # C'est obligatoire dans le format GeoJSON
            carre = [[
                [lon - d, lat + d],   # coin haut-gauche
                [lon + d, lat + d],   # coin haut-droite
                [lon + d, lat - d],   # coin bas-droite
                [lon - d, lat - d],   # coin bas-gauche
                [lon - d, lat + d],   # fermeture = retour au départ
            ]]
            polygons.append(carre)

        # ── ÉTAPE 4 : Construire la Feature GeoJSON ──────────────────────
        # Une Feature GeoJSON c'est : propriétés + géométrie
        feature = {
            "type": "Feature",
            "properties": {
                "time_horizon": config["label"],
                "minutes":      minutes,
                "color":        config["color"],
                "nb_cases":     len(fire_cells),
                "surface_m2":   len(fire_cells) * 100,  # chaque case = 10m×10m = 100m²
            },
            "geometry": {
                "type":        "MultiPolygon",
                "coordinates": polygons
            }
        }
        features.append(feature)

    # ── ÉTAPE 5 : Assembler la FeatureCollection ─────────────────────────
    # C'est le format final que Leaflet.js va recevoir et afficher
    geojson = {
        "type":     "FeatureCollection",
        "features": features
    }

    return geojson


def sauvegarder_geojson(geojson: dict, fichier: str = "propagation.geojson"):
    """
    Sauvegarde le GeoJSON dans un fichier lisible.
    Tu peux l'ouvrir sur geojson.io pour vérifier visuellement.
    """
    with open(fichier, "w", encoding="utf-8") as f:
        json.dump(geojson, f, indent=2, ensure_ascii=False)
    print(f"💾 Fichier sauvegardé : {fichier}")


# ── TEST ──────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    from API_Météo import get_wind_data
    from simulation import run_simulation

    print("═" * 55)
    print("  PHOENIX — Export GeoJSON des isochrones")
    print("═" * 55)

    # 1. Météo réelle
    print("\n📡 Récupération météo...")
    wind = get_wind_data(48.84013163789159, 2.5837427716557353)

    # 2. Simulation
    print("\n🔥 Lancement simulation...")
    np.random.seed(42)
    snapshots = run_simulation(
        origin_row     = 38,
        origin_col     = 3,
        wind_speed     = wind["vitesse_ms"],
        wind_direction = wind["direction"],
        n_steps        = 30
    )

    # 3. Conversion en GeoJSON
    print("\n🗺️  Conversion en GeoJSON...")
    geojson = snapshots_to_geojson(snapshots)

    # 4. Affichage du résumé
    print("\n📊 Résultats :\n")
    for feature in geojson["features"]:
        p = feature["properties"]
        print(f"  ⏱️  {p['time_horizon']:<10} → "
              f"{p['nb_cases']:>4} cases brûlées  "
              f"({p['surface_m2']} m²)")

    # 5. Sauvegarde dans un fichier
    sauvegarder_geojson(geojson)

    # 6. Aperçu de la structure GeoJSON
    print("\n📋 Structure du fichier GeoJSON généré :")
    print(f"  Type         : {geojson['type']}")
    print(f"  Nb features  : {len(geojson['features'])}")
    print(f"  1ère feature : {geojson['features'][0]['properties']}")

    print("\n✅ GeoJSON généré avec succès !")
    print("   → Ouvre propagation.geojson sur geojson.io pour vérifier visuellement")