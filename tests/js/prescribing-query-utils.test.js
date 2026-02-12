import {
  hasDirectlyExcludedAncestor,
  hasDirectlyExcludedDescendant,
  hasDirectlyIncludedAncestor,
  hasDirectlyIncludedDescendant,
  isDirectlyExcluded,
  isDirectlyIncluded,
  isExcluded,
  isIncluded,
  isPartiallyIncludedChemical,
} from "@js/prescribing-query-utils.js";
import { describe, expect, it } from "vitest";

const CHAPTER = "01";
const SECTION = "0101";
const CHEMICAL = "010101000";
const PRODUCT = "010101000AA";

describe("isDirectlyIncluded", () => {
  it("returns true when code is directly included", () => {
    const query = { included: [SECTION], excluded: [] };
    expect(isDirectlyIncluded(query, SECTION)).toBe(true);
  });

  it("returns false when code is indirectly included", () => {
    const query = { included: [CHAPTER], excluded: [] };
    expect(isDirectlyIncluded(query, SECTION)).toBe(false);
  });
});

describe("isDirectlyExcluded", () => {
  it("returns true when code is directly excluded", () => {
    const query = { included: [], excluded: [SECTION] };
    expect(isDirectlyExcluded(query, SECTION)).toBe(true);
  });

  it("returns false when code is indirectly excluded", () => {
    const query = { included: [], excluded: [CHAPTER] };
    expect(isDirectlyExcluded(query, SECTION)).toBe(false);
  });
});

describe("isIncluded", () => {
  it("returns true when code is directly included", () => {
    const query = { included: [SECTION], excluded: [] };
    expect(isIncluded(query, SECTION)).toBe(true);
  });

  it("returns true when code is indirectly included", () => {
    const query = { included: [CHAPTER], excluded: [] };
    expect(isIncluded(query, SECTION)).toBe(true);
  });

  it("returns false when code's descendant is included", () => {
    const query = { included: [PRODUCT], excluded: [] };
    expect(isIncluded(query, SECTION)).toBe(false);
  });
});

describe("isExcluded", () => {
  it("returns true when code is directly excluded", () => {
    const query = { included: [], excluded: [SECTION] };
    expect(isExcluded(query, SECTION)).toBe(true);
  });

  it("returns true when code is indirectly excluded", () => {
    const query = { included: [], excluded: [CHAPTER] };
    expect(isExcluded(query, SECTION)).toBe(true);
  });

  it("returns false when code's descendant is excluded", () => {
    const query = { included: [], excluded: [PRODUCT] };
    expect(isExcluded(query, SECTION)).toBe(false);
  });
});

describe("hasDirectlyIncludedDescendant", () => {
  it("returns true when code only has directly included descendants", () => {
    const query = { included: [SECTION], excluded: [] };
    expect(hasDirectlyIncludedDescendant(query, CHAPTER)).toBe(true);
  });

  it("returns true when code has directly included and directly excluded descendants", () => {
    const query = { included: [SECTION], excluded: [CHEMICAL] };
    expect(hasDirectlyIncludedDescendant(query, CHAPTER)).toBe(true);
  });

  it("returns false when code only has directly excluded descendants", () => {
    const query = { included: [], excluded: [SECTION] };
    expect(hasDirectlyIncludedDescendant(query, CHAPTER)).toBe(false);
  });
});

describe("hasDirectlyExcludedDescendant", () => {
  it("returns true when code only has directly excluded descendants", () => {
    const query = { included: [], excluded: [SECTION] };
    expect(hasDirectlyExcludedDescendant(query, CHAPTER)).toBe(true);
  });

  it("returns true when code has directly included and directly excluded descendants", () => {
    const query = { included: [SECTION], excluded: [CHEMICAL] };
    expect(hasDirectlyExcludedDescendant(query, CHAPTER)).toBe(true);
  });

  it("returns false when code only has directly included descendants", () => {
    const query = { included: [SECTION], excluded: [] };
    expect(hasDirectlyExcludedDescendant(query, CHAPTER)).toBe(false);
  });
});

describe("hasDirectlyIncludedAncestor", () => {
  it("returns true when code only has directly included ancestors", () => {
    const query = { included: [CHAPTER], excluded: [] };
    expect(hasDirectlyIncludedAncestor(query, CHEMICAL)).toBe(true);
  });

  it("returns true when code has directly included and directly excluded ancestors", () => {
    const query = { included: [CHAPTER], excluded: [SECTION] };
    expect(hasDirectlyIncludedAncestor(query, CHEMICAL)).toBe(true);
  });

  it("returns false when code only has directly excluded ancestors", () => {
    const query = { included: [], excluded: [CHAPTER] };
    expect(hasDirectlyIncludedAncestor(query, CHEMICAL)).toBe(false);
  });
});

describe("hasDirectlyExcludedAncestor", () => {
  it("returns true when code only has directly excluded ancestors", () => {
    const query = { included: [], excluded: [CHAPTER] };
    expect(hasDirectlyExcludedAncestor(query, CHEMICAL)).toBe(true);
  });

  it("returns true when code has directly included and directly excluded ancestors", () => {
    const query = { included: [CHAPTER], excluded: [SECTION] };
    expect(hasDirectlyExcludedAncestor(query, CHEMICAL)).toBe(true);
  });

  it("returns false when code only has directly included ancestors", () => {
    const query = { included: [CHAPTER], excluded: [] };
    expect(hasDirectlyExcludedAncestor(query, CHEMICAL)).toBe(false);
  });
});

describe("isPartiallyIncludedChemical", () => {
  it("returns false when code is not a chemical", () => {
    const query = { included: [], excluded: [] };
    expect(isPartiallyIncludedChemical(query, SECTION)).toBe(false);
  });

  it("returns true when chemical has directly included descendants", () => {
    const query = { included: [PRODUCT], excluded: [] };
    expect(isPartiallyIncludedChemical(query, CHEMICAL)).toBe(true);
  });

  it("returns true when chemical has directly excluded descendants", () => {
    const query = { included: [], excluded: [PRODUCT] };
    expect(isPartiallyIncludedChemical(query, CHEMICAL)).toBe(true);
  });

  it("returns false when chemical has no included or excluded descendants", () => {
    const query = { included: [SECTION], excluded: [] };
    expect(isPartiallyIncludedChemical(query, CHEMICAL)).toBe(false);
  });
});
