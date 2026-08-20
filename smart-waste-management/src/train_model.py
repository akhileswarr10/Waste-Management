import os
import joblib
import pandas as pd
import numpy as np

from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import (
    mean_absolute_error,
    mean_squared_error,
    r2_score
)

from preprocessing import (
    load_datasets,
    prepare_features,
    create_preprocessor
)


# ============================================================
# CONFIGURATION
# ============================================================

MODEL_PATH = "models/random_forest_waste_model.pkl"
PREPROCESSOR_PATH = "models/preprocessor.pkl"


# ============================================================
# MAIN
# ============================================================

def main():

    print("=" * 70)
    print("SMART WASTE MANAGEMENT")
    print("RANDOM FOREST BASELINE MODEL")
    print("=" * 70)


    # ========================================================
    # 1. LOAD DATA
    # ========================================================

    print("\n[1/6] Loading datasets...")

    train, validation, test = load_datasets()

    print("Train      :", train.shape)
    print("Validation :", validation.shape)
    print("Test       :", test.shape)


    # ========================================================
    # 2. PREPARE FEATURES
    # ========================================================

    print("\n[2/6] Preparing features...")

    X_train, y_train = prepare_features(train)
    X_val, y_val = prepare_features(validation)
    X_test, y_test = prepare_features(test)

    print("X_train :", X_train.shape)
    print("X_val   :", X_val.shape)
    print("X_test  :", X_test.shape)

    print("Target  :", "target_fill_level_6h_pct")


    # ========================================================
    # 3. PREPROCESS
    # ========================================================

    print("\n[3/6] Preprocessing data...")

    preprocessor = create_preprocessor()

    X_train_processed = preprocessor.fit_transform(
        X_train
    )

    X_val_processed = preprocessor.transform(
        X_val
    )

    X_test_processed = preprocessor.transform(
        X_test
    )

    print(
        "Processed X_train:",
        X_train_processed.shape
    )

    print(
        "Processed X_val:",
        X_val_processed.shape
    )

    print(
        "Processed X_test:",
        X_test_processed.shape
    )


    # ========================================================
    # 4. TRAIN RANDOM FOREST
    # ========================================================

    print("\n[4/6] Training Random Forest...")

    model = RandomForestRegressor(
        n_estimators=100,
        max_depth=20,
        min_samples_split=5,
        min_samples_leaf=2,
        n_jobs=-1,
        random_state=42
    )

    model.fit(
        X_train_processed,
        y_train
    )

    print("Random Forest training completed!")


    # ========================================================
    # 5. VALIDATION
    # ========================================================

    print("\n[5/6] Evaluating on validation set...")

    validation_predictions = model.predict(
        X_val_processed
    )

    val_mae = mean_absolute_error(
        y_val,
        validation_predictions
    )

    val_rmse = np.sqrt(
        mean_squared_error(
            y_val,
            validation_predictions
        )
    )

    val_r2 = r2_score(
        y_val,
        validation_predictions
    )

    print("\n" + "-" * 45)
    print("VALIDATION RESULTS")
    print("-" * 45)

    print(f"MAE  : {val_mae:.4f}")
    print(f"RMSE : {val_rmse:.4f}")
    print(f"R²   : {val_r2:.4f}")


    # ========================================================
    # 6. FINAL TEST
    # ========================================================

    print("\n[6/6] Evaluating on test set...")

    test_predictions = model.predict(
        X_test_processed
    )

    test_mae = mean_absolute_error(
        y_test,
        test_predictions
    )

    test_rmse = np.sqrt(
        mean_squared_error(
            y_test,
            test_predictions
        )
    )

    test_r2 = r2_score(
        y_test,
        test_predictions
    )

    print("\n" + "-" * 45)
    print("FINAL TEST RESULTS")
    print("-" * 45)

    print(f"MAE  : {test_mae:.4f}")
    print(f"RMSE : {test_rmse:.4f}")
    print(f"R²   : {test_r2:.4f}")


    # ========================================================
    # SAVE MODEL
    # ========================================================

    print("\nSaving model...")

    os.makedirs(
        "models",
        exist_ok=True
    )

    joblib.dump(
        model,
        MODEL_PATH
    )

    joblib.dump(
        preprocessor,
        PREPROCESSOR_PATH
    )

    print("\nSaved:")
    print(MODEL_PATH)
    print(PREPROCESSOR_PATH)


    # ========================================================
    # SAMPLE PREDICTIONS
    # ========================================================

    print("\n" + "=" * 70)
    print("SAMPLE PREDICTIONS")
    print("=" * 70)

    sample_results = pd.DataFrame({
        "Actual_Fill_6h": y_test.iloc[:10].values,
        "Predicted_Fill_6h": test_predictions[:10]
    })

    sample_results["Error"] = (
        sample_results["Actual_Fill_6h"]
        - sample_results["Predicted_Fill_6h"]
    ).abs()

    print(sample_results.to_string(index=False))

    print("\nTraining pipeline completed successfully!")


# ============================================================
# RUN
# ============================================================

if __name__ == "__main__":
    main()