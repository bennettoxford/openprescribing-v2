// This module contains code to render the filters and the results table.

import {
  FILTER_DEFINITIONS,
  getFilterControlKey,
  getFilterControlLabel,
} from "./filters.js";
import { STATUS } from "./query.js";

export function renderAddFilterOptions(panel) {
  // Populate the Add filter dropdown for the panel.
  const options = [makeAddFilterOption("", "Choose a filter...")];
  const hasAnyFilterControls = getActiveFilterControlCount(panel) > 0;

  FILTER_DEFINITIONS.forEach((definition) => {
    const includeKey = getFilterControlKey(definition, false);

    if (!panel.dropdowns.has(includeKey)) {
      options.push(makeAddFilterOption(includeKey, definition.label));
    }

    if (hasAnyFilterControls) {
      const excludeKey = getFilterControlKey(definition, true);

      if (!panel.dropdowns.has(excludeKey)) {
        options.push(
          makeAddFilterOption(
            excludeKey,
            getFilterControlLabel(definition, true),
          ),
        );
      }
    }
  });

  panel.refs.addFilterSelect.replaceChildren(...options);
  panel.refs.addFilterSelect.value = "";
}

export function renderSummary(sectionsByPrefix, panels, metadata, templates) {
  // Render the active filters for each panel into the summary tab.
  panels.forEach((panel) => {
    renderSummarySection(sectionsByPrefix.get(panel.prefix), panel, templates);
  });
}

function makeAddFilterOption(value, label) {
  // Build an Add filter dropdown option.
  const option = document.createElement("option");
  option.value = value;
  option.textContent = label;
  return option;
}

function getActiveFilterControlCount(panel) {
  // Return the number of active filter controls in the panel.
  // TODO move this inline.
  return Object.keys(panel.dropdowns.getAllSelected()).length;
}

function renderSummarySection(sectionEl, panel, templates) {
  // Render given panel's active filters into its summary section.
  const selectedNamesByKey = panel.dropdowns.getAllSelectedNames();
  const activeFilters = FILTER_DEFINITIONS.flatMap((definition) =>
    [false, true].flatMap((isExcluded) => {
      const filterKey = getFilterControlKey(definition, isExcluded);
      const values = selectedNamesByKey[filterKey] ?? [];

      if (values.length === 0) {
        return [];
      }

      return [
        {
          label: getFilterControlLabel(definition, isExcluded),
          values: selectedNamesByKey[filterKey],
        },
      ];
    }),
  );

  const listEl = cloneTemplateElement(templates.summaryListTemplate);

  if (activeFilters.length === 0) {
    listEl.appendChild(
      cloneTemplateElement(templates.summaryEmptyListItemTemplate),
    );
    sectionEl.replaceChildren(listEl);
    return;
  }

  activeFilters.forEach((filter) => {
    const itemEl = cloneTemplateElement(templates.summaryListItemTemplate);
    itemEl.querySelector("[data-label]").textContent = filter.label;
    itemEl.querySelector("[data-values]").textContent =
      ` ${filter.values.join(", ")}`;
    listEl.appendChild(itemEl);
  });

  sectionEl.replaceChildren(listEl);
}

function cloneTemplateElement(template) {
  // Clone a template's first element.
  return template.content.firstElementChild.cloneNode(true);
}

export function renderPromptState(panel) {
  // Render the panel in its initial prompt state.
  panel.refs.resultsPromptEl.hidden = false;
  panel.refs.resultsCountsEl.hidden = true;
  panel.refs.resultsEmptyEl.hidden = true;
  panel.refs.resultsTableEl.hidden = true;
  panel.refs.resultsBodyEl.replaceChildren();
}

export function renderResults(panel, results, metadata, templates) {
  // Render the panel's query results.
  const medicationsToRender = getMedicationsToRender(
    panel,
    results.medications,
  );
  const groups = groupResults(medicationsToRender, metadata);

  panel.refs.resultsPromptEl.hidden = true;
  panel.refs.resultsCountsEl.hidden = false;
  panel.refs.resultsCountsEl.textContent = makeResultsCountsText(results);

  if (results.medications.length === 0) {
    panel.refs.resultsBodyEl.replaceChildren();
    panel.refs.resultsTableEl.hidden = true;
    panel.refs.resultsEmptyEl.hidden = false;
    return;
  }

  panel.refs.resultsEmptyEl.hidden = results.includedCount > 0;
  panel.refs.resultsTableEl.hidden = medicationsToRender.length === 0;
  renderResultsTable(panel, groups, templates);
}

function getMedicationsToRender(panel, medications) {
  // Return medications visible under the panel's display filter.
  if (!panel.refs.showOnlyMatchingCheckbox.checked) {
    return medications;
  }

  return medications.filter(
    (medication) => medication.status === STATUS.INCLUDED,
  );
}

function groupResults(results, metadata) {
  // Group results by VTM, then VMP, then AMP.
  const vtmGroups = new Map();

  const getOrCreateVtmGroup = (vtmId) => {
    if (!vtmGroups.has(vtmId)) {
      vtmGroups.set(vtmId, {
        id: vtmId,
        name: vtmId === null ? "No VTM" : metadata.vtmById.get(vtmId).name,
        vmps: new Map(),
      });
    }

    return vtmGroups.get(vtmId);
  };

  const getOrCreateVmpGroup = (vtmGroup, vmpId) => {
    if (!vtmGroup.vmps.has(vmpId)) {
      const { name } = metadata.vmpById.get(vmpId);
      vtmGroup.vmps.set(vmpId, {
        id: vmpId,
        name,
        status: STATUS.INCLUDED,
        amps: [],
      });
    }

    return vtmGroup.vmps.get(vmpId);
  };

  results.forEach((medication) => {
    const vtmGroup = getOrCreateVtmGroup(medication.vtm_id);
    const vmpGroup = getOrCreateVmpGroup(vtmGroup, medication.vmp_id);

    if (medication.is_amp) {
      vmpGroup.amps.push({
        id: medication.id,
        formRouteText: getFormRouteText(medication.form_route_ids, metadata),
        name: medication.name,
        status: medication.status,
      });
    } else {
      vmpGroup.formRouteText = getFormRouteText(
        medication.form_route_ids,
        metadata,
      );
      vmpGroup.status = medication.status;
    }
  });

  const groupedResults = Array.from(vtmGroups.values());

  groupedResults.forEach((vtmGroup) => {
    vtmGroup.vmps = Array.from(vtmGroup.vmps.values());

    vtmGroup.vmps.forEach((vmpGroup) => {
      sortByName(vmpGroup.amps);
    });

    vtmGroup.status = getGroupStatus(vtmGroup.vmps.map((vmp) => vmp.status));
    sortByName(vtmGroup.vmps);
  });

  sortByName(groupedResults);
  return groupedResults;
}

function getGroupStatus(statuses) {
  // Return the aggregate display status for a group of rows.
  if (statuses.every((status) => status === STATUS.EXCLUDED)) {
    return STATUS.EXCLUDED;
  }

  if (statuses.every((status) => status !== STATUS.INCLUDED)) {
    return STATUS.NOT_INCLUDED;
  }

  return STATUS.INCLUDED;
}

function makeResultsCountsText(results) {
  // Return summary text for the included medications.
  return `${results.includedCount} dm+d products (${results.includedVmpCount} VMPs, ${results.includedAmpCount} AMPs)`;
}

function renderResultsTable(panel, groups, templates) {
  // Fill the panel's results table body from grouped data.
  const rows = document.createDocumentFragment();

  groups.forEach((vtm) => {
    rows.appendChild(makeVtmRow(vtm, templates.vtmRowTemplate));

    vtm.vmps.forEach((vmp) => {
      rows.appendChild(makeVmpRow(vmp, templates.vmpRowTemplate));

      vmp.amps.forEach((amp) => {
        rows.appendChild(makeAmpRow(amp, vmp.id, templates.ampRowTemplate));
      });
    });
  });

  panel.refs.resultsBodyEl.replaceChildren(rows);
}

function makeVtmRow(vtm, template) {
  // Build a VTM table row.
  const row = cloneRow(template);
  applyStatusStyling(row, vtm.status);
  row.querySelector("[data-name]").textContent = vtm.name;
  return row;
}

function makeVmpRow(vmp, template) {
  // Build a VMP table row.
  const row = cloneRow(template);
  const toggleButton = row.querySelector("[data-amp-toggle]");

  applyStatusStyling(row, vmp.status);
  row.querySelector("[data-name]").textContent = vmp.name;
  row.querySelector("[data-form-route]").textContent = vmp.formRouteText;

  if (vmp.amps.length > 0) {
    toggleButton.style.visibility = "visible";
    toggleButton.dataset.vmpId = String(vmp.id);
  }

  return row;
}

function makeAmpRow(amp, vmpId, template) {
  // Build an AMP table row.
  const row = cloneRow(template);
  row.dataset.ampRow = String(vmpId);
  applyStatusStyling(row, amp.status);
  row.querySelector("[data-name]").textContent = amp.name;
  row.querySelector("[data-form-route]").textContent = amp.formRouteText;
  return row;
}

function cloneRow(template) {
  // Clone a template's first element.
  return template.content.firstElementChild.cloneNode(true);
}

function sortByName(items) {
  // Sort records by name in place.
  items.sort((left, right) => left.name.localeCompare(right.name));
}

function applyStatusStyling(row, status) {
  // Apply row styling for the given status.
  const nameEl = row.querySelector("[data-name]");
  row.dataset.status = status;

  if (status !== STATUS.INCLUDED) {
    row.style.opacity = "0.55";
    nameEl.classList.add("text-body-secondary");
  }

  if (status === STATUS.EXCLUDED) {
    nameEl.style.textDecoration = "line-through";
  }
}

function getFormRouteText(formRouteIds, metadata) {
  // Return comma-separated form/route descriptions.
  return formRouteIds
    .map((id) => metadata.formRouteById.get(id).descr)
    .sort((left, right) => left.localeCompare(right))
    .join(", ");
}
