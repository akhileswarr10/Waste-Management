import math
import datetime
import numpy as np
import pandas as pd
from typing import Dict, List, Any, Optional
from backend.database.db import db

# Column specifications matching training and preprocessing pipeline
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

ALL_52_FEATURES = NUMERICAL_FEATURES + CATEGORICAL_FEATURES


class FeatureBuilder:
    @staticmethod
    def _extract_lag(telemetry_series: List[Dict[str, Any]], hours_ago: int, default_val: float) -> float:
        """Finds closest telemetry reading approximately `hours_ago` in the past."""
        if not telemetry_series:
            return default_val
        if len(telemetry_series) > hours_ago:
            return float(telemetry_series[hours_ago].get("sensor_fill_level_pct", default_val))
        return float(telemetry_series[-1].get("sensor_fill_level_pct", default_val))

    @classmethod
    def build_features_for_bins(cls, bins: Optional[List[Dict[str, Any]]] = None) -> pd.DataFrame:
        """
        Extracts telemetry history for active bins in a single bulk database query
        and builds the 52-column feature DataFrame.
        """
        if bins is None:
            bins = db.get_all_bins(active_only=True)

        sim_state = db.get_simulation_state()
        v_time_str = sim_state.get("virtual_time", "2025-06-01T08:00:00+00:00")
        try:
            current_dt = datetime.datetime.fromisoformat(v_time_str)
        except Exception:
            current_dt = datetime.datetime(2025, 6, 1, 8, 0, tzinfo=datetime.timezone.utc)

        # 1. Bulk fetch all recent telemetry in ONE query
        all_telemetry = db.get_all_recent_telemetry(limit_per_bin=48)
        
        # Group telemetry by bin_id
        telemetry_by_bin: Dict[str, List[Dict[str, Any]]] = {}
        for t in all_telemetry:
            b_id = t["bin_id"]
            if b_id not in telemetry_by_bin:
                telemetry_by_bin[b_id] = []
            telemetry_by_bin[b_id].append(t)

        rows = []

        for b in bins:
            b_id = b["id"]
            telemetry = telemetry_by_bin.get(b_id, [])
            
            # Current fill (authoritative from bins table)
            curr_fill = float(b.get("current_fill_level_pct", 0.0))
            
            # Environmental readings
            latest_tel = telemetry[0] if telemetry else {}
            temp = float(latest_tel.get("temperature_c", 28.5))
            humid = float(latest_tel.get("humidity_pct", 75.0))
            rain = float(latest_tel.get("rainfall_mm", 0.0))
            is_holiday = int(latest_tel.get("is_holiday", 0))
            local_event = int(latest_tel.get("local_event", 0))
            sensor_anomaly = int(latest_tel.get("sensor_anomaly", 0))

            # Hours since collection
            last_coll_str = b.get("last_collected_at")
            hours_since_coll = 12.0
            if last_coll_str:
                try:
                    last_coll_dt = datetime.datetime.fromisoformat(last_coll_str)
                    hours_since_coll = max(0.5, (current_dt - last_coll_dt).total_seconds() / 3600.0)
                except Exception:
                    hours_since_coll = 12.0

            # Lags
            lag_1h = cls._extract_lag(telemetry, 1, max(0.0, curr_fill - 2.0))
            lag_2h = cls._extract_lag(telemetry, 2, max(0.0, curr_fill - 4.0))
            lag_3h = cls._extract_lag(telemetry, 3, max(0.0, curr_fill - 6.0))
            lag_6h = cls._extract_lag(telemetry, 6, max(0.0, curr_fill - 12.0))
            lag_12h = cls._extract_lag(telemetry, 12, max(0.0, curr_fill - 24.0))
            lag_24h = cls._extract_lag(telemetry, 24, max(0.0, curr_fill - 40.0))

            # Fill changes and rates
            change_1h = curr_fill - lag_1h
            change_6h = curr_fill - lag_6h
            rate_1h = change_1h / 1.0
            rate_6h = change_6h / 6.0

            # Rolling stats
            recent_fills = [float(t.get("sensor_fill_level_pct", curr_fill)) for t in telemetry] if telemetry else [curr_fill]
            fills_6h = recent_fills[:6] if len(recent_fills) >= 6 else recent_fills
            fills_24h = recent_fills[:24] if len(recent_fills) >= 24 else recent_fills

            avg_6h = float(np.mean(fills_6h)) if fills_6h else curr_fill
            avg_24h = float(np.mean(fills_24h)) if fills_24h else curr_fill
            avg_7d = float(np.mean(recent_fills)) if recent_fills else curr_fill
            max_24h = float(np.max(fills_24h)) if fills_24h else curr_fill

            # Time cyclical
            hour_val = current_dt.hour
            dow_val = current_dt.weekday()
            month_val = current_dt.month
            day_val = current_dt.day
            week_val = current_dt.isocalendar()[1]
            is_weekend = 1 if dow_val >= 5 else 0
            is_night = 1 if (hour_val < 6 or hour_val >= 20) else 0

            hour_sin = math.sin(2 * math.pi * hour_val / 24.0)
            hour_cos = math.cos(2 * math.pi * hour_val / 24.0)
            dow_sin = math.sin(2 * math.pi * dow_val / 7.0)
            dow_cos = math.cos(2 * math.pi * dow_val / 7.0)
            month_sin = math.sin(2 * math.pi * month_val / 12.0)
            month_cos = math.cos(2 * math.pi * month_val / 12.0)

            # Domain derived
            cap_rem = max(0.0, 100.0 - curr_fill)
            rate_24h = max(0.0, (curr_fill - lag_24h) / 24.0)
            hrs_to_full = (cap_rem / rate_6h) if rate_6h > 0.01 else 999.0
            hrs_to_full = min(999.0, max(0.0, hrs_to_full))

            # Weather condition string
            if rain > 1.0:
                weather_cond = "Rainy"
            elif temp > 32.0:
                weather_cond = "Hot"
            elif temp < 20.0:
                weather_cond = "Cold"
            else:
                weather_cond = "Clear"

            # Assemble record
            feat_row = {
                # Metadata / Identifiers (kept for reference if needed)
                "bin_id": b_id,
                
                # 45 Numerical Features
                "latitude": float(b.get("latitude", 10.0)),
                "longitude": float(b.get("longitude", 76.3)),
                "bin_capacity_liters": float(b.get("bin_capacity_liters", 800.0)),
                "demand_multiplier": float(b.get("demand_multiplier", 1.0)),
                "sensor_fill_level_pct": round(curr_fill, 2),
                "hours_since_collection": round(hours_since_coll, 2),
                "temperature_c": round(temp, 1),
                "humidity_pct": round(humid, 1),
                "rainfall_mm": round(rain, 1),
                "is_holiday": is_holiday,
                "local_event": local_event,
                "sensor_anomaly": sensor_anomaly,
                "previous_fill_1h_pct": round(lag_1h, 2),
                "previous_fill_2h_pct": round(lag_2h, 2),
                "previous_fill_3h_pct": round(lag_3h, 2),
                "previous_fill_6h_pct": round(lag_6h, 2),
                "previous_fill_12h_pct": round(lag_12h, 2),
                "previous_fill_24h_pct": round(lag_24h, 2),
                "fill_change_1h_pct": round(change_1h, 2),
                "fill_change_6h_pct": round(change_6h, 2),
                "fill_rate_1h_pct_per_hour": round(rate_1h, 3),
                "fill_rate_6h_pct_per_hour": round(rate_6h, 3),
                "avg_fill_6h_pct": round(avg_6h, 2),
                "avg_fill_24h_pct": round(avg_24h, 2),
                "avg_fill_7d_pct": round(avg_7d, 2),
                "max_fill_24h_pct": round(max_24h, 2),
                "collection_count_7d": 2,
                "day_of_week": dow_val,
                "day_of_month": day_val,
                "month": month_val,
                "week_of_year": week_val,
                "hour": hour_val,
                "is_weekend": is_weekend,
                "is_night": is_night,
                "hour_sin": round(hour_sin, 4),
                "hour_cos": round(hour_cos, 4),
                "dow_sin": round(dow_sin, 4),
                "dow_cos": round(dow_cos, 4),
                "month_sin": round(month_sin, 4),
                "month_cos": round(month_cos, 4),
                "historical_avg_fill_pct": round(avg_24h, 2),
                "historical_max_fill_pct": round(max_24h, 2),
                "capacity_remaining_pct": round(cap_rem, 2),
                "fill_rate_24h_est_pct_per_hour": round(rate_24h, 3),
                "estimated_hours_to_full": round(hrs_to_full, 2),

                # 7 Categorical Features
                "locality": str(b.get("locality", "Central")),
                "collection_zone": str(b.get("collection_zone", "Z1")),
                "area_type": str(b.get("area_type", "Residential")),
                "bin_type": str(b.get("bin_type", "Mixed")),
                "service_window": str(b.get("service_window", "08:00-14:00")),
                "weather_condition": weather_cond,
                "global_event": "None"
            }
            rows.append(feat_row)

        return pd.DataFrame(rows)
