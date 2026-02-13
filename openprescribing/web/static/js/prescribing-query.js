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

import { isChemical } from "./bnf-utils.js";
import {
  hasDirectlyExcludedDescendant,
  hasDirectlyIncludedDescendant,
  isDirectlyExcluded,
  isDirectlyIncluded,
  isExcluded,
  isIncluded,
  isPartiallyIncludedChemical,
  queryToSortedTerms,
  toggleCode,
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

const formControls = {
  ntr: document.querySelector('[data-controls="ntr"]'),
  dtr: document.querySelector('[data-controls="dtr"]'),
};
const treeModal = document.getElementById("bnf-tree-modal");
const treeModalObj = new bootstrap.Modal(treeModal);
const tree = document.getElementById("bnf-tree");
const searchForm = document.getElementById("bnf-search-form");
const tableModal = document.getElementById("bnf-table-modal");
const tableModalObj = new bootstrap.Modal(tableModal);
const tableModalTitle = tableModal.querySelector(".modal-title");
const tableModalBody = tableModal.querySelector(".modal-body");

function getCodeInput(field) {
  return formControls[field].querySelector("[data-bnf-codes-input]");
}

function getCodesList(field) {
  return formControls[field].querySelector("[data-bnf-codes-list]");
}

function getSelectorButton(field) {
  return formControls[field].querySelector("[data-bnf-selector]");
}

// }

// Activate the CSS selectors that indicate whether a node is included or not.
setBoolAttr(tree, "selectable", true);

["ntr", "dtr"].forEach((field) => {
  // Set up buttons.
  const button = getSelectorButton(field);
  button.addEventListener("click", (e) => {
    // The user has clicked on the button.
    e.preventDefault();
    state.field = field;
    const title = `Select codes for ${field === "ntr" ? "numerator" : "denominator"}`;
    treeModal.querySelector(".modal-title").innerHTML = title;
    treeModalObj.show();
  });

  // Populate the state from the hidden input.
  const input = getCodeInput(field);
  state.query[field] = textToQuery(input.value);

  // Update the list of selected codes.
  renderSelectedCodes(state.query[field], getCodesList(field));
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

  // Otherwise, we update the corresponding list of codes and hidden input with a text
  // representation of the current query.
  renderSelectedCodes(getCurrentQuery(), getCodesList(state.field));
  setInputValue(getCurrentQuery(), getCodeInput(state.field));
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

  toggleCode(getCurrentQuery(), li.dataset.code);
  setTreeState(false);
}

function handleTableCtrlClick(table, td) {
  // Respond to user clicking a table cell while holding control.

  const tr = td.closest("tr");
  toggleCode(getCurrentQuery(), tr.dataset.code);
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

function renderSelectedCodes(query, list) {
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

function setInputValue(query, input) {
  // Update the hidden input.

  const terms = queryToSortedTerms(query);

  input.value = terms
    .map(({ code, included }) => (included ? code : `-${code}`))
    .join("\n");
}

function setBoolAttr(el, attrName, val) {
  if (val) {
    el.setAttribute(`data-${attrName}`, "");
  } else {
    el.removeAttribute(`data-${attrName}`);
  }
}
