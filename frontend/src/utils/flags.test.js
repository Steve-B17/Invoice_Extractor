import assert from "node:assert/strict";
import test from "node:test";
import { countSeverities, groupFlags, topSeverity } from "./flags.js";

const flags = [
  { field: "gstin", code: "GSTIN_CHECKSUM", severity: "error", message: "a" },
  {
    field: "cgst",
    code: "CGST_SGST_MISMATCH",
    severity: "error",
    message: "b",
  },
  {
    field: "subtotal",
    code: "TAX_RATE_UNUSUAL",
    severity: "warning",
    message: "c",
  },
  { field: "subtotal", code: "OTHER", severity: "warning", message: "d" },
  {
    field: "line_items.2",
    code: "LINE_ITEM_MATH",
    severity: "error",
    message: "e",
  },
  {
    field: "line_items",
    code: "ITEMS_SUBTOTAL_MISMATCH",
    severity: "error",
    message: "f",
  },
  {
    field: "invoice",
    code: "LOW_OCR_CONFIDENCE",
    severity: "warning",
    message: "g",
  },
];

test("flags are sorted by what they point at", () => {
  const { byField, byItem, general } = groupFlags(flags);
  assert.deepEqual(Object.keys(byField).sort(), ["cgst", "gstin", "subtotal"]);
  assert.equal(byField.subtotal.length, 2);
  assert.deepEqual(Object.keys(byItem), ["2"]);
  assert.deepEqual(
    general.map((flag) => flag.code),
    ["ITEMS_SUBTOTAL_MISMATCH", "LOW_OCR_CONFIDENCE"],
  );
});

test("no flags gives empty groups", () => {
  assert.deepEqual(groupFlags(undefined), {
    byField: {},
    byItem: {},
    general: [],
  });
});

test("the most serious severity wins", () => {
  assert.equal(
    topSeverity([{ severity: "warning" }, { severity: "error" }]),
    "error",
  );
  assert.equal(topSeverity([{ severity: "warning" }]), "warning");
  assert.equal(topSeverity([]), null);
  assert.equal(topSeverity(undefined), null);
});

test("severities are counted", () => {
  assert.deepEqual(countSeverities(flags), { errors: 4, warnings: 3 });
  assert.deepEqual(countSeverities(), { errors: 0, warnings: 0 });
});
