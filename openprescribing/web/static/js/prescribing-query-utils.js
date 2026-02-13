// This module contains pure functions that have no dependency on the DOM.  They are in
// a separate module because our current JS setup makes it hard to import
// prescribing-query.js into tests.  This is a bit of a smell, and we should aim to
// fold all of these functions back into prescribing-query.js in future.

import { descendants, isAncestor, isChemical } from "./bnf-utils.js";

export function renderSelectedCodes(query, list) {
  // Update the list of codes.

  const terms = queryToSortedTerms(query);

  if (terms.length === 0) {
    list.innerHTML = `<li class="list-group-item text-muted">No presentations selected.</li>`;
  } else {
    list.innerHTML = terms
      .map(
        ({ code, included }) =>
          `<li class="list-group-item"><code>${included ? code : `-${code}`}</code></li>`,
      )
      .join("");
  }
}

export function setInputValue(query, input) {
  // Update the hidden input.

  const terms = queryToSortedTerms(query);

  input.value = terms
    .map(({ code, included }) => (included ? code : `-${code}`))
    .join("\n");
}

export function queryToSortedTerms(query) {
  // Given a query, return an array of terms (objects with properties `code` and
  // `included`), sorted by code.
  const terms = [
    ...query.included.map((code) => ({ code, included: true })),
    ...query.excluded.map((code) => ({ code, included: false })),
  ];
  return terms.sort((a, b) => (a.code > b.code ? 1 : -1));
}

export function textToQuery(text) {
  // Given text from a hidden input, return a query object.
  const included = [];
  const excluded = [];
  const terms = text.split(/\s+/);

  terms.forEach((term) => {
    if (term.startsWith("-")) {
      excluded.push(term.slice(1));
    } else if (term !== "") {
      included.push(term);
    }
  });

  return { included, excluded };
}

export function toggleCode(query, code) {
  // Updates query to include or exclude the given code (or do nothing), depending
  // on whether the code, its ancestors, or its descendants are included.
  //
  // See comment at top of prescribing-query.js for more about inclusions and
  // exclusions.

  if (isDirectlyIncluded(query, code)) {
    // This item is directly included:
    // * Don't include it
    // * Remove descendant exclusions
    removeItem(query.included, code);
    descendants(code, query.excluded).forEach((c) => {
      removeItem(query.excluded, c);
    });
  } else if (isDirectlyExcluded(query, code)) {
    // This item is directly excluded:
    // * Don't exclude it
    removeItem(query.excluded, code);
  } else if (hasDirectlyExcludedAncestor(query, code)) {
    // An ancestor is excluded: do nothing
  } else if (hasDirectlyIncludedDescendant(query, code)) {
    // A descendant is included:
    // * Include this one
    // * Remove descendant inclusions
    query.included.push(code);
    descendants(code, query.included).forEach((c) => {
      removeItem(query.included, c);
    });
  } else if (hasDirectlyIncludedAncestor(query, code)) {
    // An ancestor is included:
    // * Exclude this one
    // * Remove descendant exclusions
    query.excluded.push(code);
    descendants(code, query.excluded).forEach((c) => {
      removeItem(query.excluded, c);
    });
  } else {
    // No ancestors or descendants are included:
    // * Include this one
    query.included.push(code);
  }
}

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

export function hasDirectlyIncludedDescendant(query, code) {
  // Indicates whether any of code's descendants are directly included by query.
  return query.included.some((c) => isAncestor(code, c));
}

export function hasDirectlyExcludedDescendant(query, code) {
  // Indicates whether any of code's descendants are directly excluded by query.
  return query.excluded.some((c) => isAncestor(code, c));
}

export function hasDirectlyIncludedAncestor(query, code) {
  // Indicates whether any of code's ancestors are directly included by query.
  return query.included.some((c) => isAncestor(c, code));
}

export function hasDirectlyExcludedAncestor(query, code) {
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
    (hasDirectlyIncludedDescendant(query, code) ||
      hasDirectlyExcludedDescendant(query, code))
  );
}

function removeItem(array, item) {
  // Removes the first occurrence of the item from the array.
  const ix = array.indexOf(item);
  array.splice(ix, 1);
}
