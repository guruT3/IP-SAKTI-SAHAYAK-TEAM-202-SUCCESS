// IP-SAKTI SAHAYAK — Source registry listing page.

(async () => {
  const listEl = document.getElementById('sources-list');
  const data = await apiFetch('/api/sources');
  if (!data.success || !data.sources.length) {
    listEl.innerHTML = '<p class="muted">No sources found.</p>';
    return;
  }
  listEl.innerHTML = data.sources.map(s => `
    <div class="source-row">
      <div>
        <div class="name">${escapeHtml(s.source_name)}</div>
        <div class="meta">${escapeHtml(s.authority || '')} · ${escapeHtml(s.jurisdiction || '')} · ${escapeHtml(s.source_type || '')}</div>
      </div>
      <div>
        <span class="priority-tag">Priority ${s.priority}</span>
        <a href="${s.base_url}" target="_blank" rel="noopener" style="margin-left:10px;">Visit ↗</a>
      </div>
    </div>
  `).join('');
})();
