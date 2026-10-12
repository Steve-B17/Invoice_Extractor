export const STATUS_FILTERS = [
  { key: "ALL", label: "All" },
  { key: "PROCESSING", label: "Processing" },
  { key: "NEEDS_REVIEW", label: "Needs review" },
  { key: "VERIFIED", label: "Verified" },
  { key: "FAILED", label: "Failed" },
];

export function countByStatus(invoices) {
  const counts = { ALL: invoices.length, PROCESSING: 0, NEEDS_REVIEW: 0, VERIFIED: 0, FAILED: 0 };
  for (const invoice of invoices) {
    if (invoice.status in counts) counts[invoice.status] += 1;
  }
  return counts;
}

export function filterByStatus(invoices, key) {
  return key === "ALL" ? invoices : invoices.filter((invoice) => invoice.status === key);
}

export function flagCounts(invoice) {
  const flags = invoice.flags ?? [];
  const errors = flags.filter((flag) => flag.severity === "error").length;
  return { errors, warnings: flags.length - errors };
}

export function hasProcessing(invoices) {
  return Boolean(invoices?.some((invoice) => invoice.status === "PROCESSING"));
}

// "123456.5" -> "Rs 1,23,456.50" (Indian digit grouping)
export function formatMoney(value) {
  if (value === null || value === undefined || value === "") return "";
  const number = Number(value);
  if (Number.isNaN(number)) return String(value);
  return `Rs ${number.toLocaleString("en-IN", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
}