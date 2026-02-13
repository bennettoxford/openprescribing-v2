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
  queryToSortedTerms,
  renderSelectedCodes,
  setInputValue,
  toggleCode,
} from "@js/prescribing-query-utils.js";
import { describe, expect, it } from "vitest";

const CHAPTER = "01";
const SECTION = "0101";
const CHEMICAL = "010101000";
const PRODUCT = "010101000AA";

describe("renderSelectedCodes", () => {
  describe("with empty query", () => {
    it("shows 'No presentations selected.'", () => {
      const query = { included: [], excluded: [] };
      const list = document.createElement("ul");
      renderSelectedCodes(query, list);
      expect(list.querySelectorAll("li").length).toEqual(1);
      expect(list.querySelector("li").innerHTML).toEqual(
        "No presentations selected.",
      );
    });
  });

  describe("with non-empty query", () => {
    it("shows one li per term", () => {
      const query = { included: ["01", "02"], excluded: ["0101", "0102"] };
      const list = document.createElement("ul");
      renderSelectedCodes(query, list);
      expect(list.querySelectorAll("li").length).toEqual(4);
      expect(list.querySelectorAll("li")[0].innerHTML).toEqual(
        "<code>01</code>",
      );
      expect(list.querySelectorAll("li")[1].innerHTML).toEqual(
        "<code>-0101</code>",
      );
      expect(list.querySelectorAll("li")[2].innerHTML).toEqual(
        "<code>-0102</code>",
      );
      expect(list.querySelectorAll("li")[3].innerHTML).toEqual(
        "<code>02</code>",
      );
    });
  });
});

describe("setInputValue", () => {
  it("sets input value", () => {
    const query = { included: ["01", "02"], excluded: ["0101", "0102"] };
    const input = document.createElement("textarea");
    setInputValue(query, input);
    expect(input.value).toEqual("01\n-0101\n-0102\n02");
  });
});

describe("queryToSortedTerms", () => {
  it("returns terms sorted by code", () => {
    const query = { included: ["01", "02"], excluded: ["0101", "0102"] };
    expect(queryToSortedTerms(query)).toEqual([
      { code: "01", included: true },
      { code: "0101", included: false },
      { code: "0102", included: false },
      { code: "02", included: true },
    ]);
  });
});

describe("toggleCode", () => {
  it("toggling unselected code adds it to included", () => {
    const query = { included: [], excluded: [] };
    toggleCode(query, CHAPTER);
    expect(query).toEqual({ included: [CHAPTER], excluded: [] });
  });

  it("toggling included code removes it from included and removes excluded descendants", () => {
    const query = { included: [CHAPTER], excluded: [SECTION] };
    toggleCode(query, CHAPTER);
    expect(query).toEqual({ included: [], excluded: [] });
  });

  it("toggling descendant of included code adds it to excluded", () => {
    const query = { included: [CHAPTER], excluded: [] };
    toggleCode(query, SECTION);
    expect(query).toEqual({ included: [CHAPTER], excluded: [SECTION] });
  });

  it("toggling descendant of excluded code does nothing", () => {
    const query = { included: [CHAPTER], excluded: [SECTION] };
    toggleCode(query, CHEMICAL);
    expect(query).toEqual({ included: [CHAPTER], excluded: [SECTION] });
  });

  it("toggling excluded code removes it from excluded", () => {
    const query = { included: [CHAPTER], excluded: [SECTION] };
    toggleCode(query, SECTION);
    expect(query).toEqual({ included: [CHAPTER], excluded: [] });
  });

  it("toggling ancestor of included code includes it and removes included descendants", () => {
    const query = { included: [SECTION], excluded: [CHEMICAL] };
    toggleCode(query, CHAPTER);
    expect(query).toEqual({ included: [CHAPTER], excluded: [CHEMICAL] });
  });
});

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
