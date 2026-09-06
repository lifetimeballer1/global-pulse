/** Interactive World Map (Leaflet) */

import { getState } from '../core/state.js';
import { CONFIG } from '../core/config.js';
import { escapeHtml } from '../core/utils.js';

let map = null;
let layerGroups = {};

export function initMap() {
  const container = document.getElementById('mapContainer');
  if (!container || map) return;

  map = L.map(container, {
    center: CONFIG.mapDefaultCenter,
    zoom: CONFIG.mapDefaultZoom,
    zoomControl: true,
    attributionControl: true
  });

  L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png', {
    attribution: '&copy; OpenStreetMap &copy; CARTO',
    subdomains: 'abcd',
    maxZoom: 19
  }).addTo(map);

  layerGroups = {
    conflicts: L.layerGroup().addTo(map),
    hazards: L.layerGroup().addTo(map),
    strategic: L.layerGroup().addTo(map)
  };

  // Layer toggle buttons
  document.querySelectorAll('[data-layer]').forEach(btn => {
    btn.addEventListener('click', () => {
      const key = btn.dataset.layer;
      if (!layerGroups[key]) return;
      if (map.hasLayer(layerGroups[key])) {
        map.removeLayer(layerGroups[key]);
        btn.classList.remove('primary');
      } else {
        map.addLayer(layerGroups[key]);
        btn.classList.add('primary');
      }
    });
  });

  // Default: conflicts on
  document.querySelector('[data-layer="conflicts"]')?.classList.add('primary');
}

export function renderMap() {
  if (!map) initMap();
  if (!map) return;

  const { snapshot } = getState();
  if (!snapshot) return;

  // Clear existing
  Object.values(layerGroups).forEach(g => g.clearLayers());

  // Conflicts / events with coords
  const points = [
    ...(snapshot.mapPoints || []),
    ...(snapshot.conflicts || []).filter(c => c.lat && c.lon),
    ...(snapshot.hazards || []),
    ...(snapshot.strategic || [])
  ];

  points.forEach(p => {
    const lat = p.lat ?? p.latitude;
    const lon = p.lon ?? p.lng ?? p.longitude;
    if (lat == null || lon == null) return;

    const type = (p.type || p.layer || 'conflicts').toLowerCase();
    const group = layerGroups[type] || layerGroups.conflicts;
    const color = type === 'hazards' ? '#ffc857' : type === 'strategic' ? '#62a0ff' : '#ff6678';

    const marker = L.circleMarker([lat, lon], {
      radius: 6,
      color,
      fillColor: color,
      fillOpacity: 0.7,
      weight: 1
    });

    const title = p.name || p.title || p.location || 'Event';
    marker.bindPopup(`<strong>${escapeHtml(title)}</strong><br><span style="font-size:12px;color:#91a4b8">${escapeHtml(type)}</span>`);
    marker.on('click', () => showSidePanel(p));
    group.addLayer(marker);
  });
}

function showSidePanel(p) {
  const panel = document.getElementById('mapSidePanel');
  if (!panel) return;
  panel.style.display = 'block';
  panel.innerHTML = `
    <div class="gp-card-title">${escapeHtml(p.name || p.title || 'Location')}</div>
    <div style="font-size:12px;color:var(--muted);margin:4px 0 8px">${escapeHtml(p.type || p.layer || '')}</div>
    <div style="font-size:13px;color:var(--text-secondary)">${escapeHtml(p.summary || p.description || 'No additional detail in snapshot.')}</div>
    <button class="gp-btn" style="margin-top:10px" type="button" onclick="this.parentElement.style.display='none'">Close</button>
  `;
}
