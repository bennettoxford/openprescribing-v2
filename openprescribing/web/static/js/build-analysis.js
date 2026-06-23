// Analysis builder
// =================
//
// This is the entry point for the "build an analysis" page.  It lets a user describe a
// set of medications by combining filters, shows which medications match, and builds a
// shareable URL that drives the resulting prescribing analysis.
//
// Panels
// ------
// The page has two independent query panels (for the numerator and denominator queries
// of an analysis).  Each panel has its own filters, its own results, and its own slice
// of the URL parameters (namespaced by a per-panel prefix).  Everything below applies
// to a single panel.
//
// Filters
// -------
// The available filters are defined in filters.js.  To build a medications query, users
// can add filter controls, to either include or exclude medications that match the
// filter.  Users can select one or more items from a filter control.
//
// Queries
// ------
//
// A query is made up of one or more filters, and returns a collection of medications
// that match the filters, according to these rules:
//
//  - a medication matches a filter if it matches any of the items from the filter
//  - a medication is *excluded* if it matches any exclusion filter
//  - otherwise a medication is *included* only if it matches every active inclusion
//    filter
//
// Evaluating the filters gives each medication one of three statuses:
//
//  - INCLUDED: matches all inclusion filters and no exclusion filter
//  - EXCLUDED: matches at least one exclusion filter
//  - NOT_INCLUDED: does not match all inclusion filters
//
// A fourth status, VMP_NOT_INCLUDED_BUT_CHILD_AMP_IS, is then derived for any
// not-included VMP that has an included AMP child (see the subtlety under Results).
//
// Baseline filters and visibility
// -------------------------------
// Some filters are "baseline" filters: they additionally determine which medications
// are visible in the results.  Currently, only form/route is not a baseline filter.
// This allows users to filter the results progressively, by adding one filter at a
// time, while still being able to see medications that match all other filters.
//
// As/when we add new filters, we'll have to decide whether they should be baseline
// filters or not.  A possible rule of thumb: if a filter would match many medications,
// most of which a user wouldn't want to include in their results, then the filter
// should not be a baseline filter.
//
// Results
// -------
// Results are shown as a tree of VTM > VMP > AMP, with a count of the included VMPs and
// AMPs above it.  Each row is styled by its status:
//
//  - INCLUDED: shown normally
//  - EXCLUDED: greyed out and struck through
//  - NOT_INCLUDED: greyed out
//
// A "show only matching" toggle hides everything except included rows.  Until at least
// one inclusion filter is added, the panel shows a prompt instead of results.
//
// One subtlety: a VMP can sit in a different BNF chapter from its AMPs (eg Amantadine
// capsules is classified under Parkinson's but has an antiviral AMP).  When a baseline
// filter keeps an AMP but drops its parent VMP, the VMP is still shown for context,
// greyed out and expanded so the matching AMP is visible.
//
// Dropdowns
// ---------
// As filters change, each dropdown only offers values that could still match something
// given the other active filters, so the user can't accidentally build an empty query.
//
// URL state
// ---------
// All filter state lives in the URL, so a query is shareable and survives a reload.
// The page reads its initial state from the URL, writes back on every change, and the
// summary tab's submit button points at the analysis page for the current state.
//
// Module layout
// -------------
//   - filters.js   filter definitions and value matching
//   - metadata.js  fetches medication/dm+d/BNF metadata and builds lookup maps
//   - query.js     applies filters to produce statuses, counts and dropdown options
//   - render.js    renders the results tree, filter summary and dropdown options
//   - dropdown.js  the reusable multi-select dropdown control

import {
  applyFiltersToUrlParams,
  FILTER_DEFINITIONS,
  getEmptyFilters,
  getFilterControlKey,
  getFilterControlLabel,
  getFilterControlUrlParamSuffix,
  getFilterDefinitionForControlKey,
  hasAnyFilters,
  hasAnyInclusionFilters,
  isExcludedFilterControlKey,
  parseFiltersFromUrlParams,
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
  return parseFiltersFromUrlParams(params, (filterKey) =>
    getUrlParamName(panel, filterKey),
  );
}

function updateUrlFromFilters(panel, filters) {
  // Replace the current URL with the panel's filter state.
  const url = new URL(window.location.href);
  applyFiltersToUrlParams(url.searchParams, filters, (filterKey) =>
    getUrlParamName(panel, filterKey),
  );
  window.history.replaceState({}, "", url);
}

function getUrlParamName(panel, filterKey) {
  // Return the URL parameter name for a panel/filter pair.
  const definition = getFilterDefinitionForControlKey(filterKey);
  const suffix = getFilterControlUrlParamSuffix(
    definition,
    isExcludedFilterControlKey(filterKey),
  );
  return `${panel.prefix}_${suffix}`;
}

initialisePage();
