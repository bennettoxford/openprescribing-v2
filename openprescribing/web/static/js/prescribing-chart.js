const setupOrgSearch = () => {
  const orgs = JSON.parse(document.getElementById("orgs").textContent);
  const orgTypes = Object.fromEntries(
    JSON.parse(document.getElementById("org-types").textContent),
  );

  const orgSearch = document.getElementById("org-search");
  const orgResults = document.getElementById("org-results");

  createTypeahead({
    input: orgSearch,
    results: orgResults,
    minChars: 2,
    getMatches: (query) =>
      orgs.filter((org) => {
        return (
          org.name.toLowerCase().includes(query) ||
          org.id.toLowerCase().includes(query)
        );
      }),
    renderItem: (org) => `
            <div class="fw-semibold">${org.name}</div>
            <div class="text-muted small">${org.id} - ${orgTypes[org.org_type]}</div>
        `,
    onSelect: (org) => {
      const url = new URL(window.location.href);
      url.searchParams.set("org_id", org.id);
      window.location.assign(url);
    },
  });
};

const createTypeahead = ({
  input,
  results,
  minChars,
  getMatches,
  renderItem,
  onSelect,
}) => {
  input.addEventListener("input", () => {
    const query = input.value.trim().toLowerCase();
    if (query.length < minChars) {
      results.innerHTML = "";
      results.classList.add("d-none");
      return;
    }

    const matches = getMatches(query);
    results.innerHTML = "";
    if (!matches.length) {
      results.classList.add("d-none");
      return;
    }

    const fragment = document.createDocumentFragment();
    matches.forEach((match) => {
      const item = document.createElement("button");
      item.type = "button";
      item.className = "list-group-item list-group-item-action";
      item.innerHTML = renderItem(match);
      item.addEventListener("click", () => {
        onSelect(match);
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

const updateChart = (dataUrl, apiDatasetName, addDatasetName) => {
  const chartLoading = document.querySelector("#chart-loading");
  const chartContainer = document.querySelector("#chart-container");
  if (!chartContainer.classList.contains("vega-embed")) {
    createChart(chartContainer);
  }

  const all_dataset_names = ["deciles", "all_orgs_dots", "all_orgs_line"];
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
        result.view.insert(addDatasetName, response[apiDatasetName]);
        if (response.org) {
          result.view.insert("org", response.org);
        }
        all_dataset_names.forEach((removeDatasetName) => {
          if (removeDatasetName !== addDatasetName) {
            result.view.remove(removeDatasetName, () => true);
          }
        });
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
    radio: document.getElementById("deciles"),
    dataUrl: prescribingDecilesUrl,
    apiDatasetName: "deciles",
    addDatasetName: "deciles",
  },
  "all-orgs-line": {
    radio: document.getElementById("all-orgs-line"),
    dataUrl: prescribingAllOrgsUrl,
    apiDatasetName: "all_orgs",
    addDatasetName: "all_orgs_line",
  },
  "all-orgs-dots": {
    radio: document.getElementById("all-orgs-dots"),
    dataUrl: prescribingAllOrgsUrl,
    apiDatasetName: "all_orgs",
    addDatasetName: "all_orgs_dots",
  },
};

const renderChartType = (chartType) => {
  const chartConfig = chartConfigs[chartType];
  updateChart(
    chartConfig.dataUrl,
    chartConfig.apiDatasetName,
    chartConfig.addDatasetName,
  );
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
  chartConfigs[chartType].radio.checked = true;
  renderChartType(chartType);

  if (!pushHistory) {
    return;
  }

  const url = new URL(window.location.href);
  url.searchParams.set("chart_type", chartType);
  window.history.pushState({}, "", url);
};

Object.entries(chartConfigs).forEach(([chartType, chartConfig]) => {
  chartConfig.radio.addEventListener("change", () => {
    if (!chartConfig.radio.checked) {
      return;
    }
    setChartType(chartType, true);
  });
});

window.addEventListener("popstate", () => {
  setChartType(chartTypeFromUrl());
});

setChartType(chartTypeFromUrl());
