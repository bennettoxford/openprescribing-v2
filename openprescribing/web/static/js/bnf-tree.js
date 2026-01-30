export function setUpBNFTree(outerModalObj = null, handleShiftClick = null) {
  const tree = document.getElementById("bnf-tree");
  const searchForm = document.getElementById("bnf-search-form");
  const modal = document.getElementById("bnf-table-modal");

  tree.addEventListener("click", (e) => {
    const li = e.target.closest("li");
    const code = li.dataset.code;

    if (e.shiftKey) {
      if (handleShiftClick !== null) {
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

  if (code.length === 9) {
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
  } else {
    li.toggleAttribute("data-open");
  }
}
