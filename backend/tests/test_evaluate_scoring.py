from scripts.evaluate import same, same_number, score_items


def test_numbers_are_compared_by_value_and_text_by_exact_words():
    assert same("total", "370", "370.00")
    assert same("total", None, None)
    assert not same("total", None, "370.00")
    assert same("vendor_name", "karthik   mess", "KARTHIK MESS")
    assert not same("vendor_name", "KA RTHIK MESS", "KARTHIK MESS")
    assert not same_number("abc", "1")


def test_line_items_are_scored_by_position():
    truth = [
        {"description": "Tea", "quantity": "2", "rate": "10.00", "amount": "20.00"},
        {"description": "Coffee", "quantity": "1", "rate": "15.00", "amount": "15.00"},
    ]
    got = [
        {"description": "Tea", "quantity": "2.000", "rate": "10.00", "amount": "20.00"},
        {"description": "Cofee", "quantity": None, "rate": "15.00", "amount": "51.00"},
    ]
    scores = score_items(got, truth)
    assert scores["amount"] == [1, 2]
    assert scores["quantity"] == [1, 2]
    assert scores["rate"] == [2, 2]
    assert scores["description"] == [2, 2]   # "Cofee" is close enough to "Coffee"


def test_missing_items_count_as_wrong():
    truth = [{"description": "Tea", "quantity": "1", "rate": "5.00", "amount": "5.00"}]
    scores = score_items([], truth)
    assert scores["amount"] == [0, 1]
    assert scores["description"] == [0, 1]