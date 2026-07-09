// Clone the first element of a <template>'s content.
export function cloneTemplateElement(template) {
  return template.content.firstElementChild.cloneNode(true);
}
