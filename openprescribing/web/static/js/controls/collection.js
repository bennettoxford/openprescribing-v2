import { Dropdown } from "./dropdown.js";
import { RadioGroup } from "./radio.js";

// Control classes that the collection can instantiate.
const CONTROL_CLASSES = {
  dropdown: Dropdown,
  radio: RadioGroup,
};

// A collection of filter controls sharing a container element. Each control is
// instantiated from CONTROL_CLASSES.  All control classes must have the same interface:
// getSelected, getSelectedNames, open, close, destroy.

export class ControlCollection {
  constructor(
    el, // container element for all controls
    {
      template, // template for a control's shell
      onChange = null, // called whenever selections change or a control is added/removed
    },
  ) {
    this._el = el;
    this._template = template;
    this._onChange = onChange;
    this._controls = new Map(); // key -> { control, wrapperEl }
  }

  // Add a new control with the given key and options.
  add(key, opts) {
    if (this._controls.has(key)) {
      throw new Error(`Control with key "${key}" already exists`);
    }
    const wrapperEl = document.createElement("div");
    this._el.appendChild(wrapperEl);
    const userOnChange = opts.onChange;
    const ControlClass = CONTROL_CLASSES[opts.control];
    const control = new ControlClass(wrapperEl, {
      ...opts,
      template: this._template,
      onChange: (selectedIds) => {
        if (userOnChange) userOnChange(selectedIds);
        if (this._onChange) this._onChange(this.getAllSelected());
      },
      onRemove: () => this.remove(key),
      onOpen: () => this._closeAllExcept(key),
    });
    this._controls.set(key, { control, wrapperEl });
    control.open();
    return control;
  }

  // Remove the control with the given key and its DOM element.
  remove(key) {
    const entry = this._controls.get(key);
    if (!entry) {
      throw new Error(`Control with key "${key}" not found`);
    }
    entry.control.destroy();
    entry.wrapperEl.remove();
    this._controls.delete(key);
    if (this._onChange) this._onChange(this.getAllSelected());
  }

  // Close all controls except the one with the given key.
  _closeAllExcept(key) {
    for (const [k, { control }] of this._controls) {
      if (k !== key) control.close();
    }
  }

  // Check whether a control with the given key exists.
  has(key) {
    return this._controls.has(key);
  }

  // Return an object mapping each key to its array of selected IDs.
  getAllSelected() {
    const result = {};
    for (const [key, { control }] of this._controls) {
      result[key] = control.getSelected();
    }
    return result;
  }

  // Return an object mapping each key to its array of selected names.
  getAllSelectedNames() {
    const result = {};
    for (const [key, { control }] of this._controls) {
      result[key] = control.getSelectedNames();
    }
    return result;
  }
}
