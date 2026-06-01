const setupOrgSearch = () => {
  const orgs = JSON.parse(document.getElementById("orgs").textContent);
  const orgTypes = Object.fromEntries(
    JSON.parse(document.getElementById("org-types").textContent),
  );

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

var chartResult;

const createChart = (chartContainer) => {
  const chartSpec = JSON.parse(document.getElementById("chart").textContent);

  const opt = { renderer: "svg" };
  chartResult = vegaEmbed(chartContainer, chartSpec, opt);
};

const updateChart = (chartConfig) => {
  const { dataUrl, apiDatasetName, addDatasetName } = chartConfig;
  const chartLoading = document.querySelector("#chart-loading");
  const chartContainer = document.querySelector("#chart-container");
  if (!chartContainer.classList.contains("vega-embed")) {
    createChart(chartContainer);
  }

  chartLoading.textContent = "Loading chart...";
  fetch(dataUrl)
    .then((response) => {
      if (!response.ok) {
        throw new Error(`Failed to fetch chart data: ${response.status}`);
      }
      return response.json();
    })
    .then((response) => {
      response[apiDatasetName].forEach((record) => {
        record.month = new Date(record.month);
      });
      if (response.org) {
        response.org.forEach((record) => {
          record.month = new Date(record.month);
        });
      }
      chartResult.then((result) => {
        const datasetNames = result.spec.layer.map((layer) => layer.data.name);
        datasetNames.forEach((datasetName) => {
          result.view.remove(datasetName, () => true);
        });
        result.view.insert(addDatasetName, response[apiDatasetName]);
        if (response.org) {
          result.view.insert("org", response.org);
        }
        result.view.run();

        chartLoading.classList.add("invisible");
        chartContainer.classList.add("visible");
        chartLoading.classList.remove("visible");
        chartContainer.classList.remove("invisible");
      });
    })
    .catch((error) => {
      console.error("Unable to render deciles chart", error);
      chartLoading.textContent =
        "Unable to load chart data. Please try again later.";
    });
};

setupOrgSearch();

const prescribingDecilesUrl = JSON.parse(
  document.getElementById("prescribing-deciles-url").textContent,
);
const prescribingAllOrgsUrl = JSON.parse(
  document.getElementById("prescribing-all-orgs-url").textContent,
);

const chartConfigs = {
  deciles: {
    dataUrl: prescribingDecilesUrl,
    apiDatasetName: "deciles",
    addDatasetName: "deciles",
  },
  "all-orgs-line": {
    dataUrl: prescribingAllOrgsUrl,
    apiDatasetName: "all_orgs",
    addDatasetName: "all_orgs_line",
  },
  "all-orgs-dots": {
    dataUrl: prescribingAllOrgsUrl,
    apiDatasetName: "all_orgs",
    addDatasetName: "all_orgs_dots",
  },
};

const renderChartType = (chartType) => {
  updateChart(chartConfigs[chartType]);
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

const setChartType = (chartType, pushHistory = false) => {
  document.getElementById(chartType).checked = true;
  renderChartType(chartType);

  if (!pushHistory) {
    return;
  }

  const url = new URL(window.location.href);
  url.searchParams.set("chart_type", chartType);
  window.history.pushState({}, "", url);
};

Object.keys(chartConfigs).forEach((chartType) => {
  const radio = document.getElementById(chartType);
  radio.addEventListener("change", () => {
    if (!radio.checked) {
      return;
    }
    setChartType(chartType, true);
  });
});

window.addEventListener("popstate", () => {
  setChartType(chartTypeFromUrl());
});

setChartType(chartTypeFromUrl());
