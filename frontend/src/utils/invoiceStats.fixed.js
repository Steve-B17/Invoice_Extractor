export const SORT_OPTIONS = [
  { key: "newest", label: "Newest first" },
  { key: "oldest", label: "Oldest first" },
  { key: "total", label: "Highest total" },
  { key: "attention", label: "Needs attention first" },
];

export function countByStatus(invoices) {
  const list = invoices ?? [];
  const counts = {
    ALL: list.length,
    PROCESSING: 0,
    NEEDS_REVIEW: 0,
    VERIFIED: 0,
    FAILED: 0,
  };

  for (const invoice of list) {
    if (invoice?.status && counts[invoice.status] != null) {
      counts[invoice.status] += 1;
    }
  }

  return counts;
}

export function filterByStatus(invoices, filter) {
  const list = invoices ?? [];
  if (!filter || filter === "ALL") return list;
  return list.filter((invoice) => invoice.status === filter);
}

export function flagCounts(invoice) {
  const flags = Array.isArray(invoice?.flags) ? invoice.flags : [];
  return {
    errors: flags.filter((flag) => flag?.severity === "error").length,
    warnings: flags.filter((flag) => flag?.severity === "warning").length,
  };
}

export function hasProcessing(invoices) {
  return (invoices ?? []).some((invoice) => invoice?.status === "PROCESSING");
}

export function formatMoney(value) {
  if (value == null || value === "") return "";

  const raw = String(value).trim();
  if (!raw) return "";

  const normalized = raw.replace(/,/g, "");
  if (!/^-?\d+(?:\.\d+)?$/.test(normalized)) return raw;

  const numeric = Number(normalized);
  if (!Number.isFinite(numeric)) return raw;

  const sign = numeric < 0 ? "-" : "";
  const magnitude = Math.abs(numeric);
  const [wholePart, decimalPart = "00"] = magnitude.toFixed(2).split(".");
  return `${sign}Rs ${indianGroup(wholePart)}.${decimalPart}`;
}

function indianGroup(wholePart) {
  const digits = String(wholePart).replace(/^0+/, "") || "0";
  if (digits.length <= 3) return digits;

  const lastThree = digits.slice(-3);
  const rest = digits.slice(0, -3);
  const chunks = [];
  let remaining = rest;

  while (remaining.length > 2) {
    chunks.unshift(remaining.slice(-2));
    remaining = remaining.slice(0, -2);
  }

  if (remaining.length > 0) chunks.unshift(remaining);
  return [...chunks, lastThree].join(",");
}

export function searchInvoices(invoices, text) {
  const query = String(text ?? "")
    .trim()
    .toLowerCase();
  if (!query) return invoices;
  return invoices.filter((invoice) =>
    [
      invoice.vendor_name,
      invoice.invoice_number,
      invoice.gstin,
      invoice.original_filename,
    ].some((value) => value && String(value).toLowerCase().includes(query)),
  );
}

function attentionScore(invoice) {
  if (invoice.status === "FAILED") return 100;
  if (invoice.status === "NEEDS_REVIEW") {
    const { errors, warnings } = flagCounts(invoice);
    return 50 + errors * 5 + warnings;
  }
  if (invoice.status === "PROCESSING") return 10;
  return 0;
}

export function sortInvoices(invoices, key) {
  const list = [...invoices];
  switch (key) {
    case "oldest":
      return list.sort((a, b) => a.id - b.id);
    case "total":
      return list.sort(
        (a, b) => (Number(b.total) || 0) - (Number(a.total) || 0),
      );
    case "attention":
      return list.sort(
        (a, b) => attentionScore(b) - attentionScore(a) || b.id - a.id,
      );
    default:
      return list.sort((a, b) => b.id - a.id);
  }
}

export function timeAgo(value, now = Date.now()) {
  const then = new Date(value).getTime();
  if (Number.isNaN(then)) return "";
  const seconds = Math.max(0, Math.round((now - then) / 1000));
  if (seconds < 60) return "just now";
  const minutes = Math.round(seconds / 60);
  if (minutes < 60) return `${minutes} min ago`;
  const hours = Math.round(minutes / 60);
  if (hours < 24) return `${hours} h ago`;
  const days = Math.round(hours / 24);
  if (days < 7) return `${days} d ago`;
  return new Date(then).toLocaleDateString("en-IN", { dateStyle: "medium" });
}

export function initialsFor(email) {
  const local = String(email ?? "")
    .split("@")[0]
    .replace(/[^a-zA-Z0-9]/g, "");
  return (local.slice(0, 2) || "?").toUpperCase();
}

export function nextToReview(invoices, currentId) {
  const list = invoices ?? [];
  const waiting = list.filter(
    (invoice) => invoice.status === "NEEDS_REVIEW" && invoice.id !== currentId,
  );
  if (waiting.length === 0) return null;
  const position = list.findIndex((invoice) => invoice.id === currentId);
  return (
    waiting.find((invoice) => list.indexOf(invoice) > position) ?? waiting[0]
  );
}
