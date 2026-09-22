// IP-SAKTI SAHAYAK — Regulation Time Machine Client Engine

let allRegulations = [];

document.addEventListener("DOMContentLoaded", async () => {
  await loadRegulations();
});

async function loadRegulations() {
  const container = document.getElementById("amendments-buttons");
  if (!container) return;

  container.innerHTML = '<p class="muted">Loading official statutory amendment records…</p>';

  try {
    const data = await apiFetch("/api/regulations");
    if (!data.success || !data.updates) {
      container.innerHTML = '<p class="error-text">Could not load regulatory updates.</p>';
      return;
    }

    allRegulations = data.updates;
    renderAmendmentButtons(allRegulations);

    if (allRegulations.length > 0) {
      selectAmendment(allRegulations[0].id);
    }
  } catch (err) {
    console.error("Regulations load error:", err);
    container.innerHTML = '<p class="error-text">Failed to fetch regulatory data.</p>';
  }
}

function renderAmendmentButtons(amendments) {
  const container = document.getElementById("amendments-buttons");
  if (!container) return;

  container.innerHTML = amendments.map((a, i) => `
    <button type="button" class="amendment-card-btn ${i === 0 ? 'active' : ''}" id="btn-${a.id}" onclick="selectAmendment('${a.id}')">
      <div class="a-date">${escapeHtml(a.effective_date)}</div>
      <div class="a-title">${escapeHtml(a.title)}</div>
      <div class="a-authority">${escapeHtml(a.authority)}</div>
    </button>
  `).join("");
}

function selectAmendment(id) {
  const activeBtn = document.querySelector(".amendment-card-btn.active");
  if (activeBtn) activeBtn.classList.remove("active");

  const targetBtn = document.getElementById(`btn-${id}`);
  if (targetBtn) targetBtn.classList.add("active");

  const reg = allRegulations.find((r) => r.id === id);
  if (!reg) return;

  document.getElementById("diff-effective-date").textContent = `Effective Date: ${reg.effective_date}`;
  document.getElementById("diff-title").textContent = reg.title;
  document.getElementById("diff-authority").textContent = `Enforcing Authority: ${reg.authority}`;

  const urlEl = document.getElementById("diff-url");
  if (urlEl) {
    urlEl.href = reg.source_url || "https://ipindia.gov.in";
    urlEl.textContent = `Open Official Gazette / Source (${reg.authority.split("/")[0].trim()}) ↗`;
  }

  document.getElementById("diff-practical-impact").textContent = reg.practical_significance || "No impact noted.";
  document.getElementById("diff-old-ver").textContent = reg.old_version || "Previous Version";
  document.getElementById("diff-new-ver").textContent = reg.new_version || "Amended Enactment";
  document.getElementById("diff-old-text").textContent = reg.old_provision || "N/A";
  document.getElementById("diff-new-text").textContent = reg.new_provision || "N/A";
  document.getElementById("diff-change-detected").textContent = reg.change_detected || "Statutory text amended.";
}
