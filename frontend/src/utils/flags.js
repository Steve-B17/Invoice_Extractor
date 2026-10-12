// The backend names the field each validation flag is about:
//   "gstin", "total", ...   a single form field
//   "line_items.2"          the third line item (counting from 0)
//   "line_items", "invoice" the invoice as a whole
export function groupFlags(flags = []) {
  const byField = {};
  const byItem = {};
  const general = [];

  for (const flag of flags) {
    const itemMatch = /^line_items\.(\d+)$/.exec(flag.field);
    if (itemMatch) {
      (byItem[Number(itemMatch[1])] ??= []).push(flag);
    } else if (flag.field === "line_items" || flag.field === "invoice") {
      general.push(flag);
    } else {
      (byField[flag.field] ??= []).push(flag);
    }
  }
  return { byField, byItem, general };
}

// "error" beats "warning"; null when there is nothing to show
export function topSeverity(flags) {
  if (!flags || flags.length === 0) return null;
  return flags.some((flag) => flag.severity === "error") ? "error" : "warning";
}

export function countSeverities(flags = []) {
  const errors = flags.filter((flag) => flag.severity === "error").length;
  return { errors, warnings: flags.length - errors };
}
