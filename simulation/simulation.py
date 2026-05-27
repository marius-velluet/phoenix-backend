# simulation.py
import numpy as np
from grid import create_campus_grid, VEGETATION
from propagation import propagation_probability, MOORE_NEIGHBORS

# ── ÉTATS POSSIBLES D'UNE CELLULE ───────────────────────────────────────
INTACT  = 0   # végétation non brûlée  → peut s'enflammer
BURNING = 1   # en feu en ce moment    → va se propager
BURNT   = 2   # cendres                → ne brûle plus
INERT   = 3   # béton/bâtiment         → ne brûle jamais

def run_simulation(
    origin_row: int,
    origin_col: int,
    wind_speed: float,
    wind_direction: float,
    n_steps: int = 30
) -> list[np.ndarray]:
    """
    Lance la simulation de propagation du feu.

    origin_row/col  : case de départ du feu sur la grille
    wind_speed      : vitesse du vent en m/s (depuis API_Météo.py)
    wind_direction  : direction du vent en degrés (depuis API_Météo.py)
    n_steps         : nombre de minutes simulées (défaut = 30 minutes)

    Retourne la liste des états de la grille à chaque minute.
    """

    # ── ÉTAPE 1 : Préparer la grille de départ ──────────────────────────
    # On récupère la grille du campus (0=asphalte, 1=végétation, 2=bâtiment)
    base_grid = create_campus_grid()
    rows, cols = base_grid.shape

    # On convertit en états de simulation :
    # végétation → INTACT (peut brûler)
    # tout le reste → INERT (ne brûle pas)
    state = np.where(base_grid == VEGETATION, INTACT, INERT)

    # ── ÉTAPE 2 : Allumer le feu à l'origine ────────────────────────────
    if state[origin_row, origin_col] == INTACT:
        # La case d'origine est végétalisée → on l'allume directement
        state[origin_row, origin_col] = BURNING
    else:
        # La case d'origine est du béton → on cherche
        # la case végétalisée la plus proche
        print("⚠️  Case d'origine non végétalisée, recherche de la plus proche...")
        veg_cells = np.argwhere(state == INTACT)
        distances = np.sqrt(
            (veg_cells[:, 0] - origin_row) ** 2 +
            (veg_cells[:, 1] - origin_col) ** 2
        )
        nearest = veg_cells[np.argmin(distances)]
        state[nearest[0], nearest[1]] = BURNING
        print(f"🔥 Feu allumé à la case végétalisée la plus proche : {nearest}")

    # On garde une photo de la grille à chaque minute
    snapshots = [state.copy()]

    # ── ÉTAPE 3 : Boucle principale (1 itération = 1 minute simulée) ────
    for step in range(n_steps):
        new_state = state.copy()

        # On trouve toutes les cases actuellement en feu
        burning_cells = np.argwhere(state == BURNING)

        # Si plus rien ne brûle → on arrête la simulation
        if len(burning_cells) == 0:
            print(f"🏁 Feu éteint après {step} minutes")
            break

        for (r, c) in burning_cells:

            # La case en feu devient cendre au prochain tick
            new_state[r, c] = BURNT

            # On regarde ses 8 voisines
            for (dr, dc, angle) in MOORE_NEIGHBORS:
                nr = r + dr
                nc = c + dc

                # Vérification qu'on ne sort pas de la grille
                if not (0 <= nr < rows and 0 <= nc < cols):
                    continue

                # On ne propage que vers la végétation intacte
                if state[nr, nc] != INTACT:
                    continue

                # Calcul de la probabilité de propagation
                prob = propagation_probability(wind_speed, wind_direction, angle)

                # Tirage au sort → le feu se propage ou pas
                if np.random.random() < prob:
                    new_state[nr, nc] = BURNING

        # On sauvegarde l'état de cette minute
        state = new_state
        snapshots.append(state.copy())

    return snapshots


def afficher_simulation(snapshots: list[np.ndarray], minutes: list[int] = [0, 5, 15, 30]):
    """
    Affiche la grille dans le terminal à plusieurs moments clés.
    """
    symboles = {
        INTACT:  "🌿",   # végétation saine
        BURNING: "🔥",   # en feu
        BURNT:   "⬛",   # cendres
        INERT:   "░ ",   # béton/bâtiment
    }

    for minute in minutes:
        # On prend le snapshot le plus proche de la minute demandée
        idx = min(minute, len(snapshots) - 1)
        snap = snapshots[idx]

        # Comptage des cases
        n_burning = np.sum(snap == BURNING)
        n_burnt   = np.sum(snap == BURNT)
        n_intact  = np.sum(snap == INTACT)

        print(f"\n{'═' * 55}")
        print(f"  ⏱️  t = {minute} minutes")
        print(f"  🔥 En feu : {n_burning} cases  |  "
              f"⬛ Brûlées : {n_burnt}  |  "
              f"🌿 Intactes : {n_intact}")
        print(f"{'═' * 55}")

        for row in snap:
            print("".join(symboles[cell] for cell in row))


# ── TEST ─────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    from API_Météo import get_wind_data

    print("═" * 55)
    print("  PHOENIX — Simulation de propagation du feu")
    print("═" * 55)

    # 1. Récupération des vraies données météo du campus
    print("\n📡 Récupération météo en cours...")
    wind = get_wind_data(48.84013163789159, 2.5837427716557353)

    # 2. Point de départ du feu : case (38, 3) = zone végétalisée sud-ouest
    origin_row, origin_col = 40, 2
    print(f"\n🔥 Départ du feu : case ({origin_row}, {origin_col})")
    print(f"💨 Vent : {wind['vitesse_ms']} m/s, direction {wind['direction']}°\n")

    # 3. Lancement de la simulation sur 30 minutes
    np.random.seed(42)   # seed fixe → résultat reproductible
    snapshots = run_simulation(
        origin_row    = origin_row,
        origin_col    = origin_col,
        wind_speed    = wind["vitesse_ms"],
        wind_direction= wind["direction"],
        n_steps       = 30
    )

    # 4. Affichage à t=0, t=5, t=15 et t=30 minutes
    afficher_simulation(snapshots, minutes=[0, 5, 15, 30])

    print(f"\n✅ Simulation terminée — {len(snapshots)} snapshots générés")
    print("   → Prêt pour geojson_export.py")