// IP-SAKTI SAHAYAK — Comparative IP Matrix Client

const COMPARATIVE_DATA = {
  patentability: {
    india: "Section 3(d) excludes new forms, derivatives, or new uses of known substances unless enhanced therapeutic efficacy is proven (Novartis AG v. Union of India 2013). Section 3(p) bars traditional knowledge aggregations. Section 3(e) bars mere admixtures.",
    us: "35 U.S.C. 101/102/103. Under the Alice/Mayo framework, natural products and unmodified botanical extracts are patent-ineligible natural phenomena. However, isolated/purified fractions with synthetic alterations or novel synergy are patentable.",
    europe: "EPC Articles 52, 54, 56. Methods of medical treatment are excluded under Art. 53(c), but first and second medical uses of known substances are patentable. Requires proven technical effect and non-obvious therapeutic indication.",
    international: "WTO TRIPS Article 27 permits members to exclude diagnostic, therapeutic, and surgical methods, and allows exclusions to protect human health and the environment.",
  },
  traditional_knowledge: {
    india: "Codified in CSIR Traditional Knowledge Digital Library (TKDL) covering >4.5 lakh formulations from Charaka, Sushruta, Unani, and Siddha. Section 3(p) provides an explicit statutory bar on traditional knowledge claims.",
    us: "USPTO has an official TKDL search agreement. Traditional knowledge is examined as non-patent prior art against 35 U.S.C. 102 novelty. Landmark: US Patent 5,401,504 on Turmeric wound healing was revoked upon Indian TKDL challenge.",
    europe: "EPO systematically integrates TKDL into examiner search workflows. Landmark: European Patent 0436257 on Neem fungicidal properties was successfully revoked on traditional Indian prior art grounds.",
    international: "2024 WIPO Treaty on Intellectual Property, Genetic Resources and Associated Traditional Knowledge mandates patent applicants to disclose country of origin and indigenous traditional knowledge providers.",
  },
  biodiversity_abs: {
    india: "Mandatory Section 6 prior approval from National Biodiversity Authority (NBA) before applying for any IPR. Access and Benefit Sharing (ABS) requires fee of 0.1%–0.5% of ex-factory commercial sales or 3%–5% of patent royalties.",
    us: "United States has not ratified the UN Convention on Biological Diversity (CBD) or the Nagoya Protocol. No domestic federal ABS clearance or benefit-sharing checkpoint is required for US patent filing.",
    europe: "EU Regulation 511/2014 strictly enforces Nagoya Protocol compliance. Due diligence declarations must be submitted when receiving research funding or commercializing products derived from foreign genetic resources.",
    international: "Nagoya Protocol on Access to Genetic Resources and Benefit-Sharing establishes international Prior Informed Consent (PIC) and Mutually Agreed Terms (MAT) obligations.",
  },
  regulatory_approval: {
    india: "Drugs and Cosmetics Act, Rule 158B. Classical formulations listed in First Schedule authoritative texts require textual citation only. Proprietary formulations require published safety/toxicity data and Schedule T GMP compliance.",
    us: "FDA Botanical Drug Guidance. Complex herbal mixtures require full CMC batch-to-batch consistency controls, non-clinical toxicology, and multi-phase IND/NDA clinical trials before commercial marketing.",
    europe: "EMA Traditional Herbal Medicinal Products Directive (THMPD 2004/24/EC). Simplified registration for herbal products with ≥30 years documented medicinal use (including ≥15 years within the EU).",
    international: "WHO Guidelines on Good Agricultural and Collection Practices (GACP) and Quality Control Methods for Herbal Materials set baseline international quality benchmarks.",
  },
};

function showTopic(topicKey) {
  const tabs = document.querySelectorAll("#matrix-tabs .tab-btn");
  tabs.forEach((t) => t.classList.remove("active"));

  // Set active tab
  const btn = Array.from(tabs).find((b) => b.getAttribute("onclick")?.includes(topicKey));
  if (btn) btn.classList.add("active");

  const data = COMPARATIVE_DATA[topicKey];
  if (!data) return;

  document.getElementById("cell-india").innerHTML = `<strong>IP India / NBA / AYUSH:</strong><br>${escapeHtml(data.india)}`;
  document.getElementById("cell-us").innerHTML = `<strong>USPTO / FDA:</strong><br>${escapeHtml(data.us)}`;
  document.getElementById("cell-europe").innerHTML = `<strong>EPO / EMA:</strong><br>${escapeHtml(data.europe)}`;
  document.getElementById("cell-intl").innerHTML = `<strong>WIPO / Treaties:</strong><br>${escapeHtml(data.international)}`;
}

document.addEventListener("DOMContentLoaded", () => {
  showTopic("patentability");

  const form = document.getElementById("comparative-form");
  if (!form) return;

  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    const query = document.getElementById("comp-query").value.trim();
    const focus = document.getElementById("comp-focus").value;
    const btn = document.getElementById("comp-btn");
    const resultBox = document.getElementById("comp-custom-result");
    const resultTitle = document.getElementById("comp-result-title");
    const resultBody = document.getElementById("comp-result-body");

    if (!query) return;

    btn.disabled = true;
    btn.textContent = "Synthesizing Comparative Analysis…";
    resultBox.style.display = "none";

    try {
      const data = await apiFetch("/api/comparative-ip", {
        method: "POST",
        body: JSON.stringify({ query: query, domain_focus: focus }),
      });

      if (!data.success) {
        alert(data.error || "Comparative query failed.");
        return;
      }

      resultTitle.textContent = `Comparative Matrix for: "${query}" (${focus})`;
      resultBody.textContent = data.ai_synthesis || "Comparative synthesis complete.";
      resultBox.style.display = "block";
      resultBox.scrollIntoView({ behavior: "smooth", block: "nearest" });
    } catch (err) {
      console.error("Comparative error:", err);
      alert("Error generating comparative analysis.");
    } finally {
      btn.disabled = false;
      btn.textContent = "Generate Comparative Assessment";
    }
  });
});
