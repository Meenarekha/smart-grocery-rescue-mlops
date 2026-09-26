import os
import re
import pandas as pd
from datetime import timedelta


# ============================================================
# PROJECT PATH
# ============================================================

PROJECT_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "../..")
)

SHELF_LIFE_FILE = os.path.join(
    PROJECT_ROOT,
    "data",
    "processed",
    "shelf_life_processed.csv"
)


# ============================================================
# LOAD DATA
# ============================================================

def load_shelf_life_data():
    return pd.read_csv(SHELF_LIFE_FILE)


# ============================================================
# NORMALIZE GROCERY NAME
# ============================================================

def normalize_food_name(food_name):
    """
    Convert receipt-style product names into
    standard grocery names.
    """

    name = str(food_name).lower().strip()

    # Remove common product/package information
    name = re.sub(
        r"\b\d+\s*(ct|pk|pack|pcs|lb|kg|oz|gal)\b",
        "",
        name,
        flags=re.IGNORECASE
    )

    # Remove standalone package/unit words
    name = re.sub(
        r"\b(ct|pk|pack|pcs|lb|kg|oz|gal)\b",
        "",
        name,
        flags=re.IGNORECASE
    )

    # Remove common product codes such as M32
    name = re.sub(
        r"\b[a-z]\d+\b",
        "",
        name,
        flags=re.IGNORECASE
    )

    # Product-specific/general receipt words
    words_to_remove = [
        "whole",
        "large",
        "small",
        "medium",
        "fresh",
        "organic",
        "premium",
        "wheat",
        "white",
        "natural",
        "reduced",
        "fat",
        "low",
        "free",
        "brand"
    ]

    words = name.split()

    words = [
        word
        for word in words
        if word not in words_to_remove
    ]

    name = " ".join(words)

    return name.strip()


# ============================================================
# GET SHELF LIFE
# ============================================================

def get_shelf_life(food_name):

    df = load_shelf_life_data()

    original_name = str(food_name).lower().strip()

    normalized_name = normalize_food_name(
        original_name
    )

    # --------------------------------------------------------
    # Exact match
    # --------------------------------------------------------

    exact_match = df[
        df["food"] == normalized_name
    ]

    if not exact_match.empty:

        row = exact_match.iloc[0]

        return {
            "food": row["food"],
            "shelf_life_days": int(
                row["shelf_life_days"]
            ),
            "storage": row["storage"]
        }

    # --------------------------------------------------------
    # Match individual food names
    # --------------------------------------------------------

    for food in df["food"]:

        if food in normalized_name:

            row = df[
                df["food"] == food
            ].iloc[0]

            return {
                "food": row["food"],
                "shelf_life_days": int(
                    row["shelf_life_days"]
                ),
                "storage": row["storage"]
            }

    # --------------------------------------------------------
    # Original-name partial match
    # --------------------------------------------------------

    for food in df["food"]:

        if food in original_name:

            row = df[
                df["food"] == food
            ].iloc[0]

            return {
                "food": row["food"],
                "shelf_life_days": int(
                    row["shelf_life_days"]
                ),
                "storage": row["storage"]
            }

    return None


# ============================================================
# CALCULATE EXPIRY
# ============================================================

def calculate_expiry_date(
    purchase_date,
    shelf_life_days
):

    return purchase_date + timedelta(
        days=shelf_life_days
    )


# ============================================================
# MANUAL TEST
# ============================================================

if __name__ == "__main__":

    test_items = [
        "banana",
        "WHOLE MILK GAL",
        "PC LARGE EGGS",
        "M32 WHEAT BREAD",
        "PEPSI",
        "fresh tomato",
        "organic apple",
        "large chicken"
    ]

    print("\nGeneric Shelf-Life Lookup")
    print("=" * 60)

    for item in test_items:

        result = get_shelf_life(item)

        print(f"\n{item}")

        if result:

            print(
                f"  Standard Name : {result['food']}"
            )

            print(
                f"  Shelf Life    : "
                f"{result['shelf_life_days']} days"
            )

            print(
                f"  Storage       : "
                f"{result['storage']}"
            )

        else:

            print(
                "  Shelf-life information not available"
            )