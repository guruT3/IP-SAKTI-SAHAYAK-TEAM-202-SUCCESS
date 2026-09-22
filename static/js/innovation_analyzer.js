// IP-SAKTI SAHAYAK — Innovation Analyzer Client Engine (Flagship Feature)

let latestAnalysisPayload = null;

const PRESETS = {
  joint_gel: {
    name: "Herbo-Joint Synergistic Relief Gel",
    ingredients: "Standardized Curcumin (Curcuma longa 95%), Withania somnifera root extract (5% Withanolides), Piperine (Piper nigrum 98%) as bioavailability enhancer",
    process: "High-pressure lipid micro-emulsion with ultrasonic cavitation at 45°C, yielding particle size of 80-120nm with 4x enhanced transdermal permeability over aqueous decoctions",
    use: "Rapid topical alleviation of pain and cartilage inflammation in knee osteoarthritis and rheumatoid joint stiffness",
    jurisdiction: "India",
    desc: "In-vitro COX-2 and TNF-alpha inhibition assays demonstrate 3.2x synergistic bio-enhancement compared to unformulated raw herbal powder sum.",
  },
  antidiabetic: {
    name: "Polyherbal Glycemic Regulator Kwatha",
    ingredients: "Purified Guggulu (Commiphora mukul), Triphala extract (Emblica officinalis + Terminalia chebula + Terminalia bellirica), Neem leaf extract (Azadirachta indica)",
    process: "Aqueous hydro-alcoholic decoction concentrated under vacuum at low temperature (50°C), spray dried into micro-granules",
    use: "Adjuvant glycemic control, insulin sensitization, and diabetic neuropathic symptom reduction",
    jurisdiction: "India",
    desc: "Classical First Schedule Sharangadhara Samhita reference combined with standardized 2.5% Guggulsterones E&Z assay.",
  },
  nano_curcumin: {
    name: "Targeted Nano-Curcuminoid Phytosome Complex",
    ingredients: "Phospholipid-complexed Curcuminoids (Curcuma longa) with Boswellic Acids (Boswellia serrata AKBA 30%)",
    process: "Solvent-free phytosomal complexation yielding vesicular nanocarriers with sustained 24-hour plasma bioavailability",
    use: "Anti-inflammatory modulation and joint cartilage preservation in chronic osteoarthritic degradation",
    jurisdiction: "International",
    desc: "Comparative pharmacokinetic human PK trials demonstrate 18-fold increased AUC compared to standard unformulated 95% curcumin crystals.",
  },
  resp_spray: {
    name: "Tulsi-Ginger Bioenhanced Inhalation Mist",
    ingredients: "Standardized Tulsi essential oil (Ocimum sanctum Eugenol 65%), Ginger CO2 supercritical extract (Zingiber officinale 20% Gingerols)",
    process: "Supercritical fluid CO2 extraction followed by micro-droplet nebulization formulation without synthetic propellants",
    use: "Bronchodilation, anti-tussive relief, and respiratory mucosal barrier enhancement in viral cough",
    jurisdiction: "India",
    desc: "Documented in Charaka Samhita Kasa-Chikitsa, modified with pressurized metered aerosol delivery.",
  },
};

function loadPreset(key) {
  const p = PRESETS[key];
  if (!p) return;
  document.getElementById("inv-name").value = p.name;
  document.getElementById("inv-ingredients").value = p.ingredients;
  document.getElementById("inv-process").value = p.process;
  document.getElementById("inv-use").value = p.use;
  document.getElementById("inv-jurisdiction").value = p.jurisdiction;
  document.getElementById("inv-desc").value = p.desc;
}

function resetForm() {
  document.getElementById("innovation-form").reset();
  document.getElementById("analyzer-results").style.display = "none";
}

document.addEventListener("DOMContentLoaded", () => {
  const form = document.getElementById("innovation-form");
  if (!form) return;

  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    await runInnovationAnalysis();
  });
});

async function runInnovationAnalysis() {
  const name = document.getElementById("inv-name").value.trim();
  const ingredients = document.getElementById("inv-ingredients").value.trim();
  const process = document.getElementById("inv-process").value.trim();
  const use = document.getElementById("inv-use").value.trim();
  const jurisdiction = document.getElementById("inv-jurisdiction").value;
  const desc = document.getElementById("inv-desc").value.trim();

  if (!name || !ingredients) {
    alert("Please provide at least the Innovation Name and Ingredients.");
    return;
  }

  const loadingCard = document.getElementById("analyzer-loading");
  const resultsWrapper = document.getElementById("analyzer-results");
  const analyzeBtn = document.getElementById("analyze-btn");

  loadingCard.style.display = "block";
  resultsWrapper.style.display = "none";
  analyzeBtn.disabled = true;

  try {
    const data = await apiFetch("/api/analyze-innovation", {
      method: "POST",
      body: JSON.stringify({
        innovation_name: name,
        ingredients: ingredients,
        preparation_process: process,
        intended_use: use,
        target_jurisdiction: jurisdiction,
        optional_description: desc,
      }),
    });

    if (!data.success) {
      alert(data.error || "Innovation analysis failed. Please try again.");
      return;
    }

    latestAnalysisPayload = data;
    renderAnalysisResults(data);
    resultsWrapper.style.display = "block";
    resultsWrapper.scrollIntoView({ behavior: "smooth", block: "start" });
  } catch (err) {
    console.error("Analysis error:", err);
    alert("Connection error occurred during analysis.");
  } finally {
    loadingCard.style.display = "none";
    analyzeBtn.disabled = false;
  }
}

function renderAnalysisResults(data) {
  // Title & Jurisdiction
  document.getElementById("res-inv-title").textContent = data.innovation_name || "Innovation Dossier";
  document.getElementById("res-inv-jurisdiction").textContent = `Jurisdiction: ${data.target_jurisdiction || "India"}`;

  // Composite Risk Badge
  const radar = data.risk_radar || {};
  const compositeVal = radar.composite_risk || 50;
  const compEl = document.getElementById("composite-risk-val");
  compEl.textContent = `${compositeVal}%`;
  compEl.className = "risk-value " + (compositeVal >= 70 ? "high" : compositeVal >= 45 ? "medium" : "low");

  // Render SVG Spider Radar Chart & Cards
  renderSpiderChart(radar.scores || {});
  renderRadarCards(radar);

  // Render Botanical Entities
  renderBotanicals(data.extracted_botanicals || []);

  // Render Legal Report Body
  document.getElementById("report-text-container").textContent = data.comprehensive_report || "Report synthesized.";

  // Render Prior Art References
  renderPriorArt(data.prior_art_references || []);
}

function renderSpiderChart(scores) {
  const svg = document.getElementById("spider-radar-svg");
  if (!svg) return;

  const width = 320;
  const height = 280;
  const cx = width / 2;
  const cy = height / 2 + 10;
  const radius = 95;

  const axes = [
    { key: "tk_overlap", label: "TKDL Overlap", score: scores.tk_overlap || 20 },
    { key: "novelty_risk", label: "Novelty / Sec 3(d)", score: scores.novelty_risk || 25 },
    { key: "abs_compliance", label: "NBA / ABS", score: scores.abs_compliance || 30 },
    { key: "regulatory_complexity", label: "AYUSH Reg", score: scores.regulatory_complexity || 35 },
    { key: "international_friction", label: "International", score: scores.international_friction || 25 },
  ];

  const totalAxes = axes.length;
  let bgRings = "";
  [0.25, 0.5, 0.75, 1.0].forEach((level) => {
    const ringRadius = radius * level;
    let points = [];
    for (let i = 0; i < totalAxes; i++) {
      const angle = (2 * Math.PI * i) / totalAxes - Math.PI / 2;
      const x = cx + ringRadius * Math.cos(angle);
      const y = cy + ringRadius * Math.sin(angle);
      points.push(`${x},${y}`);
    }
    bgRings += `<polygon points="${points.join(" ")}" fill="none" stroke="var(--border)" stroke-width="1" stroke-dasharray="${level === 1.0 ? '0' : '2,2'}"/>`;
  });

  let axisLines = "";
  let dataPoints = [];
  axes.forEach((axis, i) => {
    const angle = (2 * Math.PI * i) / totalAxes - Math.PI / 2;
    const xMax = cx + radius * Math.cos(angle);
    const yMax = cy + radius * Math.sin(angle);
    axisLines += `<line x1="${cx}" y1="${cy}" x2="${xMax}" y2="${yMax}" stroke="var(--border)" stroke-width="1.2"/>`;

    // Data position
    const valRatio = Math.max(0.1, Math.min(1.0, axis.score / 100));
    const xData = cx + radius * valRatio * Math.cos(angle);
    const yData = cy + radius * valRatio * Math.sin(angle);
    dataPoints.push(`${xData},${yData}`);

    // Label position
    const xLabel = cx + (radius + 20) * Math.cos(angle);
    const yLabel = cy + (radius + 14) * Math.sin(angle);
    const anchor = Math.abs(xLabel - cx) < 10 ? "middle" : xLabel > cx ? "start" : "end";
    axisLines += `
      <text x="${xLabel}" y="${yLabel}" text-anchor="${anchor}" dominant-baseline="middle" font-size="10.5" font-weight="600" fill="var(--text-muted)">
        ${axis.label} (${axis.score}%)
      </text>`;
  });

  const polygonData = `<polygon points="${dataPoints.join(" ")}" fill="rgba(15, 118, 110, 0.25)" stroke="var(--primary)" stroke-width="2.5"/>`;

  let dots = "";
  dataPoints.forEach((pt) => {
    const [px, py] = pt.split(",");
    dots += `<circle cx="${px}" cy="${py}" r="4.5" fill="var(--primary)" stroke="#fff" stroke-width="2"/>`;
  });

  svg.innerHTML = bgRings + axisLines + polygonData + dots;
}

function renderRadarCards(radar) {
  const container = document.getElementById("radar-cards-container");
  if (!container) return;

  const scores = radar.scores || {};
  const levels = radar.levels || {};
  const drivers = radar.drivers || {};

  const axesConfig = [
    { key: "tk_overlap", name: "Traditional Knowledge Overlap", score: scores.tk_overlap || 0, level: levels.tk_overlap || "LOW", desc: drivers.tk_overlap || [] },
    { key: "novelty_risk", name: "Novelty & Sec 3(d)/3(e) Friction", score: scores.novelty_risk || 0, level: levels.novelty_risk || "LOW", desc: drivers.novelty_risk || [] },
    { key: "abs_compliance", name: "Biological Diversity (NBA/ABS)", score: scores.abs_compliance || 0, level: levels.abs_compliance || "LOW", desc: drivers.abs_compliance || [] },
    { key: "regulatory_complexity", name: "AYUSH Regulatory Pathway", score: scores.regulatory_complexity || 0, level: levels.regulatory_complexity || "LOW", desc: drivers.regulatory_complexity || [] },
    { key: "international_friction", name: "International Friction (USPTO/EPO)", score: scores.international_friction || 0, level: levels.international_friction || "LOW", desc: drivers.international_friction || [] },
  ];

  container.innerHTML = axesConfig.map((axis) => {
    const fillClass = axis.score >= 70 ? "fill-high" : axis.score >= 45 ? "fill-medium" : "fill-low";
    const badgeClass = axis.score >= 70 ? "badge-danger" : axis.score >= 45 ? "badge-warning" : "badge-success";
    const driversHtml = Array.isArray(axis.desc) ? axis.desc.map((d) => `• ${d}`).join("<br>") : axis.desc || "";

    return `
      <div class="radar-card">
        <div class="radar-card-title">${axis.name}</div>
        <div class="radar-score-row">
          <span class="radar-score-value">${axis.score}%</span>
          <span class="badge ${badgeClass}">${axis.level} RISK</span>
        </div>
        <div class="progress-bar-bg">
          <div class="progress-bar-fill ${fillClass}" style="width:${axis.score}%"></div>
        </div>
        <div class="radar-drivers">${driversHtml}</div>
      </div>
    `;
  }).join("");
}

function renderBotanicals(botanicals) {
  const container = document.getElementById("botanicals-container");
  const badge = document.getElementById("bot-count-badge");
  if (!container) return;

  if (badge) badge.textContent = `${botanicals.length} Identified`;

  if (!botanicals || botanicals.length === 0) {
    container.innerHTML = `
      <div class="empty-botanicals-box">
        <p class="muted">No classical Ayurvedic botanicals detected from the static index. Custom synthetic or proprietary components will be evaluated under general patent criteria.</p>
      </div>`;
    return;
  }

  container.innerHTML = botanicals.map((b) => `
    <div class="botanical-card">
      <div class="bot-header">
        <h4>${escapeHtml(b.matched_name)} <em>(${escapeHtml(b.latin_name)})</em></h4>
        <span class="sanskrit-pill">Sanskrit: ${escapeHtml(b.sanskrit_name)}</span>
      </div>
      <div class="bot-body">
        <p><strong>Classical Text:</strong> <span>${escapeHtml(b.classical_text)}</span></p>
        <p><strong>Traditional Uses:</strong> <span>${(b.traditional_uses || []).join(", ")}</span></p>
        <p><strong>Landmark Legal Precedent:</strong> <span class="precedent-text">${escapeHtml(b.landmark_precedent)}</span></p>
      </div>
    </div>
  `).join("");
}

function renderPriorArt(references) {
  const container = document.getElementById("prior-art-container");
  if (!container) return;

  if (!references || references.length === 0) {
    container.innerHTML = `<p class="muted">No direct statutory citations retrieved.</p>`;
    return;
  }

  container.innerHTML = references.map((r, i) => `
    <div class="prior-art-item-card">
      <div class="pa-header">
        <span class="badge badge-primary">Evidence #${r.index || i + 1}</span>
        <h4>${escapeHtml(r.title || "Statutory Record")}</h4>
        <span class="pa-score">Relevance: ${Math.round((r.relevance_score || 0.8) * 100)}%</span>
      </div>
      <div class="pa-meta">
        <span><strong>Authority:</strong> ${escapeHtml(r.authority || "Official Authority")}</span>
        <span><strong>Jurisdiction:</strong> ${escapeHtml(r.jurisdiction || "India")}</span>
      </div>
      <p class="pa-excerpt">"${escapeHtml(r.excerpt || "")}"</p>
      <div class="pa-footer">
        ${r.source_url ? `<a href="${r.source_url}" target="_blank" rel="noopener" class="pa-link">View Official Gazette / Statute ↗</a>` : '<span class="muted">Official URL unavailable</span>'}
      </div>
    </div>
  `).join("");
}

async function exportReport(format = "html") {
  if (!latestAnalysisPayload) {
    alert("Please run an innovation analysis first.");
    return;
  }

  try {
    const payload = {
      format: format,
      answer_payload: latestAnalysisPayload,
    };

    const data = await apiFetch("/api/reports", {
      method: "POST",
      body: JSON.stringify(payload),
    });

    if (data.success && data.download_url) {
      window.open(data.download_url, "_blank");
    } else {
      alert("Failed to export report: " + (data.error || "Unknown error"));
    }
  } catch (err) {
    console.error("Export error:", err);
    alert("Error downloading report.");
  }
}
