import { setUpBNFTree } from "./bnf-tree.js";

export function setUpBNFQuery() {
  const modal = document.getElementById("bnf-tree-modal");
  const modalObj = new bootstrap.Modal(modal);

  document.querySelectorAll("textarea").forEach((textarea) => {
    textarea.addEventListener("focus", (e) => {
      e.preventDefault();
      const field = e.target.dataset.field;
      const title = `Select codes for ${field === "ntr" ? "numerator" : "denominator"}`;
      modal.querySelector(".modal-title").innerHTML = title;
      modalObj.show();
    });
  });

  setUpBNFTree(modalObj);
}
