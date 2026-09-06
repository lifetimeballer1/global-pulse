/** Interactive World Map — uses markers + layers from real snapshot */

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
    strategic: L.layerGroup().addTo(map),
    cartel: L.layerGroup()
  };

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

  document.querySelector('[data-layer="conflicts"]')?.classList.add('primary');
}

export function renderMap() {
  if (!map) initMap();
  if (!map) return;

  const { snapshot } = getState();
  if (!snapshot) return;

  Object.values(layerGroups).forEach(g => g.clearLayers());

  const markers = Array.isArray(snapshot.markers) ? snapshot.markers : [];
  const extra = [
    ...(snapshot.mapPoints || []),
    ...(snapshot.hazards || []),
    ...(snapshot.strategic || []),
    ...((snapshot.counterCartelLayer && snapshot.counterCartelLayer.points) || [])
  ];

  const all = markers.length ? markers : extra;
  const maxPoints = 800;
  const points = all.length > maxPoints
    ? all.filter(p => (p.importance || 0) >= 0.4).slice(0, maxPoints)
    : all;

  points.forEach(p => {
    const lat = p.lat ?? p.latitude;
    const lon = p.lng ?? p.lon ?? p.longitude;
    if (lat == null || lon == null) return;

    const rawType = (p.type || p.layer || p.eventType || 'conflicts').toString().toLowerCase();
    let groupKey = 'conflicts';
    if (rawType.includes('hazard') || rawType.includes('quake') || rawType.includes('disaster') || rawType.includes('fire')) groupKey = 'hazards';
    else if (rawType.includes('strategic') || rawType.includes('base') || rawType.includes('infra')) groupKey = 'strategic';
    else if (rawType.includes('cartel') || rawType.includes('crime') || rawType.includes('enforcer')) groupKey = 'cartel';

    const group = layerGroups[groupKey] || layerGroups.conflicts;
    const color = groupKey === 'hazards' ? '#ffc857'
      : groupKey === 'strategic' ? '#62a0ff'
      : groupKey === 'cartel' ? '#fb923c'
      : '#ff6678';

    const marker = L.circleMarker([lat, lon], {
      radius: Math.max(4, Math.min(10, (p.importance || 0.5) * 10)),
      color,
      fillColor: color,
      fillOpacity: 0.65,
      weight: 1
    });

    const title = p.title || p.name || p.location || 'Event';
    const detail = p.detail || p.summary || p.description || '';
    marker.bindPopup(`
      <strong>${escapeHtml(title)}</strong><br>
      <span style="font-size:12px;color:#91a4b8">${escapeHtml(rawType)}</span>
      ${detail ? `<br><span style="font-size:12px">${escapeHtml(String(detail).slice(0, 180))}</span>` : ''}
    `);
    marker.on('click', () => showSidePanel(p));
    group.addLayer(marker);
  });
}

function showSidePanel(p) {
  const panel = document.getElementById('mapSidePanel');
  if (!panel) return;
  panel.style.display = 'block';
  const title = p.title || p.name || 'Location';
  const detail = p.detail || p.summary || p.description || 'No additional detail in snapshot.';
  const url = p.url || p.sourceUrl || null;
  panel.innerHTML = `
    <div class="gp-card-title">${escapeHtml(title)}</div>
    <div style="font-size:12px;color:var(--muted);margin:4px 0 8px">${escapeHtml(p.type || p.layer || p.eventType || '')}</div>
    <div style="font-size:13px;color:var(--text-secondary)">${escapeHtml(String(detail).slice(0, 400))}</div>
    ${url ? `<div style="margin-top:8px"><a href="${escapeHtml(url)}" target="_blank" rel="noopener" style="color:var(--blue);font-size:12px">Open source ↗</a></div>` : ''}
    <button class="gp-btn" style="margin-top:10px" type="button" onclick="this.parentElement.style.display='none'">Close</button>
  `;
}
