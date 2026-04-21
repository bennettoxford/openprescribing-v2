import { FILTER_DEFINITIONS } from "./filters.js";

const BNF_LEVEL_LABELS = new Map([
  [1, "Chapter"],
  [2, "Section"],
  [3, "Paragraph"],
  [4, "Subparagraph"],
  [5, "Chemical"],
  [6, "Product"],
  [7, "Presentation"],
]);

export async function fetchMetadata(containerEl) {
  // Fetch metadata from the medications, dm+d, and BNF endpoints and build the lookup
  // maps and per-filter medication indexes used elsewhere.
  const medications = await fetchJson(containerEl.dataset.medicationsUrl);
  const dmd = await fetchJson(containerEl.dataset.dmdUrl);
  const bnf = await fetchJson(containerEl.dataset.bnfUrl);
  const lookupRecordsByFilterKey = buildLookupRecordsByFilterKey(dmd, bnf.bnf);
  const indexedMedications = medications.medications.map(
    (medication, index) => ({
      ...medication,
      medicationIndex: index,
    }),
  );
  const medicationIndexesByFilterValue = buildMedicationIndexesByFilterValue(
    indexedMedications,
    lookupRecordsByFilterKey.get("bnfCodePrefix"),
  );

  return {
    medications: indexedMedications,
    ...dmd,
    bnf: bnf.bnf,
    lookupRecordsByFilterKey,
    medicationIndexesByFilterValue,
    formRouteById: new Map(dmd.ont_form_route.map((item) => [item.id, item])),
    vtmById: new Map(dmd.vtm.map((vtm) => [vtm.id, vtm])),
    vmpById: new Map(dmd.vmp.map((vmp) => [vmp.id, vmp])),
  };
}

async function fetchJson(url) {
  // Fetch and parse a JSON endpoint.
  const response = await fetch(url);

  if (!response.ok) {
    throw new Error(`Request failed with status ${response.status}`);
  }

  return response.json();
}

function buildLookupRecordsByFilterKey(dmd, bnf) {
  // Return searchable lookup records for each filter.
  //
  // Each entry maps a filter key to a list of lookup records. A dm+d lookup
  // record has the shape { label, value }, where `label` is shown to the user
  // and `value` is the filter value used for matching. BNF lookup records
  // carry extra `searchCode`, `searchName`, and `sortLevel` fields used by the
  // dropdown's search and ordering.
  const metadataByLookupKey = {
    ingredient: dmd.ingredient,
    vtm: dmd.vtm,
    ont_form_route: dmd.ont_form_route,
    bnf: bnf,
  };

  return new Map(
    FILTER_DEFINITIONS.map((definition) => {
      const records = metadataByLookupKey[definition.lookupKey];
      const lookupRecords =
        definition.lookupKey === "bnf"
          ? buildBnfLookupRecords(records)
          : buildDmdLookupRecords(records, definition);
      return [definition.key, lookupRecords];
    }),
  );
}

function buildDmdLookupRecords(records, definition) {
  // Return dm+d lookup records ordered by label.
  return records
    .map((record) => ({
      label: record[definition.labelField],
      value: record[definition.valueField],
    }))
    .sort((left, right) => left.label.localeCompare(right.label));
}

function buildBnfLookupRecords(records) {
  // Return BNF lookup records ordered by hierarchy level, then name, then code.
  return records
    .filter((record) => record.level <= 6)
    .map((record) => ({
      label: `${record.name} (${BNF_LEVEL_LABELS.get(record.level)})`,
      searchCode: record.code,
      searchName: record.name,
      sortLevel: record.level,
      value: record.code,
    }))
    .sort((left, right) => {
      if (left.sortLevel !== right.sortLevel) {
        return left.sortLevel - right.sortLevel;
      }

      const nameComparison = left.label.localeCompare(right.label);

      if (nameComparison !== 0) {
        return nameComparison;
      }

      return left.value.localeCompare(right.value);
    });
}

function buildMedicationIndexesByFilterValue(medications, bnfLookupRecords) {
  // Return option-to-medication indexes for each filter definition.
  //
  // For each filter key, the index is a Map from an option value to the list
  // of medication indexes (into the `medications` list) that match that
  // option. Used by query.js to narrow the set of selectable options in each
  // filter control without re-scanning the full medication list.
  const indexesByFilterValue = {
    bnfCodePrefix: new Map(),
    formRouteId: new Map(),
    ingredientId: new Map(),
    vtmId: new Map(),
  };
  const bnfLookupValues = new Set(
    bnfLookupRecords
      .map((record) => record.value)
      .filter((value) => !value.includes("_")),
  );
  const bnfPrefixLengths = Array.from(
    new Set(Array.from(bnfLookupValues, (value) => value.length)),
  ).sort((left, right) => left - right);

  medications.forEach((medication) => {
    medication.ingredient_ids.forEach((ingredientId) => {
      addMedicationIndex(
        indexesByFilterValue.ingredientId,
        ingredientId,
        medication,
      );
    });

    if (medication.vtm_id !== null) {
      addMedicationIndex(
        indexesByFilterValue.vtmId,
        medication.vtm_id,
        medication,
      );
    }

    medication.form_route_ids.forEach((formRouteId) => {
      addMedicationIndex(
        indexesByFilterValue.formRouteId,
        formRouteId,
        medication,
      );
    });

    if (medication.bnf_code === null) {
      return;
    }

    bnfPrefixLengths.forEach((prefixLength) => {
      const prefix = medication.bnf_code.slice(0, prefixLength);

      if (bnfLookupValues.has(prefix)) {
        addMedicationIndex(
          indexesByFilterValue.bnfCodePrefix,
          prefix,
          medication,
        );
      }
    });
  });

  return indexesByFilterValue;
}

function addMedicationIndex(indexesByValue, value, medication) {
  // Add a medication index to the given option value index.
  if (!indexesByValue.has(value)) {
    indexesByValue.set(value, []);
  }

  indexesByValue.get(value).push(medication.medicationIndex);
}
