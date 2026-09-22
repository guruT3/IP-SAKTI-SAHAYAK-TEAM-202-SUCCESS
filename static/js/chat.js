// IP-SAKTI SAHAYAK — Chat & Agentic Deep Research Engine

let currentConversationId = null;
let currentResearchMode = "quick";

const messagesEl = document.getElementById('chat-messages');
const formEl = document.getElementById('chat-form');
const inputEl = document.getElementById('chat-input');
const sendBtn = document.getElementById('chat-send-btn');
const evidenceContentEl = document.getElementById('evidence-content');
const evidenceCountBadge = document.getElementById('evidence-count-badge');
const jurisdictionSelect = document.getElementById('jurisdiction-select');
const languageSelect = document.getElementById('language-select');
const newChatBtn = document.getElementById('new-chat-btn');
const deepProgressEl = document.getElementById('deep-research-progress');
const deepStepsContainer = document.getElementById('deep-steps-container');

function setResearchMode(mode) {
  currentResearchMode = mode;
  const qBtn = document.getElementById('mode-quick-btn');
  const dBtn = document.getElementById('mode-deep-btn');
  const hint = document.getElementById('mode-hint');

  if (mode === 'deep') {
    dBtn.classList.add('active');
    qBtn.classList.remove('active');
    hint.textContent = 'Agentic Multi-Track: Decomposes query into 5 specialized IP tracks.';
  } else {
    qBtn.classList.add('active');
    dBtn.classList.remove('active');
    hint.textContent = 'Fast hybrid retrieval + cross-encoder reranking.';
  }
}

function setSampleQuery(text) {
  inputEl.value = text;
  inputEl.focus();
}

function clearEmptyState() {
  const empty = messagesEl.querySelector('.chat-empty-state');
  if (empty) empty.remove();
}

function confidenceClass(level) {
  if (level === 'HIGH') return '';
  if (level === 'MEDIUM') return 'medium';
  return 'low';
}

function displayMessage(role, content, meta = {}) {
  clearEmptyState();
  const bubble = document.createElement('div');
  bubble.className = `chat-bubble ${role}`;

  if (role === 'assistant') {
    const metaBar = document.createElement('div');
    metaBar.className = 'answer-meta';

    if (meta.abstained) {
      metaBar.innerHTML = `
        <span class="badge badge-warning">🛡️ Safe Abstention Gate</span>
        <span class="badge">${escapeHtml(meta.domain || 'General IP')}</span>
        <span class="confidence-meter">
          <span class="confidence-bar"><span class="confidence-fill low" style="width:20%"></span></span>
          VERY LOW (Safe Abstain)
        </span>`;
    } else if (meta.confidence !== undefined) {
      const pct = Math.round((meta.confidence || 0) * 100);
      const modeTag = meta.mode === 'deep' ? '<span class="badge badge-primary">🔬 Deep Research Dossier</span>' : '';
      metaBar.innerHTML = `
        ${modeTag}
        <span class="badge">${escapeHtml(meta.domain || 'General IP')}</span>
        <span class="badge">${escapeHtml(meta.jurisdiction || 'India')}</span>
        <span class="confidence-meter" title="${escapeHtml(meta.confidence_level || '')}">
          <span class="confidence-bar"><span class="confidence-fill ${confidenceClass(meta.confidence_level)}" style="width:${pct}%"></span></span>
          ${meta.confidence_level || 'MED'} (${pct}%)
        </span>`;
    }
    bubble.appendChild(metaBar);
  }

  const textDiv = document.createElement('div');
  textDiv.className = 'message-text-body pre-text';
  textDiv.textContent = content;
  bubble.appendChild(textDiv);

  if (role === 'assistant' && !meta.abstained) {
    const actions = document.createElement('div');
    actions.className = 'msg-actions';
    actions.innerHTML = `
      <button type="button" class="btn btn-secondary btn-sm copy-btn">📋 Copy</button>
      <button type="button" class="btn btn-secondary btn-sm why-btn">🔍 Why did AI say this?</button>
      <button type="button" class="btn btn-secondary btn-sm regen-btn">↺ Regenerate</button>
      <button type="button" class="btn btn-primary btn-sm report-btn">📄 Export Dossier</button>`;
    bubble.appendChild(actions);

    actions.querySelector('.copy-btn').addEventListener('click', () => {
      navigator.clipboard.writeText(content);
      alert('Answer copied to clipboard!');
    });

    actions.querySelector('.why-btn').addEventListener('click', () => {
      showTraceabilityModal(meta.claim_trace_map, meta.sources, content);
    });

    actions.querySelector('.regen-btn').addEventListener('click', () => {
      sendMessage(meta.originalQuery, true);
    });

    actions.querySelector('.report-btn').addEventListener('click', async () => {
      const payload = {
        format: 'html',
        answer_payload: {
          query: meta.originalQuery,
          answer: content,
          domain: meta.domain,
          jurisdiction: meta.jurisdiction,
          confidence: meta.confidence,
          confidence_level: meta.confidence_level,
          sources: meta.sources || [],
        },
      };
      const data = await apiFetch('/api/reports', { method: 'POST', body: JSON.stringify(payload) });
      if (data.success && data.download_url) {
        window.open(data.download_url, '_blank');
      } else {
        alert(`Report error: ${data.error || 'Could not export report'}`);
      }
    });
  }

  messagesEl.appendChild(bubble);
  messagesEl.scrollTop = messagesEl.scrollHeight;
  return bubble;
}

function showTraceabilityModal(claimTraceMap, sources, answerText) {
  const modal = document.getElementById('evidence-modal');
  const title = document.getElementById('modal-title');
  const content = document.getElementById('modal-content');
  if (!modal || !content) return;

  title.textContent = 'Evidence Traceability: "Why Did AI Say This?"';

  if (!claimTraceMap || claimTraceMap.length === 0) {
    // Fallback: render source cards
    if (sources && sources.length > 0) {
      content.innerHTML = `
        <div class="trace-intro">
          <p class="muted">Every statement in the generated response was verified against the following authoritative statutory records:</p>
        </div>
        <div class="trace-list">
          ${sources.map((s, i) => `
            <div class="claim-trace-item">
              <div class="trace-header">
                <strong>[Source ${s.index || i + 1}] ${escapeHtml(s.source_name || s.authority || 'Official Authority')}</strong>
                <span class="badge badge-success">Verified Ground Truth</span>
              </div>
              <p class="trace-section"><strong>Provision:</strong> ${escapeHtml(s.section || 'Statutory Section')}</p>
              <p class="trace-snippet">"${escapeHtml(s.text_snippet || '')}"</p>
              ${s.url ? `<a href="${s.url}" target="_blank" rel="noopener" class="trace-url">Open Official Gazette Source ↗</a>` : ''}
            </div>
          `).join('')}
        </div>`;
    } else {
      content.innerHTML = '<p class="muted">No explicit citation trace available for this answer.</p>';
    }
  } else {
    content.innerHTML = `
      <div class="trace-intro">
        <p class="muted"><strong>Claim-by-Claim Verification Map:</strong> Each sentence was verified for lexical and concept overlap against the retrieved statutory excerpts:</p>
      </div>
      <div class="trace-list">
        ${claimTraceMap.map((t) => `
          <div class="claim-trace-item">
            <div class="trace-header">
              <strong>Source ${t.citation_index}: ${escapeHtml(t.authority || 'Official Authority')}</strong>
              <span class="badge ${t.verified ? 'badge-success' : 'badge-warning'}">
                ${t.verified ? '✓ Grounded' : '⚠ Low Overlap'} (${t.overlap_pct || 0}% match)
              </span>
            </div>
            <p class="trace-claim"><strong>AI Claim:</strong> "${escapeHtml(t.claim)}"</p>
            <p class="trace-section"><strong>Statutory Anchor:</strong> ${escapeHtml(t.section || 'N/A')}</p>
            <p class="trace-snippet"><strong>Retrieved Evidence Text:</strong> "${escapeHtml(t.evidence_text || '')}"</p>
            ${t.url ? `<a href="${t.url}" target="_blank" rel="noopener" class="trace-url">View Source URL ↗</a>` : ''}
          </div>
        `).join('')}
      </div>`;
  }

  modal.style.display = 'flex';
}

function showSources(sources) {
  if (evidenceCountBadge) {
    evidenceCountBadge.textContent = `${(sources || []).length} Sources`;
  }

  if (!sources || sources.length === 0) {
    evidenceContentEl.innerHTML = '<p class="muted">No statutory sources were retrieved for this query.</p>';
    return;
  }

  evidenceContentEl.innerHTML = sources.map((s, i) => `
    <div class="source-card">
      <div class="src-header">
        <span class="badge badge-primary">Source ${s.index || i + 1}</span>
        <h5>${escapeHtml(s.source_name || s.authority || 'Authoritative Source')}</h5>
      </div>
      <div class="src-meta">
        ${escapeHtml(s.jurisdiction || 'India')} ${s.section ? '· <strong>' + escapeHtml(s.section) + '</strong>' : ''}
      </div>
      <p class="src-snippet">"${escapeHtml((s.text_snippet || '').slice(0, 180))}…"</p>
      ${s.url ? `<a href="${s.url}" target="_blank" rel="noopener" class="src-link">Open Official Source ↗</a>` : '<span class="muted">URL unavailable</span>'}
    </div>
  `).join('');
}

async function sendMessage(overrideQuery, isRegenerate = false) {
  const query = (overrideQuery !== undefined ? overrideQuery : inputEl.value).trim();
  if (!query) return;

  if (!isRegenerate) {
    displayMessage('user', query);
    inputEl.value = '';
  }

  const mode = currentResearchMode;
  if (mode === 'deep' && deepProgressEl) {
    deepProgressEl.style.display = 'block';
    deepStepsContainer.innerHTML = `
      <div class="timeline-step"><div class="timeline-icon">1</div><div class="timeline-content"><h4>Indian Patents Act Track</h4><p>Analyzing Sections 3(d), 3(p), 3(e)…</p></div></div>
      <div class="timeline-step"><div class="timeline-icon">2</div><div class="timeline-content"><h4>Traditional Knowledge &amp; TKDL</h4><p>Scanning classical Samhita and CSIR records…</p></div></div>
      <div class="timeline-step"><div class="timeline-icon">3</div><div class="timeline-content"><h4>Biological Diversity &amp; ABS</h4><p>Evaluating Section 6 NBA approval obligations…</p></div></div>
      <div class="timeline-step"><div class="timeline-icon">4</div><div class="timeline-content"><h4>AYUSH Regulatory Pathway</h4><p>Checking Drugs Act Rule 158B &amp; Schedule T GMP…</p></div></div>
      <div class="timeline-step"><div class="timeline-icon">5</div><div class="timeline-content"><h4>International Comparative (PCT/WIPO)</h4><p>Synthesizing global filing and 2024 treaty impacts…</p></div></div>
    `;
  }

  const loadingBubble = displayMessage('assistant', mode === 'deep' ? 'Executing 5-Track Deep IP Research Pipeline…' : 'Researching authoritative statutory sources…');
  loadingBubble.classList.add('loading');
  sendBtn.disabled = true;

  try {
    const data = await apiFetch('/api/chat', {
      method: 'POST',
      body: JSON.stringify({
        query: query,
        conversation_id: currentConversationId,
        jurisdiction: jurisdictionSelect.value,
        language: languageSelect.value,
        mode: mode,
      }),
    });

    loadingBubble.remove();
    if (deepProgressEl) deepProgressEl.style.display = 'none';

    if (!data.success) {
      displayMessage('assistant', data.error || 'Something went wrong.', { originalQuery: query });
      return;
    }

    currentConversationId = data.conversation_id;
    displayMessage('assistant', data.answer, {
      confidence: data.confidence,
      confidence_level: data.confidence_level,
      domain: data.domain,
      jurisdiction: data.jurisdiction,
      mode: data.mode,
      sources: data.sources,
      citations: data.citations,
      claim_trace_map: data.claim_trace_map,
      abstained: data.abstained,
      originalQuery: query,
    });

    showSources(data.sources);
  } catch (err) {
    loadingBubble.remove();
    if (deepProgressEl) deepProgressEl.style.display = 'none';
    displayMessage('assistant', 'Connection error. Please try again shortly.', { originalQuery: query });
  } finally {
    sendBtn.disabled = false;
  }
}

document.addEventListener('DOMContentLoaded', () => {
  if (formEl) {
    formEl.addEventListener('submit', (e) => {
      e.preventDefault();
      sendMessage();
    });
  }

  if (inputEl) {
    inputEl.addEventListener('keydown', (e) => {
      if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        sendMessage();
      }
    });

    inputEl.addEventListener('input', () => {
      inputEl.style.height = 'auto';
      inputEl.style.height = Math.min(inputEl.scrollHeight, 140) + 'px';
    });
  }

  if (newChatBtn) {
    newChatBtn.addEventListener('click', () => {
      currentConversationId = null;
      messagesEl.innerHTML = `
        <div class="chat-empty-state">
          <div class="empty-icon">⚖️</div>
          <h2>New Research Session Initialized</h2>
          <p>Ask an authoritative IP, Ayurveda, or Traditional Knowledge research question.</p>
        </div>`;
      evidenceContentEl.innerHTML = '<p class="muted">Sources for the latest answer will appear here.</p>';
      if (evidenceCountBadge) evidenceCountBadge.textContent = '0 Sources';
    });
  }

  // Modal close handler
  const modalCloseBtn = document.getElementById('modal-close-btn');
  const modal = document.getElementById('evidence-modal');
  if (modalCloseBtn && modal) {
    modalCloseBtn.addEventListener('click', () => {
      modal.style.display = 'none';
    });
    modal.addEventListener('click', (e) => {
      if (e.target === modal) modal.style.display = 'none';
    });
  }
});
