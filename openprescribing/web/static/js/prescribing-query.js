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

const state = {
  // Records the code of the chemical substance that is currently being shown in the
  // table modal.  If it is not null, we infer that the table modal is open.
  chemicalCode: null,
};

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

textareas.forEach((textarea) => {
  textarea.addEventListener("focus", (e) => {
    // The user has clicked on the textarea.
    e.preventDefault();
    const field = e.target.dataset.field;
    const title = `Select codes for ${field === "ntr" ? "numerator" : "denominator"}`;
    treeModal.querySelector(".modal-title").innerHTML = title;
    treeModalObj.show();
  });
});

tree.addEventListener("click", (e) => {
  // The user has clicked on the tree.

  const li = e.target.closest("li");
  if (li) {
    handleTreeClick(li);
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
  // We'll add code here soon.
});

tableModalBody.addEventListener("htmx:afterSwap", () => {
  // The table modal has opened and the modals' contents have been swapped in by HTMX.
  // We'll add code here soon.
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

  // We'll add code here soon.
});

// }

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

function isChemical(code) {
  // Indicate whether code is for a chemical substance.
  return code.length === 9;
}
