import {
  getEmptyFilters,
  getFilterControlKey,
} from "@js/build-analysis/filters.js";
import { queryMedications, STATUS } from "@js/build-analysis/query.js";
import { describe, expect, it } from "vitest";

// A small world of three VMPs, each with one AMP child, spanning two VTMs, three
// ingredients, BNF chapters 04-06, and three form/routes.
//
// VMP3 shares VTM 10 with VMP1 but sits in chapter 05, so it can match one baseline
// filter without matching another. Its AMP child (AMP3) sits in chapter 06 -- a
// different chapter from its parent -- so a chapter 06 filter drops VMP3 while keeping
// AMP3 (the excluded-parent-VMP case).  See #410 for more context.
const VMP1 = {
  id: 1,
  name: "VMP1",
  is_amp: false,
  vmp_id: 1,
  vtm_id: 10,
  bnf_code: "0401000A0AAAAAA",
  form_routes: ["tablet.oral"],
  ingredient_ids: [100],
};
const AMP1 = {
  id: 2,
  name: "AMP1",
  is_amp: true,
  vmp_id: 1,
  vtm_id: 10,
  bnf_code: "0401000A0AAAAAA",
  form_routes: ["tablet.oral"],
  ingredient_ids: [100],
};
const VMP2 = {
  id: 3,
  name: "VMP2",
  is_amp: false,
  vmp_id: 3,
  vtm_id: 20,
  bnf_code: "0501000B0AAAAAA",
  form_routes: ["capsule.oral"],
  ingredient_ids: [200],
};
const AMP2 = {
  id: 4,
  name: "AMP2",
  is_amp: true,
  vmp_id: 3,
  vtm_id: 20,
  bnf_code: "0501000B0AAAAAA",
  form_routes: ["capsule.oral"],
  ingredient_ids: [200],
};
const VMP3 = {
  id: 5,
  name: "VMP3",
  is_amp: false,
  vmp_id: 5,
  vtm_id: 10,
  bnf_code: "0502000C0AAAAAA",
  form_routes: ["solution.oral"],
  ingredient_ids: [300],
};
const AMP3 = {
  id: 6,
  name: "AMP3",
  is_amp: true,
  vmp_id: 5,
  vtm_id: 10,
  bnf_code: "0601000D0AAAAAA",  // note a different BNF code to VMP3
  form_routes: ["solution.oral"],
  ingredient_ids: [300],
};

const METADATA = makeMetadata([VMP1, AMP1, VMP2, AMP2, VMP3, AMP3]);

describe("queryMedications", () => {
  it("drops medications outside a single baseline inclusion filter", () => {
    const result = queryMedications(
      METADATA,
      makeFilters({ [include("bnfCodePrefix")]: ["04"] }),
    );
    expectMedications(result, [
      [VMP1, STATUS.INCLUDED],
      [AMP1, STATUS.INCLUDED],
    ]);
    expect(result.includedCount).toBe(2);
    expect(result.includedVmpCount).toBe(1);
    expect(result.includedAmpCount).toBe(1);
  });

  it("ORs the values within a single filter control", () => {
    const result = queryMedications(
      METADATA,
      makeFilters({ [include("bnfCodePrefix")]: ["0401", "0501"] }),
    );
    expectMedications(result, [
      [VMP1, STATUS.INCLUDED],
      [AMP1, STATUS.INCLUDED],
      [VMP2, STATUS.INCLUDED],
      [AMP2, STATUS.INCLUDED],
    ]);
    expect(result.includedCount).toBe(4);
    expect(result.includedVmpCount).toBe(2);
    expect(result.includedAmpCount).toBe(2);
  });

  it("ANDs the values between filter controls", () => {
    const result = queryMedications(
      METADATA,
      makeFilters({ [include("vtmId")]: [10], [include("bnfCodePrefix")]: ["04"] }),
    );
    expectMedications(result, [
      [VMP1, STATUS.INCLUDED],
      [AMP1, STATUS.INCLUDED],
      [VMP3, STATUS.NOT_INCLUDED],
      [AMP3, STATUS.NOT_INCLUDED],
    ]);
    expect(result.includedCount).toBe(2);
    expect(result.includedVmpCount).toBe(1);
    expect(result.includedAmpCount).toBe(1);
  });

  it("marks medications matching an exclusion filter as excluded and omits them from the count", () => {
    const result = queryMedications(
      METADATA,
      makeFilters({
        [include("bnfCodePrefix")]: ["05"],
        [exclude("formRouteId")]: ["capsule.oral"],
      }),
    );
    expectMedications(result, [
      [VMP2, STATUS.EXCLUDED],
      [AMP2, STATUS.EXCLUDED],
      [VMP3, STATUS.INCLUDED],
    ]);
    expect(result.includedCount).toBe(1);
    expect(result.includedVmpCount).toBe(1);
    expect(result.includedAmpCount).toBe(0);
  });

  it("prefers excluded over not-included when both apply", () => {
    const result = queryMedications(
      METADATA,
      makeFilters({
        [include("vtmId")]: [10],
        [include("ingredientId")]: [100],
        [exclude("formRouteId")]: ["solution.oral"],
      }),
    );

    expectMedications(result, [
      [VMP1, STATUS.INCLUDED],
      [AMP1, STATUS.INCLUDED],
      [VMP3, STATUS.EXCLUDED],
      [AMP3, STATUS.EXCLUDED],
    ]);
    expect(result.includedCount).toBe(2);
    expect(result.includedVmpCount).toBe(1);
    expect(result.includedAmpCount).toBe(1);
  });
});

describe("queryMedications with excluded parent VMPs", () => {
  // These exercise VMP3, whose AMP child sits in a different BNF chapter, so a chapter
  // 06 filter drops VMP3 itself while keeping AMP3.

  it("retains a parent VMP excluded by a baseline filter when one of its AMPs matches", () => {
    const result = queryMedications(
      METADATA,
      makeFilters({ [include("bnfCodePrefix")]: ["06"] }),
    );
    expectMedications(result, [
      [VMP3, STATUS.VMP_NOT_INCLUDED_BUT_CHILD_AMP_IS],
      [AMP3, STATUS.INCLUDED],
    ]);
    expect(result.includedCount).toBe(1);
    expect(result.includedVmpCount).toBe(0);
    expect(result.includedAmpCount).toBe(1);
  });

  it("retains a parent VMP when it matches a non-baseline filter", () => {
    const result = queryMedications(
      METADATA,
      makeFilters({
        [include("bnfCodePrefix")]: ["06"],
        [include("formRouteId")]: ["solution.oral"],
      }),
    );
    expectMedications(result, [
      [VMP3, STATUS.VMP_NOT_INCLUDED_BUT_CHILD_AMP_IS],
      [AMP3, STATUS.INCLUDED],
    ]);
    expect(result.includedVmpCount).toBe(0);
  });
});

function makeMetadata(medications) {
  // Build the subset of the metadata object that queryMedications relies on.
  return {
    medications,
    medicationById: new Map(
      medications.map((medication) => [medication.id, medication]),
    ),
  };
}

function makeFilters(overrides) {
  return { ...getEmptyFilters(), ...overrides };
}

function include(key) {
  return getFilterControlKey({ key }, false);
}
function exclude(key) {
  return getFilterControlKey({ key }, true);
}

function expectMedications(result, expectedStatuses) {
  // Assert exactly which medications are in the results, and the status of each.
  const actualStatusById = new Map(
    result.medications.map((medication) => [medication.id, medication.status]),
  );
  const expectedStatusById = new Map(
    expectedStatuses.map(([medication, status]) => [medication.id, status]),
  );

  expect(actualStatusById).toEqual(expectedStatusById);
  expect(result.medications).toHaveLength(expectedStatuses.length);
}
