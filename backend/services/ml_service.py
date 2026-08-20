import os
import joblib
import numpy as np
import pandas as pd
from typing import Dict, List, Any
from backend.config import Config
from backend.services.feature_builder import FeatureBuilder, ALL_52_FEATURES
from backend.database.db import db

class MLService:
    _instance = None

    def __init__(self):
        models_dir = Config.MODELS_DIR
        print(f"[ML] Loading ML artifacts from {models_dir}...")
        
        reg_model_path = os.path.join(models_dir, "random_forest_waste_model.pkl")
        reg_preproc_path = os.path.join(models_dir, "preprocessor.pkl")
        ovf_model_path = os.path.join(models_dir, "random_forest_overflow_model.pkl")
        ovf_preproc_path = os.path.join(models_dir, "overflow_preprocessor.pkl")
        threshold_path = os.path.join(models_dir, "overflow_threshold.txt")

        # Load models
        self.regression_model = joblib.load(reg_model_path)
        self.regression_preprocessor = joblib.load(reg_preproc_path)
        self.overflow_model = joblib.load(ovf_model_path)
        self.overflow_preprocessor = joblib.load(ovf_preproc_path)

        # Load threshold
        try:
            with open(threshold_path, "r") as f:
                self.overflow_threshold = float(f.read().strip())
        except Exception:
            self.overflow_threshold = 0.62

        print(f"[ML] Models successfully loaded. Overflow Threshold: {self.overflow_threshold:.4f}")

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = MLService()
        return cls._instance

    def predict_bins(self, bins: List[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Builds features from telemetry and executes inference through both
        the regression and classification models.
        """
        if bins is None:
            bins = db.get_all_bins(active_only=True)

        if not bins:
            return {"count": 0, "predictions": [], "summary": {}}

        # 1. Feature Engineering
        feature_df = FeatureBuilder.build_features_for_bins(bins)
        bin_ids = feature_df["bin_id"].tolist()
        
        # Prepare feature matrix X (52 columns in exact required order)
        X = feature_df[ALL_52_FEATURES].copy()

        # 2. Regression Model Inference (6-hour fill level %)
        X_reg = self.regression_preprocessor.transform(X)
        pred_fills = self.regression_model.predict(X_reg)
        pred_fills = np.clip(pred_fills, 0.0, 120.0)

        # 3. Overflow Classifier Inference (Risk probability)
        X_ovf = self.overflow_preprocessor.transform(X)
        ovf_probs = self.overflow_model.predict_proba(X_ovf)[:, 1]
        ovf_flags = (ovf_probs >= self.overflow_threshold).astype(int)

        # 4. Assemble Priority Scores & Risk Classifications
        predictions = []
        tier_counts = {"EMERGENCY": 0, "CRITICAL": 0, "HIGH": 0, "MEDIUM": 0, "LOW": 0}

        for i, b in enumerate(bins):
            b_id = bin_ids[i]
            curr_fill = min(100.0, max(0.0, float(feature_df.loc[i, "sensor_fill_level_pct"])))
            pred_fill = min(100.0, max(0.0, float(pred_fills[i])))
            ovf_prob = min(100.0, max(0.0, float(ovf_probs[i] * 100.0)))
            ovf_flag = int(ovf_flags[i])

            # Calculate growth score (0-10 points for up to 30% fill increase in 6h)
            growth = max(0.0, pred_fill - curr_fill)
            growth_score = (min(30.0, growth) / 30.0) * 10.0

            # Component scoring
            c_pred = (min(100.0, max(0.0, pred_fill)) / 100.0) * 40.0
            c_ovf = (ovf_prob / 100.0) * 35.0
            c_curr = (min(100.0, max(0.0, curr_fill)) / 100.0) * 15.0
            c_growth = growth_score

            base_priority = c_pred + c_ovf + c_curr + c_growth
            if pred_fill >= 100.0 or curr_fill >= 100.0:
                base_priority += 5.0 # Overflow penalty bonus

            priority_score = round(float(np.clip(base_priority, 0.0, 100.0)), 2)

            # Determine Urgency Tier
            if curr_fill >= 100.0 or pred_fill >= 100.0 or ovf_prob >= 85.0:
                urgency_tier = "EMERGENCY"
                action = "IMMEDIATE DISPATCH"
            elif pred_fill >= 90.0 or ovf_prob >= (self.overflow_threshold * 100.0) or curr_fill >= 90.0:
                urgency_tier = "CRITICAL"
                action = "SCHEDULE URGENT PICKUP"
            elif pred_fill >= 75.0 or ovf_prob >= 40.0 or curr_fill >= 75.0:
                urgency_tier = "HIGH"
                action = "ROUTE OPTIMIZATION CANDIDATE"
            elif pred_fill >= 50.0 or curr_fill >= 50.0:
                urgency_tier = "MEDIUM"
                action = "ON-THE-WAY CANDIDATE"
            else:
                urgency_tier = "LOW"
                action = "MONITOR"

            tier_counts[urgency_tier] = tier_counts.get(urgency_tier, 0) + 1

            # Estimated hours to full
            rate_6h = float(feature_df.loc[i, "fill_rate_6h_pct_per_hour"])
            if curr_fill >= 100.0:
                hours_to_full = 0.0
            elif rate_6h > 0.01:
                hours_to_full = round(min(999.0, max(0.0, (100.0 - curr_fill) / rate_6h)), 1)
            else:
                hours_to_full = 999.0

            predictions.append({
                "bin_id": b_id,
                "latitude": float(b.get("latitude", 0.0)),
                "longitude": float(b.get("longitude", 0.0)),
                "locality": b.get("locality", "Central"),
                "collection_zone": b.get("collection_zone", "Z1"),
                "area_type": b.get("area_type", "Residential"),
                "bin_capacity_liters": float(b.get("bin_capacity_liters", 800.0)),
                "bin_type": b.get("bin_type", "Mixed"),
                "current_fill_level_pct": round(curr_fill, 1),
                "predicted_fill_6h_pct": round(pred_fill, 1),
                "overflow_probability_pct": round(ovf_prob, 1),
                "predicted_overflow": bool(ovf_flag or pred_fill >= 95.0),
                "priority_score": priority_score,
                "urgency_tier": urgency_tier,
                "recommended_action": action,
                "estimated_hours_to_full": hours_to_full
            })

        # Sort predictions by priority score descending
        predictions.sort(key=lambda x: x["priority_score"], reverse=True)

        avg_current_fill = round(sum(p["current_fill_level_pct"] for p in predictions) / len(predictions), 1)
        avg_predicted_fill = round(sum(p["predicted_fill_6h_pct"] for p in predictions) / len(predictions), 1)
        at_risk_count = sum(1 for p in predictions if p["urgency_tier"] in ("EMERGENCY", "CRITICAL", "HIGH"))

        return {
            "total_bins": len(predictions),
            "at_risk_bins_count": at_risk_count,
            "average_current_fill_pct": avg_current_fill,
            "average_predicted_fill_pct": avg_predicted_fill,
            "overflow_threshold": self.overflow_threshold,
            "tier_distribution": tier_counts,
            "predictions": predictions
        }
