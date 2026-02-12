import { descendants, isAncestor, isChemical } from "@js/bnf-utils.js";
import { describe, expect, it } from "vitest";

describe("isChemical", () => {
  it("returns true for 9-character codes", () => {
    expect(isChemical("010101000")).toBe(true);
  });

  it("returns false for non-9-character codes", () => {
    expect(isChemical("01")).toBe(false);
    expect(isChemical("010101000BBAJA0")).toBe(false);
  });
});

describe("isAncestor", () => {
  it("returns true when code1 is an ancestor of code2", () => {
    expect(isAncestor("01", "010101000")).toBe(true);
  });

  it("returns false when code2 is an ancestor of code1", () => {
    expect(isAncestor("010101000", "01")).toBe(false);
  });

  it("returns false when code1 is code2", () => {
    expect(isAncestor("010101000", "010101000")).toBe(false);
  });

  it("returns false when code1 and code2 are not directly related", () => {
    expect(isAncestor("010101000", "020101000")).toBe(false);
  });
});

describe("descendants", () => {
  it("returns the descendants of given code", () => {
    expect(descendants("01", ["0101", "0102", "0201"])).toEqual([
      "0101",
      "0102",
    ]);
  });

  it("returns doesn't include given code in results", () => {
    expect(descendants("01", ["01", "0101", "0102", "0201"])).toEqual([
      "0101",
      "0102",
    ]);
  });
});
