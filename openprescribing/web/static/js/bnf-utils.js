export function isChemical(code) {
  // Indicate whether code is for a chemical substance.
  return code.length === 9;
}

export function isAncestor(code1, code2) {
  // Indicates whether code1 is an ancestor of code2.
  return code2.startsWith(code1) && code1 !== code2;
}

export function descendants(code, codes) {
  return codes.filter((c) => isAncestor(code, c));
}
