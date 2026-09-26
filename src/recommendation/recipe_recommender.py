"""
Smart Grocery Rescue System - Recipe Recommender Engine
Includes alias matching, expiry urgency scoring, and user feedback adjustments.
"""

from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any
import ast
import pandas as pd

from src.feedback.feedback_manager import FeedbackManager

GROCERY_ALIASES = {
    "whole milk gal": "milk",
    "pc large eggs": "egg",
    "wheat bread": "bread",
    "bananas": "banana",
    "pepsi": "soda",
    "organic apple": "apple",
    "fresh tomato": "tomato",
}


class RecipeRecommender:
    def __init__(self, recipes_csv_path: str = None):
        if recipes_csv_path:
            self.csv_path = Path(recipes_csv_path)
        else:
            base_dir = Path(__file__).resolve().parent.parent.parent
            self.csv_path = base_dir / "data" / "processed" / "recipes_processed.csv"

        self.df = None
        self.feedback_manager = FeedbackManager()
        self._load_recipes()

    def _load_recipes(self):
        if self.csv_path.exists():
            self.df = pd.read_csv(self.csv_path)
            # Evaluate ingredients column safely into list
            if "ingredients" in self.df.columns and isinstance(self.df["ingredients"].iloc[0], str):
                self.df["ingredients"] = self.df["ingredients"].apply(self._parse_ingredients)
        else:
            self.df = pd.DataFrame(columns=["id", "cuisine", "ingredients"])

    @staticmethod
    def _parse_ingredients(val):
        try:
            return ast.literal_eval(val)
        except Exception:
            return [x.strip() for x in str(val).replace("[", "").replace("]", "").replace("'", "").split(",")]

    def recommend(self, active_groceries: List[Dict[str, Any]], top_k: int = 5) -> List[Dict[str, Any]]:
        """
        Ranks recipes using coverage, expiry urgency, and feedback modifiers.
        """
        if self.df is None or self.df.empty or not active_groceries:
            return []

        # Prepare normalized active inventory items and urgency weights
        now_dt = datetime.now()
        inventory_items = {}

        for item in active_groceries:
            std_name = item.get("standard_food", item.get("food", "")).lower().strip()
            std_name = GROCERY_ALIASES.get(std_name, std_name)

            # Calculate days left until expiry
            days_left = 99
            exp_str = item.get("expiry_date", "")
            try:
                exp_dt = datetime.strptime(exp_str, "%d/%m/%Y")
                days_left = (exp_dt.date() - now_dt.date()).days
            except Exception:
                pass

            inventory_items[std_name] = min(inventory_items.get(std_name, 99), days_left)

        scored_recipes = []

        for _, row in self.df.iterrows():
            r_id = int(row["id"])
            cuisine = str(row["cuisine"])
            r_ings = [str(x).lower().strip() for x in row["ingredients"]]
            if not r_ings:
                continue

            matched = []
            missing = []
            urgency_score = 0.0

            for ing in r_ings:
                # Substring/equality matching against available groceries
                match_found = False
                for g_item, d_left in inventory_items.items():
                    if g_item in ing or ing in g_item:
                        matched.append(ing)
                        match_found = True
                        if 0 <= d_left <= 2:
                            urgency_score += 10.0
                        elif 3 <= d_left <= 5:
                            urgency_score += 5.0
                        break
                if not match_found:
                    missing.append(ing)

            matched_count = len(matched)
            if matched_count == 0:
                continue

            total_recipe_ings = len(r_ings)
            coverage = matched_count / total_recipe_ings

            # Feedback ranking adjustment
            feedback_boost = self.feedback_manager.get_score_modifier(r_id, cuisine)

            total_score = (coverage * 70.0) + (matched_count * 5.0) + urgency_score + feedback_boost

            scored_recipes.append({
                "id": r_id,
                "cuisine": cuisine,
                "match_percentage": round(coverage * 100, 1),
                "matched_ingredients": matched,
                "missing_ingredients": missing,
                "recommendation_score": round(total_score, 2),
                "urgency_bonus": round(urgency_score, 1),
                "feedback_bonus": round(feedback_boost, 1)
            })

        # Sort recipes by total score in descending order
        scored_recipes.sort(key=lambda x: x["recommendation_score"], reverse=True)
        return scored_recipes[:top_k]