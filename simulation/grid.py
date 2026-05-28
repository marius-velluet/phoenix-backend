# grid.py
import numpy as np

# Résolution de la grille
GRID_SIZE   = 50        # 50×50 cases = zone de 500m × 500m
CELL_SIZE_M = 10        # chaque case = 10 mètres

# Coordonnées GPS de ta forêt (à ajuster selon l'emplacement réel)
ORIGIN_LAT = 48.84013163789159
ORIGIN_LON = 2.5837427716557353

# Types de cellules — on garde BETON et BATIMENT au cas où
# mais la grille n'en contient plus
BETON      = 0
VEGETATION = 1
BATIMENT   = 2

def create_campus_grid() -> np.ndarray:
    """
    Grille 50×50 représentant une zone forestière.
    100% végétation — aucun obstacle pour le feu.
    """
    grid = np.ones((GRID_SIZE, GRID_SIZE), dtype=np.int8)
    return grid


def grid_to_gps(row: int, col: int) -> tuple[float, float]:
    """Convertit une position grille en coordonnées GPS."""
    lat = ORIGIN_LAT - row * (CELL_SIZE_M / 111320)
    lon = ORIGIN_LON + col * (CELL_SIZE_M / (111320 * np.cos(np.radians(ORIGIN_LAT))))
    return lat, lon


def gps_to_grid(lat: float, lon: float) -> tuple[int, int]:
    """Convertit des coordonnées GPS en position grille."""
    row = int((ORIGIN_LAT - lat) * 111320 / CELL_SIZE_M)
    col = int((lon - ORIGIN_LON) * 111320 * np.cos(np.radians(ORIGIN_LAT)) / CELL_SIZE_M)
    row = np.clip(row, 0, GRID_SIZE - 1)
    col = np.clip(col, 0, GRID_SIZE - 1)
    return int(row), int(col)


# Visualisation rapide dans le terminal
if __name__ == "__main__":
    grid = create_campus_grid()

    symboles = {0: "░", 1: "🌿", 2: "█"}
    print("Carte de la forêt (🌿=végétation)\n")
    for row in grid:
        print(" ".join(symboles[cell] for cell in row))

    print(f"\nGrille : {GRID_SIZE}×{GRID_SIZE} cases de {CELL_SIZE_M}m")
    print(f"Végétation : {np.sum(grid == VEGETATION)} cases")
    print(f"Bâtiments  : {np.sum(grid == BATIMENT)} cases")
    print(f"Béton      : {np.sum(grid == BETON)} cases")