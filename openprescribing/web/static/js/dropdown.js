export class DropdownCollection {
  constructor(
    el, // container element for all dropdowns
    {
      template, // template for a dropdown control
      optionTemplate, // template for an option in the open list
      onChange = null, // called whenever selections change or a dropdown is added/removed
    },
  ) {
    this._el = el;
    this._template = template;
    this._optionTemplate = optionTemplate;
    this._onChange = onChange;
    this._dropdowns = new Map(); // key -> { dropdown, wrapperEl }
  }

  // Add a new dropdown with the given key and options.
  add(key, opts) {
    if (this._dropdowns.has(key)) {
      throw new Error(`Dropdown with key "${key}" already exists`);
    }
    const wrapperEl = document.createElement("div");
    this._el.appendChild(wrapperEl);
    const userOnChange = opts.onChange;
    const dropdown = new Dropdown(wrapperEl, {
      ...opts,
      template: this._template,
      optionTemplate: this._optionTemplate,
      onChange: (selectedIds) => {
        if (userOnChange) userOnChange(selectedIds);
        if (this._onChange) this._onChange(this.getAllSelected());
      },
      onRemove: () => this.remove(key),
      onOpen: () => this._closeAllExcept(key),
    });
    this._dropdowns.set(key, { dropdown, wrapperEl });
    dropdown.open();
    return dropdown;
  }

  // Remove the dropdown with the given key and its DOM element.
  remove(key) {
    const entry = this._dropdowns.get(key);
    if (!entry) {
      throw new Error(`Dropdown with key "${key}" not found`);
    }
    entry.dropdown.destroy();
    entry.wrapperEl.remove();
    this._dropdowns.delete(key);
    if (this._onChange) this._onChange(this.getAllSelected());
  }

  // Close all dropdowns except the one with the given key.
  _closeAllExcept(key) {
    for (const [k, { dropdown }] of this._dropdowns) {
      if (k !== key) dropdown.close();
    }
  }

  // Check whether a dropdown with the given key exists.
  has(key) {
    return this._dropdowns.has(key);
  }

  // Return an object mapping each key to its array of selected IDs.
  getAllSelected() {
    const result = {};
    for (const [key, { dropdown }] of this._dropdowns) {
      result[key] = dropdown.getSelected();
    }
    return result;
  }

  // Return an object mapping each key to its array of selected names.
  getAllSelectedNames() {
    const result = {};
    for (const [key, { dropdown }] of this._dropdowns) {
      result[key] = dropdown.getSelectedNames();
    }
    return result;
  }
}

class Dropdown {
  constructor(
    el, // container element for this dropdown
    {
      title, // header label shown for the dropdown
      options, // all possible options for this dropdown
      getValidOptionIds, // returns the latest precomputed valid IDs when the dropdown opens
      template, // template for the dropdown control
      optionTemplate, // template for an option in the open list
      selected = [], // initially selected option IDs
      onChange = null, // called whenever the selection changes
      onRemove = null, // called when the remove button is clicked
      onOpen = null, // called when the dropdown is opened
    },
  ) {
    this._el = el;
    this._title = title;
    this._options = options;
    this._optionsById = new Map(options.map((o) => [o.id, o]));
    this._getValidOptionIds = getValidOptionIds;
    this._template = template;
    this._optionTemplate = optionTemplate;
    this._validIds = null;
    this._selected = new Set(selected);
    this._onChange = onChange;
    this._onRemove = onRemove;
    this._onOpen = onOpen;
    this._isOpen = false;

    this._render();
    this._bindEvents();
  }

  // Return the IDs of all currently selected options.
  getSelected() {
    return [...this._selected];
  }

  // Return the names of all currently selected options, sorted alphabetically.
  getSelectedNames() {
    return [...this._selected]
      .map((id) => this._optionsById.get(id).name)
      .sort((a, b) => a.localeCompare(b));
  }

  // Remove the component's DOM contents from its container element.
  destroy() {
    this._el.innerHTML = "";
  }

  // Build the component's DOM structure: header, summary, and panel.
  _render() {
    this._el.innerHTML = "";
    const filterControl = cloneTemplateElement(this._template);

    this._el.appendChild(filterControl);
    this._headerEl = this._el.querySelector("[data-dropdown-header]");
    this._labelEl = this._el.querySelector("[data-dropdown-label]");
    this._caretEl = this._el.querySelector("[data-dropdown-caret]");
    this._removeEl = this._el.querySelector("[data-dropdown-remove]");
    this._summaryEl = this._el.querySelector("[data-dropdown-summary]");
    this._panelEl = this._el.querySelector("[data-dropdown-body]");
    this._searchEl = this._el.querySelector("[data-dropdown-input]");
    this._clearSearchEl = this._el.querySelector("[data-clear-search]");
    this._listEl = this._el.querySelector("[data-dropdown-options]");

    this._labelEl.textContent = this._title;
    this._renderSummary();
  }

  // Attach event listeners for toggling, searching, and selecting.
  _bindEvents() {
    this._headerEl.addEventListener("click", (e) => {
      if (e.target.closest("[data-dropdown-remove]")) {
        return;
      }

      this._toggle();
    });

    this._removeEl.addEventListener("click", (e) => {
      e.stopPropagation();
      if (this._onRemove) {
        this._onRemove();
      }
    });

    this._searchEl.addEventListener("input", () => this._renderOptions());
    this._clearSearchEl.addEventListener("click", () => {
      this._searchEl.value = "";
      this._renderOptions();
      this._searchEl.focus();
    });

    this._listEl.addEventListener("mousedown", (e) => {
      const option = e.target.closest("option");

      if (!option) {
        return;
      }

      e.preventDefault();
      option.selected = !option.selected;
      this._syncSelectedFromList();
      this._renderSummary();

      if (this._onChange) {
        this._onChange(this.getSelected());
      }

      this._listEl.focus();
    });

    this._listEl.addEventListener("change", () => {
      this._syncSelectedFromList();
      this._renderSummary();
      if (this._onChange) {
        this._onChange(this.getSelected());
      }
    });
  }

  // Open the dropdown panel.
  open() {
    if (this._isOpen) return;
    this._isOpen = true;
    this._refreshValidIds();
    this._panelEl.hidden = false;
    this._summaryEl.hidden = true;
    this._caretEl.classList.replace(
      "bi-caret-right-fill",
      "bi-caret-down-fill",
    );
    this._searchEl.value = "";
    this._renderOptions();
    this._searchEl.focus();
    if (this._onOpen) this._onOpen();
  }

  // Close the dropdown panel.
  close() {
    if (!this._isOpen) return;
    this._isOpen = false;
    this._panelEl.hidden = true;
    this._summaryEl.hidden = false;
    this._caretEl.classList.replace(
      "bi-caret-down-fill",
      "bi-caret-right-fill",
    );
  }

  // Switch between open and closed states.
  _toggle() {
    if (this._isOpen) {
      this.close();
    } else {
      this.open();
    }
  }

  // Refresh which option IDs are currently valid by calling getValidOptionIds.
  _refreshValidIds() {
    this._validIds = new Set(this._getValidOptionIds());
  }

  // Render the closed-state list of selected names, sorted alphabetically.
  _renderSummary() {
    this._summaryEl.innerHTML = "";
    const names = this.getSelectedNames();

    if (names.length === 0) {
      const li = document.createElement("li");
      li.className = "text-body-secondary";
      li.textContent = "No items selected";
      this._summaryEl.appendChild(li);
      return;
    }

    for (const name of names) {
      const li = document.createElement("li");
      li.textContent = name;
      this._summaryEl.appendChild(li);
    }
  }

  // Render the open-state options list.
  // Shows valid options plus any selected-but-invalid options.
  _renderOptions() {
    this._listEl.innerHTML = "";

    const visible = this._options.filter(
      (o) => this._validIds.has(o.id) || this._selected.has(o.id),
    );
    const query = this._searchEl.value.toLowerCase();
    const filtered = visible.filter((opt) => {
      if (query === "") {
        return true;
      }

      if (opt.searchCode !== undefined && opt.searchName !== undefined) {
        return (
          opt.searchCode.toLowerCase().startsWith(query) ||
          opt.searchName.toLowerCase().includes(query)
        );
      }

      const haystack = opt.searchText ?? opt.name;
      return haystack.toLowerCase().includes(query);
    });

    for (const opt of filtered) {
      const option = cloneTemplateElement(this._optionTemplate);
      option.textContent = opt.name;
      option.value = opt.id;
      option.selected = this._selected.has(opt.id);
      this._listEl.appendChild(option);
    }
  }

  _syncSelectedFromList() {
    const renderedIds = Array.from(
      this._listEl.options,
      (option) => option.value,
    );

    renderedIds.forEach((id) => {
      this._selected.delete(id);
    });

    Array.from(this._listEl.selectedOptions).forEach((option) => {
      this._selected.add(option.value);
    });
  }
}

function cloneTemplateElement(template) {
  return template.content.firstElementChild.cloneNode(true);
}
