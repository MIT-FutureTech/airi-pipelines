export function anchorSelector(anchor: string): string {
  return `[data-tour="${anchor}"]`;
}

export function findAnchor(anchor: string): HTMLElement | null {
  const element = document.querySelector<HTMLElement>(anchorSelector(anchor));
  if (element === null && import.meta.env.DEV) {
    console.error(`Tour anchor not found: ${anchor}`);
  }
  return element;
}

export function click(anchor: string, value?: string): void {
  const target = findAnchor(anchor);
  if (target === null) {
    return;
  }
  if (value === undefined) {
    target.click();
    return;
  }
  target.querySelector<HTMLElement>(`[data-value="${value}"]`)?.click();
}

export function fill(anchor: string, text: string): void {
  const field = findAnchor(anchor);
  if (!(field instanceof HTMLTextAreaElement)) {
    return;
  }
  // React reads the value through its own descriptor, so assigning to
  // `field.value` directly would leave its state untouched.
  const setter = Object.getOwnPropertyDescriptor(
    HTMLTextAreaElement.prototype,
    "value",
  )?.set;
  setter?.call(field, text);
  field.dispatchEvent(new Event("input", { bubbles: true }));
}
