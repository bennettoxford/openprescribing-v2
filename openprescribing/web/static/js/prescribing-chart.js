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
      navigateWithParams((params) => {
        params.set("org_id", org.id);
      });
    },
  });
};

const navigateWithParams = (updateFn) => {
  const url = new URL(window.location.href);
  updateFn(url.searchParams);
  window.location.href = url.toString();
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

const updateOrgTypeLabel = (org_type) => {
  document.getElementById("decile_org_type").textContent = ` for ${org_type}s`;
  ["line_chart_org_types", "dots_chart_org_types"].forEach((o) => {
    document.getElementById(o).textContent = `${org_type}s`;
  });
};

var chartResult;
const allDatasetNames = [
  "deciles",
  "all_orgs_dots_chart",
  "all_orgs_line_chart",
  "relative_to_median",
  "relative_to_median_bounds",
  "relative_to_median_zero_line",
];

const createDecilesChart = () => {
  const chartContainer = document.querySelector("#deciles-chart-container");
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
  fetch(prescribingDecilesUrl)
    .then((response) => {
      if (!response.ok) {
        throw new Error(`Failed to fetch chart data: ${response.status}`);
      }
      return response.json();
    })
    .then((response) => {
      updateOrgTypeLabel(response.org_type);

      chartResult.then((result) => {
        const chart = result.view;
        if (add_dataset_name === "relative_to_median") {
          updateRelativeToMedianDataset(chart, response);
        } else {
          updateNonRelativeDataset(
            chart,
            response,
            api_dataset_name,
            add_dataset_name,
          );
        }
        chart.run();
      });
    })
    .catch((error) => {
      console.error("Unable to render deciles chart", error);
      const chartContainer = document.querySelector("#deciles-chart-container");
      chartContainer.textContent =
        "Unable to load chart data. Please try again later.";
    });
};

const updateNonRelativeDataset = (
  chart,
  response,
  apiDatasetName,
  addDatasetName,
) => {
  parseRecordMonths(response[apiDatasetName]);
  chart.insert(addDatasetName, response[apiDatasetName]);

  if (response.org) {
    parseRecordMonths(response.org);
    chart.insert("org", response.org);
  }

  allDatasetNames.forEach((removeDatasetName) => {
    if (removeDatasetName !== addDatasetName) {
      chart.remove(removeDatasetName, () => true);
    }
  });
};

const updateRelativeToMedianDataset = (chart, response) => {
  const { relativeToMedian, relativeToMedianBounds, relativeToMedianZeroLine } =
    buildRelativeToMedianData(response.deciles, response.org ?? []);
  chart.insert("relative_to_median", relativeToMedian);
  chart.insert("relative_to_median_bounds", relativeToMedianBounds);
  chart.insert("relative_to_median_zero_line", relativeToMedianZeroLine);
  chart.remove("org", () => true);

  allDatasetNames.forEach((removeDatasetName) => {
    if (
      ![
        "relative_to_median",
        "relative_to_median_bounds",
        "relative_to_median_zero_line",
      ].includes(removeDatasetName)
    ) {
      chart.remove(removeDatasetName, () => true);
    }
  });
};

const buildRelativeToMedianData = (deciles, org) => {
  const medianByMonth = new Map();
  deciles.forEach((record) => {
    if (record.centile === 50 && record.value !== null) {
      medianByMonth.set(record.month, record.value);
    }
  });

  const relativeToMedian = [];
  org.forEach((record) => {
    if (record.value === null) {
      return;
    }
    const median = medianByMonth.get(record.month);
    if (median === undefined || median === null) {
      return;
    }
    relativeToMedian.push({
      month: new Date(record.month),
      value: record.value - median,
    });
  });

  const maxAbsDifference = Math.max(
    ...relativeToMedian.map((record) => Math.abs(record.value)),
    0,
  );
  const yDomainExtent = maxAbsDifference > 0 ? maxAbsDifference : 0.01;
  const boundMonth =
    relativeToMedian.length > 0
      ? relativeToMedian[0].month
      : org.length > 0
        ? new Date(org[0].month)
        : new Date();
  const relativeToMedianBounds = [
    { month: boundMonth, value: yDomainExtent },
    { month: boundMonth, value: -yDomainExtent },
  ];

  return {
    relativeToMedian,
    relativeToMedianBounds,
    relativeToMedianZeroLine: [{ value: 0 }],
  };
};

const parseRecordMonths = (records) => {
  records.forEach((record) => {
    record.month = new Date(record.month);
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
    createDecilesChart();

    document.getElementById("decile").addEventListener("click", () => {
      if (prescribingDecilesUrl) {
        updateDecilesChart(prescribingDecilesUrl, "deciles", "deciles");
      }
    });

    if (prescribingAllOrgsUrl) {
      document
        .getElementById("all_orgs_line_chart")
        .addEventListener("click", () => {
          if (prescribingAllOrgsUrl) {
            updateDecilesChart(
              prescribingAllOrgsUrl,
              "all_orgs",
              "all_orgs_line_chart",
            );
          }
        });

      document
        .getElementById("all_orgs_dots_chart")
        .addEventListener("click", () => {
          if (prescribingAllOrgsUrl) {
            updateDecilesChart(
              prescribingAllOrgsUrl,
              "all_orgs",
              "all_orgs_dots_chart",
            );
          }
        });
    }

    const relativeToMedianChart = document.getElementById(
      "relative_to_median_chart",
    );
    if (relativeToMedianChart) {
      // Will only be present if an org has been selected.
      relativeToMedianChart.addEventListener("click", () => {
        if (prescribingDecilesUrl) {
          updateDecilesChart(
            prescribingDecilesUrl,
            "deciles",
            "relative_to_median",
          );
        }
      });
    }

    // default to decile view!
    document.getElementById("decile").click();
  }
});
