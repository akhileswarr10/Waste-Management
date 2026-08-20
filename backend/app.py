import os
import sys
from flask import Flask, jsonify, request
from flask_cors import CORS

# Ensure project root is in sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.config import Config
from backend.database.db import db
from backend.services.simulation_engine import SimulationEngine

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

# ---------------- ROOT & HEALTH ----------------
@app.route("/", methods=["GET"])
def index():
    return jsonify({
        "service": "WasteFlow Simulation & ML Backend API",
        "status": "online",
        "database": "Supabase" if db.use_supabase else "Local SQLite",
        "endpoints": {
            "health": "/api/health",
            "simulation_status": "/api/simulation/status",
            "simulation_advance": "POST /api/simulation/advance",
            "simulation_reset": "POST /api/simulation/reset",
            "bins": "/api/bins",
            "predictions": "/api/predictions",
            "optimized_route": "/api/routes/optimized",
            "recent_telemetry": "/api/telemetry/recent"
        }
    })

@app.route("/api/health", methods=["GET"])
def health_check():
    return jsonify({
        "status": "healthy",
        "service": "WasteFlow Simulation & ML Backend",
        "database_backend": "Supabase" if db.use_supabase else "Local SQLite"
    })

# ---------------- ML PREDICTIONS ENDPOINT ----------------
@app.route("/api/predictions", methods=["GET"])
def get_predictions():
    """
    Assembles real-time 52 telemetry features and executes regression + classifier inference.
    Returns predicted fill, overflow risk, priority scores, and urgency tiers.
    """
    from backend.services.ml_service import MLService
    try:
        service = MLService.get_instance()
        data = service.predict_bins()
        return jsonify({
            "status": "success",
            "data": data
        })
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"status": "error", "message": str(e)}), 500

# ---------------- ROUTE OPTIMIZER ENDPOINT ----------------
@app.route("/api/routes/optimized", methods=["GET"])
def get_optimized_route():
    """
    Executes Greedy Nearest-Neighbor optimization with Cross-Track Corridor detection.
    Returns ordered collection stops, route polyline coordinates, ETAs, and fuel savings metrics.
    """
    from backend.services.optimizer import RouteOptimizer
    try:
        route_result = RouteOptimizer.generate_optimized_route()
        if route_result.get("status") == "error":
            return jsonify({"status": "error", "message": route_result.get("message")}), 400
        return jsonify({
            "status": "success",
            "data": route_result
        })
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"status": "error", "message": str(e)}), 500

# ---------------- SIMULATION ENDPOINTS ----------------
@app.route("/api/simulation/status", methods=["GET"])
def get_simulation_status():
    state = db.get_simulation_state()
    bins = db.get_all_bins(active_only=True)
    avg_fill = round(sum(b.get("current_fill_level_pct", 0) for b in bins) / max(1, len(bins)), 1)
    
    return jsonify({
        "status": "success",
        "simulation_state": state,
        "total_active_bins": len(bins),
        "average_fill_pct": avg_fill
    })

@app.route("/api/simulation/advance", methods=["POST"])
def advance_simulation():
    """
    Advances the virtual simulation clock by `hours` (default 6h, or 24h).
    Simulates proportional fill rate increases across bins and generates telemetry logs.
    """
    data = request.get_json(silent=True) or {}
    hours = int(data.get("hours", 6))
    if hours not in (6, 24) and hours <= 0:
        hours = 6
        
    result = SimulationEngine.advance_time(hours=hours)
    if "error" in result:
        return jsonify({"status": "error", "message": result["error"]}), 400
        
    return jsonify({
        "status": "success",
        "data": result
    })

@app.route("/api/simulation/reset", methods=["POST"])
def reset_simulation():
    data = request.get_json(silent=True) or {}
    base_date = data.get("base_date", "2025-06-01T08:00:00+00:00")
    result = SimulationEngine.reset_simulation(base_date_str=base_date)
    return jsonify({
        "status": "success",
        "data": result
    })

# ---------------- BINS ENDPOINTS ----------------
@app.route("/api/bins", methods=["GET"])
def get_bins():
    bins = db.get_all_bins(active_only=False)
    return jsonify({
        "status": "success",
        "count": len(bins),
        "bins": bins
    })

@app.route("/api/bins/<bin_id>", methods=["GET"])
def get_single_bin(bin_id):
    bin_record = db.get_bin(bin_id)
    if not bin_record:
        return jsonify({"status": "error", "message": "Bin not found"}), 404
    telemetry = db.get_bin_telemetry_history(bin_id, limit=24)
    return jsonify({
        "status": "success",
        "bin": bin_record,
        "recent_telemetry": telemetry
    })

@app.route("/api/bins/<bin_id>/collect", methods=["POST"])
def collect_bin(bin_id):
    """
    Simulates driver waste pickup:
    Resets bin current_fill_level_pct to 0.0, records collection log, inserts 0% telemetry, and updates DB.
    """
    import datetime
    bin_record = db.get_bin(bin_id)
    if not bin_record:
        return jsonify({"status": "error", "message": f"Bin {bin_id} not found"}), 404

    curr_fill = float(bin_record.get("current_fill_level_pct", 80.0))
    cap = float(bin_record.get("bin_capacity_liters", 800.0))
    weight_kg = round(cap * (curr_fill / 100.0) * 0.55, 1) # 0.55 kg/L waste density
    
    sim_state = db.get_simulation_state()
    v_time_str = sim_state.get("virtual_time") or datetime.datetime.now(datetime.timezone.utc).isoformat()
    now_str = datetime.datetime.now(datetime.timezone.utc).isoformat()

    # 1. Reset bin fill to 0.0%
    db.update_bin_fill(bin_id, 0.0, last_collected_at=v_time_str)

    # 2. Insert collection log
    collection_log = {
        "bin_id": bin_id,
        "driver_id": "22222222-2222-2222-2222-222222222222",
        "collected_at": v_time_str,
        "fill_level_before_pct": curr_fill,
        "fill_level_after_pct": 0.0,
        "collected_weight_kg": weight_kg,
        "notes": "Collected via WasteFlow Interface"
    }
    db.insert_collection(collection_log)

    # 3. Append 0% telemetry record
    db.insert_telemetry([{
        "bin_id": bin_id,
        "timestamp": v_time_str,
        "sensor_fill_level_pct": 0.0,
        "temperature_c": 28.5,
        "humidity_pct": 75.0,
        "rainfall_mm": 0.0,
        "is_holiday": 0,
        "local_event": 0,
        "sensor_anomaly": 0
    }])

@app.route("/api/routes/collect-all", methods=["POST"])
def collect_all_route_stops():
    """
    Simulates driver/admin completing the entire active route:
    Collects all bins currently in the active route, resets their fill to 0.0%,
    inserts collection records and 0.0% telemetry, and refreshes the route.
    """
    import datetime
    from backend.services.optimizer import RouteOptimizer
    
    route_result = RouteOptimizer.generate_optimized_route()
    stops = route_result.get("stops", [])
    collection_stops = [s for s in stops if not s.get("is_depot") and s.get("bin_id") and not str(s.get("bin_id")).startswith("DEPOT")]
    
    if not collection_stops:
        return jsonify({
            "status": "success",
            "message": "No active route stops pending collection.",
            "collected_count": 0
        })

    sim_state = db.get_simulation_state()
    v_time_str = sim_state.get("virtual_time") or datetime.datetime.now(datetime.timezone.utc).isoformat()
    now_str = datetime.datetime.now(datetime.timezone.utc).isoformat()

    collected_bin_ids = []
    total_weight_kg = 0.0
    telemetry_records = []
    collection_logs = []
    fills_dict = {}

    for s in collection_stops:
        b_id = s["bin_id"]
        curr_fill = float(s.get("current_fill_level_pct", 80.0))
        cap = float(s.get("bin_capacity_liters", 800.0))
        weight_kg = round(cap * (curr_fill / 100.0) * 0.55, 1)
        total_weight_kg += weight_kg
        collected_bin_ids.append(b_id)
        fills_dict[b_id] = 0.0

        collection_logs.append({
            "bin_id": b_id,
            "driver_id": "22222222-2222-2222-2222-222222222222",
            "collected_at": v_time_str,
            "fill_level_before_pct": curr_fill,
            "fill_level_after_pct": 0.0,
            "collected_weight_kg": weight_kg,
            "notes": "Bulk collected via Mark All as Completed"
        })

        telemetry_records.append({
            "bin_id": b_id,
            "timestamp": v_time_str,
            "sensor_fill_level_pct": 0.0,
            "temperature_c": 28.5,
            "humidity_pct": 75.0,
            "rainfall_mm": 0.0,
            "is_holiday": 0,
            "local_event": 0,
            "sensor_anomaly": 0
        })

    # 1. Update all bin fills to 0.0% in DB
    db.update_multiple_bin_fills(fills_dict)

    # 2. Insert telemetry rows
    db.insert_telemetry(telemetry_records)

    # 3. Insert collection logs
    for log in collection_logs:
        db.insert_collection(log)

    return jsonify({
        "status": "success",
        "message": f"Successfully collected all {len(collected_bin_ids)} route stops ({round(total_weight_kg, 1)} kg waste).",
        "collected_bins": collected_bin_ids,
        "total_weight_kg": round(total_weight_kg, 1)
    })

# ---------------- TELEMETRY ENDPOINTS ----------------
@app.route("/api/telemetry/recent", methods=["GET"])
def get_recent_telemetry():
    limit = int(request.args.get("limit", 50))
    rows = db.get_all_recent_telemetry(limit_per_bin=limit)
    return jsonify({
        "status": "success",
        "count": len(rows),
        "telemetry": rows
    })

if __name__ == "__main__":
    print(f"[*] Starting WasteFlow Backend Server on port {Config.PORT}...")
    app.run(host="0.0.0.0", port=Config.PORT, debug=Config.DEBUG)
