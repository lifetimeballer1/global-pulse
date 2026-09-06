/** Intelligence Brain — cross-domain view of the canonical brain artifact. */
import { getState } from '../core/state.js';
import { escapeHtml, formatRelativeTime } from '../core/utils.js';

let selectedId = null;

function selectBrainNode(id, {scroll=true}={}) {
  selectedId = id ? String(id) : null;
  renderIntelligenceBrain();
  if (scroll) document.getElementById('brainBody')?.scrollIntoView({behavior:'smooth',block:'nearest'});
}

export function renderIntelligenceBrain() {
  const el = document.getElementById('brainBody');
  const updatedEl = document.getElementById('brainUpdated');
  if (!el) return;
  const { snapshot } = getState();
  const brain = snapshot?.intelligenceBrain || null;
  if (!brain || !Array.isArray(brain.nodes)) {
    el.innerHTML = '<div class="gp-state"><div class="gp-state-title">Intelligence Brain unavailable</div><div>The latest cross-domain brain artifact is not present in this snapshot.</div></div>';
    return;
  }
  const nodes = brain.nodes;
  const edges = Array.isArray(brain.edges) ? brain.edges : [];
  const stats = brain.stats || {};
  if (updatedEl) updatedEl.textContent = formatRelativeTime(brain.updatedAt || snapshot?.updatedAt);
  const byId = new Map(nodes.map(n => [String(n.id), n]));
  const degree = {};
  edges.forEach(e => { const s=String(e.source||''), t=String(e.target||''); if(s)degree[s]=(degree[s]||0)+1; if(t)degree[t]=(degree[t]||0)+1; });
  const ranked = [...nodes].sort((a,b)=>(degree[b.id]||0)-(degree[a.id]||0)).slice(0,10);
  const selected = selectedId ? byId.get(selectedId) : null;
  const selectedEdges = selected ? edges.filter(e => String(e.source)===selectedId || String(e.target)===selectedId).slice(0,12) : [];
  el.innerHTML = `
    <div class="gp-brain-summary">
      <span class="gp-brain-chip">${nodes.length} nodes</span><span class="gp-brain-chip">${edges.length} relationships</span>
      <span class="gp-brain-chip">${Number(stats.marketIndicators||0)} market indicators</span><span class="gp-brain-chip">${Number(stats.countryNodes||0)} countries</span>
      <span class="gp-brain-chip">${Number(stats.economicNodes||0)} economic</span><span class="gp-brain-chip">${Number(stats.cartelNodes||0)} cartel/crime</span>
    </div>
    <div style="font-size:12px;color:var(--text-secondary);margin-bottom:10px">The Brain connects news, conflicts, geographic signals, events, claims, assessments, markets and macro context when public evidence supports the relationship. Connections are contextual relevance, not proof of causation, coordination or intent.</div>
    <div class="gp-brain-grid">${ranked.map(n=>`<button class="gp-card gp-brain-node ${selectedId===String(n.id)?'selected':''}" data-brain-node="${escapeHtml(String(n.id))}" type="button"><div class="gp-card-title">${escapeHtml(n.label||n.name||n.id)}</div><div class="gp-card-meta"><span class="gp-badge category">${escapeHtml(n.kind||n.type||'entity')}</span><span>${degree[n.id]||0} links</span></div></button>`).join('')}</div>
    ${selected ? `<div class="gp-card gp-brain-details"><div class="gp-card-title">${escapeHtml(selected.label||selected.name||selected.id)}</div><div style="font-size:12px;color:var(--text-secondary);margin-top:6px">${escapeHtml(selected.description||selected.summary||'No additional description in the current evidence artifact.')}</div>${selectedEdges.map(e=>{const other=String(e.source)===selectedId?byId.get(String(e.target)):byId.get(String(e.source));return `<div style="margin-top:7px;padding:7px;border:1px solid var(--line);border-radius:8px;font-size:11px"><strong>${escapeHtml(other?.label||other?.name||'Connected signal')}</strong><br>${escapeHtml(e.relationship||e.label||e.type||'contextual relationship')}</div>`}).join('')}<button class="gp-btn" id="brainClearSelection" type="button" style="margin-top:9px">Close node</button></div>` : ''}
    <div style="margin-top:10px;font-size:10px;color:var(--muted-2)">Source-backed only: ${brain.sourceBackedOnly===true?'YES':'NO'} · Consolidated: ${brain.consolidated===true?'YES':'NO'}</div>`;
  el.querySelectorAll('[data-brain-node]').forEach(btn=>btn.addEventListener('click',()=>{
    const id=btn.dataset.brainNode;
    selectBrainNode(id);
    window.dispatchEvent(new CustomEvent('gp:brain-select',{detail:{id,source:'brain'}}));
  }));
  el.querySelector('#brainClearSelection')?.addEventListener('click',()=>{selectedId=null;window.dispatchEvent(new CustomEvent('gp:brain-select',{detail:{id:null,source:'brain'}}));renderIntelligenceBrain();});
}

window.addEventListener('gp:brain-select', event => {
  const id = event.detail?.id;
  if (!id || event.detail?.source === 'brain') return;
  selectBrainNode(String(id), {scroll:false});
});
