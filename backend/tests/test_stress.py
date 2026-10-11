import random

from scripts.validator_stress import (
    CAUGHT_BY_DESIGN,
    error_codes,
    run_group,
)

GOOD = {
    "vendor_name": "KARTHIK MESS",
    "gstin": "33BECPS1148N1ZB",
    "invoice_number": "501",
    "invoice_date": "2026-01-15",
    "line_items": [
        {"description": "Meals", "quantity": "3", "rate": "47.62", "amount": "142.86"},
        {"description": "Tea", "quantity": "4", "rate": "14.29", "amount": "57.16"},
        {"description": "Curry", "quantity": "2", "rate": "76.19", "amount": "152.38"},
    ],
    "subtotal": "352.40",
    "cgst": "8.81",
    "sgst": "8.81",
    "igst": None,
    "round_off": "-0.02",
    "total": "370.00",
}


def test_a_correct_invoice_raises_no_error_flags():
    assert error_codes(GOOD) == set()


def test_gstin_misreads_and_lost_decimal_points_are_always_caught():
    wanted = {
        label: mutation
        for label, mutation in CAUGHT_BY_DESIGN.items()
        if label.startswith("GSTIN: any single") or label.startswith("Money: decimal point")
    }
    assert len(wanted) == 2
    rows = run_group(wanted, [("good", GOOD)], trials=30, rng=random.Random(1))
    for label, tried, caught in rows:
        assert tried > 0, label
        assert caught == tried, label