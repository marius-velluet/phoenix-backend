import React from 'react';
import { MapContainer, TileLayer } from 'react-leaflet';
import NodeMarkers from './NodeMarkers';

const CAMPUS_CENTER = [48.8393, 2.5874];
const CAMPUS_ZOOM   = 17;

function PhoenixMap({ nodeStates }) {
  return (
    <MapContainer
      center={CAMPUS_CENTER}
      zoom={CAMPUS_ZOOM}
      style={{ width: '100%', height: '100vh' }}
    >
      <TileLayer
        url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        attribution='&copy; OpenStreetMap contributors'
      />
      <NodeMarkers nodeStates={nodeStates} />
    </MapContainer>
  );
}

export default PhoenixMap;