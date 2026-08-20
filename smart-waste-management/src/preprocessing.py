import pandas as pd
import numpy as np

from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import OneHotEncoder
from sklearn.pipeline import Pipeline


# ============================================================
# CONFIGURATION
# ============================================================

TARGET = "target_fill_level_6h_pct"


# Features that should NOT be given to the model
# because they are IDs, raw timestamps, or future information.
DROP_COLUMNS = [
    "reading_id",
    "bin_id",
    "timestamp",

    # Future targets - DATA LEAKAGE
    "target_fill_level_3h_pct",
    "target_fill_level_6h_pct",
    "target_fill_level_12h_pct",
    "target_fill_level_24h_pct",
    "target_overflow_6h",
]


# ============================================================
# FEATURE LIST
# ============================================================

NUMERICAL_FEATURES = [
    "latitude",
    "longitude",

    "bin_capacity_liters",
    "demand_multiplier",

    "sensor_fill_level_pct",
    "hours_since_collection",

    "temperature_c",
    "humidity_pct",
    "rainfall_mm",

    "is_holiday",
    "local_event",
    "sensor_anomaly",

    "previous_fill_1h_pct",
    "previous_fill_2h_pct",
    "previous_fill_3h_pct",
    "previous_fill_6h_pct",
    "previous_fill_12h_pct",
    "previous_fill_24h_pct",

    "fill_change_1h_pct",
    "fill_change_6h_pct",

    "fill_rate_1h_pct_per_hour",
    "fill_rate_6h_pct_per_hour",

    "avg_fill_6h_pct",
    "avg_fill_24h_pct",
    "avg_fill_7d_pct",

    "max_fill_24h_pct",
    "collection_count_7d",

    "day_of_week",
    "day_of_month",
    "month",
    "week_of_year",
    "hour",

    "is_weekend",
    "is_night",

    "hour_sin",
    "hour_cos",

    "dow_sin",
    "dow_cos",

    "month_sin",
    "month_cos",

    "historical_avg_fill_pct",
    "historical_max_fill_pct",

    "capacity_remaining_pct",

    "fill_rate_24h_est_pct_per_hour",

    "estimated_hours_to_full",
]


CATEGORICAL_FEATURES = [
    "locality",
    "collection_zone",
    "area_type",
    "bin_type",
    "service_window",
    "weather_condition",
    "global_event",
]


# ============================================================
# PREPROCESSOR
# ============================================================

def create_preprocessor():

    # Numerical columns:
    # Replace missing numerical values with the median.
    numerical_pipeline = Pipeline(
        steps=[
            (
                "imputer",
                SimpleImputer(strategy="median")
            )
        ]
    )

    # Categorical columns:
    # 1. Fill missing categories
    # 2. Convert categories into numerical columns
    try:
        encoder = OneHotEncoder(
            handle_unknown="ignore",
            sparse_output=True
        )
    except TypeError:
        # For older versions of scikit-learn
        encoder = OneHotEncoder(
            handle_unknown="ignore",
            sparse=True
        )

    categorical_pipeline = Pipeline(
        steps=[
            (
                "imputer",
                SimpleImputer(strategy="most_frequent")
            ),
            (
                "encoder",
                encoder
            )
        ]
    )

    # Combine numerical and categorical preprocessing
    preprocessor = ColumnTransformer(
        transformers=[
            (
                "numerical",
                numerical_pipeline,
                NUMERICAL_FEATURES
            ),
            (
                "categorical",
                categorical_pipeline,
                CATEGORICAL_FEATURES
            )
        ]
    )

    return preprocessor


# ============================================================
# LOAD DATA
# ============================================================

def load_datasets():

    train = pd.read_csv(
        "data/processed/train.csv"
    )

    validation = pd.read_csv(
        "data/processed/validation.csv"
    )

    test = pd.read_csv(
        "data/processed/test.csv"
    )

    return train, validation, test


# ============================================================
# PREPARE X AND Y
# ============================================================

def prepare_features(df):

    X = df.drop(
        columns=DROP_COLUMNS,
        errors="ignore"
    )

    y = df[TARGET].copy()

    return X, y


# ============================================================
# MAIN TEST
# ============================================================

if __name__ == "__main__":

    print("=" * 60)
    print("SMART WASTE MANAGEMENT")
    print("PREPROCESSING TEST")
    print("=" * 60)

    train, validation, test = load_datasets()

    print("\nDataset sizes:")
    print("Train:", train.shape)
    print("Validation:", validation.shape)
    print("Test:", test.shape)

    X_train, y_train = prepare_features(train)
    X_val, y_val = prepare_features(validation)
    X_test, y_test = prepare_features(test)

    print("\nFeature shapes before preprocessing:")
    print("X_train:", X_train.shape)
    print("X_validation:", X_val.shape)
    print("X_test:", X_test.shape)

    print("\nTarget:")
    print("y_train:", y_train.shape)
    print("y_validation:", y_val.shape)
    print("y_test:", y_test.shape)

    print("\nCreating preprocessing pipeline...")

    preprocessor = create_preprocessor()

    X_train_processed = preprocessor.fit_transform(X_train)

    X_val_processed = preprocessor.transform(X_val)

    X_test_processed = preprocessor.transform(X_test)

    print("\nFeature shapes after preprocessing:")
    print("X_train:", X_train_processed.shape)
    print("X_validation:", X_val_processed.shape)
    print("X_test:", X_test_processed.shape)

    print("\nPreprocessing completed successfully!")

