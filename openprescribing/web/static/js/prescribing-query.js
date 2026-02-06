// This module defines the behaviour of a component that can (in a few commits' time) be
// used to pick presentations by BNF code for the numerator and denominator of a
// prescribing query.
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
// The tree modal is opened by clicking on one of the two textarea elements.  (This will
// change!)  The table modal is opened by clicking on a chemical substance in the tree.
// When the table modal opens, the tree modal closes, and when the table modal closes,
// the tree modal is reopened.
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

const textareas = document.querySelectorAll("textarea");
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
tree.setAttribute("data-selectable", "");

textareas.forEach((textarea) => {
  // Populate the state from the textarea.
  state.query[textarea.dataset.field] = textToQuery(textarea.value);

  textarea.addEventListener("focus", (e) => {
    // The user has clicked on the textarea.
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
    if (e.ctrlKey) {
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
      li.setAttribute("data-matches-search", "");
    } else {
      li.removeAttribute("data-matches-search");
    }
  });
});

// These events handle the transition between the two modals.  {

treeModal.addEventListener("show.bs.modal", () => {
  // The tree modal has opened.

  setTreeState();
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
  container.setAttribute("data-selectable", "");

  setTableState(table);

  table.addEventListener("click", (e) => {
    if (e.ctrlKey) {
      const td = e.target.closest("td");
      if (td) {
        handleTableCtrlClick(td);
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

  // Otherwise, we update the corresponding textarea with a text representation of the
  // current query.
  const textarea = document.querySelector(
    `textarea[data-field="${state.field}"]`,
  );
  textarea.value = queryToText(getCurrentQuery());
  state.field = null;
});

// }

function setTreeState() {
  // Set the data attributes required to show the current query in the tree.

  const query = getCurrentQuery();

  tree.querySelectorAll("li").forEach((li) => {
    const code = li.dataset.code;

    // First, remove all data attributes.
    li.removeAttribute("data-open");
    li.removeAttribute("data-matches-search");
    li.removeAttribute("data-partially-included");
    li.removeAttribute("data-included");
    li.removeAttribute("data-excluded");

    // Then set any that are necessary.
    if (descendantIsDirectlyIncluded(query, code)) {
      li.setAttribute("data-open", "");
    }
    if (descendantIsDirectlyExcluded(query, code)) {
      li.setAttribute("data-open", "");
    }

    if (isPartiallyIncludedChemical(query, code)) {
      li.setAttribute("data-partially-included", "");
    } else if (isDirectlyIncluded(query, code)) {
      li.setAttribute("data-included", "");
    } else if (isDirectlyExcluded(query, code)) {
      li.setAttribute("data-excluded", "");
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
    table.setAttribute("data-included", "");
  }

  table.querySelectorAll("tr").forEach((tr) => {
    const code = tr.dataset.code;
    if (isDirectlyIncluded(query, code)) {
      tr.setAttribute("data-included", "");
    } else if (isDirectlyExcluded(query, code)) {
      tr.setAttribute("data-excluded", "");
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
    li.removeAttribute("data-included");
    li.querySelectorAll("li[data-excluded]").forEach((n) => {
      removeItem(query.excluded, n.dataset.code);
      n.removeAttribute("data-excluded");
    });
    // descendant exclusions which are part of the table aren't
    // found by the li selector, so remove them directly
    query.excluded.forEach((n) => {
      if (isAncestor(code, n)) {
        removeItem(query.excluded, n);
      }
    });
    li.removeAttribute("data-partially-included");
    li.querySelectorAll("li[data-partially-included]").forEach((n) => {
      n.removeAttribute("data-partially-included");
    });
  } else if (isDirectlyExcluded(query, code)) {
    // This item is directly excluded:
    // * Don't exclude it
    removeItem(query.excluded, code);
    li.removeAttribute("data-excluded");
  } else if (ancestorIsDirectlyExcluded(query, code)) {
    // An ancestor is excluded: do nothing
  } else if (descendantIsDirectlyIncluded(query, code)) {
    // A descendant is included:
    // * Include this one
    // * Remove descendant inclusions
    query.included.push(code);
    li.setAttribute("data-included", "");
    li.querySelectorAll("li[data-included]").forEach((n) => {
      removeItem(query.included, n.dataset.code);
      n.removeAttribute("data-included");
    });
  } else if (ancestorIsDirectlyIncluded(query, code)) {
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
    // No ancestors or descendants are included:
    // * Include this one
    query.included.push(code);
    li.setAttribute("data-included", "");
  }
}

function handleTableCtrlClick(td) {
  // Respond to user clicking a table cell while holding control.

  const tr = td.closest("tr");
  const code = tr.dataset.code;
  const query = getCurrentQuery();

  if (isDirectlyIncluded(query, code)) {
    // This item is directly included:
    // * Don't include it
    removeItem(query.included, code);
    tr.removeAttribute("data-included");
  } else if (isDirectlyExcluded(query, code)) {
    // This item is directly excluded:
    // * Don't exclude it
    removeItem(query.excluded, code);
    tr.removeAttribute("data-excluded");
  } else if (isIncluded(query, state.chemicalCode)) {
    // An ancestor is included:
    // * Exclude this one
    query.excluded.push(code);
    tr.setAttribute("data-excluded", "");
  } else {
    // No ancestors or descendants are included:
    // * Include this one
    query.included.push(code);
    tr.setAttribute("data-included", "");
  }
}

function textToQuery(text) {
  // Given text from a textarea, return a query object.
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

function queryToText(query) {
  // Given a query, return a newline-separated string for the corresponding
  // textarea.  The terms in the query are sorted by code.
  const terms = [
    ...query.included.map((code) => ({ code, included: true })),
    ...query.excluded.map((code) => ({ code, included: false })),
  ];
  const sortedTerms = terms.sort((a, b) => a.code > b.code);
  return sortedTerms
    .map(({ code, included }) => (included ? code : `-${code}`))
    .join("\n");
}

function isChemical(code) {
  // Indicate whether code is for a chemical substance.
  return code.length === 9;
}

function isAncestor(code1, code2) {
  // Indicates whether code1 is an ancestor of code2.
  return code2.startsWith(code1) && code1 !== code2;
}

function isDirectlyIncluded(query, code) {
  // Indicates whether code is directly included by query.
  return query.included.includes(code);
}

function isDirectlyExcluded(query, code) {
  // Indicates whether code is directly excluded by query.
  return query.excluded.includes(code);
}

function isIncluded(query, code) {
  // Indicates whether code is directly or indirectly included by query.
  return query.included.some((c) => code.startsWith(c));
}

function isExcluded(query, code) {
  // Indicates whether code is directly or indirectly excluded by query.
  return query.excluded.some((c) => code.startsWith(c));
}

function descendantIsDirectlyIncluded(query, code) {
  // Indicates whether any of code's descendants are directly included by query.
  return query.included.some((c) => isAncestor(code, c));
}

function descendantIsDirectlyExcluded(query, code) {
  // Indicates whether any of code's descendants are directly excluded by query.
  return query.excluded.some((c) => isAncestor(code, c));
}

function ancestorIsDirectlyIncluded(query, code) {
  // Indicates whether any of code's ancestors are directly included by query.
  return query.included.some((c) => isAncestor(c, code));
}

function ancestorIsDirectlyExcluded(query, code) {
  // Indicates whether any of code's ancestors are directly excluded by query.
  return query.excluded.some((c) => isAncestor(c, code));
}

function isPartiallyIncludedChemical(query, code) {
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

function removeItem(array, item) {
  // Removes the first occurrence of the item from the array.
  const ix = array.indexOf(item);
  array.splice(ix, 1);
}
