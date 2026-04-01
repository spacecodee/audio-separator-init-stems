const METRICS = ["SDR", "SIR", "SAR", "ISR"];
const BEST_STEM_VALUE = "best_available";

const state = {
  sourceName: "models.json",
  models: [],
  filtered: [],
  allArchitectures: [],
  allStems: [],
  selectedArchitectures: new Set(),
  searchText: "",
  stemFilter: "any",
  scoreStem: BEST_STEM_VALUE,
  selectedMetric: "SDR",
  minScore: -5,
  sortBy: "metric_desc",
  page: 1,
  pageSize: 50,
  selectedModelId: null,
  compareIds: new Set(),
  compareStem: BEST_STEM_VALUE,
  compareMetric: "SDR",
};

const chartRefs = {
  arch: null,
  stem: null,
  top: null,
  compare: null,
};

const dom = {};

document.addEventListener("DOMContentLoaded", () => {
  cacheDom();
  bindGlobalEvents();
  loadFromPath("models.json");
});

function cacheDom() {
  dom.reloadBtn = document.getElementById("reloadBtn");
  dom.uploadInput = document.getElementById("jsonUploadInput");
  dom.loadStatus = document.getElementById("loadStatus");
  dom.totalModelsInline = document.getElementById("totalModelsInline");

  dom.searchInput = document.getElementById("searchInput");
  dom.stemFilterSelect = document.getElementById("stemFilterSelect");
  dom.scoreStemSelect = document.getElementById("scoreStemSelect");
  dom.metricSelect = document.getElementById("metricSelect");
  dom.minMetricRange = document.getElementById("minMetricRange");
  dom.minMetricNumber = document.getElementById("minMetricNumber");
  dom.sortSelect = document.getElementById("sortSelect");
  dom.archFilterGroup = document.getElementById("archFilterGroup");
  dom.archAllBtn = document.getElementById("archAllBtn");
  dom.archNoneBtn = document.getElementById("archNoneBtn");
  dom.resetFiltersBtn = document.getElementById("resetFiltersBtn");

  dom.statVisible = document.getElementById("statVisible");
  dom.statTotal = document.getElementById("statTotal");
  dom.statArch = document.getElementById("statArch");
  dom.statStems = document.getElementById("statStems");
  dom.statMetricAvg = document.getElementById("statMetricAvg");
  dom.statCoverage = document.getElementById("statCoverage");

  dom.tableSummary = document.getElementById("tableSummary");
  dom.pageSizeSelect = document.getElementById("pageSizeSelect");
  dom.prevPageBtn = document.getElementById("prevPageBtn");
  dom.nextPageBtn = document.getElementById("nextPageBtn");
  dom.pageIndicator = document.getElementById("pageIndicator");
  dom.modelsTableBody = document.getElementById("modelsTableBody");

  dom.modelDetailEmpty = document.getElementById("modelDetailEmpty");
  dom.modelDetailContent = document.getElementById("modelDetailContent");

  dom.compareStemSelect = document.getElementById("compareStemSelect");
  dom.compareMetricSelect = document.getElementById("compareMetricSelect");
  dom.clearCompareBtn = document.getElementById("clearCompareBtn");
  dom.compareSelection = document.getElementById("compareSelection");
  dom.compareRanking = document.getElementById("compareRanking");

  dom.archChart = document.getElementById("archChart");
  dom.stemChart = document.getElementById("stemChart");
  dom.topModelsChart = document.getElementById("topModelsChart");
  dom.compareChart = document.getElementById("compareChart");
}

function bindGlobalEvents() {
  dom.reloadBtn.addEventListener("click", () => loadFromPath("models.json"));

  dom.uploadInput.addEventListener("change", async (event) => {
    const file = event.target.files?.[0];
    if (!file) return;

    try {
      setStatus(`Cargando ${file.name}...`);
      const text = await file.text();
      const parsed = JSON.parse(text);
      loadFromObject(parsed, file.name);
    } catch (error) {
      setStatus(`No se pudo cargar JSON: ${error.message}`, true);
    } finally {
      event.target.value = "";
    }
  });

  dom.searchInput.addEventListener("input", (event) => {
    state.searchText = event.target.value.trim().toLowerCase();
    state.page = 1;
    applyFilters();
  });

  dom.stemFilterSelect.addEventListener("change", (event) => {
    state.stemFilter = event.target.value;
    state.page = 1;
    applyFilters();
  });

  dom.scoreStemSelect.addEventListener("change", (event) => {
    state.scoreStem = event.target.value;
    state.page = 1;
    applyFilters();
  });

  dom.metricSelect.addEventListener("change", (event) => {
    state.selectedMetric = event.target.value;
    state.page = 1;
    applyFilters();
  });

  dom.minMetricRange.addEventListener("input", (event) => {
    state.minScore = Number(event.target.value);
    dom.minMetricNumber.value = String(state.minScore);
    state.page = 1;
    applyFilters();
  });

  dom.minMetricNumber.addEventListener("input", (event) => {
    state.minScore = Number(event.target.value);
    if (!Number.isFinite(state.minScore)) state.minScore = -5;
    dom.minMetricRange.value = String(state.minScore);
    state.page = 1;
    applyFilters();
  });

  dom.sortSelect.addEventListener("change", (event) => {
    state.sortBy = event.target.value;
    state.page = 1;
    applyFilters();
  });

  dom.archFilterGroup.addEventListener("change", (event) => {
    if (!(event.target instanceof HTMLInputElement)) return;
    if (event.target.name !== "archFilter") return;

    const arch = event.target.value;
    if (event.target.checked) state.selectedArchitectures.add(arch);
    else state.selectedArchitectures.delete(arch);

    state.page = 1;
    applyFilters();
  });

  dom.archAllBtn.addEventListener("click", () => {
    state.selectedArchitectures = new Set(state.allArchitectures);
    renderArchitectureFilters();
    state.page = 1;
    applyFilters();
  });

  dom.archNoneBtn.addEventListener("click", () => {
    state.selectedArchitectures.clear();
    renderArchitectureFilters();
    state.page = 1;
    applyFilters();
  });

  dom.resetFiltersBtn.addEventListener("click", resetFilters);

  dom.pageSizeSelect.addEventListener("change", (event) => {
    state.pageSize = Number(event.target.value);
    state.page = 1;
    renderTable();
  });

  dom.prevPageBtn.addEventListener("click", () => {
    if (state.page <= 1) return;
    state.page -= 1;
    renderTable();
  });

  dom.nextPageBtn.addEventListener("click", () => {
    const totalPages = getTotalPages();
    if (state.page >= totalPages) return;
    state.page += 1;
    renderTable();
  });

  dom.modelsTableBody.addEventListener("click", (event) => {
    const compareButton = event.target.closest("button.compare-toggle");
    if (compareButton) {
      event.stopPropagation();
      const modelId = compareButton.dataset.modelId;
      toggleCompare(modelId);
      return;
    }

    const row = event.target.closest("tr[data-model-id]");
    if (!row) return;
    state.selectedModelId = row.dataset.modelId;
    renderTable();
    renderModelDetails();
  });

  dom.compareStemSelect.addEventListener("change", (event) => {
    state.compareStem = event.target.value;
    renderComparison();
  });

  dom.compareMetricSelect.addEventListener("change", (event) => {
    state.compareMetric = event.target.value;
    renderComparison();
  });

  dom.clearCompareBtn.addEventListener("click", () => {
    state.compareIds.clear();
    renderTable();
    renderComparison();
  });

  dom.compareSelection.addEventListener("click", (event) => {
    const removeButton = event.target.closest("button[data-remove-id]");
    if (!removeButton) return;
    const modelId = removeButton.dataset.removeId;
    state.compareIds.delete(modelId);
    renderTable();
    renderComparison();
  });
}

async function loadFromPath(path) {
  try {
    setStatus(`Cargando ${path}...`);
    const response = await fetch(path, { cache: "no-store" });
    if (!response.ok) {
      throw new Error(`HTTP ${response.status} ${response.statusText}`);
    }
    const json = await response.json();
    loadFromObject(json, path);
  } catch (error) {
    setStatus(
      "No se pudo cargar models.json automaticamente. Usa el boton de carga manual.",
      true
    );
    console.error(error);
  }
}

function loadFromObject(raw, sourceName) {
  const parsed = normalizeModels(raw);
  if (!parsed.length) {
    setStatus("JSON cargado pero sin modelos validos", true);
    return;
  }

  state.sourceName = sourceName;
  state.models = parsed;
  state.filtered = [...parsed];
  state.allArchitectures = [...new Set(parsed.map((model) => model.arch))].sort((a, b) =>
    a.localeCompare(b)
  );
  state.allStems = getAllStems(parsed);
  state.selectedArchitectures = new Set(state.allArchitectures);

  setStatus(`Fuente: ${sourceName}. Modelos cargados: ${parsed.length}`);
  dom.totalModelsInline.textContent = String(parsed.length);

  populateStemSelect(dom.stemFilterSelect, {
    includeAny: true,
    includeBest: false,
    stems: state.allStems,
    selected: "any",
  });

  populateStemSelect(dom.scoreStemSelect, {
    includeAny: false,
    includeBest: true,
    stems: state.allStems,
    selected: BEST_STEM_VALUE,
  });

  populateStemSelect(dom.compareStemSelect, {
    includeAny: false,
    includeBest: true,
    stems: state.allStems,
    selected: BEST_STEM_VALUE,
  });

  renderArchitectureFilters();
  resetFilters();
}

function normalizeModels(raw) {
  const models = [];
  let index = 1;

  for (const [arch, archModels] of Object.entries(raw || {})) {
    for (const [friendlyName, meta] of Object.entries(archModels || {})) {
      models.push(buildModelEntry(arch, friendlyName, meta, index));
      index += 1;
    }
  }

  return models;
}

function buildModelEntry(arch, friendlyName, meta, index) {
  const safeMeta = meta || {};
  const scoreObject = getScoreObject(safeMeta);
  const normalizedScores = normalizeScoresByStem(scoreObject);

  return {
    id: `m-${index}`,
    arch: safeString(arch),
    friendlyName: safeString(friendlyName),
    filename: safeString(safeMeta.filename),
    stems: getMergedStems(safeMeta, scoreObject),
    targetStem: safeString(safeMeta.target_stem),
    downloadFiles: getDownloadFiles(safeMeta),
    scores: normalizedScores,
    bestByMetric: getBestByMetric(normalizedScores),
  };
}

function getScoreObject(meta) {
  if (!meta.scores || typeof meta.scores !== "object") return {};
  return meta.scores;
}

function getMergedStems(meta, scoreObject) {
  const stemsFromMeta = Array.isArray(meta.stems) ? meta.stems.map(safeString).filter(Boolean) : [];
  const stemsFromScores = Object.keys(scoreObject);
  return [...new Set([...stemsFromMeta, ...stemsFromScores])].filter(Boolean);
}

function getDownloadFiles(meta) {
  return Array.isArray(meta.download_files) ? meta.download_files.map(safeString).filter(Boolean) : [];
}

function normalizeScoresByStem(scoreObject) {
  const normalizedScores = {};

  for (const [stemName, metrics] of Object.entries(scoreObject)) {
    if (!metrics || typeof metrics !== "object") continue;

    const normalizedMetrics = {};
    for (const metric of METRICS) {
      const value = Number(metrics[metric]);
      if (Number.isFinite(value)) {
        normalizedMetrics[metric] = value;
      }
    }

    normalizedScores[stemName] = normalizedMetrics;
  }

  return normalizedScores;
}

function getBestByMetric(normalizedScores) {
  const bestByMetric = {};
  for (const metric of METRICS) {
    bestByMetric[metric] = getBestMetricValue(normalizedScores, metric);
  }
  return bestByMetric;
}

function safeString(value) {
  if (value === null || value === undefined) return "";
  return String(value).trim();
}

function getAllStems(models) {
  const stems = new Set();
  for (const model of models) {
    for (const stem of model.stems) stems.add(stem);
  }
  return [...stems].sort((a, b) => a.localeCompare(b));
}

function populateStemSelect(selectElement, { includeAny, includeBest, stems, selected }) {
  const options = [];
  if (includeAny) options.push({ value: "any", label: "Any stem" });
  if (includeBest) options.push({ value: BEST_STEM_VALUE, label: "Best available stem" });
  for (const stem of stems) {
    options.push({ value: stem, label: stem });
  }

  selectElement.innerHTML = options
    .map((option) => `<option value="${escapeHtml(option.value)}">${escapeHtml(option.label)}</option>`)
    .join("");

  selectElement.value = selected;
}

function resetFilters() {
  state.searchText = "";
  state.stemFilter = "any";
  state.scoreStem = BEST_STEM_VALUE;
  state.selectedMetric = "SDR";
  state.minScore = -5;
  state.sortBy = "metric_desc";
  state.page = 1;

  state.selectedArchitectures = new Set(state.allArchitectures);

  dom.searchInput.value = "";
  dom.stemFilterSelect.value = "any";
  dom.scoreStemSelect.value = BEST_STEM_VALUE;
  dom.metricSelect.value = "SDR";
  dom.minMetricRange.value = "-5";
  dom.minMetricNumber.value = "-5";
  dom.sortSelect.value = "metric_desc";

  renderArchitectureFilters();
  applyFilters();
}

function renderArchitectureFilters() {
  dom.archFilterGroup.innerHTML = state.allArchitectures
    .map((arch) => {
      const checked = state.selectedArchitectures.has(arch) ? "checked" : "";
      return `
        <label class="arch-item">
          <input type="checkbox" name="archFilter" value="${escapeHtml(arch)}" ${checked} />
          <span>${escapeHtml(arch)}</span>
        </label>
      `;
    })
    .join("");
}

function applyFilters() {
  const search = state.searchText;
  const metric = state.selectedMetric;

  let result = state.models.filter((model) => {
    if (state.selectedArchitectures.size > 0 && !state.selectedArchitectures.has(model.arch)) {
      return false;
    }

    if (search) {
      const haystack = `${model.friendlyName} ${model.filename}`.toLowerCase();
      if (!haystack.includes(search)) return false;
    }

    if (state.stemFilter !== "any") {
      if (!hasStem(model, state.stemFilter)) return false;
    }

    const scoreValue = getModelContextMetric(model, metric, state.scoreStem);
    if (scoreValue === null) return false;
    if (scoreValue < state.minScore) return false;

    return true;
  });

  result = sortModels(result);

  state.filtered = result;
  state.page = clampPage(state.page, getTotalPages());

  if (!state.selectedModelId || !state.filtered.some((m) => m.id === state.selectedModelId)) {
    state.selectedModelId = state.filtered[0]?.id || null;
  }

  renderStats();
  renderCharts();
  renderTable();
  renderModelDetails();
  renderComparison();
}

function sortModels(models) {
  const metric = state.selectedMetric;
  const scoreStem = state.scoreStem;

  const clone = [...models];
  clone.sort((a, b) => {
    if (state.sortBy === "metric_desc") {
      const av = getModelContextMetric(a, metric, scoreStem) ?? -Infinity;
      const bv = getModelContextMetric(b, metric, scoreStem) ?? -Infinity;
      return bv - av;
    }

    if (state.sortBy === "metric_asc") {
      const av = getModelContextMetric(a, metric, scoreStem) ?? Infinity;
      const bv = getModelContextMetric(b, metric, scoreStem) ?? Infinity;
      return av - bv;
    }

    if (state.sortBy === "name_asc") {
      return a.friendlyName.localeCompare(b.friendlyName);
    }

    if (state.sortBy === "name_desc") {
      return b.friendlyName.localeCompare(a.friendlyName);
    }

    if (state.sortBy === "arch_name") {
      const archCmp = a.arch.localeCompare(b.arch);
      if (archCmp !== 0) return archCmp;
      return a.friendlyName.localeCompare(b.friendlyName);
    }

    if (state.sortBy === "stems_desc") {
      return b.stems.length - a.stems.length;
    }

    return 0;
  });

  return clone;
}

function renderStats() {
  const total = state.models.length;
  const visible = state.filtered.length;
  const archVisible = new Set(state.filtered.map((model) => model.arch)).size;
  const stemsVisible = getAllStems(state.filtered).length;

  const metricValues = state.filtered
    .map((model) => getModelContextMetric(model, state.selectedMetric, state.scoreStem))
    .filter((value) => value !== null);

  const metricAvg = metricValues.length
    ? metricValues.reduce((sum, value) => sum + value, 0) / metricValues.length
    : null;

  const coverage = visible
    ? (metricValues.length / visible) * 100
    : 0;

  dom.statVisible.textContent = formatInteger(visible);
  dom.statTotal.textContent = formatInteger(total);
  dom.statArch.textContent = formatInteger(archVisible);
  dom.statStems.textContent = formatInteger(stemsVisible);
  dom.statMetricAvg.textContent = metricAvg === null ? "-" : formatFloat(metricAvg);
  dom.statCoverage.textContent = `${formatFloat(coverage)}%`;
}

function renderCharts() {
  if (!globalThis.Chart) {
    setStatus("Chart.js no disponible. La tabla y comparaciones siguen funcionando.", true);
    return;
  }

  renderArchitectureChart();
  renderStemCoverageChart();
  renderTopModelsChart();
}

function renderArchitectureChart() {
  const counts = new Map();
  for (const model of state.filtered) {
    counts.set(model.arch, (counts.get(model.arch) || 0) + 1);
  }

  const labels = [...counts.keys()];
  const data = labels.map((label) => counts.get(label));

  const config = {
    type: "doughnut",
    data: {
      labels,
      datasets: [
        {
          label: "Modelos",
          data,
          backgroundColor: ["#14b8a6", "#0ea5e9", "#f59e0b", "#22c55e", "#f97316", "#a3e635"],
          borderColor: "#0b1320",
          borderWidth: 2,
        },
      ],
    },
    options: chartBaseOptions({
      plugins: {
        legend: { position: "bottom", labels: { color: "#cfe0f7" } },
      },
    }),
  };

  chartRefs.arch = updateChart(chartRefs.arch, dom.archChart, config);
}

function renderStemCoverageChart() {
  const stems = getAllStems(state.filtered);
  const counts = stems.map((stem) =>
    state.filtered.reduce((sum, model) => (hasStem(model, stem) ? sum + 1 : sum), 0)
  );

  const config = {
    type: "bar",
    data: {
      labels: stems,
      datasets: [
        {
          label: "Modelos que incluyen el stem",
          data: counts,
          backgroundColor: "rgba(45, 212, 191, 0.7)",
          borderColor: "rgba(45, 212, 191, 1)",
          borderWidth: 1,
        },
      ],
    },
    options: chartBaseOptions({
      scales: {
        x: {
          ticks: { color: "#cfe0f7" },
          grid: { color: "rgba(120, 144, 172, 0.15)" },
        },
        y: {
          ticks: { color: "#cfe0f7" },
          grid: { color: "rgba(120, 144, 172, 0.15)" },
          beginAtZero: true,
        },
      },
      plugins: {
        legend: { display: false },
      },
    }),
  };

  chartRefs.stem = updateChart(chartRefs.stem, dom.stemChart, config);
}

function renderTopModelsChart() {
  const metric = state.selectedMetric;
  const rows = state.filtered
    .map((model) => ({
      model,
      value: getModelContextMetric(model, metric, state.scoreStem),
    }))
    .filter((entry) => entry.value !== null)
    .sort((a, b) => b.value - a.value)
    .slice(0, 12);

  const labels = rows.map((row) => shorten(row.model.friendlyName, 34));
  const values = rows.map((row) => row.value);

  const config = {
    type: "bar",
    data: {
      labels,
      datasets: [
        {
          label: `${metric} top`,
          data: values,
          backgroundColor: "rgba(245, 158, 11, 0.7)",
          borderColor: "rgba(245, 158, 11, 1)",
          borderWidth: 1,
        },
      ],
    },
    options: chartBaseOptions({
      indexAxis: "y",
      scales: {
        x: {
          ticks: { color: "#cfe0f7" },
          grid: { color: "rgba(120, 144, 172, 0.15)" },
        },
        y: {
          ticks: { color: "#cfe0f7" },
          grid: { color: "rgba(120, 144, 172, 0.12)" },
        },
      },
      plugins: {
        legend: { display: false },
      },
    }),
  };

  chartRefs.top = updateChart(chartRefs.top, dom.topModelsChart, config);
}

function chartBaseOptions(extra) {
  return {
    responsive: true,
    maintainAspectRatio: false,
    animation: { duration: 200 },
    plugins: {
      tooltip: {
        backgroundColor: "rgba(6, 12, 20, 0.96)",
        titleColor: "#f2f8ff",
        bodyColor: "#d9e7fb",
        borderColor: "rgba(139, 164, 192, 0.3)",
        borderWidth: 1,
      },
    },
    ...extra,
  };
}

function updateChart(currentChart, canvas, config) {
  if (currentChart) {
    currentChart.destroy();
  }
  return new globalThis.Chart(canvas, config);
}

function renderTable() {
  const total = state.filtered.length;
  const totalPages = getTotalPages();
  state.page = clampPage(state.page, totalPages);

  const start = (state.page - 1) * state.pageSize;
  const end = Math.min(start + state.pageSize, total);
  const rows = state.filtered.slice(start, end);

  dom.tableSummary.textContent = `${formatInteger(total)} resultados. Mostrando ${formatInteger(start + 1)}-${formatInteger(end)}.`;
  dom.pageIndicator.textContent = `${totalPages === 0 ? 0 : state.page} / ${totalPages}`;

  dom.prevPageBtn.disabled = state.page <= 1;
  dom.nextPageBtn.disabled = state.page >= totalPages;

  if (!rows.length) {
    dom.modelsTableBody.innerHTML = `
      <tr>
        <td colspan="7" class="muted">No hay resultados para los filtros actuales.</td>
      </tr>
    `;
    return;
  }

  const metric = state.selectedMetric;

  dom.modelsTableBody.innerHTML = rows
    .map((model) => {
      const scoreValue = getModelContextMetric(model, metric, state.scoreStem);
      const scoreText = scoreValue === null ? "-" : formatFloat(scoreValue);
      const activeClass = model.id === state.selectedModelId ? "active" : "";
      const compareActive = state.compareIds.has(model.id) ? "active" : "";

      return `
        <tr data-model-id="${escapeHtml(model.id)}" class="${activeClass}">
          <td>
            <button
              type="button"
              class="compare-toggle ${compareActive}"
              data-model-id="${escapeHtml(model.id)}"
            >
              ${state.compareIds.has(model.id) ? "Quitar" : "Comparar"}
            </button>
          </td>
          <td>${escapeHtml(model.friendlyName || "-")}</td>
          <td><span class="mono">${escapeHtml(model.arch)}</span></td>
          <td><span class="mono">${escapeHtml(model.filename || "-")}</span></td>
          <td>${renderChips(model.stems)}</td>
          <td>${escapeHtml(model.targetStem || "-")}</td>
          <td class="mono">${escapeHtml(scoreText)}</td>
        </tr>
      `;
    })
    .join("");
}

function renderModelDetails() {
  const model = state.filtered.find((entry) => entry.id === state.selectedModelId);

  if (!model) {
    dom.modelDetailEmpty.classList.remove("hidden");
    dom.modelDetailContent.classList.add("hidden");
    dom.modelDetailContent.innerHTML = "";
    return;
  }

  dom.modelDetailEmpty.classList.add("hidden");
  dom.modelDetailContent.classList.remove("hidden");

  const metricsRows = Object.entries(model.scores)
    .sort((a, b) => a[0].localeCompare(b[0]))
    .map(([stem, metricValues]) => {
      return `
        <tr>
          <td>${escapeHtml(stem)}</td>
          <td class="mono">${formatMaybe(metricValues.SDR)}</td>
          <td class="mono">${formatMaybe(metricValues.SIR)}</td>
          <td class="mono">${formatMaybe(metricValues.SAR)}</td>
          <td class="mono">${formatMaybe(metricValues.ISR)}</td>
        </tr>
      `;
    })
    .join("");

  const downloadChips = model.downloadFiles
    .map((file) => `<span class="chip mono">${escapeHtml(file)}</span>`)
    .join("");
  const downloads = model.downloadFiles.length
    ? `<div class="chips">${downloadChips}</div>`
    : "<p class=\"muted\">No download_files reportado.</p>";

  dom.modelDetailContent.innerHTML = `
    <div class="kv-grid">
      <div class="kv-item"><p class="k">Friendly name</p><p class="v">${escapeHtml(model.friendlyName || "-")}</p></div>
      <div class="kv-item"><p class="k">Architecture</p><p class="v mono">${escapeHtml(model.arch)}</p></div>
      <div class="kv-item"><p class="k">Filename</p><p class="v mono">${escapeHtml(model.filename || "-")}</p></div>
      <div class="kv-item"><p class="k">Target stem</p><p class="v">${escapeHtml(model.targetStem || "-")}</p></div>
      <div class="kv-item"><p class="k">Stems</p><p class="v">${renderChips(model.stems)}</p></div>
      <div class="kv-item"><p class="k">Best SDR</p><p class="v mono">${formatMaybe(model.bestByMetric.SDR)}</p></div>
    </div>

    <div>
      <h3>Metricas por stem</h3>
      <table class="metrics-table">
        <thead>
          <tr>
            <th>Stem</th>
            <th>SDR</th>
            <th>SIR</th>
            <th>SAR</th>
            <th>ISR</th>
          </tr>
        </thead>
        <tbody>
          ${metricsRows || `<tr><td colspan="5" class="muted">Sin metricas por stem.</td></tr>`}
        </tbody>
      </table>
    </div>

    <div>
      <h3>download_files</h3>
      ${downloads}
    </div>
  `;
}

function renderComparison() {
  const selectedModels = state.models.filter((model) => state.compareIds.has(model.id));

  dom.compareSelection.innerHTML = selectedModels.length
    ? selectedModels
        .map(
          (model) => `
            <span class="compare-pill" title="${escapeHtml(model.friendlyName)}">
              ${escapeHtml(shorten(model.friendlyName, 34))}
              <button type="button" data-remove-id="${escapeHtml(model.id)}">x</button>
            </span>
          `
        )
        .join("")
    : "<span class=\"muted\">No hay modelos seleccionados para comparar.</span>";

  const rows = selectedModels
    .map((model) => ({
      model,
      value: getModelContextMetric(model, state.compareMetric, state.compareStem),
    }))
    .filter((entry) => entry.value !== null)
    .sort((a, b) => b.value - a.value);

  dom.compareRanking.innerHTML = rows.length
    ? rows
        .map(
          (entry) =>
            `<li><strong>${escapeHtml(entry.model.friendlyName)}</strong> - <span class="mono">${formatFloat(entry.value)}</span></li>`
        )
        .join("")
    : "<li class=\"muted\">No hay valores comparables para ese stem/metrica.</li>";

  if (!globalThis.Chart) return;

  const labels = rows.map((entry) => shorten(entry.model.friendlyName, 34));
  const values = rows.map((entry) => entry.value);

  const config = {
    type: "bar",
    data: {
      labels,
      datasets: [
        {
          label: `${state.compareMetric} comparado`,
          data: values,
          backgroundColor: "rgba(52, 211, 153, 0.72)",
          borderColor: "rgba(52, 211, 153, 1)",
          borderWidth: 1,
        },
      ],
    },
    options: chartBaseOptions({
      indexAxis: "y",
      scales: {
        x: {
          ticks: { color: "#cfe0f7" },
          grid: { color: "rgba(120, 144, 172, 0.15)" },
        },
        y: {
          ticks: { color: "#cfe0f7" },
          grid: { color: "rgba(120, 144, 172, 0.12)" },
        },
      },
      plugins: {
        legend: { display: false },
      },
    }),
  };

  chartRefs.compare = updateChart(chartRefs.compare, dom.compareChart, config);
}

function toggleCompare(modelId) {
  if (!modelId) return;

  if (state.compareIds.has(modelId)) {
    state.compareIds.delete(modelId);
  } else {
    if (state.compareIds.size >= 8) {
      setStatus("Maximo 8 modelos en comparacion para mantener legibilidad.", true);
      return;
    }
    state.compareIds.add(modelId);
  }

  renderTable();
  renderComparison();
}

function getModelContextMetric(model, metric, contextStem) {
  if (contextStem === BEST_STEM_VALUE) {
    const best = model.bestByMetric[metric];
    return Number.isFinite(best) ? best : null;
  }

  const stemMetrics = model.scores[contextStem];
  if (!stemMetrics) return null;

  const value = stemMetrics[metric];
  return Number.isFinite(value) ? value : null;
}

function getBestMetricValue(scoresByStem, metric) {
  let best = null;

  for (const stemMetrics of Object.values(scoresByStem)) {
    const value = Number(stemMetrics[metric]);
    if (!Number.isFinite(value)) continue;
    if (best === null || value > best) best = value;
  }

  return best;
}

function hasStem(model, stem) {
  if (model.stems.includes(stem)) return true;
  return Object.hasOwn(model.scores, stem);
}

function getTotalPages() {
  if (!state.filtered.length) return 1;
  return Math.max(1, Math.ceil(state.filtered.length / state.pageSize));
}

function clampPage(page, totalPages) {
  if (totalPages <= 0) return 1;
  return Math.max(1, Math.min(page, totalPages));
}

function formatFloat(value) {
  return Number(value).toFixed(3);
}

function formatMaybe(value) {
  if (!Number.isFinite(value)) return "-";
  return formatFloat(value);
}

function formatInteger(value) {
  return new Intl.NumberFormat("en-US").format(value);
}

function renderChips(values) {
  if (!values?.length) return "<span class=\"muted\">-</span>";
  return `<div class="chips">${values
    .map((value) => `<span class="chip">${escapeHtml(value)}</span>`)
    .join("")}</div>`;
}

function shorten(text, maxLength) {
  if (!text) return "";
  if (text.length <= maxLength) return text;
  return `${text.slice(0, maxLength - 1)}...`;
}

function escapeHtml(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll("\"", "&quot;")
    .replaceAll("'", "&#039;");
}

function setStatus(message, isError = false) {
  dom.loadStatus.textContent = message;
  dom.loadStatus.style.color = isError ? "#fb7185" : "#9eb4cf";
}
