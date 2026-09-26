import json
import pandas as pd
from pathlib import Path


# Project paths
RAW_DIR = Path("data/raw")
PROCESSED_DIR = Path("data/processed")


# Create processed-data folder automatically
PROCESSED_DIR.mkdir(parents=True, exist_ok=True)


# Load recipe dataset
with open(RAW_DIR / "train.json", "r", encoding="utf-8") as file:
    recipes = json.load(file)


# Convert JSON to DataFrame
recipe_df = pd.DataFrame(recipes)


# Keep required columns
recipe_df = recipe_df[["id", "cuisine", "ingredients"]]


# Convert ingredient list into searchable text
recipe_df["ingredients"] = recipe_df["ingredients"].apply(
    lambda ingredients: ", ".join(ingredients)
)


# Remove duplicate recipes
recipe_df = recipe_df.drop_duplicates(subset="id")


# Save processed dataset
output_path = PROCESSED_DIR / "recipes_processed.csv"
recipe_df.to_csv(output_path, index=False)


print("Recipe preprocessing completed.")
print("Shape:", recipe_df.shape)
print("Saved to:", output_path)
print("\nSample:")
print(recipe_df.head())