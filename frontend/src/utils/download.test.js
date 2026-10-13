import assert from "node:assert/strict";
import test from "node:test";
import { filenameFromDisposition } from "./download.js";

test("a quoted file name is read from the header", () => {
  assert.equal(
    filenameFromDisposition(
      'attachment; filename="invoices-2026-10-12.csv"',
      "x.csv",
    ),
    "invoices-2026-10-12.csv",
  );
});

test("an unquoted name and an encoded name both work", () => {
  assert.equal(
    filenameFromDisposition("attachment; filename=items.csv", "x.csv"),
    "items.csv",
  );
  assert.equal(
    filenameFromDisposition(
      "attachment; filename*=UTF-8''%E0%AE%87%E0%AE%9F%E0%AF%8D%E0%AE%B2%E0%AE%BF.csv",
      "x.csv",
    ),
    "இட்லி.csv",
  );
});

test("a missing header or a path in the name falls back", () => {
  assert.equal(filenameFromDisposition(null, "fallback.csv"), "fallback.csv");
  assert.equal(
    filenameFromDisposition(undefined, "fallback.csv"),
    "fallback.csv",
  );
  assert.equal(
    filenameFromDisposition(
      'attachment; filename="../../evil.csv"',
      "fallback.csv",
    ),
    "fallback.csv",
  );
  assert.equal(
    filenameFromDisposition("inline", "fallback.csv"),
    "fallback.csv",
  );
});
    