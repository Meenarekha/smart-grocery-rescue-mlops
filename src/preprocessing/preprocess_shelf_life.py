import pandas as pd
from pathlib import Path


# Project paths
RAW_DIR = Path("data/raw")
PROCESSED_DIR = Path("data/processed")

# Create processed folder if needed
PROCESSED_DIR.mkdir(parents=True, exist_ok=True)


# Load shelf-life dataset
shelf_life_df = pd.read_csv(
    RAW_DIR / "food_shelf_life.csv"
)


# Clean column names
shelf_life_df.columns = shelf_life_df.columns.str.strip().str.lower()


# Remove duplicate food names
shelf_life_df = shelf_life_df.drop_duplicates(
    subset="food"
)


# Remove rows with missing values
shelf_life_df = shelf_life_df.dropna(
    subset=["food", "shelf_life_days", "storage"]
)


# Standardize food names
shelf_life_df["food"] = (
    shelf_life_df["food"]
    .str.strip()
    .str.lower()
)


# Save processed dataset
output_path = PROCESSED_DIR / "shelf_life_processed.csv"

shelf_life_df.to_csv(
    output_path,
    index=False
)


print("Shelf-life preprocessing completed.")
print("Shape:", shelf_life_df.shape)
print("Saved to:", output_path)
print("\nProcessed data:")
print(shelf_life_df)