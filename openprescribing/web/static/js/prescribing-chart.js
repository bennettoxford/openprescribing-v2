const setupOrgSearch = () => {
  const orgs = JSON.parse(document.getElementById("orgs").textContent);
  const orgTypes = Object.fromEntries(
    JSON.parse(document.getElementById("org-types").textContent),
  );

  const orgSearch = document.getElementById("org-search");
  const orgResults = document.getElementById("org-results");
  const prescribingQueryForm = document.getElementById(
    "prescribing-query-form",
  );
  const prescribingQueryOrgIdInput = document.getElementById(
    "prescribing-query-org-id",
  );
  const prescribingQueryNtrCodesInput =
    prescribingQueryForm?.querySelector('[name="ntr_codes"]');

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
      prescribingQueryOrgIdInput.disabled = false;
      prescribingQueryOrgIdInput.value = org.id;

      if (!prescribingQueryNtrCodesInput.value) {
        // Don't submit when no numerator has been selected yet.
        return;
      }

      prescribingQueryForm.requestSubmit();
    },
    onEmpty: () => {
      prescribingQueryOrgIdInput.disabled = true;
      prescribingQueryOrgIdInput.value = "";
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
  onEmpty,
}) => {
  input.addEventListener("input", () => {
    const query = input.value.trim().toLowerCase();
    if (query.length < minChars) {
      results.innerHTML = "";
      results.classList.add("d-none");
      onEmpty();
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

const updateOrgTypeLabel = (orgType) => {
  const orgTypes = Object.fromEntries(
    JSON.parse(document.getElementById("org-types").textContent),
  );

  document.getElementById("decile_org_type").textContent =
    ` for ${orgTypes[orgType]}s`;
  ["line_chart_org_types", "dots_chart_org_types"].forEach((o) => {
    document.getElementById(o).textContent = `${orgTypes[orgType]}s`;
  });
};

var chartResult;

const createDecilesChart = (chartContainer) => {
  const chartSpec = JSON.parse(
    document.getElementById("deciles-chart").textContent,
  );

  const opt = { renderer: "svg" };
  chartResult = vegaEmbed(chartContainer, chartSpec, opt);
};

const updateDecilesChart = (
  prescribingDecilesUrl,
  api_dataset_name,
  add_dataset_name,
) => {
  const chartLoading = document.querySelector("#deciles-chart-loading");
  const chartContainer = document.querySelector("#deciles-chart-container");
  if (!chartContainer.classList.contains("vega-embed")) {
    createDecilesChart(chartContainer);
  }

  const truncate_string = (str) => {
    const maxLength = 65;
    if (str.length > maxLength) {
      return `${str.slice(0, maxLength)}...`;
    }
    return str;
  };

  const all_dataset_names = ["deciles", "all_orgs_dots", "all_orgs_line"];
  chartLoading.textContent = "Loading chart...";
  fetch(prescribingDecilesUrl)
    .then((response) => {
      if (!response.ok) {
        throw new Error(`Failed to fetch chart data: ${response.status}`);
      }
      return response.json();
    })
    .then((response) => {
      response[api_dataset_name].forEach((record) => {
        record.month = new Date(record.month);
      });
      if (response.org) {
        response.org.forEach((record) => {
          record.month = new Date(record.month);
        });
      }
      updateOrgTypeLabel(response.org_type);
      chartResult.then((result) => {
        const orgs = JSON.parse(document.getElementById("orgs").textContent);

        if (api_dataset_name === "all_orgs") {
          for (const element of response[api_dataset_name]) {
            element.org_name = truncate_string(
              orgs.find((e) => e.id === element.org).name,
            );
          }
        }
        result.view.insert(add_dataset_name, response[api_dataset_name]);
        if (response.org) {
          result.view.insert("org", response.org);
        }
        all_dataset_names.forEach((remove_dataset_name) => {
          if (remove_dataset_name !== add_dataset_name) {
            result.view.remove(remove_dataset_name, () => true);
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

document.addEventListener("DOMContentLoaded", () => {
  // Only initialise the Typeahead search on pages that use it
  if (document.getElementById("orgs")) {
    setupOrgSearch();
  }
  const prescribingDecilesUrl = JSON.parse(
    document.getElementById("prescribing-deciles-url").textContent,
  );
  const prescribingAllOrgsUrl = JSON.parse(
    document.getElementById("prescribing-all-orgs-url").textContent,
  );

  if (prescribingDecilesUrl) {
    const chartConfigs = {
      deciles: {
        radio: document.getElementById("decile"),
        dataUrl: prescribingDecilesUrl,
        apiDatasetName: "deciles",
        addDatasetName: "deciles",
      },
      "all-orgs-line": {
        radio: document.getElementById("all_orgs_line_chart"),
        dataUrl: prescribingAllOrgsUrl,
        apiDatasetName: "all_orgs",
        addDatasetName: "all_orgs_line",
      },
      "all-orgs-dots": {
        radio: document.getElementById("all_orgs_dots_chart"),
        dataUrl: prescribingAllOrgsUrl,
        apiDatasetName: "all_orgs",
        addDatasetName: "all_orgs_dots",
      },
    };

    const renderChartType = (chartType) => {
      const chartConfig = chartConfigs[chartType];
      updateDecilesChart(
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
      const queryFormChartTypeInput = document.getElementById(
        "prescribing-query-chart-type",
      );
      queryFormChartTypeInput.value = chartType;
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
  }
});
