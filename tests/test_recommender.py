from src.recommendation.recipe_recommender import RecipeRecommender
import pandas as pd

def test_recommender_scoring(tmp_path):
    csv_file = tmp_path / "recipes.csv"
    mock_recipes = pd.DataFrame([
        {"id": 1, "cuisine": "mexican", "ingredients": str(["tomato", "onion", "cheese"])},
        {"id": 2, "cuisine": "bakery", "ingredients": str(["flour", "sugar"])}
    ])
    mock_recipes.to_csv(csv_file, index=False)
    
    recommender = RecipeRecommender(recipes_csv_path=str(csv_file))
    
    active_inv = [
        {"food": "tomato", "standard_food": "tomato", "expiry_date": "30/12/2026"},
        {"food": "onion", "standard_food": "onion", "expiry_date": "30/12/2026"}
    ]
    
    recs = recommender.recommend(active_inv, top_k=1)
    assert len(recs) == 1
    assert recs[0]["id"] == 1
    assert "tomato" in recs[0]["matched_ingredients"]