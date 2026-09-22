// IP-SAKTI SAHAYAK — Prior-Art & Traditional Knowledge Explorer Engine

document.addEventListener("DOMContentLoaded", () => {
  const form = document.getElementById("prior-art-form");
  if (!form) return;

  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    const desc = document.getElementById("invention-description").value.trim();
    const jur = document.getElementById("prior-art-jurisdiction").value;
    const btn = document.getElementById("prior-art-btn");
    const resultsWrapper = document.getElementById("prior-art-results-wrapper");
    const conceptsBox = document.getElementById("concepts-chips");
    const conceptsBadge = document.getElementById("concept-count-badge");
    const resultsList = document.getElementById("prior-art-results-list");

    if (!desc) return;

    btn.disabled = true;
    btn.textContent = "Retrieving Classical TK & Prior-Art Records…";
    resultsWrapper.style.display = "none";

    try {
      const data = await apiFetch("/api/prior-art", {
        method: "POST",
        body: JSON.stringify({ description: desc, jurisdiction: jur }),
      });

      if (!data.success) {
        alert(data.error || "Prior-art search failed.");
        return;
      }

      // Render Concept Chips
      const concepts = data.extracted_concepts || [];
      conceptsBadge.textContent = `${concepts.length} Concepts`;
      conceptsBox.innerHTML = concepts.map((c) => `<span class="concept-chip">🌿 ${escapeHtml(c)}</span>`).join("");

      // Render Prior Art Results
      const results = data.results || [];
      if (results.length === 0) {
        resultsList.innerHTML = `<p class="muted">No directly conflicting prior art identified in the indexed corpus.</p>`;
      } else {
        resultsList.innerHTML = results.map((r, i) => {
          const sharedHtml = (r.shared_concepts || []).map((s) => `<span class="shared-tag">${escapeHtml(s)}</span>`).join(" ");

          return `
            <div class="prior-art-card">
              <div class="pa-card-header">
                <div>
                  <span class="badge badge-primary">Record #${i + 1}</span>
                  <h4>${escapeHtml(r.title)}</h4>
                  <span class="pa-source-meta">${escapeHtml(r.authority)} &middot; ${escapeHtml(r.jurisdiction)}</span>
                </div>
                <div class="pa-relevance-meter">
                  <span class="relevance-val">${Math.round((r.relevance_score || 0.75) * 100)}%</span>
                  <span class="relevance-lbl">Relevance</span>
                </div>
              </div>

              <div class="pa-card-body">
                <p class="pa-excerpt">"${escapeHtml(r.excerpt)}"</p>
                <div class="shared-concepts-row">
                  <strong>Shared Concepts / Botanical Actives:</strong>
                  <div class="shared-tags-list">${sharedHtml || '<span class="muted">None explicitly mapped</span>'}</div>
                </div>
                <div class="differentiating-note">
                  <strong>Differentiating Feature Examination:</strong>
                  <p>${escapeHtml(r.differentiating_aspects || "Assess particle size, carrier complexes, or extraction ratios.")}</p>
                </div>
              </div>

              <div class="pa-card-footer">
                <span class="legal-note">ℹ️ ${escapeHtml(r.note || "Potentially relevant prior art identified.")}</span>
                ${r.url ? `<a href="${r.url}" target="_blank" rel="noopener" class="pa-official-link">Open Official Record ↗</a>` : ''}
              </div>
            </div>
          `;
        }).join("");
      }

      resultsWrapper.style.display = "block";
      resultsWrapper.scrollIntoView({ behavior: "smooth", block: "start" });
    } catch (err) {
      console.error("Prior art error:", err);
      alert("Error executing prior-art search.");
    } finally {
      btn.disabled = false;
      btn.textContent = "🔍 Search Potentially Relevant Prior Art";
    }
  });
});
