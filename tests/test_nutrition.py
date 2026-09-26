from src.nutrition.nutrition_service import NutritionService

def test_nutrition_lookup_fallback():
    service = NutritionService(data_path="non_existent.csv")
    res = service.get_nutrition_estimate("banana")
    assert res["available"] is True
    assert res["approx_calories_100g"] == 89.0
    assert res["matched_ingredient"] == "banana"

def test_nutrition_lookup_unknown():
    service = NutritionService(data_path="non_existent.csv")
    res = service.get_nutrition_estimate("unknown_synthetic_food_item")
    assert res["available"] is False
    assert res["approx_calories_100g"] is None