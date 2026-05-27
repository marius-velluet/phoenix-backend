import numpy as np

# Les 8 directions possibles autour d'une cellule (voisinage de Moore)
# (déplacement_ligne, déplacement_colonne, angle_en_degrés)
MOORE_NEIGHBORS = [
    (-1,  0,   0),   # Nord
    (-1,  1,  45),   # Nord-Est
    ( 0,  1,  90),   # Est
    ( 1,  1, 135),   # Sud-Est
    ( 1,  0, 180),   # Sud
    ( 1, -1, 225),   # Sud-Ouest
    ( 0, -1, 270),   # Ouest
    (-1, -1, 315),   # Nord-Ouest
]

def propagation_probability(
    wind_speed: float,
    wind_direction: float,
    cell_direction_deg: float
) -> float:
    """
    Calcule la probabilité que le feu se propage vers une cellule voisine.

    wind_speed         : vitesse du vent en m/s  (vient de ton API_Météo.py)
    wind_direction     : direction d'où VIENT le vent en degrés (0°=Nord, 270°=Ouest)
    cell_direction_deg : direction vers la cellule voisine en degrés

    Retourne une probabilité entre 0.0 et 1.0
    """

    # ── ÉTAPE 1 : Probabilité de base ──────────────────────────────────
    # Sans vent, le feu a quand même 30% de chance de se propager
    # dans n'importe quelle direction (chaleur rayonnante)
    base_prob = 0.3

    # ── ÉTAPE 2 : Direction de propagation du vent ─────────────────────
    # ATTENTION : le vent "vient de" une direction, mais le feu va VERS
    # la direction opposée.
    # Exemple : vent venant de l'Ouest (270°) → feu pousse vers l'Est (90°)
    vent_pousse_vers = (wind_direction + 180) % 360

    # ── ÉTAPE 3 : Angle entre le vent et la direction de la cellule ────
    # On calcule de combien de degrés la cellule voisine est "dans le sens du vent"
    delta = abs(cell_direction_deg - vent_pousse_vers) % 360
    if delta > 180:
        delta = 360 - delta
    # delta = 0°   → cellule exactement dans le sens du vent  (favorable)
    # delta = 90°  → cellule perpendiculaire au vent          (neutre)
    # delta = 180° → cellule exactement contre le vent        (défavorable)

    # ── ÉTAPE 4 : Facteur directionnel ────────────────────────────────
    # cos(0°)   = 1.0  → dans le sens du vent  = facteur max
    # cos(90°)  = 0.0  → perpendiculaire        = facteur neutre
    # cos(180°) = -1.0 → contre le vent         = facteur min
    # On ramène entre 0 et 1 pour avoir une probabilité
    facteur_direction = (np.cos(np.radians(delta)) + 1) / 2

    # ── ÉTAPE 5 : Facteur vitesse ──────────────────────────────────────
    # Plus le vent est fort, plus le feu se propage vite
    # On sature à 10 m/s (au-delà ça ne change plus grand chose)
    # Exemple : vent à 5 m/s  → facteur = 0.5
    #           vent à 10 m/s → facteur = 1.0
    #           vent à 0 m/s  → facteur = 0.0
    facteur_vitesse = min(1.0, wind_speed / 10.0)

    # ── ÉTAPE 6 : Probabilité finale ───────────────────────────────────
    # On combine les deux facteurs avec la probabilité de base
    prob = base_prob + (1 - base_prob) * facteur_direction * facteur_vitesse

    return round(prob, 3)


# ── TEST VISUEL ─────────────────────────────────────────────────────────
if __name__ == "__main__":

    # Simulation avec les vraies données météo du campus
    # (tu peux remplacer par les valeurs que ton API t'a renvoyées)
    wind_speed     = 4.12   # m/s
    wind_direction = 0   # vent venant de l'Ouest → feu pousse vers l'Est

    print(f"💨 Vent : {wind_speed} m/s venant de {wind_direction}°")
    print(f"🔥 Le feu va se propager vers : {(wind_direction + 180) % 360}°  (Est)\n")
    print("Probabilités de propagation vers chaque direction :\n")

    directions_noms = {
        0:   "Nord     ",
        45:  "Nord-Est ",
        90:  "Est      ",
        135: "Sud-Est  ",
        180: "Sud      ",
        225: "Sud-Ouest",
        270: "Ouest    ",
        315: "Nord-Ouest",
    }

    for angle, nom in directions_noms.items():
        prob = propagation_probability(wind_speed, wind_direction, angle)

        # Barre visuelle proportionnelle à la probabilité
        barre = "█" * int(prob * 20)
        print(f"  {nom} ({angle:3}°) : {barre:<20} {prob:.1%}")