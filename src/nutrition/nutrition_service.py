"""
Smart Grocery Rescue System - Nutrition Service
Resolves grocery items against USDA preprocessed datasets.
Returns safe approximate calorie estimates with robust fallbacks.
"""

import os
from pathlib import Path
from typing import Dict, Optional, Tuple
import pandas as pd

# Hardcoded reference fallbacks (approximate kcal per 100g edible portion)
# Sourced from USDA National Nutrient Database references for common household staples
FALLBACK_NUTRITION_LOOKUP: Dict[str, float] = {
    "apple": 52.0,
    "banana": 89.0,
    "orange": 47.0,
    "mango": 60.0,
    "grape": 69.0,
    "watermelon": 30.0,
    "pineapple": 50.0,
    "strawberry": 33.0,
    "lemon": 29.0,
    "papaya": 43.0,
    "tomato": 18.0,
    "potato": 77.0,
    "onion": 40.0,
    "carrot": 41.0,
    "spinach": 23.0,
    "cabbage": 25.0,
    "cucumber": 15.0,
    "broccoli": 34.0,
    "cauliflower": 25.0,
    "garlic": 149.0,
    "ginger": 80.0,
    "milk": 61.0,
    "cheese": 402.0,
    "butter": 717.0,
    "yogurt": 59.0,
    "curd": 60.0,
    "egg": 143.0,
    "chicken": 165.0,
    "fish": 206.0,
    "bread": 265.0,
    "rice": 130.0,
    "flour": 364.0,
    "pasta": 131.0,
    "pepsi": 43.0,
    "soda": 40.0,
    "oil": 884.0,
    "salt": 0.0,
    "sugar": 387.0,
    "honey": 304.0,
    "chocolate": 546.0,
}

# Explicit food alias mapping to USDA standard keywords
USDA_ALIAS_INDEX: Dict[str, str] = {
    "whole milk gal": "milk",
    "pc large eggs": "egg",
    "wheat bread": "bread",
    "bananas": "banana",
    "green beans": "beans",
    "dry fruit": "nut",
}


class NutritionService:
    """Manages USDA nutrition data loading, alias matching, and fallback lookup."""

    def __init__(self, data_path: Optional[str] = None):
        if data_path:
            self.csv_path = Path(data_path)
        else:
            base_dir = Path(__file__).resolve().parent.parent.parent
            self.csv_path = base_dir / "data" / "processed" / "nutrition_processed.csv"

        self.nutrition_df: Optional[pd.DataFrame] = None
        self._load_nutrition_data()

    def _load_nutrition_data(self) -> None:
        """Loads USDA processed dataset safely."""
        if self.csv_path.exists():
            try:
                self.nutrition_df = pd.read_csv(self.csv_path)
                # Ensure columns match expected structure
                self.nutrition_df["description_clean"] = (
                    self.nutrition_df["description"].astype(str).str.lower()
                )
            except Exception:
                self.nutrition_df = None
        else:
            self.nutrition_df = None

    def get_nutrition_estimate(self, raw_food_name: str) -> Dict[str, any]:
        """
        Attempts to resolve approximate calories via USDA dataset first,
        then via standard fallback lookup table.
        """
        cleaned_food = str(raw_food_name).strip().lower()

        # Handle alias substitution
        target_name = USDA_ALIAS_INDEX.get(cleaned_food, cleaned_food)

        # 1. Attempt lookup in processed USDA dataframe
        if self.nutrition_df is not None and not self.nutrition_df.empty:
            match = self.nutrition_df[
                self.nutrition_df["description_clean"].str.contains(r"\b" + target_name + r"\b", regex=True, na=False)
            ]
            if not match.empty:
                val = match.iloc[0]["calories"]
                try:
                    cal_float = round(float(val), 1)
                    return {
                        "food": raw_food_name,
                        "matched_ingredient": target_name,
                        "approx_calories_100g": cal_float,
                        "source": "USDA Foundation Foods",
                        "available": True,
                    }
                except (ValueError, TypeError):
                    pass

        # 2. Check Static Fallback Catalog
        for key, val in FALLBACK_NUTRITION_LOOKUP.items():
            if key in target_name or target_name in key:
                return {
                    "food": raw_food_name,
                    "matched_ingredient": key,
                    "approx_calories_100g": round(val, 1),
                    "source": "Verified Standard Reference",
                    "available": True,
                }

        # 3. Graceful Missing Return
        return {
            "food": raw_food_name,
            "matched_ingredient": None,
            "approx_calories_100g": None,
            "source": "Not Available",
            "available": False,
        }

    def compute_recipe_calories(self, ingredients: list) -> Tuple[Optional[float], int]:
        """
        Sums known baseline calories across ingredient list.
        Returns total estimated calories and the count of resolved ingredients.
        """
        total_calories = 0.0
        resolved_count = 0

        for ing in ingredients:
            res = self.get_nutrition_estimate(ing)
            if res["available"] and res["approx_calories_100g"] is not None:
                total_calories += res["approx_calories_100g"]
                resolved_count += 1

        if resolved_count == 0:
            return None, 0

        return round(total_calories, 1), resolved_count