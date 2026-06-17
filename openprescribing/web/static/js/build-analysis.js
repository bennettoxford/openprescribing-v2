import {
  FILTER_DEFINITIONS,
  filtersFromQueryDict,
  getEmptyFilters,
  getFilterControlKey,
  getFilterControlLabel,
  getFilterDefinitionForControlKey,
  hasAnyFilters,
  hasAnyInclusionFilters,
  isExcludedFilterControlKey,
  queryDictFromFilters,
} from "./build-analysis/filters.js";
import { fetchMetadata } from "./build-analysis/metadata.js";
import {
  getCachedValidOptionIds,
  queryMedications,
  refreshAvailableOptionIds,
} from "./build-analysis/query.js";
import {
  renderAddFilterOptions,
  renderPromptState,
  renderResults,
  renderSummary,
} from "./build-analysis/render.js";
import { DropdownCollection } from "./dropdown.js";

// Maps a panel prefix to its role in the analysis dict's query.
const QUERY_ROLE_BY_PREFIX = { ntr: "numerator", dtr: "denominator" };

// Parts of the document that we'll interact with.
const containerEl = document.querySelector("[data-container]");
const loadingEl = containerEl.querySelector("[data-loading]");
const errorEl = containerEl.querySelector("[data-error]");
const appEl = containerEl.querySelector("[data-app]");
const summarySubmitEl = containerEl.querySelector("[data-summary-submit]");
const summarySectionElsByPrefix = new Map(
  Array.from(containerEl.querySelectorAll("[data-summary-section]")).map(
    (element) => [element.dataset.summarySection, element],
  ),
);

// Templates that we'll use to generate elements in the document.
const templates = {
  dropdownTemplate: containerEl.querySelector("[data-dropdown-template]"),
  dropdownOptionTemplate: containerEl.querySelector(
    "[data-dropdown-option-template]",
  ),
  summaryListTemplate: containerEl.querySelector(
    "[data-summary-list-template]",
  ),
  summaryListItemTemplate: containerEl.querySelector(
    "[data-summary-list-item-template]",
  ),
  summaryEmptyListItemTemplate: containerEl.querySelector(
    "[data-summary-empty-list-item-template]",
  ),
  vtmRowTemplate: containerEl.querySelector("[data-vtm-row-template]"),
  vmpRowTemplate: containerEl.querySelector("[data-vmp-row-template]"),
  ampRowTemplate: containerEl.querySelector("[data-amp-row-template]"),
};

// We'll store metadata from the API here.
let metadata;

const initialisePage = async () => {
  // Load metadata, initialise the query panels, and show the page.
  try {
    metadata = await fetchMetadata(containerEl);
    const panels = createQueryPanels();

    panels.forEach((panel) => {
      initialiseQueryPanel(panel);
    });

    initialiseQueriesFromUrl(panels);
    refreshSummary(panels);
    loadingEl.hidden = true;
    appEl.hidden = false;
  } catch (error) {
    loadingEl.hidden = true;
    errorEl.textContent = `Unable to load metadata: ${error.message}`;
    errorEl.hidden = false;
  }
};

function createQueryPanels() {
  // Return the independent query panel states.
  return Array.from(containerEl.querySelectorAll("[data-query-panel]")).map(
    (root) => ({
      prefix: root.dataset.panelPrefix,
      root,
      refs: {
        filterListEl: root.querySelector("[data-filter-list]"),
        addFilterSelect: root.querySelector("[data-add-filter]"),
        resultsEmptyEl: root.querySelector("[data-results-empty]"),
        resultsBodyEl: root.querySelector("[data-results-body]"),
        resultsCountsEl: root.querySelector("[data-results-counts]"),
        resultsEl: root.querySelector("[data-results]"),
        resultsPromptEl: root.querySelector("[data-results-prompt]"),
        resultsTableEl: root.querySelector("[data-results-table]"),
        showOnlyMatchingCheckbox: root.querySelector(
          "[data-show-only-matching]",
        ),
      },
      dropdowns: null,
      currentResults: null,
      availableOptionIdsByFilterKey: new Map(),
    }),
  );
}

function initialiseQueryPanel(panel) {
  // Wire up the panel.
  panel.dropdowns = new DropdownCollection(panel.refs.filterListEl, {
    template: templates.dropdownTemplate,
    optionTemplate: templates.dropdownOptionTemplate,
    onChange: () => {
      const filters = getFilters(panel);
      renderAddFilterOptions(panel);
      refreshAvailableOptionIds(panel, metadata, filters);
      runQuery(panel, filters, true);
      refreshSummary([panel]);
    },
  });

  renderAddFilterOptions(panel);
  refreshAvailableOptionIds(panel, metadata, getFilters(panel));

  panel.refs.addFilterSelect.addEventListener("change", () => {
    handleAddFilterChange(panel);
  });
  panel.refs.resultsEl.addEventListener("click", (event) => {
    handleResultsClick(panel, event);
  });
  panel.refs.showOnlyMatchingCheckbox.addEventListener("change", () => {
    handleShowOnlyMatchingChange(panel);
  });
}

function initialiseQueriesFromUrl(panels) {
  // Populate each panel from the URL and auto-run when needed.
  panels.forEach((panel) => {
    const filters = getFiltersFromUrl(panel);

    setFilters(panel, filters);

    if (hasAnyFilters(filters)) {
      runQuery(panel, filters);
    }
  });
}

function refreshSummary(panels) {
  // Re-render the summary tab for the given panels.
  renderSummary(summarySectionElsByPrefix, panels, templates);
  updateSummarySubmitUrl();
}

function updateSummarySubmitUrl() {
  // Point the summary submit button at the analysis page for the current filters.
  const url = new URL(containerEl.dataset.analysisUrl, window.location.href);
  url.search = new URL(window.location.href).search;

  summarySubmitEl.href = url.toString();
}

function handleAddFilterChange(panel) {
  // Add the selected filter control to the panel.
  const filterKey = panel.refs.addFilterSelect.value;

  if (filterKey === "") {
    return;
  }

  addFilterControl(panel, filterKey);
  panel.refs.addFilterSelect.value = "";
  renderAddFilterOptions(panel);
}

function handleResultsClick(panel, event) {
  // Toggle AMP rows for a VMP within the panel.
  const button = event.target.closest("[data-amp-toggle]");

  if (!button) {
    return;
  }

  const vmpId = button.dataset.vmpId;
  const ampRows = panel.refs.resultsEl.querySelectorAll(
    `[data-amp-row="${vmpId}"]`,
  );
  const isExpanded = button.dataset.expanded === "true";
  const icon = button.querySelector("i");

  ampRows.forEach((row) => {
    row.hidden = isExpanded;
  });

  button.dataset.expanded = String(!isExpanded);
  icon.className = isExpanded
    ? "bi bi-caret-right-fill"
    : "bi bi-caret-down-fill";
}

function handleShowOnlyMatchingChange(panel) {
  // Re-render the panel after toggling the visibility filter.
  if (panel.currentResults) {
    renderResults(panel, panel.currentResults, metadata, templates);
  }
}

function runQuery(panel, filters, updateUrl = false) {
  // Run the panel query and optionally update the URL.
  if (updateUrl) {
    updateUrlFromFilters(panel, filters);
  }

  if (!hasAnyInclusionFilters(filters)) {
    panel.currentResults = null;
    renderPromptState(panel);
    return;
  }

  panel.currentResults = queryMedications(metadata, filters);
  renderResults(panel, panel.currentResults, metadata, templates);
}

function addFilterControl(
  panel,
  filterKey,
  selectedValues = null,
  expanded = true,
) {
  // Add a filter control to the panel.
  if (panel.dropdowns.has(filterKey)) {
    return null;
  }

  const definition = getFilterDefinitionForControlKey(filterKey);
  const isExcluded = isExcludedFilterControlKey(filterKey);
  const dropdown = panel.dropdowns.add(filterKey, {
    title: getFilterControlLabel(definition, isExcluded),
    options: metadata.lookupRecordsByFilterKey
      .get(definition.key)
      .map((record) => ({
        id: String(record.value),
        name: record.label,
        searchCode: record.searchCode,
        searchName: record.searchName,
      })),
    getValidOptionIds: () => getCachedValidOptionIds(panel, filterKey),
    selected: (selectedValues ?? []).map(String),
  });

  if (!expanded) {
    dropdown.close();
  }

  return dropdown;
}

function getFilters(panel) {
  // Return the active query filters for the panel.
  //
  // The result is an object keyed by filter control key (for example `vtmId` or
  // `formRouteIdExclude`) with array values of the parsed filter values for that
  // control.
  const filters = getEmptyFilters();
  const selectedByKey = panel.dropdowns.getAllSelected();

  Object.entries(selectedByKey).forEach(([filterKey, values]) => {
    const definition = getFilterDefinitionForControlKey(filterKey);
    filters[filterKey] = values.map((value) => definition.parse(value));
  });

  return filters;
}

function setFilters(panel, filters) {
  // Populate the panel's filter inputs.
  FILTER_DEFINITIONS.forEach((definition) => {
    [false, true].forEach((isExcluded) => {
      const filterKey = getFilterControlKey(definition, isExcluded);

      if (panel.dropdowns.has(filterKey)) {
        panel.dropdowns.remove(filterKey);
      }
    });
  });

  FILTER_DEFINITIONS.forEach((definition) => {
    const value = filters[getFilterControlKey(definition, false)];

    if (value.length > 0) {
      addFilterControl(
        panel,
        getFilterControlKey(definition, false),
        value,
        false,
      );
    }

    const excludedValue = filters[getFilterControlKey(definition, true)];

    if (excludedValue.length > 0) {
      addFilterControl(
        panel,
        getFilterControlKey(definition, true),
        excludedValue,
        false,
      );
    }
  });

  renderAddFilterOptions(panel);
  refreshAvailableOptionIds(panel, metadata, getFilters(panel));
}

function getFiltersFromUrl(panel) {
  // Return filters parsed from the current URL for the panel.
  const params = new URL(window.location.href).searchParams;
  const analysisDict = readAnalysisDict(params);
  const queryDict = analysisDict
    ? getQueryDict(analysisDict, panel.prefix)
    : null;
  return filtersFromQueryDict(queryDict);
}

function updateUrlFromFilters(panel, filters) {
  // Replace the current URL with the combined filter state of both panels, updating the
  // `analysis` parameter and preserving the `org_id` parameter.
  const url = new URL(window.location.href);
  const currentAnalysisDict = readAnalysisDict(url.searchParams);

  const queryDicts = { numerator: null, denominator: null };
  if (currentAnalysisDict) {
    queryDicts.numerator = getQueryDict(currentAnalysisDict, "ntr");
    queryDicts.denominator = getQueryDict(currentAnalysisDict, "dtr");
  }

  const queryDict = queryDictFromFilters(filters);
  queryDicts[QUERY_ROLE_BY_PREFIX[panel.prefix]] =
    Object.keys(queryDict).length > 0 ? queryDict : null;

  if (queryDicts.numerator || queryDicts.denominator) {
    const analysisDict = buildAnalysisDict(
      queryDicts.numerator,
      queryDicts.denominator,
      currentAnalysisDict?.org_id,
    );
    url.searchParams.set("analysis", JSON.stringify(analysisDict));
  } else {
    url.searchParams.delete("analysis");
  }

  window.history.replaceState({}, "", url);
}

function readAnalysisDict(params) {
  // Parse the `analysis` query parameter, returning null when it is absent.
  return JSON.parse(params.get("analysis"));
}

function buildAnalysisDict(numerator, denominator, orgId) {
  // Build an analysis dict matching the backend's Analysis.to_dict shape.
  const analysisDict = {
    options: { output_value: "items" },
    queries: [{ numerator: numerator ?? {} }],
  };

  if (denominator) {
    analysisDict.queries[0].denominator = denominator;
    analysisDict.options.type = "prescribing_vs_prescribing";
  } else {
    analysisDict.options.type = "prescribing_vs_list_size";
  }

  if (orgId) {
    analysisDict.org_id = orgId;
  }

  return analysisDict;
}

function getQueryDict(analysisDict, prefix) {
  // Return the BNFQuery dict for the given panel's role, or null if that role is
  // absent (eg a numerator-only analysis that has no denominator).
  return analysisDict.queries[0][QUERY_ROLE_BY_PREFIX[prefix]] ?? null;
}

initialisePage();
