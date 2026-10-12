export const TEXT_FIELDS = [
  "vendor_name",
  "gstin",
  "invoice_number",
  "invoice_date",
];
export const MONEY_FIELDS = [
  "subtotal",
  "cgst",
  "sgst",
  "igst",
  "round_off",
  "total",
];

const blank = (value) =>
  value === null || value === undefined ? "" : String(value);

// "3.000" -> "3", "2.500" -> "2.5"
export function trimQuantity(value) {
  const text = blank(value);
  if (!text.includes(".")) return text;
  return text.replace(/0+$/, "").replace(/\.$/, "");
}

// Invoice from the API -> the values the form starts with (no nulls: inputs need strings)
export function toFormValues(invoice) {
  const values = {};
  for (const name of [...TEXT_FIELDS, ...MONEY_FIELDS])
    values[name] = blank(invoice[name]);
  values.line_items = (invoice.line_items ?? []).map((item) => ({
    description: blank(item.description),
    hsn_code: blank(item.hsn_code),
    quantity: trimQuantity(item.quantity),
    rate: blank(item.rate),
    amount: blank(item.amount),
  }));
  return values;
}

export function cleanNumber(text) {
  return String(text ?? "").replace(/[,\s]/g, "");
}

// Same limits as the backend (12 digits in total, 2 or 3 after the point)
export function isMoney(text) {
  const cleaned = cleanNumber(text);
  return cleaned === "" || /^-?\d{1,10}(\.\d{1,2})?$/.test(cleaned);
}

export function isQuantity(text) {
  const cleaned = cleanNumber(text);
  return cleaned === "" || /^\d{1,9}(\.\d{1,3})?$/.test(cleaned);
}

const textOrNull = (text) => {
  const trimmed = String(text ?? "").trim();
  return trimmed === "" ? null : trimmed;
};

const numberOrNull = (text) => {
  const cleaned = cleanNumber(text);
  return cleaned === "" ? null : cleaned;
};

// Form values -> the body of PATCH /invoices/{id}. Empty boxes become null.
export function toPayload(values) {
  const gstin = textOrNull(values.gstin);
  const payload = {
    vendor_name: textOrNull(values.vendor_name),
    gstin: gstin ? gstin.replace(/\s+/g, "").toUpperCase() : null,
    invoice_number: textOrNull(values.invoice_number),
    invoice_date: textOrNull(values.invoice_date),
  };
  for (const name of MONEY_FIELDS) payload[name] = numberOrNull(values[name]);

  payload.line_items = (values.line_items ?? [])
    .map((item) => ({
      description: textOrNull(item.description),
      hsn_code: textOrNull(item.hsn_code),
      quantity: numberOrNull(item.quantity),
      rate: numberOrNull(item.rate),
      amount: numberOrNull(item.amount),
    }))
    .filter((item) => Object.values(item).some((value) => value !== null)); // drop blank rows
  return payload;
}
