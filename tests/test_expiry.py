from datetime import datetime

from src.expiry.shelf_life import (
    normalize_food_name,
    get_shelf_life,
    calculate_expiry_date,
)


def test_shelf_life_calculations():

    # Normalization
    assert normalize_food_name("WHOLE MILK GAL") == "milk"
    assert normalize_food_name("PC LARGE EGGS") == "pc eggs"
    assert normalize_food_name("WHEAT BREAD") == "bread"

    # Shelf-life lookup
    result = get_shelf_life("WHOLE MILK GAL")

    assert result is not None
    assert result["food"] == "milk"
    assert result["shelf_life_days"] == 5
    assert result["storage"] == "refrigerator"

    # Expiry-date calculation
    purchase_date = datetime(2026, 3, 15)

    expiry_date = calculate_expiry_date(
        purchase_date,
        result["shelf_life_days"]
    )

    assert expiry_date == datetime(2026, 3, 20)