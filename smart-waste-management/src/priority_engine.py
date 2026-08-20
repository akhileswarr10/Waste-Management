"""
SMART WASTE MANAGEMENT
PHASE 3 - PRIORITY & DECISION ENGINE

Combines:
    1. Current bin fill
    2. Predicted 6-hour fill
    3. Overflow probability
    4. Fill growth rate

to produce:

    - Priority score (0-100)
    - Risk level
    - Recommended collection action

This module does NOT train a model.
It uses the two trained models from Phase 1 and Phase 2.
"""

import os
import joblib
import numpy as np
import pandas as pd

from preprocessing import prepare_features


# ============================================================
# CONFIGURATION
# ============================================================

DATA_DIR = "data/processed"
MODEL_DIR = "models"

TEST_FILE = os.path.join(
    DATA_DIR,
    "test.csv"
)

REGRESSION_MODEL_FILE = os.path.join(
    MODEL_DIR,
    "random_forest_waste_model.pkl"
)

REGRESSION_PREPROCESSOR_FILE = os.path.join(
    MODEL_DIR,
    "preprocessor.pkl"
)

OVERFLOW_MODEL_FILE = os.path.join(
    MODEL_DIR,
    "random_forest_overflow_model.pkl"
)

OVERFLOW_PREPROCESSOR_FILE = os.path.join(
    MODEL_DIR,
    "overflow_preprocessor.pkl"
)

OVERFLOW_THRESHOLD_FILE = os.path.join(
    MODEL_DIR,
    "overflow_threshold.txt"
)

OUTPUT_FILE = os.path.join(
    DATA_DIR,
    "priority_predictions.csv"
)


# ============================================================
# LOAD MODELS
# ============================================================

print("=" * 70)
print("SMART WASTE MANAGEMENT")
print("PHASE 3 - PRIORITY & DECISION ENGINE")
print("=" * 70)


print("\n[1/7] Loading dataset and trained models...")

data = pd.read_csv(TEST_FILE)

regression_model = joblib.load(
    REGRESSION_MODEL_FILE
)

regression_preprocessor = joblib.load(
    REGRESSION_PREPROCESSOR_FILE
)

overflow_model = joblib.load(
    OVERFLOW_MODEL_FILE
)

overflow_preprocessor = joblib.load(
    OVERFLOW_PREPROCESSOR_FILE
)

with open(OVERFLOW_THRESHOLD_FILE, "r") as f:
    overflow_threshold = float(
        f.read().strip()
    )


print(f"Dataset: {data.shape}")

print("\nModels loaded successfully.")

print(
    f"Overflow decision threshold: "
    f"{overflow_threshold:.2f}"
)


# ============================================================
# PREPARE FEATURES
# ============================================================

print("\n[2/7] Preparing features...")

X, _ = prepare_features(data)

print(
    f"Feature shape: {X.shape}"
)


# ============================================================
# REGRESSION PREDICTION
# ============================================================

print("\n[3/7] Predicting future fill level...")

X_regression = regression_preprocessor.transform(X)

predicted_fill = regression_model.predict(
    X_regression
)

# Keep predictions within meaningful operational range.
predicted_fill = np.clip(
    predicted_fill,
    0,
    120
)

print("6-hour fill predictions generated.")


# ============================================================
# OVERFLOW PREDICTION
# ============================================================

print("\n[4/7] Predicting overflow probability...")

X_overflow = overflow_preprocessor.transform(X)

overflow_probability = overflow_model.predict_proba(
    X_overflow
)[:, 1]

overflow_prediction = (
    overflow_probability >= overflow_threshold
).astype(int)

print("Overflow probabilities generated.")


# ============================================================
# BUILD DECISION FEATURES
# ============================================================

print("\n[5/7] Calculating priority factors...")

result = data[
    [
        "reading_id",
        "bin_id",
        "timestamp",
        "latitude",
        "longitude",
        "locality",
        "collection_zone",
        "area_type",
        "bin_capacity_liters",
        "sensor_fill_level_pct",
        "hours_since_collection"
    ]
].copy()


# ------------------------------------------------------------
# Model outputs
# ------------------------------------------------------------

result["predicted_fill_6h_pct"] = predicted_fill

result["overflow_probability"] = (
    overflow_probability * 100
)

result["predicted_overflow"] = (
    overflow_prediction
)


# ------------------------------------------------------------
# Fill growth
# ------------------------------------------------------------

result["predicted_fill_growth_6h_pct"] = (
    result["predicted_fill_6h_pct"]
    - result["sensor_fill_level_pct"]
)


# ------------------------------------------------------------
# Capacity status
# ------------------------------------------------------------

result["remaining_capacity_pct"] = (
    100
    - result["sensor_fill_level_pct"]
)


# ------------------------------------------------------------
# Estimated hours to full
#
# Uses current estimated rate from the dataset where
# available. If the rate is not usable, we estimate it
# from current vs predicted fill.
# ------------------------------------------------------------

current_fill = result[
    "sensor_fill_level_pct"
].to_numpy()

future_fill = result[
    "predicted_fill_6h_pct"
].to_numpy()

growth = future_fill - current_fill

estimated_rate = growth / 6

hours_to_full = np.where(
    estimated_rate > 0,
    np.maximum(
        0,
        (100 - current_fill)
        / estimated_rate
    ),
    999
)

# Already above capacity
hours_to_full[current_fill >= 100] = 0

result["estimated_hours_to_full"] = np.clip(
    hours_to_full,
    0,
    999
)


# ============================================================
# PRIORITY SCORE
# ============================================================

"""
Priority score components:

Predicted future fill       → 40 points
Overflow probability        → 35 points
Current fill                → 15 points
Future fill growth          → 10 points

Total                       → 100 points
"""


# ------------------------------------------------------------
# Component 1: Predicted fill
# ------------------------------------------------------------

predicted_fill_score = (
    np.clip(
        result["predicted_fill_6h_pct"],
        0,
        100
    ) / 100
) * 40


# ------------------------------------------------------------
# Component 2: Overflow probability
# ------------------------------------------------------------

overflow_score = (
    result["overflow_probability"]
    / 100
) * 35


# ------------------------------------------------------------
# Component 3: Current fill
# ------------------------------------------------------------

current_fill_score = (
    np.clip(
        result["sensor_fill_level_pct"],
        0,
        100
    ) / 100
) * 15


# ------------------------------------------------------------
# Component 4: Growth rate
#
# +30 percentage points over 6h = maximum growth score.
# ------------------------------------------------------------

growth_score = (
    np.clip(
        result["predicted_fill_growth_6h_pct"],
        0,
        30
    ) / 30
) * 10


# ------------------------------------------------------------
# Base priority
# ------------------------------------------------------------

result["priority_score"] = (
    predicted_fill_score
    + overflow_score
    + current_fill_score
    + growth_score
)


# ============================================================
# EMERGENCY / OVERFLOW BONUS
# ============================================================

# If the predicted fill itself crosses 100%, we want
# the system to treat it as especially urgent.

overflow_bonus = np.where(
    result["predicted_fill_6h_pct"] >= 100,
    5,
    0
)

result["priority_score"] += overflow_bonus

result["priority_score"] = np.clip(
    result["priority_score"],
    0,
    100
)

result["priority_score"] = (
    result["priority_score"]
    .round(2)
)


# ============================================================
# RISK CLASSIFICATION
# ============================================================

def determine_risk(row):

    current = row["sensor_fill_level_pct"]
    predicted = row["predicted_fill_6h_pct"]
    probability = row["overflow_probability"]

    # --------------------------------------------------------
    # Emergency
    # --------------------------------------------------------

    if (
        current >= 100
        or predicted >= 100
        or probability >= 85
    ):
        return "EMERGENCY"

    # --------------------------------------------------------
    # Critical
    # --------------------------------------------------------

    if (
        predicted >= 90
        or probability >= 62
        or current >= 90
    ):
        return "CRITICAL"

    # --------------------------------------------------------
    # High
    # --------------------------------------------------------

    if (
        predicted >= 75
        or probability >= 40
        or current >= 75
    ):
        return "HIGH"

    # --------------------------------------------------------
    # Medium
    # --------------------------------------------------------

    if (
        predicted >= 50
        or current >= 50
    ):
        return "MEDIUM"

    # --------------------------------------------------------
    # Low
    # --------------------------------------------------------

    return "LOW"


result["risk_level"] = result.apply(
    determine_risk,
    axis=1
)


# ============================================================
# COLLECTION ACTION
# ============================================================

def determine_action(row):

    risk = row["risk_level"]
    hours = row["estimated_hours_to_full"]

    if risk == "EMERGENCY":
        return "COLLECT NOW"

    if risk == "CRITICAL":
        if hours <= 6:
            return "COLLECT WITHIN 2 HOURS"

        return "PRIORITY COLLECTION"

    if risk == "HIGH":
        return "SCHEDULE NEXT ROUTE"

    if risk == "MEDIUM":
        return "MONITOR"

    return "ROUTINE COLLECTION"


result["recommended_action"] = result.apply(
    determine_action,
    axis=1
)


# ============================================================
# PRIORITY RANK
# ============================================================

result = result.sort_values(
    by="priority_score",
    ascending=False
).reset_index(drop=True)

result["priority_rank"] = (
    np.arange(len(result)) + 1
)


# ============================================================
# SUMMARY
# ============================================================

print("\n[6/7] Priority analysis completed.")

print("\n---------------------------------------------")
print("RISK DISTRIBUTION")
print("---------------------------------------------")

print(
    result["risk_level"]
    .value_counts()
    .reindex(
        [
            "EMERGENCY",
            "CRITICAL",
            "HIGH",
            "MEDIUM",
            "LOW"
        ],
        fill_value=0
    )
)


print("\n---------------------------------------------")
print("RECOMMENDED ACTIONS")
print("---------------------------------------------")

print(
    result["recommended_action"]
    .value_counts()
)


# ============================================================
# TOP PRIORITY BINS
# ============================================================

print("\n=============================================")
print("TOP 20 PRIORITY BINS")
print("=============================================")

display_columns = [
    "priority_rank",
    "bin_id",
    "timestamp",
    "area_type",
    "sensor_fill_level_pct",
    "predicted_fill_6h_pct",
    "overflow_probability",
    "predicted_fill_growth_6h_pct",
    "estimated_hours_to_full",
    "priority_score",
    "risk_level",
    "recommended_action"
]

print(
    result[
        display_columns
    ]
    .head(20)
    .to_string(index=False)
)


# ============================================================
# OVERFLOW SUMMARY
# ============================================================

print("\n---------------------------------------------")
print("OVERFLOW RISK SUMMARY")
print("---------------------------------------------")

overflow_count = (
    result["predicted_overflow"]
    .sum()
)

print(
    f"Predicted overflow bins : "
    f"{overflow_count}"
)

print(
    f"Total bins evaluated    : "
    f"{len(result)}"
)

print(
    f"Overflow percentage     : "
    f"{overflow_count / len(result) * 100:.2f}%"
)


# ============================================================
# SAVE
# ============================================================

print("\n[7/7] Saving priority results...")

result.to_csv(
    OUTPUT_FILE,
    index=False
)

print(
    f"\nSaved:\n{OUTPUT_FILE}"
)


print("\n" + "=" * 70)
print("PRIORITY ENGINE COMPLETED SUCCESSFULLY")
print("=" * 70)
