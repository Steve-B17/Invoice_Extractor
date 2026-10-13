import assert from "node:assert/strict";
import test from "node:test";
import {
  countByStatus,
  filterByStatus,
  flagCounts,
  formatMoney,
  hasProcessing,
  initialsFor,
  nextToReview,
  searchInvoices,
  sortInvoices,
  timeAgo,
} from "./invoiceStats.js";

const invoices = [
  { id: 1, status: "PROCESSING", flags: [] },
  {
    id: 2,
    status: "NEEDS_REVIEW",
    flags: [
      { severity: "error" },
      { severity: "warning" },
      { severity: "warning" },
    ],
  },
  { id: 3, status: "VERIFIED", flags: [] },
  { id: 4, status: "NEEDS_REVIEW" },
];

test("invoices are counted per status", () => {
  assert.deepEqual(countByStatus(invoices), {
    ALL: 4,
    PROCESSING: 1,
    NEEDS_REVIEW: 2,
    VERIFIED: 1,
    FAILED: 0,
  });
});

test("filtering by status", () => {
  assert.equal(filterByStatus(invoices, "ALL").length, 4);
  assert.deepEqual(
    filterByStatus(invoices, "NEEDS_REVIEW").map((i) => i.id),
    [2, 4],
  );
});

test("flags are split into errors and warnings, and missing flags are fine", () => {
  assert.deepEqual(flagCounts(invoices[1]), { errors: 1, warnings: 2 });
  assert.deepEqual(flagCounts(invoices[3]), { errors: 0, warnings: 0 });
});

test("polling is needed only while something is processing", () => {
  assert.equal(hasProcessing(invoices), true);
  assert.equal(hasProcessing(invoices.slice(1)), false);
  assert.equal(hasProcessing(undefined), false);
});

test("money uses Indian digit grouping", () => {
  assert.equal(formatMoney("370.00"), "Rs 370.00");
  assert.equal(formatMoney("123456.5"), "Rs 1,23,456.50");
  assert.equal(formatMoney(null), "");
  assert.equal(formatMoney("abc"), "abc");
});

const library = [
  {
    id: 1,
    status: "VERIFIED",
    vendor_name: "Annai Electricals",
    invoice_number: "INV-4150",
    gstin: "33PUSNZ3586L1Z7",
    original_filename: "a.jpg",
    total: "14419.60",
  },
  {
    id: 2,
    status: "NEEDS_REVIEW",
    vendor_name: "KARTHIK MESS",
    invoice_number: "501",
    gstin: null,
    original_filename: "bill.jpg",
    total: "370.00",
    flags: [{ severity: "error" }, { severity: "warning" }],
  },
  {
    id: 3,
    status: "FAILED",
    vendor_name: null,
    invoice_number: null,
    gstin: null,
    original_filename: "blank.png",
    total: null,
  },
  {
    id: 4,
    status: "NEEDS_REVIEW",
    vendor_name: "Kaveri Traders",
    invoice_number: "INV-9",
    gstin: null,
    original_filename: "k.jpg",
    total: "50.00",
    flags: [],
  },
];

test("search looks at vendor, number, GSTIN and file name", () => {
  assert.deepEqual(
    searchInvoices(library, "karthik").map((i) => i.id),
    [2],
  );
  assert.deepEqual(
    searchInvoices(library, "INV-").map((i) => i.id),
    [1, 4],
  );
  assert.deepEqual(
    searchInvoices(library, "33pus").map((i) => i.id),
    [1],
  );
  assert.deepEqual(
    searchInvoices(library, "blank").map((i) => i.id),
    [3],
  );
  assert.equal(searchInvoices(library, "  ").length, 4);
  assert.equal(searchInvoices(library, "zzz").length, 0);
});

test("sorting by date, total and need for attention", () => {
  assert.deepEqual(
    sortInvoices(library, "newest").map((i) => i.id),
    [4, 3, 2, 1],
  );
  assert.deepEqual(
    sortInvoices(library, "oldest").map((i) => i.id),
    [1, 2, 3, 4],
  );
  assert.deepEqual(
    sortInvoices(library, "total").map((i) => i.id),
    [1, 2, 4, 3],
  );
  // failed first, then bills with more problems, then clean ones, verified last
  assert.deepEqual(
    sortInvoices(library, "attention").map((i) => i.id),
    [3, 2, 4, 1],
  );
});

test("relative times", () => {
  const now = new Date("2026-10-12T12:00:00Z").getTime();
  assert.equal(timeAgo("2026-10-12T11:59:40Z", now), "just now");
  assert.equal(timeAgo("2026-10-12T11:55:00Z", now), "5 min ago");
  assert.equal(timeAgo("2026-10-12T09:00:00Z", now), "3 h ago");
  assert.equal(timeAgo("2026-10-09T12:00:00Z", now), "3 d ago");
  assert.equal(timeAgo("not a date", now), "");
});

test("initials come from the part of the email before the @", () => {
  assert.equal(initialsFor("frontend@example.com"), "FR");
  assert.equal(initialsFor("a@x.com"), "A");
  assert.equal(initialsFor(undefined), "?");
});

test("the next bill to review is chosen after the current one, wrapping round", () => {
  const list = [
    { id: 9, status: "NEEDS_REVIEW" },
    { id: 8, status: "VERIFIED" },
    { id: 7, status: "NEEDS_REVIEW" },
    { id: 6, status: "NEEDS_REVIEW" },
  ];
  assert.equal(nextToReview(list, 9).id, 7);
  assert.equal(nextToReview(list, 7).id, 6);
  assert.equal(nextToReview(list, 6).id, 9);
  assert.equal(nextToReview([{ id: 1, status: "NEEDS_REVIEW" }], 1), null);
  assert.equal(nextToReview(undefined, 1), null);
});
