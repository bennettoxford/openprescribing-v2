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
    urlParamSuffix: "form_routes",
    isBaseline: false,
    lookupKey: "ont_form_route",
    valueField: "descr",
    labelField: "descr",
    parse: parseOptionalString,
    matches: (medication, value) => medication.form_routes.includes(value),
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

export function parseFilterValues(definition, rawValues) {
  // Parse a list of raw values (from a query dict) into filter values.
  if (!rawValues) {
    return [];
  }

  return rawValues
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

export function filtersFromQueryDict(queryDict) {
  // Return a filters object built from a BNFQuery dict (as produced by the
  // backend's BNFQuery.to_dict).  Keys are the filter URL param suffixes, e.g.
  // `bnf_codes` and `bnf_codes_excluded`.  Unknown keys (such as `product_type`,
  // which the builder has no control for) are ignored.
  const filters = getEmptyFilters();

  if (!queryDict) {
    return filters;
  }

  FILTER_DEFINITIONS.forEach((definition) => {
    [false, true].forEach((isExcluded) => {
      const filterKey = getFilterControlKey(definition, isExcluded);
      const dictKey = getFilterControlUrlParamSuffix(definition, isExcluded);
      filters[filterKey] = parseFilterValues(definition, queryDict[dictKey]);
    });
  });

  return filters;
}

export function queryDictFromFilters(filters) {
  // Return a BNFQuery dict (matching the backend's BNFQuery.to_dict shape) for
  // the given filters, omitting empty values.
  const queryDict = {};

  FILTER_DEFINITIONS.forEach((definition) => {
    [false, true].forEach((isExcluded) => {
      const filterKey = getFilterControlKey(definition, isExcluded);
      const values = filters[filterKey];

      if (values.length > 0) {
        const dictKey = getFilterControlUrlParamSuffix(definition, isExcluded);
        queryDict[dictKey] = values;
      }
    });
  });

  return queryDict;
}

function parseOptionalInteger(value) {
  // Parse an integer filter value.
  return value === "" ? null : Number.parseInt(value, 10);
}

function parseOptionalString(value) {
  // Parse a string filter value.
  return value === "" ? null : value;
}
