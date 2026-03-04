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

const createChart = () => {
  const chartContainer = document.querySelector("#chart-container");
  const chartSpec = JSON.parse(
    document.getElementById("chart-spec").textContent,
  );

  const opt = { renderer: "svg" };
  chartResult = vegaEmbed(chartContainer, chartSpec, opt);
};

const updateChart = (
  url,
  apiDatasetName,
  addDatasetName,
) => {
  const allDatasetNames = [
    "deciles",
    "all_orgs_dots_chart",
    "all_orgs_line_chart",
  ];
  fetch(url)
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
      updateOrgTypeLabel(response.org_type);
      chartResult.then((result) => {
        result.view.insert(addDatasetName, response[apiDatasetName]);
        if (response.org) {
          result.view.insert("org", response.org);
        }
        allDatasetNames.forEach((removeDatasetName) => {
          if (removeDatasetName !== addDatasetName) {
            result.view.remove(removeDatasetName, () => true).run();
          }
        });
      });
    })
    .catch((error) => {
      console.error("Unable to render deciles chart", error);
      chartContainer.textContent =
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
    createChart();

    document.getElementById("decile").addEventListener("click", () => {
      updateChart(prescribingDecilesUrl, "deciles", "deciles");
    });

    document
      .getElementById("all_orgs_line_chart")
      .addEventListener("click", () => {
        updateChart(
          prescribingAllOrgsUrl,
          "all_orgs",
          "all_orgs_line_chart",
        );
      });

    document
      .getElementById("all_orgs_dots_chart")
      .addEventListener("click", () => {
        updateChart(
          prescribingAllOrgsUrl,
          "all_orgs",
          "all_orgs_dots_chart",
        );
      });

    // default to decile view!
    document.getElementById("decile").click();
  }
});
