const state = {
  query: {
    ntr: { included: [], excluded: [] },
    dtr: { included: [], excluded: [] },
  },
  modal: {
    field: null, // one of "ntr", "dtr", or null
  },
};

const treeModalElement = document.getElementById("bnf-tree-modal");
const treeModalTitle = document.getElementById("bnf-tree-modal-title");
const treeModalBody = document.getElementById("bnf-tree-modal-body");
const treeModal = new bootstrap.Modal(treeModalElement);

const tableModalElement = document.getElementById("bnf-table-modal");
const tableModalTitle = document.getElementById("bnf-table-modal-title");
const tableModalBody = document.getElementById("bnf-table-modal-body");
const tableModal = new bootstrap.Modal(tableModalElement);

document.querySelectorAll("textarea").forEach((textarea) => {
  textarea.addEventListener("focus", (e) => {
    e.preventDefault();
    field = e.target.dataset["field"];
    state.modal.field = field;
    treeModalTitle.innerHTML = `Select codes for ${field === "ntr" ? "numerator" : "denominator"}`;
    treeModalBody.innerHTML = `
      <div class="text-center py-5">
        <div class="spinner-border">
        </div>
      </div>
    `;
    treeModal.show();
    htmx.ajax("GET", "/bnf/", {
      target: "#bnf-tree-modal-body",
      swap: "innerHTML",
    });
  });
});

treeModalElement.addEventListener("hidden.bs.modal", (e) => {
  const query = state.query[state.modal.field];
  const sortedTerms = [
    ...query.included.map((code) => ({ code, included: true })),
    ...query.excluded.map((code) => ({ code, included: false })),
  ].sort((a, b) => a.code.localeCompare(b.code));
  const output = sortedTerms
    .map(({ code, included }) => (included ? code : `-${code}`))
    .join("\n");
  document.getElementById("ntr_codes").value = output;
  document.querySelector(`textarea[data-field="${state.modal.field}"]`).value =
    output;
  state.modal.field = null;
});

tableModalElement.addEventListener("hidden.bs.modal", () => {
  treeModal.show();
});

document.addEventListener("htmx:afterRequest", (e) => {
  if (e.detail.target.id !== "bnf-tree-modal-body") {
    return;
  }

  const tree = document.getElementById("bnf-tree");
  const searchForm = document.getElementById("search-form");
  const searchInput = searchForm.querySelector("input");

  tree.addEventListener("click", (e) => {
    const li = e.target.closest("li");
    if (e.shiftKey) {
      handleShiftClick(li);
    } else {
      handleClick(li);
    }
  });

  searchForm.addEventListener("submit", (e) => {
    e.preventDefault();
    const needle = searchInput.value.trim().toLowerCase();
    document.querySelectorAll("#bnf-tree li").forEach((li) => {
      if (
        li.dataset["code"].toLowerCase() === needle ||
        li.dataset["name"].toLowerCase().includes(needle)
      ) {
        li.setAttribute("data-matches-search", "");
      } else {
        li.removeAttribute("data-matches-search");
      }
    });
  });
});

function handleClick(li) {
  const code = li.dataset["code"];
  if (code.length == 9) {
    tableModalTitle.innerHTML = `<code>${code}</code> ${li.dataset["name"]}`;
    tableModalBody.innerHTML = `
            <div class="text-center py-5">
                <div class="spinner-border">
                </div>
            </div>
        `;
    treeModal.hide();
    tableModal.show();
    htmx.ajax("GET", `/bnf/${code}/`, {
      target: "#bnf-table-modal-body",
      swap: "innerHTML",
    });
  } else {
    li.toggleAttribute("data-open");
  }
}

function handleShiftClick(li) {
	const query = state.query[state.modal.field];
  const code = li.dataset["code"];

  if (li.hasAttribute("data-included")) {
    // This item is included:
    // * Don't include it
    // * Remove descendant exclusions
    removeItem(query["included"], code);
    li.removeAttribute("data-included");
    li.querySelectorAll("li[data-excluded]").forEach((n) => {
      removeItem(query["excluded"], n.dataset["code"]);
      n.removeAttribute("data-excluded");
    });
  } else if (li.hasAttribute("data-excluded")) {
    // This item is excluded:
    // * Don't exclude it
    removeItem(query["excluded"], code);
    li.removeAttribute("data-excluded");
  } else if (li.parentElement.closest("li[data-excluded]")) {
    // An ancestor is excluded: do nothing
  } else if (li.querySelector("li[data-included]")) {
    // A descendant is included: do nothing
  } else if (li.parentElement.closest("li[data-included]")) {
    // An ancestor is included:
    // * Exclude this one
    // * Remove descendant exclusions
    query["excluded"].push(code);
    li.setAttribute("data-excluded", "");
    li.querySelectorAll("li[data-excluded]").forEach((n) => {
      removeItem(query["excluded"], n.dataset["code"]);
      n.removeAttribute("data-excluded");
    });
  } else {
    // No ancestors are included:
    // * Include this one
    query["included"].push(code);
    li.setAttribute("data-included", "");
  }
}

function removeItem(array, item) {
  const ix = array.indexOf(item);
  array.splice(ix, 1);
}
