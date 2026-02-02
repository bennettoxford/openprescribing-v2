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
}
