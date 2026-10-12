import assert from "node:assert/strict";
import test from "node:test";
import { countByStatus, filterByStatus, flagCounts, formatMoney, hasProcessing } from "./invoiceStats.js";

const invoices = [
  { id: 1, status: "PROCESSING", flags: [] },
  { id: 2, status: "NEEDS_REVIEW", flags: [{ severity: "error" }, { severity: "warning" }, { severity: "warning" }] },
  { id: 3, status: "VERIFIED", flags: [] },
  { id: 4, status: "NEEDS_REVIEW" },
];

test("invoices are counted per status", () => {
  assert.deepEqual(countByStatus(invoices), {
    ALL: 4, PROCESSING: 1, NEEDS_REVIEW: 2, VERIFIED: 1, FAILED: 0,
  });
});

test("filtering by status", () => {
  assert.equal(filterByStatus(invoices, "ALL").length, 4);
  assert.deepEqual(filterByStatus(invoices, "NEEDS_REVIEW").map((i) => i.id), [2, 4]);
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