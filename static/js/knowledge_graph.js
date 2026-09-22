// IP-SAKTI SAHAYAK — Interactive Force-Directed Knowledge Graph Engine

let graphNodes = [];
let graphEdges = [];
let activeFilteredNodes = [];
let activeFilteredEdges = [];
let selectedNode = null;
let activeTypeFilters = new Set(["botanical", "active", "classical_text", "law_section", "authority", "case_law", "treaty", "formulation", "institution"]);

const typeColors = {
  botanical: "#10b981",       // Emerald Green
  active: "#06b6d4",          // Cyan
  classical_text: "#f59e0b",  // Amber
  formulation: "#8b5cf6",     // Purple
  law_section: "#ef4444",     // Red / Coral
  regulation: "#ec4899",      // Pink
  authority: "#3b82f6",       // Blue
  case_law: "#6366f1",        // Indigo
  treaty: "#d97706",          // Gold
  institution: "#14b8a6",     // Teal
};

document.addEventListener("DOMContentLoaded", async () => {
  await loadKnowledgeGraph();
});

async function loadKnowledgeGraph() {
  const container = document.getElementById("graph-container");
  if (!container) return;

  container.innerHTML = '<p class="muted" style="padding:40px;text-align:center;">Initializing Knowledge Graph Ontology…</p>';

  try {
    const data = await apiFetch("/api/knowledge-graph");
    if (!data.success || !data.graph) {
      container.innerHTML = '<p class="error-text">Failed to load knowledge graph data.</p>';
      return;
    }

    graphNodes = data.graph.nodes || [];
    graphEdges = data.graph.edges || [];

    applyFiltersAndRender();
  } catch (err) {
    console.error("Knowledge graph error:", err);
    container.innerHTML = '<p class="error-text">Connection error loading graph.</p>';
  }
}

function toggleNodeType(type) {
  if (activeTypeFilters.has(type)) {
    activeTypeFilters.delete(type);
  } else {
    activeTypeFilters.add(type);
  }
  applyFiltersAndRender();
}

function filterGraphSearch() {
  const query = (document.getElementById("kg-search")?.value || "").toLowerCase().trim();
  applyFiltersAndRender(query);
}

function resetGraphView() {
  const searchInput = document.getElementById("kg-search");
  if (searchInput) searchInput.value = "";
  activeTypeFilters = new Set(["botanical", "active", "classical_text", "law_section", "authority", "case_law", "treaty", "formulation", "institution"]);
  document.querySelectorAll(".kg-filter-chip input").forEach((cb) => (cb.checked = true));
  applyFiltersAndRender();
}

function applyFiltersAndRender(searchQuery = "") {
  activeFilteredNodes = graphNodes.filter((n) => {
    const matchesType = activeTypeFilters.has(n.type);
    const matchesSearch = !searchQuery || n.label.toLowerCase().includes(searchQuery) || n.id.toLowerCase().includes(searchQuery);
    return matchesType && matchesSearch;
  });

  const nodeIds = new Set(activeFilteredNodes.map((n) => n.id));
  activeFilteredEdges = graphEdges.filter((e) => nodeIds.has(e.source) && nodeIds.has(e.target));

  const label = document.getElementById("kg-node-count-label");
  if (label) {
    label.textContent = `Displaying ${activeFilteredNodes.length} Entities & ${activeFilteredEdges.length} Inter-Domain Relationships`;
  }

  renderGraphSVG();
}

function renderGraphSVG() {
  const container = document.getElementById("graph-container");
  if (!container) return;

  const width = container.clientWidth || 740;
  const height = 540;
  const cx = width / 2;
  const cy = height / 2;

  // Compute Layout Positions (Grouped force layout simulation)
  const groupAngles = {
    Botanicals: 0,
    Actives: (2 * Math.PI) / 6,
    "Classical Texts": (4 * Math.PI) / 6,
    Statutes: (6 * Math.PI) / 6,
    Authorities: (8 * Math.PI) / 6,
    "Landmark Cases": (10 * Math.PI) / 6,
  };

  const positionedNodes = {};
  activeFilteredNodes.forEach((node, idx) => {
    const baseAngle = groupAngles[node.group] || (2 * Math.PI * idx) / Math.max(1, activeFilteredNodes.length);
    const offset = (idx % 4) * 28;
    const dist = 140 + offset;
    positionedNodes[node.id] = {
      ...node,
      x: cx + dist * Math.cos(baseAngle + (idx * 0.35)),
      y: cy + dist * Math.sin(baseAngle + (idx * 0.35)),
    };
  });

  // Clamp within SVG boundary
  Object.values(positionedNodes).forEach((n) => {
    n.x = Math.max(45, Math.min(width - 45, n.x));
    n.y = Math.max(45, Math.min(height - 45, n.y));
  });

  let edgesSvg = "";
  activeFilteredEdges.forEach((e) => {
    const s = positionedNodes[e.source];
    const t = positionedNodes[e.target];
    if (!s || !t) return;

    const isHighlight = selectedNode && (selectedNode.id === e.source || selectedNode.id === e.target);
    const strokeColor = isHighlight ? "var(--primary)" : "var(--border)";
    const strokeWidth = isHighlight ? 2.5 : 1.2;

    edgesSvg += `<line x1="${s.x}" y1="${s.y}" x2="${t.x}" y2="${t.y}" stroke="${strokeColor}" stroke-width="${strokeWidth}" stroke-opacity="${isHighlight ? 1.0 : 0.6}" />`;
  });

  let nodesSvg = "";
  Object.values(positionedNodes).forEach((n) => {
    const isSelected = selectedNode && selectedNode.id === n.id;
    const color = typeColors[n.type] || "var(--primary)";
    const r = isSelected ? 24 : 18;
    const strokeWidth = isSelected ? 3.5 : 1.5;

    nodesSvg += `
      <g class="graph-node-group" style="cursor:pointer;" onclick="selectGraphNode('${n.id}')">
        <circle cx="${n.x}" cy="${n.y}" r="${r}" fill="${color}" stroke="${isSelected ? '#fff' : 'var(--border)'}" stroke-width="${strokeWidth}" opacity="0.92"/>
        <text x="${n.x}" y="${n.y + r + 13}" text-anchor="middle" font-size="10" font-weight="${isSelected ? '700' : '600'}" fill="var(--text-main)" font-family="sans-serif">
          ${escapeHtml(n.label.length > 20 ? n.label.slice(0, 18) + '…' : n.label)}
        </text>
      </g>
    `;
  });

  container.innerHTML = `
    <svg width="100%" height="${height}" viewBox="0 0 ${width} ${height}" style="background:var(--bg-card);border-radius:12px;">
      ${edgesSvg}
      ${nodesSvg}
    </svg>
  `;
}

function selectGraphNode(nodeId) {
  selectedNode = graphNodes.find((n) => n.id === nodeId);
  if (!selectedNode) return;

  renderGraphSVG();

  const labelEl = document.getElementById("inspector-label");
  const typeEl = document.getElementById("inspector-type");
  const descEl = document.getElementById("inspector-desc");
  const connsBox = document.getElementById("inspector-connections-box");
  const connsList = document.getElementById("inspector-edges-list");

  labelEl.textContent = selectedNode.label;
  typeEl.textContent = (selectedNode.type || "Entity").toUpperCase();
  typeEl.style.backgroundColor = typeColors[selectedNode.type] || "var(--primary)";
  typeEl.style.color = "#fff";

  // Descriptions by type
  const descriptions = {
    botanical: "Classical Ayurvedic botanical medicinal plant documented in the Ayurvedic Pharmacopoeia of India (API) and classical Samhita treatises.",
    active: "Purified or standardized phytochemical constituent capable of therapeutic activity; evaluated under Section 3(d) for enhanced efficacy.",
    classical_text: "Authoritative Sanskrit medical treatise specified under the First Schedule of the Drugs and Cosmetics Act, 1940.",
    law_section: "Statutory provision establishing patent eligibility criteria, exclusions, or mandatory disclosure obligations.",
    authority: "Regulatory or statutory body empowered with administrative jurisdiction over intellectual property, AYUSH, or biological diversity.",
    case_law: "Landmark legal precedent establishing global and domestic interpretation of Traditional Knowledge prior art and Section 3(d).",
  };
  descEl.textContent = descriptions[selectedNode.type] || "Ontology node in the IP-SAKTI intelligence network.";

  // Find incoming & outgoing edges
  const relatedEdges = graphEdges.filter((e) => e.source === selectedNode.id || e.target === selectedNode.id);
  if (relatedEdges.length > 0) {
    connsBox.style.display = "block";
    connsList.innerHTML = relatedEdges.map((e) => {
      const isOut = e.source === selectedNode.id;
      const otherId = isOut ? e.target : e.source;
      const otherNode = graphNodes.find((n) => n.id === otherId);
      const otherLabel = otherNode ? otherNode.label : otherId;
      const relName = e.relation.replace(/_/g, " ");

      return `<li><strong>${escapeHtml(relName)}</strong> ➔ <span>${escapeHtml(otherLabel)}</span></li>`;
    }).join("");
  } else {
    connsBox.style.display = "none";
  }
}
