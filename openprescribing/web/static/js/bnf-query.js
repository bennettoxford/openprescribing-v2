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

  setUpBNFTree(modalObj, handleShiftClick);
}

function handleShiftClick(li) {
  // Adds the `included` or `excluded` data attributes to an item in the BNF tree to
  // indicate inclusion or exclusion.  There can be at most one level of exclusion:
  // users cannot include one code, exclude a descendant, and then reinclude a
  // descendant of the excluded code.  This is a significant simplifaction over
  // similar functionality in OpenCodelists.

  if (li.hasAttribute("data-included")) {
    // This item is included:
    // * Don't include it
    // * Remove descendant exclusions
    li.removeAttribute("data-included");
    li.querySelectorAll("li[data-excluded]").forEach((n) => {
      n.removeAttribute("data-excluded");
    });
  } else if (li.hasAttribute("data-excluded")) {
    // This item is excluded:
    // * Don't exclude it
    li.removeAttribute("data-excluded");
  } else if (li.parentElement.closest("li[data-excluded]")) {
    // An ancestor is excluded: do nothing
  } else if (li.querySelector("li[data-included]")) {
    // A descendant is included: do nothing
  } else if (li.parentElement.closest("li[data-included]")) {
    // An ancestor is included:
    // * Exclude this one
    // * Remove descendant exclusions
    li.setAttribute("data-excluded", "");
    li.querySelectorAll("li[data-excluded]").forEach((n) => {
      n.removeAttribute("data-excluded");
    });
  } else {
    // No ancestors are included:
    // * Include this one
    li.setAttribute("data-included", "");
  }
}
