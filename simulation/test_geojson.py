# test_geojson.py
import numpy as np
from grid import create_campus_grid, VEGETATION, ORIGIN_LAT, ORIGIN_LON, GRID_SIZE
from simulation import run_simulation, BURNING, BURNT, INERT
from geojson_export import snapshots_to_geojson

# ── CONFIGURATION DES TESTS ──────────────────────────────────────────────
# Paramètres fixes pour que les tests soient reproductibles
np.random.seed(42)
WIND_SPEED     = 5.0   # m/s
WIND_DIRECTION = 270   # vent venant de l'Ouest → feu pousse vers l'Est
ORIGIN_ROW     = 38
ORIGIN_COL     = 3

# On lance la simulation une seule fois pour tous les tests
print("🔄 Lancement de la simulation de test...")
snapshots = run_simulation(
    origin_row     = ORIGIN_ROW,
    origin_col     = ORIGIN_COL,
    wind_speed     = WIND_SPEED,
    wind_direction = WIND_DIRECTION,
    n_steps        = 30
)
geojson = snapshots_to_geojson(snapshots)
print(f"✅ Simulation OK — {len(snapshots)} snapshots, {len(geojson['features'])} features GeoJSON\n")


# ════════════════════════════════════════════════════════════════════════
# TEST 1 — Les polygones sont bien fermés
# (premier point == dernier point, obligatoire en GeoJSON)
# ════════════════════════════════════════════════════════════════════════
def test_polygones_fermes():
    erreurs = 0
    for feature in geojson["features"]:
        horizon = feature["properties"]["time_horizon"]
        for i, polygon in enumerate(feature["geometry"]["coordinates"]):
            ring = polygon[0]
            if ring[0] != ring[-1]:
                print(f"  ❌ Polygone non fermé : feature {horizon}, polygone {i}")
                print(f"     Premier point : {ring[0]}")
                print(f"     Dernier point : {ring[-1]}")
                erreurs += 1

    if erreurs == 0:
        total = sum(len(f["geometry"]["coordinates"]) for f in geojson["features"])
        print(f"  ✅ TEST 1 PASSÉ — {total} polygones vérifiés, tous fermés correctement")
    else:
        print(f"  ❌ TEST 1 ÉCHOUÉ — {erreurs} polygone(s) non fermé(s)")
    return erreurs == 0


# ════════════════════════════════════════════════════════════════════════
# TEST 2 — Les coordonnées GPS sont dans la bounding box du campus
# (tous les points doivent être autour de Noisy-le-Grand)
# ════════════════════════════════════════════════════════════════════════
def test_dans_bounding_box():
    # Zone acceptable autour du campus ESIEE (±1km)
    LAT_MIN, LAT_MAX = 48.83, 48.85
    LON_MIN, LON_MAX = 2.57, 2.60

    erreurs = 0
    points_verifies = 0

    for feature in geojson["features"]:
        horizon = feature["properties"]["time_horizon"]
        for polygon in feature["geometry"]["coordinates"]:
            for lon, lat in polygon[0]:
                points_verifies += 1
                if not (LAT_MIN < lat < LAT_MAX):
                    print(f"  ❌ Latitude hors campus : {lat} (feature {horizon})")
                    erreurs += 1
                if not (LON_MIN < lon < LON_MAX):
                    print(f"  ❌ Longitude hors campus : {lon} (feature {horizon})")
                    erreurs += 1

    if erreurs == 0:
        print(f"  ✅ TEST 2 PASSÉ — {points_verifies} points GPS vérifiés, tous dans la zone campus")
    else:
        print(f"  ❌ TEST 2 ÉCHOUÉ — {erreurs} point(s) hors campus")
    return erreurs == 0


# ════════════════════════════════════════════════════════════════════════
# TEST 3 — Le feu grandit dans le temps
# (t+15min doit avoir plus de cases que t+5min, etc.)
# ════════════════════════════════════════════════════════════════════════
def test_propagation_croissante():
    cases_par_horizon = {}
    for feature in geojson["features"]:
        minutes  = feature["properties"]["minutes"]
        nb_cases = feature["properties"]["nb_cases"]
        cases_par_horizon[minutes] = nb_cases

    erreurs = 0

    if cases_par_horizon.get(15, 0) <= cases_par_horizon.get(5, 0):
        print(f"  ❌ t+15min ({cases_par_horizon.get(15)} cases) "
              f"n'est pas plus grand que t+5min ({cases_par_horizon.get(5)} cases)")
        erreurs += 1

    if cases_par_horizon.get(30, 0) <= cases_par_horizon.get(15, 0):
        print(f"  ❌ t+30min ({cases_par_horizon.get(30)} cases) "
              f"n'est pas plus grand que t+15min ({cases_par_horizon.get(15)} cases)")
        erreurs += 1

    if erreurs == 0:
        print(f"  ✅ TEST 3 PASSÉ — Propagation croissante confirmée :")
        for minutes in sorted(cases_par_horizon.keys()):
            print(f"     t+{minutes}min → {cases_par_horizon[minutes]} cases "
                  f"({cases_par_horizon[minutes] * 100} m²)")
    else:
        print(f"  ❌ TEST 3 ÉCHOUÉ — {erreurs} problème(s) détecté(s)")
    return erreurs == 0

def test_propagation_sens_vent():
    etat_final = snapshots[-1]

    fire_cells = np.argwhere((etat_final == BURNING) | (etat_final == BURNT))

    if len(fire_cells) == 0:
        print("  ❌ TEST 4 ÉCHOUÉ — Aucune case brûlée dans l'état final")
        return False

    col_moyenne = np.mean(fire_cells[:, 1])

    if col_moyenne > ORIGIN_COL:
        print(f"  ✅ TEST 4 PASSÉ — Le feu s'est propagé vers l'Est comme attendu")
        print(f"     Colonne origine : {ORIGIN_COL}")
        print(f"     Colonne moyenne des cases brûlées : {col_moyenne:.1f}")
    else:
        print(f"  ❌ TEST 4 ÉCHOUÉ — Le feu ne s'est pas propagé dans le sens du vent")
        print(f"     Colonne origine : {ORIGIN_COL}")
        print(f"     Colonne moyenne des cases brûlées : {col_moyenne:.1f}")
        return False
    return True

def test_pas_de_feu_sur_beton():
    grid       = create_campus_grid()
    etat_final = snapshots[-1]

    erreurs = 0
    for r in range(GRID_SIZE):
        for c in range(GRID_SIZE):
            if grid[r, c] != VEGETATION:
                if etat_final[r, c] in [BURNING, BURNT]:
                    print(f"  ❌ Feu sur case non végétalisée : ({r},{c})")
                    erreurs += 1

    if erreurs == 0:
        print(f"  ✅ TEST 5 PASSÉ — Le feu ne traverse aucun bâtiment ni béton")
    else:
        print(f"  ❌ TEST 5 ÉCHOUÉ — {erreurs} case(s) non végétalisée(s) ont brûlé")
    return erreurs == 0


def test_trois_isochrones_presentes():
    horizons_presents = [f["properties"]["time_horizon"] for f in geojson["features"]]
    horizons_attendus = ["t+5min", "t+15min", "t+30min"]

    erreurs = 0
    for h in horizons_attendus:
        if h not in horizons_presents:
            print(f"  ❌ Isochrone manquante : {h}")
            erreurs += 1

    if erreurs == 0:
        print(f"  ✅ TEST 6 PASSÉ — Les 3 isochrones sont présentes : {horizons_presents}")
    else:
        print(f"  ❌ TEST 6 ÉCHOUÉ — {erreurs} isochrone(s) manquante(s)")
    return erreurs == 0

if __name__ == "__main__":
    print("═" * 55)
    print("  PHOENIX — Tests de cohérence géospatiale")
    print("═" * 55 + "\n")

    resultats = {
        "TEST 1 — Polygones fermés"         : test_polygones_fermes(),
        "TEST 2 — Bounding box campus"      : test_dans_bounding_box(),
        "TEST 3 — Propagation croissante"   : test_propagation_croissante(),
        "TEST 4 — Sens du vent"             : test_propagation_sens_vent(),
        "TEST 5 — Pas de feu sur béton"     : test_pas_de_feu_sur_beton(),
        "TEST 6 — 3 isochrones présentes"   : test_trois_isochrones_presentes(),
    }