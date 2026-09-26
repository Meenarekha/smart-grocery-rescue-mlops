import pandas as pd
from pathlib import Path


# Project paths
RAW_DIR = Path("data/raw")
PROCESSED_DIR = Path("data/processed")

# Create processed folder if needed
PROCESSED_DIR.mkdir(parents=True, exist_ok=True)


# Load food information
food_df = pd.read_csv(
    RAW_DIR / "food.csv",
    low_memory=False
)

# Load nutrient information
nutrient_df = pd.read_csv(
    RAW_DIR / "food_nutrient.csv",
    low_memory=False
)


# Keep only the columns we need from food.csv
food_df = food_df[
    ["fdc_id", "description"]
].copy()


# Keep only Energy records
# USDA nutrient ID 1008 = Energy (kcal)
energy_df = nutrient_df[
    nutrient_df["nutrient_id"] == 1008
].copy()


# Keep required nutrient columns
energy_df = energy_df[
    ["fdc_id", "amount"]
].copy()


# Rename amount to calories
energy_df.rename(
    columns={"amount": "calories"},
    inplace=True
)


# Join food names with calorie information
nutrition_df = pd.merge(
    food_df,
    energy_df,
    on="fdc_id",
    how="inner"
)


# Remove duplicate food records
nutrition_df = nutrition_df.drop_duplicates(
    subset="fdc_id"
)


# Save processed nutrition dataset
output_path = PROCESSED_DIR / "nutrition_processed.csv"

nutrition_df.to_csv(
    output_path,
    index=False
)


print("Nutrition preprocessing completed.")
print("Shape:", nutrition_df.shape)
print("Saved to:", output_path)
print("\nSample:")
print(nutrition_df.head())