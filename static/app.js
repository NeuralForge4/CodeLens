
const codeInput = document.getElementById("codeInput");
const fileInput = document.getElementById("fileInput");
const fileName = document.getElementById("fileName");
const analyzeBtn = document.getElementById("analyzeBtn");
const statusBox = document.getElementById("status");
const results = document.getElementById("results");

const newCodeBtn = document.getElementById("newCodeBtn");
const copyResultBtn = document.getElementById("copyResultBtn");
const downloadReportBtn = document.getElementById("downloadReportBtn");
const resetBtn = document.getElementById("resetBtn");

let latestData = null;

fileInput.addEventListener("change", async () => {
  const file = fileInput.files[0];
  if (!file) return;

  if (!file.name.toLowerCase().endsWith(".py")) {
    showStatus("Please choose a .py file.", true);
    fileInput.value = "";
    return;
  }

  codeInput.value = await file.text();
  fileName.textContent = file.name;

  clearResults();
  showStatus(`Loaded ${file.name}`);
});

function showStatus(message, error = false) {
  statusBox.textContent = message;
  statusBox.className = error ? "status error" : "status";
}

function escapeHTML(value) {
  return String(value).replace(/[&<>"']/g, c =>
    ({
      "&": "&amp;",
      "<": "&lt;",
      ">": "&gt;",
      '"': "&quot;",
      "'": "&#39;"
    }[c])
  );
}

function clearResults() {
  latestData = null;
  results.classList.add("hidden");

  document.getElementById("metrics").innerHTML = "";
  document.getElementById("findings").innerHTML = "";
  document.getElementById("complexity").innerHTML = "";
  document.getElementById("notes").innerHTML = "";

  document.getElementById("findingCount").textContent = "0";
}

analyzeBtn.addEventListener("click", async () => {
  const code = codeInput.value;

  if (!code.trim()) {
    return showStatus("Paste or upload Python code first.", true);
  }

  analyzeBtn.disabled = true;
  analyzeBtn.textContent = "Analyzing…";
  clearResults();

  showStatus("Running syntax, AST, lint and complexity checks…");

  try {
    const response = await fetch("/analyze", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        code,
        filename: fileName.textContent
      })
    });

    const data = await response.json();

    if (!response.ok) {
      throw new Error(data.error || "Request failed");
    }

    latestData = data;
    renderResults(data);

    results.classList.remove("hidden");
    showStatus("Analysis complete.");

    results.scrollIntoView({
      behavior: "smooth",
      block: "start"
    });

  } catch (err) {
    showStatus(err.message, true);
  } finally {
    analyzeBtn.disabled = false;
    analyzeBtn.innerHTML = 'Analyze code <span>→</span>';
  }
});

function renderResults(data) {
  const s = data.summary;

  document.getElementById("resultTitle").textContent = data.filename;

  const mlScore = s.ml_defect_score ?? s.codebert_defect_probability;

  const metrics = [
    [
      "FINDINGS",
      s.findings,
      `${s.high} high · ${s.warnings} warnings`
    ],
    [
      "LINES OF CODE",
      s.nonblank_lines,
      `${s.lines} total lines`
    ],
    [
      "HEURISTIC RISK",
      `${s.heuristic_risk}%`,
      "Rule-based indicator"
    ],
    [
      "ML DEFECT SCORE",
      mlScore == null ? "—" : `${mlScore}%`,
      "Classifier score, not calibrated probability"
    ]
  ];

  document.getElementById("metrics").innerHTML = metrics.map(m =>
    `<div class="metric">
      <small>${m[0]}</small>
      <strong>${m[1]}</strong>
      <em>${m[2]}</em>
    </div>`
  ).join("");

  document.getElementById("findingCount").textContent =
    data.findings.length;

  const findings = document.getElementById("findings");

  if (!data.findings.length) {
    findings.innerHTML =
      '<div class="empty">No findings from the enabled checks. This does not guarantee the code is defect-free.</div>';
  } else {
    findings.innerHTML = data.findings.map(f =>
      `<div class="finding">
        <div class="finding-top">
          <span class="severity ${escapeHTML(f.severity)}">
            ${escapeHTML(f.severity)}
          </span>
          <small>Line ${f.line} · ${escapeHTML(f.tool)}</small>
        </div>
        <p>${escapeHTML(f.message)}</p>
        <small>Suggestion: ${escapeHTML(f.suggestion || "Review this code.")}</small>
      </div>`
    ).join("");
  }

  const complexity = document.getElementById("complexity");

  complexity.innerHTML = data.complexity.length
    ? data.complexity.map(c =>
      `<div class="complexity-item">
        <div>${escapeHTML(c.name)} <span>· line ${c.line}</span></div>
        <strong>${c.complexity} <span>${escapeHTML(c.rank)}</span></strong>
      </div>`
    ).join("")
    : '<div class="empty">No complexity data available. Install Radon or add functions to analyze.</div>';

  document.getElementById("notes").innerHTML =
    data.notes.map(n => `<p>ⓘ ${escapeHTML(n)}</p>`).join("");
}

// Build a readable text report from the latest analysis.
function buildReport() {
  if (!latestData) return "";

  const data = latestData;
  const s = data.summary;
  const mlScore = s.ml_defect_score ?? s.codebert_defect_probability;

  let report = "";

  report += "CODELENS - PYTHON CODE QUALITY ANALYSIS REPORT\n";
  report += "================================================\n\n";

  report += `File: ${data.filename}\n`;
  report += `Date: ${new Date().toLocaleString()}\n\n`;

  report += "SUMMARY\n";
  report += "-------\n";
  report += `Total lines: ${s.lines}\n`;
  report += `Nonblank lines: ${s.nonblank_lines}\n`;
  report += `Total findings: ${s.findings}\n`;
  report += `High severity: ${s.high}\n`;
  report += `Warnings: ${s.warnings}\n`;
  report += `Heuristic risk: ${s.heuristic_risk}%\n`;
  report += `ML defect score: ${mlScore == null ? "Unavailable" : mlScore + "%"}\n\n`;

  report += "ISSUES AND RECOMMENDATIONS\n";
  report += "--------------------------\n";

  if (data.findings.length === 0) {
    report += "No findings from the enabled checks.\n";
  } else {
    data.findings.forEach((f, index) => {
      report += `\n${index + 1}. ${f.severity.toUpperCase()}\n`;
      report += `Tool: ${f.tool}\n`;
      report += `Line: ${f.line}\n`;
      report += `Issue: ${f.message}\n`;
      report += `Suggestion: ${f.suggestion || "Review this code."}\n`;
    });
  }

  report += "\n\nCOMPLEXITY PROFILE\n";
  report += "------------------\n";

  if (data.complexity.length === 0) {
    report += "No complexity data available.\n";
  } else {
    data.complexity.forEach(c => {
      report += `${c.name} | Line ${c.line} | Complexity: ${c.complexity} | ${c.rank}\n`;
    });
  }

  report += "\nNOTES\n";
  report += "-----\n";

  if (data.notes.length === 0) {
    report += "No additional notes.\n";
  } else {
    data.notes.forEach(note => {
      report += `- ${note}\n`;
    });
  }

  report += "\nDISCLAIMER\n";
  report += "-----------\n";
  report += "Risk indicators are estimates, not proof that code contains or is free of defects.\n";
  report += "Review all findings before changing code.\n";

  return report;
}

// Copy Result button.
copyResultBtn.addEventListener("click", async () => {
  if (!latestData) {
    return showStatus("Analyze code before copying the result.", true);
  }

  try {
    await navigator.clipboard.writeText(buildReport());
    showStatus("Analysis report copied successfully!");
  } catch (err) {
    showStatus("Could not copy the report. Check clipboard permissions.", true);
  }
});

// Download Report button.
downloadReportBtn.addEventListener("click", () => {
  if (!latestData) {
    return showStatus("Analyze code before downloading the report.", true);
  }

  const report = buildReport();
  const blob = new Blob([report], {
    type: "text/plain;charset=utf-8"
  });

  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");

  link.href = url;
  link.download = "CodeLens_Analysis_Report.txt";

  document.body.appendChild(link);
  link.click();
  link.remove();

  URL.revokeObjectURL(url);

  showStatus("Analysis report downloaded successfully!");
});

// Analyze New Code button.
newCodeBtn.addEventListener("click", () => {
  codeInput.value = "";
  fileInput.value = "";
  fileName.textContent = "pasted_code.py";

  clearResults();
  showStatus("Ready for new Python code.");

  codeInput.focus();
  window.scrollTo({
    top: 0,
    behavior: "smooth"
  });
});

// Existing Clear Results button: hides results but keeps editor content.
resetBtn.addEventListener("click", () => {
  clearResults();
  showStatus("Previous results cleared.");

  window.scrollTo({
    top: 0,
    behavior: "smooth"
  });
});
