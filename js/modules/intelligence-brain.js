/** Intelligence Brain — cross-domain view of the canonical brain artifact. */
import { getState } from '../core/state.js';
import { escapeHtml, formatRelativeTime } from '../core/utils.js';

let selectedId = null;
let query = '';
let kindFilter = 'all';
let showAll = false;

function selectBrainNode(id, {scroll=true}={}) {
  selectedId = id ? String(id) : null;
  renderIntelligenceBrain();
  if (scroll) document.getElementById('brainBody')?.scrollIntoView({behavior:'smooth',block:'nearest'});
}

function matches(node) {
  const kind = String(node.kind || node.type || 'entity').toLowerCase();
  if (kindFilter !== 'all' && kind !== kindFilter) return false;
  if (!query) return true;
  const hay = [node.id,node.label,node.name,node.description,node.summary,node.country,node.region,node.group,kind].join(' ').toLowerCase();
  return hay.includes(query);
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
  const filtered = nodes.filter(matches);
  const ranked = [...filtered].sort((a,b)=>(degree[b.id]||0)-(degree[a.id]||0));
  const visible = showAll ? ranked : ranked.slice(0,5);
  const selected = selectedId ? byId.get(selectedId) : null;
  const selectedEdges = selected ? edges.filter(e => String(e.source)===selectedId || String(e.target)===selectedId).slice(0,12) : [];
  const kinds = [...new Set(nodes.map(n => String(n.kind||n.type||'entity').toLowerCase()))].filter(Boolean).sort();
  el.innerHTML = `
    <div class="gp-brain-summary">
      <span class="gp-brain-chip">${nodes.length} nodes</span><span class="gp-brain-chip">${edges.length} relationships</span>
      <span class="gp-brain-chip">${Number(stats.marketIndicators||0)} market indicators</span><span class="gp-brain-chip">${Number(stats.countryNodes||0)} countries</span>
      <span class="gp-brain-chip">${Number(stats.economicNodes||0)} economic</span><span class="gp-brain-chip">${Number(stats.cartelNodes||0)} cartel/crime</span>
    </div>
    <div style="font-size:12px;color:var(--text-secondary);margin-bottom:10px">The Brain connects news, conflicts, geographic signals, events, claims, assessments, markets and macro context when public evidence supports the relationship. Connections are contextual relevance, not proof of causation, coordination or intent.</div>
    <div class="gp-brain-controls" style="display:flex;gap:7px;flex-wrap:wrap;margin-bottom:10px">
      <input id="gpBrainSearch" type="search" value="${escapeHtml(query)}" placeholder="Search the Brain…" style="flex:1;min-width:180px">
      <select id="gpBrainKind" style="min-height:34px;border:1px solid var(--line);border-radius:9px;background:var(--bg-elevated);color:var(--text);padding:7px 9px">
        <option value="all" ${kindFilter==='all'?'selected':''}>All types</option>${kinds.map(k=>`<option value="${escapeHtml(k)}" ${kindFilter===k?'selected':''}>${escapeHtml(k)}</option>`).join('')}
      </select>
      <button id="gpBrainClear" class="gp-btn" type="button">Clear</button>
    </div>
    <div style="font-size:10px;color:var(--muted-2);margin-bottom:7px">Showing ${visible.length} of ${ranked.length} matching nodes${query||kindFilter!=='all'?' · filtered':''}</div>
    <div class="gp-brain-grid">${visible.map(n=>`<button class="gp-card gp-brain-node ${selectedId===String(n.id)?'selected':''}" data-brain-node="${escapeHtml(String(n.id))}" type="button"><div class="gp-card-title">${escapeHtml(n.label||n.name||n.id)}</div><div class="gp-card-meta"><span class="gp-badge category">${escapeHtml(n.kind||n.type||'entity')}</span><span>${degree[n.id]||0} links</span></div></button>`).join('')}</div>
    ${ranked.length===0 ? '<div class="gp-state" style="margin-top:8px">No Brain nodes match the current search/filter.</div>' : ''}
    ${ranked.length>5 ? `<button id="gpBrainMore" class="gp-btn" type="button" style="margin-top:9px;width:100%">${showAll?'Show fewer':'See more nodes'}</button>` : ''}
    ${selected ? `<div class="gp-card gp-brain-details"><div class="gp-card-title">${escapeHtml(selected.label||selected.name||selected.id)}</div><div style="font-size:12px;color:var(--text-secondary);margin-top:6px">${escapeHtml(selected.description||selected.summary||'No additional description in the current evidence artifact.')}</div>${selectedEdges.map(e=>{const other=String(e.source)===selectedId?byId.get(String(e.target)):byId.get(String(e.source));return `<div style="margin-top:7px;padding:7px;border:1px solid var(--line);border-radius:8px;font-size:11px"><strong>${escapeHtml(other?.label||other?.name||'Connected signal')}</strong><br>${escapeHtml(e.relationship||e.label||e.type||'contextual relationship')}</div>`}).join('')}<button class="gp-btn" id="brainClearSelection" type="button" style="margin-top:9px">Close node</button></div>` : ''}
    <div style="margin-top:10px;font-size:10px;color:var(--muted-2)">Source-backed only: ${brain.sourceBackedOnly===true?'YES':'NO'} · Consolidated: ${brain.consolidated===true?'YES':'NO'}</div>`;

  el.querySelectorAll('[data-brain-node]').forEach(btn=>btn.addEventListener('click',()=>{
    const id=btn.dataset.brainNode;
    selectBrainNode(id);
    window.dispatchEvent(new CustomEvent('gp:brain-select',{detail:{id,source:'brain'}}));
  }));
  el.querySelector('#brainClearSelection')?.addEventListener('click',()=>{selectedId=null;window.dispatchEvent(new CustomEvent('gp:brain-select',{detail:{id:null,source:'brain'}}));renderIntelligenceBrain();});
  el.querySelector('#gpBrainSearch')?.addEventListener('input',event=>{query=String(event.target.value||'').trim().toLowerCase();showAll=false;renderIntelligenceBrain();const input=document.getElementById('gpBrainSearch');input?.focus();input?.setSelectionRange(input.value.length,input.value.length);});
  el.querySelector('#gpBrainKind')?.addEventListener('change',event=>{kindFilter=String(event.target.value||'all');showAll=false;renderIntelligenceBrain();});
  el.querySelector('#gpBrainClear')?.addEventListener('click',()=>{query='';kindFilter='all';showAll=false;renderIntelligenceBrain();});
  el.querySelector('#gpBrainMore')?.addEventListener('click',()=>{showAll=!showAll;renderIntelligenceBrain();});
}

window.addEventListener('gp:brain-select', event => {
  const id = event.detail?.id;
  if (!id || event.detail?.source === 'brain') return;
  selectBrainNode(String(id), {scroll:false});
});
