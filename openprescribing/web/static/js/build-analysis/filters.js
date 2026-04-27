// This module defines the filters that are available for querying medications.
//
// This module has no DOM access.

export const FILTER_DEFINITIONS = [
  {
    key: "ingredientId",
    label: "Ingredient",
    urlParamSuffix: "ingredient_ids",
    isBaseline: true,
    lookupKey: "ingredient",
    valueField: "id",
    labelField: "name",
    parse: parseOptionalInteger,
    matches: (medication, value) => medication.ingredient_ids.includes(value),
  },
  {
    key: "vtmId",
    label: "VTM",
    urlParamSuffix: "vtm_ids",
    isBaseline: true,
    lookupKey: "vtm",
    valueField: "id",
    labelField: "name",
    parse: parseOptionalInteger,
    matches: (medication, value) => medication.vtm_id === value,
  },
  {
    key: "bnfCodePrefix",
    label: "BNF hierarchy",
    urlParamSuffix: "bnf_codes",
    isBaseline: true,
    lookupKey: "bnf",
    valueField: "code",
    labelField: "name",
    parse: parseOptionalString,
    matches: (medication, value) => medication.bnf_code?.startsWith(value),
  },
  {
    key: "formRouteId",
    label: "Form/route",
    urlParamSuffix: "form_route_ids",
    isBaseline: false,
    lookupKey: "ont_form_route",
    valueField: "id",
    labelField: "descr",
    parse: parseOptionalInteger,
    matches: (medication, value) => medication.form_route_ids.includes(value),
  },
];

const FILTER_DEFINITION_BY_KEY = new Map(
  FILTER_DEFINITIONS.map((definition) => [definition.key, definition]),
);

export function getFilterControlKey(definition, isExcluded) {
  // Return the control key for the given filter definition and variant.
  return isExcluded ? `${definition.key}Exclude` : definition.key;
}

export function getFilterControlLabel(definition, isExcluded) {
  // Return the control label for the given filter definition and variant.
  return isExcluded ? `${definition.label} (excluded)` : definition.label;
}

export function getFilterControlUrlParamSuffix(definition, isExcluded) {
  // Return the URL parameter suffix for the given filter definition and variant.
  return isExcluded
    ? `${definition.urlParamSuffix}_excluded`
    : definition.urlParamSuffix;
}

export function isExcludedFilterControlKey(filterKey) {
  // Return whether a filter control key is for an excluded variant.
  return filterKey.endsWith("Exclude");
}

export function getFilterDefinitionForControlKey(filterKey) {
  // Return the filter definition for the given filter control key.
  const baseKey = isExcludedFilterControlKey(filterKey)
    ? filterKey.slice(0, -"Exclude".length)
    : filterKey;
  return FILTER_DEFINITION_BY_KEY.get(baseKey);
}

export function getEmptyFilters() {
  // Return an empty filters object.
  return Object.fromEntries(
    FILTER_DEFINITIONS.flatMap((definition) => [
      [getFilterControlKey(definition, false), []],
      [getFilterControlKey(definition, true), []],
    ]),
  );
}

export function parseFilterValues(definition, rawValue) {
  // Parse a comma-separated URL parameter into filter values.
  if (rawValue === null) {
    return [];
  }

  return rawValue
    .split(",")
    .map((value) => definition.parse(value))
    .filter((value) => value !== null);
}

export function matchesAnyFilterValue(definition, medication, values) {
  // Return whether a medication matches any selected value for the given filter.
  return values.some((value) => definition.matches(medication, value));
}

export function hasAnyFilters(filters) {
  // Return whether any filter has a value.
  return Object.values(filters).some((values) => values.length > 0);
}

export function hasAnyInclusionFilters(filters) {
  // Return whether any inclusion filter has a value.
  return FILTER_DEFINITIONS.some(
    (definition) => filters[getFilterControlKey(definition, false)].length > 0,
  );
}

export function parseFiltersFromUrlParams(params, getParamName) {
  // Return a filters object built from the given URL parameters, using
  // getParamName(filterKey) to locate each control's parameter.
  const filters = getEmptyFilters();

  FILTER_DEFINITIONS.forEach((definition) => {
    [false, true].forEach((isExcluded) => {
      const filterKey = getFilterControlKey(definition, isExcluded);
      filters[filterKey] = parseFilterValues(
        definition,
        params.get(getParamName(filterKey)),
      );
    });
  });

  return filters;
}

export function applyFiltersToUrlParams(params, filters, getParamName) {
  // Write the given filters into the given URL parameters, using
  // getParamName(filterKey) to locate each control's parameter.
  FILTER_DEFINITIONS.forEach((definition) => {
    [false, true].forEach((isExcluded) => {
      const filterKey = getFilterControlKey(definition, isExcluded);
      const paramName = getParamName(filterKey);
      const values = filters[filterKey];

      if (values.length === 0) {
        params.delete(paramName);
      } else {
        params.set(paramName, values.join(","));
      }
    });
  });
}

function parseOptionalInteger(value) {
  // Parse an integer filter value.
  const trimmedValue = value.trim();
  return trimmedValue === "" ? null : Number.parseInt(trimmedValue, 10);
}

function parseOptionalString(value) {
  // Parse a string filter value.
  const trimmedValue = value.trim();
  return trimmedValue === "" ? null : trimmedValue;
}
