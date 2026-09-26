"""
Smart Grocery Rescue System - Recipe Feedback Manager
Maintains user engagement signals in JSON storage and computes adaptive rank modifiers.
"""

import json
from pathlib import Path
from typing import Dict, Any


class FeedbackManager:
    """Loads, updates, and extracts ranking weights from local feedback logs."""

    def __init__(self, feedback_path: str = None):
        if feedback_path:
            self.file_path = Path(feedback_path)
        else:
            base_dir = Path(__file__).resolve().parent.parent.parent
            self.file_path = base_dir / "data" / "app" / "recipe_feedback.json"

        self.file_path.parent.mkdir(parents=True, exist_ok=True)
        if not self.file_path.exists():
            self._save_payload({"recipes": {}, "cuisines": {}})

    def _load_payload(self) -> Dict[str, Any]:
        try:
            with open(self.file_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {"recipes": {}, "cuisines": {}}

    def _save_payload(self, data: Dict[str, Any]) -> None:
        with open(self.file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

    def record_feedback(self, recipe_id: int, cuisine: str, feedback_type: str) -> None:
        """
        Records user interaction:
        feedback_type in ['like', 'dislike', 'cooked']
        """
        payload = self._load_payload()
        r_str = str(recipe_id)

        if r_str not in payload["recipes"]:
            payload["recipes"][r_str] = {"like": 0, "dislike": 0, "cooked": 0}

        if cuisine not in payload["cuisines"]:
            payload["cuisines"][cuisine] = {"like": 0, "dislike": 0, "cooked": 0}

        if feedback_type in ["like", "dislike", "cooked"]:
            payload["recipes"][r_str][feedback_type] += 1
            payload["cuisines"][cuisine][feedback_type] += 1

        self._save_payload(payload)

    def get_score_modifier(self, recipe_id: int, cuisine: str) -> float:
        """
        Computes ranking score adjustment based on past recipe ratings and cuisine affinity.
        """
        payload = self._load_payload()
        modifier = 0.0

        # Recipe-level feedback
        r_entry = payload.get("recipes", {}).get(str(recipe_id))
        if r_entry:
            modifier += r_entry.get("like", 0) * 1.5
            modifier += r_entry.get("cooked", 0) * 3.0
            modifier -= r_entry.get("dislike", 0) * 3.0

        # Cuisine-level affinity
        c_entry = payload.get("cuisines", {}).get(cuisine)
        if c_entry:
            modifier += c_entry.get("like", 0) * 0.5
            modifier += c_entry.get("cooked", 0) * 1.0
            modifier -= c_entry.get("dislike", 0) * 1.0

        return modifier