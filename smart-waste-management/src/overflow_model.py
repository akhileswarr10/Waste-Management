"""
SMART WASTE MANAGEMENT
PHASE 2 - OVERFLOW RISK CLASSIFICATION

Predicts whether a bin is likely to naturally reach/exceed
100% fill within the next 6 hours.

IMPORTANT:
Target columns are NEVER used as input features.
"""

import os
import joblib
import numpy as np
import pandas as pd

from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    roc_auc_score,
    confusion_matrix,
    classification_report
)

from preprocessing import prepare_features, create_preprocessor


# ============================================================
# CONFIGURATION
# ============================================================

DATA_DIR = "data/processed"
MODEL_DIR = "models"

TRAIN_FILE = os.path.join(DATA_DIR, "train.csv")
VAL_FILE = os.path.join(DATA_DIR, "validation.csv")
TEST_FILE = os.path.join(DATA_DIR, "test.csv")

MODEL_FILE = os.path.join(
    MODEL_DIR,
    "random_forest_overflow_model.pkl"
)

PREPROCESSOR_FILE = os.path.join(
    MODEL_DIR,
    "overflow_preprocessor.pkl"
)


TARGET = "target_overflow_6h"

# These must NEVER become input features.
TARGET_COLUMNS = [
    "target_fill_level_3h_pct",
    "target_fill_level_6h_pct",
    "target_fill_level_12h_pct",
    "target_fill_level_24h_pct",
    "target_overflow_6h"
]


# ============================================================
# LOAD DATA
# ============================================================

print("=" * 70)
print("SMART WASTE MANAGEMENT")
print("OVERFLOW RISK CLASSIFICATION MODEL")
print("=" * 70)

print("\n[1/7] Loading datasets...")

train = pd.read_csv(TRAIN_FILE)
validation = pd.read_csv(VAL_FILE)
test = pd.read_csv(TEST_FILE)

print(f"Train      : {train.shape}")
print(f"Validation : {validation.shape}")
print(f"Test       : {test.shape}")


# ============================================================
# PREPARE FEATURES
# ============================================================

print("\n[2/7] Preparing features...")

X_train, _ = prepare_features(train)
X_val, _ = prepare_features(validation)
X_test, _ = prepare_features(test)

y_train = train[TARGET].astype(int)
y_val = validation[TARGET].astype(int)
y_test = test[TARGET].astype(int)

print(f"X_train : {X_train.shape}")
print(f"X_val   : {X_val.shape}")
print(f"X_test  : {X_test.shape}")

print("\nOverflow class distribution:")

print("\nTRAIN:")
print(y_train.value_counts())
print(y_train.value_counts(normalize=True) * 100)

print("\nVALIDATION:")
print(y_val.value_counts())
print(y_val.value_counts(normalize=True) * 100)

print("\nTEST:")
print(y_test.value_counts())
print(y_test.value_counts(normalize=True) * 100)


# ============================================================
# PREPROCESSING
# ============================================================

print("\n[3/7] Preprocessing data...")

preprocessor = create_preprocessor()

X_train_processed = preprocessor.fit_transform(X_train)
X_val_processed = preprocessor.transform(X_val)
X_test_processed = preprocessor.transform(X_test)

print(f"Processed X_train: {X_train_processed.shape}")
print(f"Processed X_val  : {X_val_processed.shape}")
print(f"Processed X_test : {X_test_processed.shape}")


# ============================================================
# TRAIN CLASSIFIER
# ============================================================

print("\n[4/7] Training Random Forest classifier...")

model = RandomForestClassifier(
    n_estimators=300,
    max_depth=18,
    min_samples_leaf=2,
    class_weight="balanced",
    random_state=42,
    n_jobs=-1
)

model.fit(X_train_processed, y_train)

print("Overflow classifier training completed!")


# ============================================================
# VALIDATION PROBABILITIES
# ============================================================

print("\n[5/7] Finding decision threshold...")

val_probabilities = model.predict_proba(
    X_val_processed
)[:, 1]


# ------------------------------------------------------------
# Find a threshold that strongly protects against
# false negatives.
#
# We prefer recall >= 95% where possible.
# Among those thresholds, choose the one with
# highest F1 score.
# ------------------------------------------------------------

threshold_results = []

for threshold in np.arange(0.05, 0.96, 0.01):

    predictions = (
        val_probabilities >= threshold
    ).astype(int)

    recall = recall_score(
        y_val,
        predictions,
        zero_division=0
    )

    precision = precision_score(
        y_val,
        predictions,
        zero_division=0
    )

    f1 = f1_score(
        y_val,
        predictions,
        zero_division=0
    )

    threshold_results.append(
        {
            "threshold": threshold,
            "recall": recall,
            "precision": precision,
            "f1": f1
        }
    )


threshold_df = pd.DataFrame(threshold_results)

safe_thresholds = threshold_df[
    threshold_df["recall"] >= 0.95
]

if len(safe_thresholds) > 0:

    best_row = safe_thresholds.sort_values(
        ["f1", "precision"],
        ascending=False
    ).iloc[0]

else:

    best_row = threshold_df.sort_values(
        "f1",
        ascending=False
    ).iloc[0]


BEST_THRESHOLD = float(best_row["threshold"])

print("\nSelected threshold:")
print(f"Threshold : {BEST_THRESHOLD:.2f}")
print(f"Recall    : {best_row['recall']:.4f}")
print(f"Precision : {best_row['precision']:.4f}")
print(f"F1        : {best_row['f1']:.4f}")


# ============================================================
# VALIDATION EVALUATION
# ============================================================

val_predictions = (
    val_probabilities >= BEST_THRESHOLD
).astype(int)

print("\n---------------------------------------------")
print("VALIDATION RESULTS")
print("---------------------------------------------")

print(
    f"Accuracy  : "
    f"{accuracy_score(y_val, val_predictions):.4f}"
)

print(
    f"Precision : "
    f"{precision_score(y_val, val_predictions, zero_division=0):.4f}"
)

print(
    f"Recall    : "
    f"{recall_score(y_val, val_predictions, zero_division=0):.4f}"
)

print(
    f"F1 Score  : "
    f"{f1_score(y_val, val_predictions, zero_division=0):.4f}"
)

print(
    f"ROC-AUC   : "
    f"{roc_auc_score(y_val, val_probabilities):.4f}"
)

print("\nValidation Confusion Matrix:")
print(confusion_matrix(y_val, val_predictions))


# ============================================================
# FINAL TEST EVALUATION
# ============================================================

print("\n[6/7] Evaluating on test set...")

test_probabilities = model.predict_proba(
    X_test_processed
)[:, 1]

test_predictions = (
    test_probabilities >= BEST_THRESHOLD
).astype(int)


print("\n---------------------------------------------")
print("FINAL TEST RESULTS")
print("---------------------------------------------")

test_accuracy = accuracy_score(
    y_test,
    test_predictions
)

test_precision = precision_score(
    y_test,
    test_predictions,
    zero_division=0
)

test_recall = recall_score(
    y_test,
    test_predictions,
    zero_division=0
)

test_f1 = f1_score(
    y_test,
    test_predictions,
    zero_division=0
)

test_auc = roc_auc_score(
    y_test,
    test_probabilities
)

print(f"Accuracy  : {test_accuracy:.4f}")
print(f"Precision : {test_precision:.4f}")
print(f"Recall    : {test_recall:.4f}")
print(f"F1 Score  : {test_f1:.4f}")
print(f"ROC-AUC   : {test_auc:.4f}")

print("\nTest Confusion Matrix:")
print(confusion_matrix(y_test, test_predictions))

print("\nClassification Report:")
print(
    classification_report(
        y_test,
        test_predictions,
        target_names=[
            "No Overflow",
            "Overflow"
        ],
        zero_division=0
    )
)


# ============================================================
# SAMPLE PREDICTIONS
# ============================================================

print("\n===========================================")
print("SAMPLE OVERFLOW PREDICTIONS")
print("===========================================")

results = test[
    [
        "reading_id",
        "bin_id",
        "timestamp",
        "sensor_fill_level_pct",
        "target_fill_level_6h_pct",
        "target_overflow_6h"
    ]
].copy()

results["overflow_probability"] = test_probabilities
results["predicted_overflow"] = test_predictions

results["correct"] = (
    results["target_overflow_6h"]
    == results["predicted_overflow"]
)

print(
    results.head(15).to_string(index=False)
)


# ============================================================
# SAVE MODEL
# ============================================================

print("\n[7/7] Saving model...")

os.makedirs(MODEL_DIR, exist_ok=True)

joblib.dump(
    model,
    MODEL_FILE
)

joblib.dump(
    preprocessor,
    PREPROCESSOR_FILE
)

# Save threshold separately
threshold_file = os.path.join(
    MODEL_DIR,
    "overflow_threshold.txt"
)

with open(threshold_file, "w") as f:
    f.write(str(BEST_THRESHOLD))

# Save complete test predictions
prediction_file = os.path.join(
    DATA_DIR,
    "overflow_predictions.csv"
)

results.to_csv(
    prediction_file,
    index=False
)

print("\nSaved:")
print(MODEL_FILE)
print(PREPROCESSOR_FILE)
print(threshold_file)
print(prediction_file)

print("\n" + "=" * 70)
print("OVERFLOW MODEL TRAINING COMPLETED")
print("=" * 70)
