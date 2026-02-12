import { isAncestor, isChemical } from "./bnf-utils.js";

export function isDirectlyIncluded(query, code) {
  // Indicates whether code is directly included by query.
  return query.included.includes(code);
}

export function isDirectlyExcluded(query, code) {
  // Indicates whether code is directly excluded by query.
  return query.excluded.includes(code);
}

export function isIncluded(query, code) {
  // Indicates whether code is directly or indirectly included by query.
  return query.included.some((c) => code.startsWith(c));
}

export function isExcluded(query, code) {
  // Indicates whether code is directly or indirectly excluded by query.
  return query.excluded.some((c) => code.startsWith(c));
}

export function descendantIsDirectlyIncluded(query, code) {
  // Indicates whether any of code's descendants are directly included by query.
  return query.included.some((c) => isAncestor(code, c));
}

export function descendantIsDirectlyExcluded(query, code) {
  // Indicates whether any of code's descendants are directly excluded by query.
  return query.excluded.some((c) => isAncestor(code, c));
}

export function ancestorIsDirectlyIncluded(query, code) {
  // Indicates whether any of code's ancestors are directly included by query.
  return query.included.some((c) => isAncestor(c, code));
}

export function ancestorIsDirectlyExcluded(query, code) {
  // Indicates whether any of code's ancestors are directly excluded by query.
  return query.excluded.some((c) => isAncestor(c, code));
}

export function isPartiallyIncludedChemical(query, code) {
  // Indicates whether code is for a chemical substance, and if so, whether it is
  // partially included.  That is, whether either:
  //   * the chemical substance is directly or indirectly included but one of its
  //     descendants is excluded, or
  //   * the chemical substance is not included but one of its descendants is.
  //
  // We only need to check whether any descendants are directly included or excluded:
  //   * if a descendant is directly excluded, then it implies the chemical substance is
  //     included;
  //   * if a descendant is directly included, then it implies the chemical substance is
  //     not included.
  return (
    isChemical(code) &&
    (descendantIsDirectlyIncluded(query, code) ||
      descendantIsDirectlyExcluded(query, code))
  );
}
