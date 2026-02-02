export function setUpBNFTree() {
  // Set up an interactive BNF browser, with BNF objects arranged in a tree.
  //
  // Initially the browser shows a list of BNF chapters, with all other objects hidden.
  // When the user clicks on an object (down to the chemical substance level), its
  // children are shown.  When the user clicks on a chemical substance, a modal is opened
  // that shows the corresponding products and presentations in a table.
  //
  // There is also a search box that lets users search for BNF objects by name or
  // code.

  const tree = document.getElementById("bnf-tree");
  const searchForm = document.getElementById("bnf-search-form");
  const modal = document.getElementById("bnf-table-modal");

  const modalObj = new bootstrap.Modal(modal);
  const modalTitle = modal.querySelector(".modal-title");
  const modalBody = modal.querySelector(".modal-body");

  tree.addEventListener("click", (e) => {
    const li = e.target.closest("li");
    const code = li.dataset.code;
    if (code.length === 9) {
      modalTitle.innerHTML = `<code>${code}</code> ${li.dataset.name}`;
      modalBody.innerHTML = `
            <div class="text-center py-5">
                <div class="spinner-border">
                </div>
            </div>
        `;
      modalObj.show();
      htmx.ajax("GET", `/bnf/${code}/`, {
        target: "#bnf-table-modal .modal-body",
        swap: "innerHTML",
      });
    } else {
      li.toggleAttribute("data-open");
    }
  });

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
