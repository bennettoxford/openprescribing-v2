import { describe, expect, it } from "vitest";

import {
  filtersFromQueryDict,
  getEmptyFilters,
  queryDictFromFilters,
} from "../../openprescribing/web/static/js/build-analysis/filters.js";

function filtersWith(overrides) {
  return { ...getEmptyFilters(), ...overrides };
}

describe("queryDictFromFilters", () => {
  it("uses the backend BNFQuery.to_dict keys and omits empty filters", () => {
    const filters = filtersWith({
      bnfCodePrefix: ["01"],
      bnfCodePrefixExclude: ["0101"],
      ingredientId: [1],
      vtmId: [5],
      formRouteId: ["tablet.oral"],
    });

    expect(queryDictFromFilters(filters)).toEqual({
      bnf_codes: ["01"],
      bnf_codes_excluded: ["0101"],
      ingredient_ids: [1],
      vtm_ids: [5],
      form_routes: ["tablet.oral"],
    });
  });

  it("returns an empty dict when no filters are set", () => {
    expect(queryDictFromFilters(getEmptyFilters())).toEqual({});
  });

  it("serializes product type as a scalar", () => {
    expect(
      queryDictFromFilters(filtersWith({ productType: ["generic"] })),
    ).toEqual({ product_type: "generic" });
  });

  it("serializes the 'all' product type", () => {
    expect(queryDictFromFilters(filtersWith({ productType: ["all"] }))).toEqual(
      {
        product_type: "all",
      },
    );
  });
});

describe("filtersFromQueryDict", () => {
  it("parses a query dict into filters, coercing ids to numbers", () => {
    const filters = filtersFromQueryDict({
      bnf_codes: ["01"],
      bnf_codes_excluded: ["0101"],
      ingredient_ids: [1],
      vtm_ids: [5],
      form_routes: ["tablet.oral"],
    });

    expect(filters.bnfCodePrefix).toEqual(["01"]);
    expect(filters.bnfCodePrefixExclude).toEqual(["0101"]);
    expect(filters.ingredientId).toEqual([1]);
    expect(filters.vtmId).toEqual([5]);
    expect(filters.formRouteId).toEqual(["tablet.oral"]);
  });

  it("parses a scalar product type into a filter value", () => {
    const filters = filtersFromQueryDict({ product_type: "branded" });

    expect(filters.productType).toEqual(["branded"]);
  });

  it("returns empty filters for a null/missing query dict", () => {
    expect(filtersFromQueryDict(null)).toEqual(getEmptyFilters());
  });
});

describe("round trip", () => {
  it("survives filters -> dict -> filters", () => {
    const filters = filtersWith({
      bnfCodePrefix: ["01"],
      ingredientId: [1, 2],
      vtmId: [5],
      formRouteIdExclude: ["solution.oral"],
    });

    expect(filtersFromQueryDict(queryDictFromFilters(filters))).toEqual(
      filters,
    );
  });

  it("survives a product type filter round trip", () => {
    const filters = filtersWith({ productType: ["branded"] });

    expect(filtersFromQueryDict(queryDictFromFilters(filters))).toEqual(
      filters,
    );
  });

  it("survives an 'all' product type round trip", () => {
    const filters = filtersWith({ productType: ["all"] });

    expect(filtersFromQueryDict(queryDictFromFilters(filters))).toEqual(
      filters,
    );
  });
});
