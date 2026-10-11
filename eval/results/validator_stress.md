# Validator stress test (2026-10-11)

Clean bills used: 7. Random variants per bill and mistake type: 20. Seed: 42.
Clean bills that raised an error-level flag (false alarms): 0 of 7

## Mistakes the validators are designed to catch

| Mistake injected | Trials | Caught | Rate |
|---|---:|---:|---:|
| GSTIN: letter/digit confusion (O/0, I/1, S/5, B/8, Z/2) | 140 | 140 | 100% |
| GSTIN: any single character misread | 140 | 140 | 100% |
| Money: decimal point lost (8.81 -> 881) | 140 | 140 | 100% |
| Money: two adjacent digits swapped | 140 | 138 | 99% |
| Money: a digit lost | 99 | 92 | 93% |
| Money: an extra digit added | 136 | 110 | 81% |
| Money: any single digit misread | 140 | 111 | 79% |
| Quantity: a digit misread | 20 | 20 | 100% |
| Date: year digits transposed (2026 -> 2062) | 140 | 140 | 100% |

Overall: 1031 of 1095 injected mistakes caught (94%).

## Controls: mistakes that no arithmetic check can notice

| Mistake injected | Trials | Caught | Rate |
|---|---:|---:|---:|
| Control: date year off by one (still plausible) | 140 | 0 | 0% |
| Control: typo in the vendor name | 140 | 0 | 0% |
| Control: a digit of the invoice number misread | 140 | 0 | 0% |
