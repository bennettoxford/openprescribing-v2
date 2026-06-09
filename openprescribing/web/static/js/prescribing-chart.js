const orgs = JSON.parse(document.getElementById("orgs").textContent);
const orgTypes = Object.fromEntries(
  JSON.parse(document.getElementById("org-types").textContent),
);
const chartSpecs = JSON.parse(
  document.getElementById("chart-specs").textContent,
);
const prescribingUrls = JSON.parse(
  document.getElementById("prescribing-urls").textContent,
);

const chartConfigs = {
  // Each record defines a how data should be displayed in a chart.
  //  - apiUrl: the URL that returns the chart data
  //  - responseKey: the key in the URL response that contains the chart data
  //  - vegaDatasetName: the name of the dataset in the Vega chart spec
  //  - specName: the key in chartSpecs of the Vega spec to embed
  deciles: {
    apiUrl: prescribingUrls.deciles,
    responseKey: "deciles",
    vegaDatasetName: "deciles",
    specName: "org",
  },
  "all-orgs-line": {
    apiUrl: prescribingUrls.all_orgs,
    responseKey: "all_orgs",
    vegaDatasetName: "all_orgs_line",
    specName: "org",
  },
  "all-orgs-dots": {
    apiUrl: prescribingUrls.all_orgs,
    responseKey: "all_orgs",
    vegaDatasetName: "all_orgs_dots",
    specName: "org",
  },
};

const chartLoading = document.querySelector("#chart-loading");
const chartContainer = document.querySelector("#chart-container");

// We'll store the Vega chart result, and the name of the spec it was built from, here.
let chartResult;
let currentSpecName;

const initialisePage = async () => {
  // Set the chart type and set up event handlers.

  setChartType(chartTypeFromUrl());

  window.addEventListener("popstate", () => {
    setChartType(chartTypeFromUrl());
  });

  Object.keys(chartConfigs).forEach((chartType) => {
    const radio = document.getElementById(chartType);
    radio.addEventListener("change", () => {
      if (radio.checked) {
        setChartType(chartType, true);
      }
    });
  });

  setupOrgSearch();
};

const setupOrgSearch = () => {
  const input = document.getElementById("org-search");
  const results = document.getElementById("org-results");

  input.addEventListener("input", () => {
    const query = input.value.trim().toLowerCase();
    results.innerHTML = "";

    const matches =
      query.length < 2
        ? []
        : orgs.filter(
            (org) =>
              org.name.toLowerCase().includes(query) ||
              org.id.toLowerCase().includes(query),
          );

    if (!matches.length) {
      results.classList.add("d-none");
      return;
    }

    const fragment = document.createDocumentFragment();
    matches.forEach((org) => {
      const item = document.createElement("button");
      item.type = "button";
      item.className = "list-group-item list-group-item-action";
      item.innerHTML = `
            <div class="fw-semibold">${org.name}</div>
            <div class="text-muted small">${org.id} - ${orgTypes[org.org_type]}</div>
        `;
      item.addEventListener("click", () => {
        const url = new URL(window.location.href);
        url.searchParams.set("org_id", org.id);
        window.location.assign(url);
      });
      fragment.appendChild(item);
    });
    results.appendChild(fragment);
    results.classList.remove("d-none");
  });
};

const setChartType = (chartType, pushHistory = false) => {
  document.getElementById(chartType).checked = true;
  updateChart(chartConfigs[chartType]);

  if (pushHistory) {
    updateUrl(chartType);
  }
};

// Embed the named spec, reusing the existing view if it's already embedded. Chart types
// that share a spec (deciles/all-orgs) avoid re-embedding.
const embedSpec = async (specName) => {
  if (specName === currentSpecName) {
    return;
  }
  currentSpecName = specName;
  if (chartResult) {
    // Tear down the previous view before replacing it, so we don't leak its listeners.
    chartResult.finalize();
  }
  chartResult = await vegaEmbed(chartContainer, chartSpecs[specName], {
    renderer: "svg",
  });
};

const updateChart = async (chartConfig) => {
  const { apiUrl, responseKey, vegaDatasetName, specName } = chartConfig;

  chartLoading.textContent = "Loading chart...";
  try {
    await embedSpec(specName);

    const response = await fetch(apiUrl);
    if (!response.ok) {
      throw new Error(`Failed to fetch chart data: ${response.status}`);
    }
    const data = await response.json();

    data[responseKey].forEach((record) => {
      record.month = new Date(record.month);
    });
    if (data.org) {
      data.org.forEach((record) => {
        record.month = new Date(record.month);
      });
    }
    // The combined ("org") spec carries its named datasets on each layer.
    const datasetNames = chartResult.spec.layer.map((layer) => layer.data.name);
    datasetNames.forEach((datasetName) => {
      chartResult.view.remove(datasetName, () => true);
    });
    chartResult.view.insert(vegaDatasetName, data[responseKey]);
    if (data.org) {
      chartResult.view.insert("org", data.org);
    }
    chartResult.view.run();

    chartLoading.classList.add("invisible");
    chartContainer.classList.add("visible");
    chartLoading.classList.remove("visible");
    chartContainer.classList.remove("invisible");
  } catch (error) {
    console.error("Unable to render chart", error);
    chartLoading.textContent =
      "Unable to load chart data. Please try again later.";
  }
};

const updateUrl = (chartType) => {
  const url = new URL(window.location.href);
  url.searchParams.set("chart_type", chartType);
  window.history.pushState({}, "", url);
};

const chartTypeFromUrl = () => {
  const chartType = new URL(window.location.href).searchParams.get(
    "chart_type",
  );
  if (!chartType || !chartConfigs[chartType]) {
    // default to decile view!
    return "deciles";
  }
  return chartType;
};

initialisePage();
