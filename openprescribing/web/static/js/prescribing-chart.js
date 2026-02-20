const setupBNFCodeSearch = () => {
  const bnfCodes = JSON.parse(document.getElementById("bnf-codes").textContent);
  const bnfLevels = Object.fromEntries(
    JSON.parse(document.getElementById("bnf-levels").textContent),
  );

  const bnfSearch = document.getElementById("bnf-search");
  const bnfResults = document.getElementById("bnf-results");

  createTypeahead({
    input: bnfSearch,
    results: bnfResults,
    minChars: 3,
    getMatches: (query) =>
      bnfCodes.filter((c) => c.name.toLowerCase().includes(query)),
    renderItem: (item) => `
            <div class="fw-semibold">${item.name}</div>
            <div class="text-muted small">${item.code} - ${bnfLevels[item.level]}</div>
        `,
    onSelect: (item) => {
      navigateWithParams((params) => {
        params.set("code", item.code);
      });
    },
  });
};

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

var chartResult;

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
  add_dataset_name,
  remove_dataset_name,
) => {
  fetch(prescribingDecilesUrl)
    .then((response) => {
      if (!response.ok) {
        throw new Error(`Failed to fetch chart data: ${response.status}`);
      }
      return response.json();
    })
    .then((response) => {
      response[add_dataset_name].forEach((record) => {
        record.month = new Date(record.month);
      });
      if (response.org) {
        response.org.forEach((record) => {
          record.month = new Date(record.month);
        });
      }
      chartResult.then((result) => {
        result.view.insert(add_dataset_name, response[add_dataset_name]);
        if (response.org) {
          result.view.insert("org", response.org);
        }
        result.view.remove(remove_dataset_name, () => true).run();
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
  if (document.getElementById("bnf-codes")) {
    setupBNFCodeSearch();
  }
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
        updateDecilesChart(prescribingDecilesUrl, "deciles", "all_orgs");
      }
    });

    if (prescribingAllOrgsUrl) {
      document.getElementById("all_orgs").addEventListener("click", () => {
        if (prescribingAllOrgsUrl) {
          updateDecilesChart(prescribingAllOrgsUrl, "all_orgs", "deciles");
        }
      });
    }

    // default to decile view!
    document.getElementById("decile").click();
  }
});
