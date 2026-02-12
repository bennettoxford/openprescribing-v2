import { describe, it, expect } from "vitest";
import { isChemical } from "../../openprescribing/web/static/js/bnf-utils.js";

describe("isChemical", () => {
  it("returns true for 9-character codes", () => {
    expect(isChemical("010101000")).toBe(true);
  });

  it("returns false for non-9-character codes", () => {
    expect(isChemical("01")).toBe(false);
    expect(isChemical("010101000BBAJA0")).toBe(false);
  });
});
