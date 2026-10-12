import assert from "node:assert/strict";
import test from "node:test";
import {
  isMoney,
  isQuantity,
  toFormValues,
  toPayload,
  trimQuantity,
} from "./invoiceForm.js";

const invoice = {
  vendor_name: "KARTHIK MESS",
  gstin: "33BECPS1148N1ZB",
  invoice_number: null,
  invoice_date: "2026-09-15",
  subtotal: "352.40",
  cgst: "8.81",
  sgst: "8.81",
  igst: null,
  round_off: "-0.02",
  total: "370.00",
  line_items: [
    {
      description: "இட்லி",
      hsn_code: null,
      quantity: "4.000",
      rate: "14.29",
      amount: "57.16",
    },
  ],
};

test("the API invoice becomes form strings with no nulls", () => {
  const values = toFormValues(invoice);
  assert.equal(values.invoice_number, "");
  assert.equal(values.igst, "");
  assert.equal(values.total, "370.00");
  assert.deepEqual(values.line_items[0], {
    description: "இட்லி",
    hsn_code: "",
    quantity: "4",
    rate: "14.29",
    amount: "57.16",
  });
});

test("quantities lose pointless zeros", () => {
  assert.equal(trimQuantity("3.000"), "3");
  assert.equal(trimQuantity("2.500"), "2.5");
  assert.equal(trimQuantity("2.505"), "2.505");
  assert.equal(trimQuantity("10"), "10");
  assert.equal(trimQuantity(null), "");
});

test("money and quantity checks match the backend limits", () => {
  assert.equal(isMoney(""), true);
  assert.equal(isMoney("1,980.50"), true);
  assert.equal(isMoney("-0.02"), true);
  assert.equal(isMoney("12.345"), false);
  assert.equal(isMoney("abc"), false);
  assert.equal(isMoney("12345678901"), false);
  assert.equal(isQuantity("2.5"), true);
  assert.equal(isQuantity("2.5555"), false);
  assert.equal(isQuantity("-1"), false);
});

test("the payload turns empty boxes into null and tidies text", () => {
  const values = toFormValues(invoice);
  values.gstin = " 33becps1148n1zb ";
  values.igst = "";
  values.total = "1,370.00";
  const payload = toPayload(values);
  assert.equal(payload.gstin, "33BECPS1148N1ZB");
  assert.equal(payload.igst, null);
  assert.equal(payload.invoice_number, null);
  assert.equal(payload.total, "1370.00");
  assert.equal(payload.round_off, "-0.02");
});

test("blank line item rows are dropped and empty cells become null", () => {
  const values = toFormValues(invoice);
  values.line_items.push({
    description: "",
    hsn_code: "",
    quantity: "",
    rate: "",
    amount: "",
  });
  values.line_items.push({
    description: "Tea",
    hsn_code: "",
    quantity: "2",
    rate: "",
    amount: "20",
  });
  const items = toPayload(values).line_items;
  assert.equal(items.length, 2);
  assert.deepEqual(items[1], {
    description: "Tea",
    hsn_code: null,
    quantity: "2",
    rate: null,
    amount: "20",
  });
});

test("the payload only contains keys the backend accepts", () => {
  const payload = toPayload(toFormValues(invoice));
  assert.deepEqual(Object.keys(payload).sort(), [
    "cgst",
    "gstin",
    "igst",
    "invoice_date",
    "invoice_number",
    "line_items",
    "round_off",
    "sgst",
    "subtotal",
    "total",
    "vendor_name",
  ]);
  assert.deepEqual(Object.keys(payload.line_items[0]).sort(), [
    "amount",
    "description",
    "hsn_code",
    "quantity",
    "rate",
  ]);
});
