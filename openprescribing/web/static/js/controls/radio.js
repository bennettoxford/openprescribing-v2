import { cloneTemplateElement } from "../template_utils.js";

// Used to give each radio group a unique input `name`.
let radioGroupCount = 0;

// A single-select control offering the same interface as Dropdown, rendered as a
// radio group. It reuses the shared control template shell (header, remove button,
// collapsible body) and only swaps the body for a radio per option.
export class RadioGroup {
  constructor(
    el, // container element for this control
    {
      title, // header label
      options, // all possible options ({ id, name })
      template, // template for the (shared) control shell
      selected = [], // initially selected option IDs (0 or 1)
      onChange = null, // called whenever the selection changes
      onRemove = null, // called when the remove button is clicked
      onOpen = null, // called when the control is opened
    },
  ) {
    this._el = el;
    this._title = title;
    this._options = options;
    this._optionsById = new Map(options.map((o) => [o.id, o]));
    this._template = template;
    // Default to the first option ("all") when nothing is preselected.
    this._selectedId = selected[0] ?? options[0].id;
    this._onChange = onChange;
    this._onRemove = onRemove;
    this._onOpen = onOpen;
    radioGroupCount += 1;
    this._name = `radio-group-${radioGroupCount}`;
    this._isOpen = false;

    this._render();
    this._bindEvents();
  }

  // Return the selected option ID (a scalar: this is a single-select control).
  getSelected() {
    return this._selectedId;
  }

  // Return the selected option name (a scalar: this is a single-select control).
  getSelectedNames() {
    return this._optionsById.get(this._selectedId).name;
  }

  // Remove the component's DOM contents from its container element.
  destroy() {
    this._el.innerHTML = "";
  }

  // Build the component's DOM structure: header, summary, and radio panel.
  _render() {
    this._el.innerHTML = "";
    this._el.appendChild(cloneTemplateElement(this._template));

    this._headerEl = this._el.querySelector("[data-control-header]");
    this._labelEl = this._el.querySelector("[data-control-label]");
    this._caretEl = this._el.querySelector("[data-control-caret]");
    this._removeEl = this._el.querySelector("[data-control-remove]");
    this._summaryEl = this._el.querySelector("[data-control-summary]");
    this._panelEl = this._el.querySelector("[data-control-body]");

    this._labelEl.textContent = this._title;
    this._panelEl.replaceChildren(
      ...this._options.map((option) => this._makeRadio(option)),
    );
    this._renderSummary();
  }

  // Build a single labelled radio input for the given option.
  _makeRadio(option) {
    const wrapper = document.createElement("div");
    wrapper.className = "form-check";

    const input = document.createElement("input");
    input.type = "radio";
    input.className = "form-check-input";
    input.name = this._name;
    input.value = option.id;
    input.id = `${this._name}-${option.id}`;
    input.checked = option.id === this._selectedId;

    const label = document.createElement("label");
    label.className = "form-check-label";
    label.setAttribute("for", input.id);
    label.textContent = option.name;

    wrapper.append(input, label);
    return wrapper;
  }

  // Attach event listeners for toggling, removing, and selecting.
  _bindEvents() {
    this._headerEl.addEventListener("click", (e) => {
      if (e.target.closest("[data-control-remove]")) {
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

    this._panelEl.addEventListener("change", (e) => {
      const input = e.target.closest("input[type=radio]");

      if (!input) {
        return;
      }

      this._selectedId = input.value;
      this._renderSummary();

      if (this._onChange) {
        this._onChange(this.getSelected());
      }
    });
  }

  // Open the radio panel.
  open() {
    if (this._isOpen) return;
    this._isOpen = true;
    this._panelEl.hidden = false;
    this._summaryEl.hidden = true;
    this._caretEl.classList.replace(
      "bi-caret-right-fill",
      "bi-caret-down-fill",
    );
    if (this._onOpen) this._onOpen();
  }

  // Close the radio panel.
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

  // Render the closed-state summary with the current choice (including "All").
  _renderSummary() {
    const li = document.createElement("li");
    li.textContent = this._optionsById.get(this._selectedId).name;
    this._summaryEl.replaceChildren(li);
  }
}
