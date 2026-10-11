# Evaluation: gpt-oss-120b (2026-10-11)

- OCR language: `eng+tam`, layout mode: `4`, preprocessing: `on`, character height: `16`
- LLM model: `openai/gpt-oss-120b`
- Bills scored: 13

## Summary by group

| Group | Bills | OCR confidence | GSTIN, date and total right | Every number right | Item amounts right | Wrong-number bills flagged | Right-number bills with a false error flag |
|---|---:|---:|---:|---:|---:|---:|---:|
| synthetic-clean | 6 | 0.96 | 50% | 0% | 23% | 100% (6/6) | n/a (0/0) |
| synthetic-photo | 6 | 0.96 | 50% | 0% | 15% | 100% (6/6) | n/a (0/0) |
| real | 1 | 0.91 | 100% | 0% | 100% | 100% (1/1) | n/a (0/0) |
| ALL | 13 | 0.95 | 54% | 0% | 24% | 100% (13/13) | n/a (0/0) |

## Accuracy per field

| Field | synthetic-clean | synthetic-photo | real | ALL |
|---|---:|---:|---:|---:|
| vendor_name | 100% | 100% | 0% | 92% |
| gstin | 50% | 50% | 100% | 54% |
| invoice_number | 100% | 100% | 0% | 92% |
| invoice_date | 100% | 100% | 100% | 100% |
| subtotal | 100% | 100% | 100% | 100% |
| cgst | 100% | 100% | 100% | 100% |
| sgst | 100% | 100% | 100% | 100% |
| igst | 100% | 100% | 100% | 100% |
| round_off | 100% | 100% | 100% | 100% |
| total | 100% | 100% | 100% | 100% |
| line item quantity | n/a | n/a | 67% | 67% |
| line item rate | 54% | 38% | 100% | 49% |
| line item amount | 23% | 15% | 100% | 24% |
| line item description | 100% | 100% | 33% | 96% |

## Per bill

| Bill | OCR conf | Fields right | Missed | Flags |
|---|---:|---:|---|---|
| synthetic_01_clean.png | 0.96 | 9/10 | gstin | GSTIN_FORMAT, LINE_ITEM_MATH, LINE_ITEM_MATH, LINE_ITEM_MATH, LINE_ITEM_MATH, ITEMS_SUBTOTAL_MISMATCH |
| synthetic_01_photo.jpg | 0.95 | 9/10 | gstin | GSTIN_CHECKSUM, LINE_ITEM_MATH, LINE_ITEM_MATH, LINE_ITEM_MATH, LINE_ITEM_MATH, ITEMS_SUBTOTAL_MISMATCH |
| synthetic_02_clean.png | 0.96 | 10/10 | - | LINE_ITEM_MATH, LINE_ITEM_MATH, LINE_ITEM_MATH, ITEMS_SUBTOTAL_MISMATCH |
| synthetic_02_photo.jpg | 0.95 | 10/10 | - | ITEM_AMOUNT_MISSING |
| synthetic_03_clean.png | 0.96 | 9/10 | gstin | GSTIN_FORMAT, LINE_ITEM_MATH, LINE_ITEM_MATH, LINE_ITEM_MATH, LINE_ITEM_MATH, ITEMS_SUBTOTAL_MISMATCH |
| synthetic_03_photo.jpg | 0.96 | 9/10 | gstin | GSTIN_FORMAT, ITEM_AMOUNT_MISSING |
| synthetic_04_clean.png | 0.96 | 10/10 | - | ITEM_AMOUNT_MISSING |
| synthetic_04_photo.jpg | 0.96 | 10/10 | - | ITEM_AMOUNT_MISSING |
| synthetic_05_clean.png | 0.96 | 9/10 | gstin | GSTIN_FORMAT, LINE_ITEM_MATH, LINE_ITEM_MATH, LINE_ITEM_MATH, ITEMS_SUBTOTAL_MISMATCH |
| synthetic_05_photo.jpg | 0.96 | 9/10 | gstin | GSTIN_FORMAT, LINE_ITEM_MATH, LINE_ITEM_MATH, LINE_ITEM_MATH, ITEMS_SUBTOTAL_MISMATCH |
| synthetic_06_clean.png | 0.96 | 10/10 | - | LINE_ITEM_MATH, LINE_ITEM_MATH, LINE_ITEM_MATH, ITEMS_SUBTOTAL_MISMATCH |
| synthetic_06_photo.jpg | 0.96 | 10/10 | - | LINE_ITEM_MATH, LINE_ITEM_MATH, LINE_ITEM_MATH, ITEMS_SUBTOTAL_MISMATCH |
| bill.jpg | 0.91 | 8/10 | vendor_name, invoice_number | INVOICE_NUMBER_MISSING, LINE_ITEM_INCOMPLETE |
