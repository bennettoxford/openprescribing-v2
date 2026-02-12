// This module defines the behaviour of a component that can be used to pick
// presentations by BNF code for the numerator and denominator of a prescribing query.
//
// Note that a similar component is defined in bnf-tree.js, which uses the same HTML.
// However, the two components are sufficiently different in behaviour that it does not
// make sense to combine implementations.  When making changes here, consider also
// making changes there.
//
// The component has two modals:
//
// * The tree modal: this shows the BNF hierarchy in an expandable/collapsable tree,
//   down to the chemical substance level.
// * The table modal: this shows the products and presentations that belong to a single
//   chemical substance.
//
// The tree modal is opened by clicking on one of the two buttons.  The table modal is
// opened by clicking on a chemical substance in the tree.  When the table modal opens,
// the tree modal closes, and when the table modal closes, the tree modal is reopened.
//
// In the tree modal, users can choose to include a BNF code in a query by clicking
// while the control key is held down.  This will include the BNF code and all its
// descendants.  By ctrl-clicking on a descendant of an included code, that descendant
// and all its descendants are excluded from the query.
//
// Unlike in OpenCodelists, there can be at most one level exclusion: users cannot
// include one code, exclude a descendant, and then reinclude a descendant of the
// excluded code.  This is not required by any of OpenPresecribing's existing measures,
// and significantly simplifies the implementation relative to OpenCodelists.

import { descendants, isChemical } from "./bnf-utils.js";
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
} from "./prescribing-query-utils.js";

const state = {
  query: {
    // Records which codes have been included/excluded for the numerator and denominator
    // respectively.
    ntr: { included: [], excluded: [] },
    dtr: { included: [], excluded: [] },
  },
  // Indicates which field the tree modal is open for ("ntr" or "dtr"), or null if no
  // modal is open.
  field: null,
  // Records the code of the chemical substance that is currently being shown in the
  // table modal.  If it is not null, we infer that the table modal is open.
  chemicalCode: null,
};

function getCurrentQuery() {
  return state.query[state.field];
}

// The various elements that we'll be interacting with.  {

const selectorButtons = document.querySelectorAll("[data-bnf-selector]");
const codeInputs = document.querySelectorAll("[data-bnf-codes-input]");
const treeModal = document.getElementById("bnf-tree-modal");
const treeModalObj = new bootstrap.Modal(treeModal);
const tree = document.getElementById("bnf-tree");
const searchForm = document.getElementById("bnf-search-form");
const tableModal = document.getElementById("bnf-table-modal");
const tableModalObj = new bootstrap.Modal(tableModal);
const tableModalTitle = tableModal.querySelector(".modal-title");
const tableModalBody = tableModal.querySelector(".modal-body");

// }

// Activate the CSS selectors that indicate whether a node is included or not.
setBoolAttr(tree, "selectable", true);

codeInputs.forEach((input) => {
  // Populate the state from the hidden input.
  state.query[input.dataset.field] = textToQuery(input.value);
  // Update the list of selected codes.
  renderSelectedCodes(input.dataset.field);
});

selectorButtons.forEach((button) => {
  button.addEventListener("click", (e) => {
    // The user has clicked on the button.
    e.preventDefault();
    state.field = e.target.dataset.field;
    const title = `Select codes for ${state.field === "ntr" ? "numerator" : "denominator"}`;
    treeModal.querySelector(".modal-title").innerHTML = title;
    treeModalObj.show();
  });
});

tree.addEventListener("click", (e) => {
  // The user has clicked on the tree.

  const li = e.target.closest("li");
  if (li) {
    if (e.ctrlKey || e.metaKey) {
      handleTreeCtrlClick(li);
    } else {
      handleTreeClick(li);
    }
  }
});

searchForm.addEventListener("submit", (e) => {
  // The user has submitted the search form.

  e.preventDefault();
  const needle = searchForm.querySelector("input").value.trim().toLowerCase();
  tree.querySelectorAll("li").forEach((li) => {
    if (
      li.dataset.code.toLowerCase() === needle ||
      li.dataset.name.toLowerCase().includes(needle)
    ) {
      setBoolAttr(li, "matches-search", true);
    } else {
      setBoolAttr(li, "matches-search", false);
    }
  });
});

// These events handle the transition between the two modals.  {

treeModal.addEventListener("show.bs.modal", () => {
  // The tree modal has opened.

  setTreeState(true);
});

tableModalBody.addEventListener("htmx:afterSwap", () => {
  // The table modal has opened and the modals' contents have been swapped in by HTMX.

  const query = getCurrentQuery();

  if (isExcluded(query, state.chemicalCode)) {
    // We don't want allow inclusions of descendants of excluded codes.
    return;
  }

  const container = document.getElementById("bnf-table");
  const table = container.querySelector("table");

  // Activate the CSS selectors that indicate whether a row is included or not.
  setBoolAttr(container, "selectable", true);

  setTableState(table);

  table.addEventListener("click", (e) => {
    if (e.ctrlKey || e.metaKey) {
      const td = e.target.closest("td");
      if (td) {
        handleTableCtrlClick(table, td);
      }
    }
  });
});

tableModal.addEventListener("hidden.bs.modal", () => {
  // The table modal has closed.

  state.chemicalCode = null;
  treeModalObj.show();
});

treeModal.addEventListener("hidden.bs.modal", () => {
  // The tree modal has closed.

  if (state.chemicalCode) {
    // The table modal has been opened, so there is nothing to do.
    return;
  }

  // Otherwise, we update the corresponding list and hidden input with a text
  // representation of the current query.
  renderSelectedCodes(state.field);
  state.field = null;
});

// }

function setTreeState(newlyOpened) {
  // Set the data attributes required to show the current query in the tree.

  const query = getCurrentQuery();

  tree.querySelectorAll("li").forEach((li) => {
    const code = li.dataset.code;

    // First, remove all data attributes.
    if (newlyOpened) {
      setBoolAttr(li, "open", false);
      setBoolAttr(li, "matches-search", false);
    }
    setBoolAttr(li, "partially-included", false);
    setBoolAttr(li, "included", false);
    setBoolAttr(li, "excluded", false);

    // Then set any that are necessary.
    if (hasDirectlyIncludedDescendant(query, code)) {
      setBoolAttr(li, "open", true);
    }
    if (hasDirectlyExcludedDescendant(query, code)) {
      setBoolAttr(li, "open", true);
    }

    if (isPartiallyIncludedChemical(query, code)) {
      setBoolAttr(li, "partially-included", true);
    } else if (isDirectlyIncluded(query, code)) {
      setBoolAttr(li, "included", true);
    } else if (isDirectlyExcluded(query, code)) {
      setBoolAttr(li, "excluded", true);
    }
  });

  searchForm.querySelector("input").value = "";
}

function setTableState(table) {
  // Set the data attributes required to show the current query in the table.
  //
  // Note that unlike setTreeState, we don't have to clear any existing data
  // attributes because the table has been loaded from the server and so the HTML
  // is fresh.

  const query = getCurrentQuery();

  if (isIncluded(query, state.chemicalCode)) {
    setBoolAttr(table, "included", true);
  }

  table.querySelectorAll("tr").forEach((tr) => {
    const code = tr.dataset.code;

    // First, remove all data attributes.
    setBoolAttr(tr, "included", false);
    setBoolAttr(tr, "excluded", false);

    // Then set any that are necessary.
    if (isDirectlyIncluded(query, code)) {
      setBoolAttr(tr, "included", true);
    } else if (isDirectlyExcluded(query, code)) {
      setBoolAttr(tr, "excluded", true);
    }
  });
}

function handleTreeClick(li) {
  // Respond to user clicking a tree node.

  const code = li.dataset.code;
  if (isChemical(code)) {
    // Open the table modal, show a spinner, and send the request for its contents
    // to the backend.
    state.chemicalCode = code;
    tableModalTitle.innerHTML = `<code>${code}</code> ${li.dataset.name}`;
    tableModalBody.innerHTML = `
    <div class="text-center py-5">
      <div class="spinner-border">
      </div>
    </div>
    `;
    treeModalObj.hide();
    tableModalObj.show();
    htmx.ajax("GET", `/bnf/${code}/`, {
      target: "#bnf-table-modal .modal-body",
      swap: "innerHTML",
    });
  } else {
    // Toggle whether the node is visible.
    li.toggleAttribute("data-open");
  }
}

function handleTreeCtrlClick(li) {
  // Respond to user clicking a tree node while holding control.

  const code = li.dataset.code;
  const query = getCurrentQuery();

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

  setTreeState(false);
}

function handleTableCtrlClick(table, td) {
  // Respond to user clicking a table cell while holding control.

  const tr = td.closest("tr");
  const code = tr.dataset.code;
  const query = getCurrentQuery();

  if (isDirectlyIncluded(query, code)) {
    // This item is directly included:
    // * Don't include it
    removeItem(query.included, code);
  } else if (isDirectlyExcluded(query, code)) {
    // This item is directly excluded:
    // * Don't exclude it
    removeItem(query.excluded, code);
  } else if (hasDirectlyIncludedAncestor(query, code)) {
    // An ancestor is included:
    // * Exclude this one
    query.excluded.push(code);
  } else {
    // No ancestors or descendants are included:
    // * Include this one
    query.included.push(code);
  }

  setTableState(table);
}

function textToQuery(text) {
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

function renderSelectedCodes(field) {
  // Update the list of codes and the hidden input.
  const query = state.query[field];
  const terms = queryToSortedTerms(query);

  const input = document.querySelector(
    `[data-bnf-codes-input][data-field="${field}"]`,
  );
  input.value = terms
    .map(({ code, included }) => (included ? code : `-${code}`))
    .join("\n");

  const list = document.querySelector(
    `[data-bnf-codes-list][data-field="${field}"]`,
  );

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

function queryToSortedTerms(query) {
  // Given a query, return an array of terms (objects with properties `code` and
  // `included`), sorted by code.
  const terms = [
    ...query.included.map((code) => ({ code, included: true })),
    ...query.excluded.map((code) => ({ code, included: false })),
  ];
  return terms.sort((a, b) => (a.code > b.code ? 1 : -1));
}

function removeItem(array, item) {
  // Removes the first occurrence of the item from the array.
  const ix = array.indexOf(item);
  array.splice(ix, 1);
}

function setBoolAttr(el, attrName, val) {
  if (val) {
    el.setAttribute(`data-${attrName}`, "");
  } else {
    el.removeAttribute(`data-${attrName}`);
  }
}
