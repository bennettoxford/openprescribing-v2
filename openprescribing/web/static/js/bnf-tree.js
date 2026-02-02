export function setUpBNFTree(outerModalObj = null, buildingQuery = false) {
  // Set up an interactive BNF browser, with BNF objects arranged in a tree.
  //
  // Initially the browser shows a list of BNF chapters, with all other objects hidden.
  // When the user clicks on an object (down to the chemical substance level), its
  // children are shown.  When the user clicks on a chemical substance, a modal is opened
  // that shows the corresponding products and presentations in a table.
  //
  // There is also a search box that lets users search for BNF objects by name or
  // code.
  //
  // Parameters:
  //  * outerModalObj: if the tree is shown in a modal, this is a reference to the
  //    Bootstrap object for that modal.
  //  * buildingQuery: boolean indicating whether we are using the tree to build a
  //  query.

  const tree = document.getElementById("bnf-tree");
  const searchForm = document.getElementById("bnf-search-form");
  const modal = document.getElementById("bnf-table-modal");

  tree.addEventListener("click", (e) => {
    const li = e.target.closest("li");
    const code = li.dataset.code;

    if (e.shiftKey) {
      if (buildingQuery) {
        handleShiftClick(li);
      }
    } else {
      handleClick(li, code, modal, outerModalObj);
    }
  });

  if (outerModalObj !== null) {
    modal.addEventListener("hidden.bs.modal", () => {
      outerModalObj.show();
    });
  }

  const searchInput = searchForm.querySelector("input");

  searchForm.addEventListener("submit", (e) => {
    e.preventDefault();
    const needle = searchInput.value.trim().toLowerCase();
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
}

function handleClick(li, code, modal, outerModalObj) {
  // For objects down to the subparagaph level, toggle the `open` data attribute.
  // For chemical substances, open the BNF table modal.

  if (code.length < 9) {
    li.toggleAttribute("data-open");
  } else {
    const modalObj = new bootstrap.Modal(modal);
    const modalTitle = modal.querySelector(".modal-title");
    const modalBody = modal.querySelector(".modal-body");
    modalTitle.innerHTML = `<code>${code}</code> ${li.dataset.name}`;
    modalBody.innerHTML = `
            <div class="text-center py-5">
                <div class="spinner-border">
                </div>
            </div>
        `;
    if (outerModalObj !== null) {
      outerModalObj.hide();
    }
    modalObj.show();
    htmx.ajax("GET", `/bnf/${code}/`, {
      target: "#bnf-table-modal .modal-body",
      swap: "innerHTML",
    });
  }
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
