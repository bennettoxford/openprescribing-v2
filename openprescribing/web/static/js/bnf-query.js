import { setUpBNFTree } from "./bnf-tree.js";

const state = {
  query: {
    // Records which codes have been included/excluded for the numerator and denominator
    // respectively.
    ntr: { included: [], excluded: [] },
    dtr: { included: [], excluded: [] },
  },
  modal: {
    // Indicates which field the tree modal is open for ("ntr" or "dtr"), or null if no
    // modal is open.
    field: null,
  },
};

export function setUpBNFQuery() {
  const modal = document.getElementById("bnf-tree-modal");
  const modalObj = new bootstrap.Modal(modal);

  document.querySelectorAll("textarea").forEach((textarea) => {
    textarea.addEventListener("focus", (e) => {
      e.preventDefault();
      state.modal.field = e.target.dataset.field;
      const title = `Select codes for ${state.modal.field === "ntr" ? "numerator" : "denominator"}`;
      modal.querySelector(".modal-title").innerHTML = title;
      modalObj.show();
    });
  });

  modal.addEventListener("hidden.bs.modal", () => {
    // When the modal is closed, update the contents of the corresponding textarea.
    document.querySelector(
      `textarea[data-field="${state.modal.field}"]`,
    ).value = queryToText(state.query[state.modal.field]);
    state.modal.field = null;
  });

  setUpBNFTree(modalObj, handleShiftClick);
}

function handleShiftClick(li) {
  // Adds the `included` or `excluded` data attributes to an item in the BNF tree to
  // indicate inclusion or exclusion.  There can be at most one level of exclusion:
  // users cannot include one code, exclude a descendant, and then reinclude a
  // descendant of the excluded code.  This is a significant simplifaction over
  // similar functionality in OpenCodelists.

  const query = state.query[state.modal.field];
  const code = li.dataset.code;

  if (li.hasAttribute("data-included")) {
    // This item is included:
    // * Don't include it
    // * Remove descendant exclusions
    removeItem(query.included, code);
    li.removeAttribute("data-included");
    li.querySelectorAll("li[data-excluded]").forEach((n) => {
      removeItem(query.excluded, n.dataset.code);
      n.removeAttribute("data-excluded");
    });
  } else if (li.hasAttribute("data-excluded")) {
    // This item is excluded:
    // * Don't exclude it
    removeItem(query.excluded, code);
    li.removeAttribute("data-excluded");
  } else if (li.parentElement.closest("li[data-excluded]")) {
    // An ancestor is excluded: do nothing
  } else if (li.querySelector("li[data-included]")) {
    // A descendant is included: do nothing
  } else if (li.parentElement.closest("li[data-included]")) {
    // An ancestor is included:
    // * Exclude this one
    // * Remove descendant exclusions
    query.excluded.push(code);
    li.setAttribute("data-excluded", "");
    li.querySelectorAll("li[data-excluded]").forEach((n) => {
      removeItem(query.excluded, n.dataset.code);
      n.removeAttribute("data-excluded");
    });
  } else {
    // No ancestors are included:
    // * Include this one
    query.included.push(code);
    li.setAttribute("data-included", "");
  }
}

function removeItem(array, item) {
  const ix = array.indexOf(item);
  array.splice(ix, 1);
}

function queryToText(query) {
  // Given a query, return a newline-separated string for the corresponding
  // textarea.  The terms in the query are sorted by code.
  //
  // This is expected to be temporary: we'll want to plumb the query directly into
  // the URL in future.
  const terms = [
    ...query.included.map((code) => ({ code, included: true })),
    ...query.excluded.map((code) => ({ code, included: false })),
  ];
  const sortedTerms = terms.sort((a, b) => a.code > b.code);
  return sortedTerms
    .map(({ code, included }) => (included ? code : `-${code}`))
    .join("\n");
}
