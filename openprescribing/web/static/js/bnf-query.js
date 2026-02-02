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
  const { setState } = setUpBNFTree(modalObj);

  document.querySelectorAll("textarea").forEach((textarea) => {
    textarea.addEventListener("focus", (e) => {
      e.preventDefault();
      state.modal.field = e.target.dataset.field;
      setState(state.query[state.modal.field]);
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
