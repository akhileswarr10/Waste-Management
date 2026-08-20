import random
import datetime
from typing import Dict, List, Any
from backend.database.db import db

class SimulationEngine:
    # Balanced realistic hourly fill rate ranges (% per hour)
    FILL_RATES = {
        "Commercial": (3.5, 7.5),
        "Market": (4.0, 8.0),
        "Residential": (1.5, 3.5),
        "Industrial": (0.8, 2.2),
        "Public_Park": (0.8, 2.5),
        "School": (1.5, 3.5),
        "Hospital": (2.0, 4.5)
    }

    @staticmethod
    def get_fill_rate_for_bin(bin_record: Dict[str, Any], current_dt: datetime.datetime) -> float:
        area_type = bin_record.get("area_type", "Residential")
        low, high = SimulationEngine.FILL_RATES.get(area_type, (1.5, 3.5))
        
        # Base hourly rate
        rate = random.uniform(low, high)
        
        # Multiplier from bin metadata
        demand_mult = float(bin_record.get("demand_multiplier") or 1.0)
        rate *= demand_mult

        # Weekend modifier
        is_weekend = current_dt.weekday() >= 5
        if is_weekend:
            if area_type in ("Market", "Commercial", "Public_Park", "Residential"):
                rate *= random.uniform(1.1, 1.25)
            elif area_type in ("School", "Industrial"):
                rate *= random.uniform(0.4, 0.7)

        # Diurnal / Hour of day modifier
        hour = current_dt.hour
        if 8 <= hour <= 20:
            rate *= random.uniform(1.0, 1.2)
        else:
            rate *= random.uniform(0.3, 0.6)

        return max(0.2, rate)

    @staticmethod
    def advance_time(hours: int = 6) -> Dict[str, Any]:
        """
        Advances the virtual clock by `hours` (e.g. 6 or 24).
        Simulates hourly stochastic fill rate increases, creates telemetry records,
        and updates bin fill levels and simulation_state.
        """
        state = db.get_simulation_state()
        current_time_str = state.get("virtual_time", "2025-06-01T08:00:00+00:00")
        
        try:
            current_dt = datetime.datetime.fromisoformat(current_time_str)
        except Exception:
            current_dt = datetime.datetime(2025, 6, 1, 8, 0, tzinfo=datetime.timezone.utc)

        bins = db.get_all_bins(active_only=True)
        if not bins:
            return {"error": "No active bins found. Please run seed script first."}

        new_telemetry_records = []
        updated_bin_fills = {}

        # Simulate in 1-hour increments for high-fidelity lag feature tracking
        # Each hour updates internal fill and generates a telemetry reading
        current_fills = {b["id"]: float(b.get("current_fill_level_pct", 20.0)) for b in bins}

        # Temperature & Weather baseline simulation
        base_temp = random.uniform(26.0, 32.0)
        is_rainy = random.random() < 0.15
        rainfall = random.uniform(2.0, 18.0) if is_rainy else 0.0

        for h in range(1, hours + 1):
            step_dt = current_dt + datetime.timedelta(hours=h)
            is_holiday_val = 1 if (step_dt.weekday() == 6 or random.random() < 0.03) else 0

            for b in bins:
                b_id = b["id"]
                hourly_rate = SimulationEngine.get_fill_rate_for_bin(b, step_dt)
                
                # Check for random spike event (5% chance of +10% to +25% fill dump)
                spike = 0.0
                has_event = 0
                if random.random() < 0.05:
                    spike = random.uniform(10.0, 25.0)
                    has_event = 1

                # Sensor noise
                noise_std = float(b.get("sensor_noise_std_pct") or 1.5)
                sensor_noise = random.gauss(0, noise_std * 0.3)

                prev_fill = current_fills[b_id]
                new_fill = prev_fill + hourly_rate + spike
                
                # Bins can overflow up to 120% physically in simulation
                new_fill = min(120.0, max(0.0, new_fill))
                current_fills[b_id] = new_fill

                sensor_reading = min(100.0, max(0.0, new_fill + sensor_noise))
                sensor_anomaly = 1 if random.random() < 0.02 else 0

                telemetry_row = {
                    "bin_id": b_id,
                    "timestamp": step_dt.isoformat(),
                    "sensor_fill_level_pct": round(sensor_reading, 2),
                    "temperature_c": round(base_temp + random.uniform(-2, 3), 1),
                    "humidity_pct": round(random.uniform(65.0, 90.0), 1),
                    "rainfall_mm": round(rainfall, 1),
                    "is_holiday": is_holiday_val,
                    "local_event": has_event,
                    "sensor_anomaly": sensor_anomaly
                }
                new_telemetry_records.append(telemetry_row)

        # Batch insert all simulated telemetry records
        inserted_count = db.insert_telemetry(new_telemetry_records)

        # Batch update current fill level for all bins in DB
        db.update_multiple_bin_fills({b_id: round(final_fill, 2) for b_id, final_fill in current_fills.items()})
        updated_bin_fills = {b_id: round(final_fill, 2) for b_id, final_fill in current_fills.items()}

        # Advance virtual clock
        new_virtual_dt = current_dt + datetime.timedelta(hours=hours)
        new_virtual_time_str = new_virtual_dt.isoformat()
        db.update_simulation_state(new_virtual_time_str, last_advance_hours=hours)

        return {
            "success": True,
            "previous_virtual_time": current_time_str,
            "new_virtual_time": new_virtual_time_str,
            "hours_advanced": hours,
            "telemetry_records_generated": inserted_count,
            "total_active_bins": len(bins),
            "updated_fills": updated_bin_fills
        }

    @staticmethod
    def reset_simulation(base_date_str: str = "2025-06-01T08:00:00+00:00") -> Dict[str, Any]:
        """
        Completely resets the database to the clean initial baseline state:
        - Clears old advanced simulation telemetry and collection logs
        - Resets all 20 bins to their exact initial gradient fill levels
        - Restores 48 hours of historical telemetry leading up to base_date
        - Resets the virtual clock to base_date
        """
        from backend.scripts.seed_database import seed_database, MOCK_BINS
        try:
            seed_database(start_date_str=base_date_str, history_hours=48)
            reset_fills = {b["id"]: b["current_fill_level_pct"] for b in MOCK_BINS}
            return {
                "success": True,
                "message": "Simulation reset successfully to baseline.",
                "virtual_time": base_date_str,
                "reset_fills": reset_fills
            }
        except Exception as e:
            return {"error": str(e)}
