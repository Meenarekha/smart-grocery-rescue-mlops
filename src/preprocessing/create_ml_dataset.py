import pandas as pd
import numpy as np
from pathlib import Path


# Project paths
PROCESSED_DIR = Path("data/processed")
ML_DIR = Path("data/ml")

ML_DIR.mkdir(parents=True, exist_ok=True)


# Load shelf-life data
shelf_life_df = pd.read_csv(
    PROCESSED_DIR / "shelf_life_processed.csv"
)


# Make results reproducible
np.random.seed(42)


# Number of training samples
N = 2000


# Randomly select food items
food_data = shelf_life_df.sample(
    n=N,
    replace=True,
    random_state=42
).reset_index(drop=True)


# Generate realistic project features
food_data["quantity"] = np.random.randint(1, 6, N)

food_data["days_since_purchase"] = np.random.randint(
    0,
    food_data["shelf_life_days"].max() + 1,
    N
)

food_data["usage_frequency"] = np.random.randint(
    0,
    6,
    N
)

food_data["previous_unused_count"] = np.random.randint(
    0,
    4,
    N
)


# Calculate how much of the shelf life has been consumed
food_data["shelf_life_usage_ratio"] = (
    food_data["days_since_purchase"]
    / food_data["shelf_life_days"]
)


# Create a risk score
risk_score = (
    food_data["shelf_life_usage_ratio"] * 0.50
    + (food_data["quantity"] / 5) * 0.15
    + (1 - food_data["usage_frequency"] / 5) * 0.20
    + (food_data["previous_unused_count"] / 3) * 0.15
)


# Convert score into risk classes
food_data["waste_risk"] = pd.cut(
    risk_score,
    bins=[-np.inf, 0.35, 0.65, np.inf],
    labels=["LOW", "MEDIUM", "HIGH"]
)


# Select final features
final_df = food_data[
    [
        "food",
        "shelf_life_days",
        "storage",
        "quantity",
        "days_since_purchase",
        "usage_frequency",
        "previous_unused_count",
        "shelf_life_usage_ratio",
        "waste_risk"
    ]
]


# Save ML dataset
output_path = ML_DIR / "waste_risk_dataset.csv"

final_df.to_csv(
    output_path,
    index=False
)


print("Waste-risk ML dataset created.")
print("Shape:", final_df.shape)
print("Saved to:", output_path)

print("\nRisk distribution:")
print(final_df["waste_risk"].value_counts())

print("\nSample:")
print(final_df.head())