# Evaluation: no-preprocess (2026-10-11)

- OCR language: `eng+tam`, layout mode: `4`, preprocessing: `off`, character height: `16`
- LLM model: `openai/gpt-oss-20b`
- Bills scored: 11 (skipped because the LLM call failed, run again to retry: synthetic_04_photo.jpg, synthetic_06_photo.jpg)

## Summary by group

| Group | Bills | OCR confidence | GSTIN, date and total right | Every number right | Item amounts right | Wrong-number bills flagged | Right-number bills with a false error flag |
|---|---:|---:|---:|---:|---:|---:|---:|
| synthetic-clean | 6 | 0.96 | 50% | 0% | 27% | 100% (6/6) | n/a (0/0) |
| synthetic-photo | 4 | 0.91 | 0% | 0% | 0% | 100% (4/4) | n/a (0/0) |
| real | 1 | 0.41 | 0% | 0% | 0% | 100% (1/1) | n/a (0/0) |
| ALL | 11 | 0.89 | 27% | 0% | 15% | 100% (11/11) | n/a (0/0) |

## Accuracy per field

| Field | synthetic-clean | synthetic-photo | real | ALL |
|---|---:|---:|---:|---:|
| vendor_name | 100% | 50% | 100% | 82% |
| gstin | 50% | 25% | 100% | 45% |
| invoice_number | 100% | 75% | 0% | 82% |
| invoice_date | 100% | 75% | 0% | 82% |
| subtotal | 100% | 50% | 0% | 73% |
| cgst | 100% | 50% | 0% | 73% |
| sgst | 100% | 50% | 0% | 73% |
| igst | 100% | 100% | 100% | 100% |
| round_off | 100% | 100% | 0% | 91% |
| total | 100% | 50% | 0% | 73% |
| line item quantity | n/a | n/a | 0% | 0% |
| line item rate | 54% | 11% | 0% | 34% |
| line item amount | 27% | 0% | 0% | 15% |
| line item description | 100% | 72% | 0% | 83% |

## Per bill

| Bill | OCR conf | Fields right | Missed | Flags |
|---|---:|---:|---|---|
| synthetic_01_clean.png | 0.96 | 9/10 | gstin | GSTIN_CHECKSUM, LINE_ITEM_MATH, LINE_ITEM_MATH, LINE_ITEM_MATH, LINE_ITEM_MATH, ITEMS_SUBTOTAL_MISMATCH |
| synthetic_01_photo.jpg | 0.78 | 6/10 | vendor_name, gstin, invoice_number, invoice_date | INVOICE_NUMBER_MISSING, GSTIN_MISSING, DATE_MISSING, LINE_ITEM_INCOMPLETE, LINE_ITEM_INCOMPLETE, LINE_ITEM_INCOMPLETE, LINE_ITEM_INCOMPLETE, LINE_ITEM_INCOMPLETE, ITEM_AMOUNT_MISSING |
| synthetic_02_clean.png | 0.96 | 10/10 | - | LINE_ITEM_MATH, LINE_ITEM_MATH, LINE_ITEM_MATH, ITEMS_SUBTOTAL_MISMATCH |
| synthetic_02_photo.jpg | 0.94 | 6/10 | subtotal, cgst, sgst, total | TOTAL_MISSING, ITEM_AMOUNT_MISSING |
| synthetic_03_clean.png | 0.96 | 9/10 | gstin | GSTIN_FORMAT, LINE_ITEM_MATH, LINE_ITEM_MATH, LINE_ITEM_MATH, LINE_ITEM_MATH, ITEMS_SUBTOTAL_MISMATCH |
| synthetic_03_photo.jpg | 0.96 | 9/10 | gstin | GSTIN_FORMAT, LINE_ITEM_MATH, LINE_ITEM_MATH, LINE_ITEM_MATH, LINE_ITEM_MATH, ITEMS_SUBTOTAL_MISMATCH |
| synthetic_04_clean.png | 0.96 | 10/10 | - | LINE_ITEM_MATH, ITEMS_SUBTOTAL_MISMATCH |
| synthetic_04_photo.jpg | 0.96 | 2/10 | vendor_name, gstin, invoice_number, invoice_date, subtotal, cgst, sgst, total (LLM: The AI service returned an error (HTTP 429)) | TOTAL_MISSING, VENDOR_MISSING, INVOICE_NUMBER_MISSING, GSTIN_MISSING, DATE_MISSING, NO_LINE_ITEMS |
| synthetic_05_clean.png | 0.96 | 9/10 | gstin | GSTIN_FORMAT, ITEM_AMOUNT_MISSING |
| synthetic_05_photo.jpg | 0.95 | 4/10 | vendor_name, gstin, subtotal, cgst, sgst, total | GSTIN_FORMAT, TOTAL_MISSING, ITEM_AMOUNT_MISSING |
| synthetic_06_clean.png | 0.96 | 10/10 | - | LINE_ITEM_MATH, LINE_ITEM_MATH, LINE_ITEM_MATH, ITEMS_SUBTOTAL_MISMATCH |
| synthetic_06_photo.jpg | 0.90 | 2/10 | vendor_name, gstin, invoice_number, invoice_date, subtotal, cgst, sgst, total (LLM: The AI service returned an error (HTTP 429)) | TOTAL_MISSING, VENDOR_MISSING, INVOICE_NUMBER_MISSING, GSTIN_MISSING, DATE_MISSING, NO_LINE_ITEMS |
| bill.jpg | 0.41 | 3/10 | invoice_number, invoice_date, subtotal, cgst, sgst, round_off, total | TOTAL_MISSING, INVOICE_NUMBER_MISSING, DATE_MISSING, NO_LINE_ITEMS, LOW_OCR_CONFIDENCE |
