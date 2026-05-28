import { useEffect } from 'react';
import { useMap } from 'react-leaflet';
import L from 'leaflet';

function FireLayers({ geoJsonLayers }) {
  const map = useMap();

  useEffect(() => {
    // On supprime les anciennes couches GeoJSON avant d'en ajouter de nouvelles
    map.eachLayer(layer => {
      if (layer._isFireLayer) {
        map.removeLayer(layer);
      }
    });

    if (!geoJsonLayers || geoJsonLayers.length === 0) return;

    // On ajoute chaque isochrone sur la carte
    geoJsonLayers.forEach(feature => {
      const color   = feature.properties.color;
      const horizon = feature.properties.time_horizon;

      const layer = L.geoJSON(feature, {
        style: {
          color:       color,
          fillColor:   color,
          fillOpacity: 0.3,
          weight:      2,
          opacity:     0.8,
        }
      });

      // Popup au clic sur un polygone
      layer.bindPopup(`
        <strong>🔥 ${horizon}</strong><br/>
        Surface : ${feature.properties.surface_m2} m²<br/>
        Cases brûlées : ${feature.properties.nb_cases}
      `);

      // Marqueur custom pour identifier la couche et pouvoir la supprimer
      layer._isFireLayer = true;
      layer.addTo(map);
    });

  }, [geoJsonLayers, map]);

  return null; // Ce composant ne rend rien visuellement, il agit sur la carte
}

export default FireLayers;