// This module contains functions to evaluate filters against the medications metadata,
// and functions to compute which option IDs remain selectable in each filter control.
//
// This module has no DOM access.

import {
  FILTER_DEFINITIONS,
  getFilterControlKey,
  getFilterDefinitionForControlKey,
  hasAnyFilters,
  matchesAnyFilterValue,
} from "./filters.js";

export const STATUS = {
  // Medication matches all inclusion filters and no exclusion filter.
  INCLUDED: "included",
  // Medication matches at least one exclusion filter.
  EXCLUDED: "excluded",
  // Medication does not match all inclusion filters.
  NOT_INCLUDED: "not_included",
  // VMP is NOT_INCLUDED, but has an included AMP child.
  VMP_NOT_INCLUDED_BUT_CHILD_AMP_IS: "vmp_not_included_but_child_amp_is",
};

export function queryMedications(metadata, filters) {
  // Return visible medications with status, as well as counts of included medications.
  const baselineMedications = metadata.medications.filter((medication) =>
    matchesBaselineFilters(medication, filters),
  );
  const medications = withVmpChildStatuses(
    baselineMedications
      .concat(getExcludedParentVmps(baselineMedications, metadata))
      .map((medication) => ({
        ...medication,
        status: getMedicationStatus(medication, filters),
      })),
  );
  const includedMedications = medications.filter(
    (medication) => medication.status === STATUS.INCLUDED,
  );
  const includedVmpCount = includedMedications.filter(
    (medication) => !medication.is_amp,
  ).length;
  const includedAmpCount = includedMedications.filter(
    (medication) => medication.is_amp,
  ).length;

  return {
    medications,
    includedCount: includedMedications.length,
    includedVmpCount,
    includedAmpCount,
  };
}

function getExcludedParentVmps(visibleMedications, metadata) {
  // Return the parent VMPs of any visible AMP whose own VMP record was excluded by the
  // baseline filters.
  const visibleVmpIds = new Set(
    visibleMedications
      .filter((medication) => !medication.is_amp)
      .map((medication) => medication.id),
  );

  const excludedVmpIds = new Set();
  visibleMedications.forEach((medication) => {
    if (medication.is_amp && !visibleVmpIds.has(medication.vmp_id)) {
      excludedVmpIds.add(medication.vmp_id);
    }
  });

  return Array.from(excludedVmpIds, (vmpId) =>
    metadata.medicationById.get(vmpId),
  );
}

function withVmpChildStatuses(medications) {
  // Update the status of each not-included VMP with an included AMP child to
  // VMP_NOT_INCLUDED_BUT_CHILD_AMP_IS.
  const vmpIdsWithIncludedAmp = new Set(
    medications
      .filter(
        (medication) =>
          medication.is_amp && medication.status === STATUS.INCLUDED,
      )
      .map((medication) => medication.vmp_id),
  );

  return medications.map((medication) => {
    if (
      !medication.is_amp &&
      medication.status === STATUS.NOT_INCLUDED &&
      vmpIdsWithIncludedAmp.has(medication.id)
    ) {
      return {
        ...medication,
        status: STATUS.VMP_NOT_INCLUDED_BUT_CHILD_AMP_IS,
      };
    }

    return medication;
  });
}

export function getCachedValidOptionIds(panel, filterKey) {
  // Return the cached valid option IDs for the given filter control.
  return panel.availableOptionIdsByFilterKey.get(filterKey);
}

export function refreshAvailableOptionIds(panel, metadata, filters) {
  // Recompute valid option IDs for all filter controls in the given panel.
  panel.availableOptionIdsByFilterKey.clear();

  FILTER_DEFINITIONS.forEach((definition) => {
    [false, true].forEach((isExcluded) => {
      const filterKey = getFilterControlKey(definition, isExcluded);
      panel.availableOptionIdsByFilterKey.set(
        filterKey,
        getValidOptionIds(filterKey, metadata, filters),
      );
    });
  });
}

function matchesVisibleFilters(medication, filters) {
  // Return whether a medication is in the visible baseline set and not excluded.
  if (!matchesBaselineFilters(medication, filters)) {
    return false;
  }

  return FILTER_DEFINITIONS.every((definition) => {
    const excludedValues = filters[getFilterControlKey(definition, true)];

    return (
      excludedValues.length === 0 ||
      !matchesAnyFilterValue(definition, medication, excludedValues)
    );
  });
}

function matchesBaselineFilters(medication, filters) {
  // Return whether a medication is in the visible baseline set.  If no baseline filters
  // returns whether it matches any of the other filters.
  const activeBaselineDefinitions = FILTER_DEFINITIONS.filter(
    (definition) =>
      definition.isBaseline &&
      filters[getFilterControlKey(definition, false)].length > 0,
  );

  if (activeBaselineDefinitions.length > 0) {
    return activeBaselineDefinitions.some((definition) =>
      matchesAnyFilterValue(
        definition,
        medication,
        filters[getFilterControlKey(definition, false)],
      ),
    );
  }

  return FILTER_DEFINITIONS.every((definition) => {
    const filterValues = filters[getFilterControlKey(definition, false)];

    if (filterValues.length === 0) {
      return true;
    }

    return matchesAnyFilterValue(definition, medication, filterValues);
  });
}

function getMedicationStatus(medication, filters) {
  // Return the display status for a medication.

  const matchesAllInclusionFilters = FILTER_DEFINITIONS.every((definition) => {
    const includedValues = filters[getFilterControlKey(definition, false)];

    return (
      includedValues.length === 0 ||
      matchesAnyFilterValue(definition, medication, includedValues)
    );
  });

  const matchesAnyExclusionFilter = FILTER_DEFINITIONS.some((definition) => {
    const excludedValues = filters[getFilterControlKey(definition, true)];

    return (
      excludedValues.length > 0 &&
      matchesAnyFilterValue(definition, medication, excludedValues)
    );
  });

  if (matchesAllInclusionFilters && !matchesAnyExclusionFilter) {
    return STATUS.INCLUDED;
  }

  if (matchesAnyExclusionFilter) {
    return STATUS.EXCLUDED;
  }

  return STATUS.NOT_INCLUDED;
}

function getValidOptionIds(filterKey, metadata, filters) {
  // Return valid option IDs for the given filter control under the other active filters.
  const definition = getFilterDefinitionForControlKey(filterKey);
  const filtersExceptCurrentControl = getFiltersExcept(filters, filterKey);

  if (!hasAnyFilters(filtersExceptCurrentControl)) {
    return getAllOptionIds(metadata, definition.key);
  }

  const medicationIndexes = getPossibleMedicationIndexes(
    filtersExceptCurrentControl,
    metadata,
  );

  return getPossibleOptionIds(definition.key, medicationIndexes, metadata);
}

function getFiltersExcept(filters, ignoredFilterKey) {
  // Return the panel filters with the given control cleared.
  return {
    ...filters,
    [ignoredFilterKey]: [],
  };
}

function getAllOptionIds(metadata, filterKey) {
  // Return all option IDs for the given filter definition.
  return metadata.lookupRecordsByFilterKey
    .get(filterKey)
    .map((record) => String(record.value));
}

function getPossibleMedicationIndexes(filters, metadata) {
  // Return medication indexes that satisfy the current filters.
  return new Set(
    metadata.medications
      .filter((medication) => matchesMedicationFilters(medication, filters))
      .map((medication) => medication.medicationIndex),
  );
}

function matchesMedicationFilters(medication, filters) {
  // Return whether a medication remains possible under the current filters.
  if (!matchesVisibleFilters(medication, filters)) {
    return false;
  }

  return FILTER_DEFINITIONS.every((definition) => {
    const includedValues = filters[getFilterControlKey(definition, false)];

    if (includedValues.length === 0) {
      return true;
    }

    return matchesAnyFilterValue(definition, medication, includedValues);
  });
}

function getPossibleOptionIds(filterKey, medicationIndexes, metadata) {
  // Return option IDs whose indexed medications intersect the possible set.
  const indexesByValue = metadata.medicationIndexesByFilterValue[filterKey];

  return metadata.lookupRecordsByFilterKey
    .get(filterKey)
    .filter((record) =>
      indexesByValue
        .get(record.value)
        ?.some((medicationIndex) => medicationIndexes.has(medicationIndex)),
    )
    .map((record) => String(record.value));
}
