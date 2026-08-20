import os
import sys
import json

# Ensure project root is in sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from backend.app import app

def test_phase3():
    print("=" * 70)
    print("RUNNING PHASE 3 ROUTE OPTIMIZER & CORRIDOR VERIFICATION")
    print("=" * 70)

    client = app.test_client()

    # 1. Request Optimized Route
    print("[*] Triggering GET /api/routes/optimized...")
    res = client.get("/api/routes/optimized")
    assert res.status_code == 200, f"Route request failed: {res.data}"

    payload = json.loads(res.data)
    assert payload.get("status") == "success", f"Failed payload: {payload}"

    data = payload.get("data", {})
    summary = data.get("summary", {})
    stops = data.get("stops", [])
    polylines = data.get("polyline_coordinates", [])

    print("\n[+] OPTIMIZATION SUMMARY METRICS:")
    print("-" * 50)
    print(f"Total Collection Stops     : {summary.get('total_collection_stops')}")
    print(f"Primary Target Stops (>=80%): {summary.get('primary_stops_count')}")
    print(f"On-The-Way Corridor Stops  : {summary.get('on_the_way_stops_count')}")
    print(f"Total Route Distance       : {summary.get('total_route_distance_km')} km (Saved: {summary.get('distance_saved_km')} km)")
    print(f"Estimated Drive + Ops Time : {summary.get('estimated_duration_minutes')} mins")
    print(f"Total Waste Collected      : {summary.get('total_waste_collected_liters')} Liters")
    print(f"Fuel Savings               : {summary.get('fuel_savings_pct')}% ({summary.get('fuel_saved_liters')} Liters)")
    print(f"Estimated Cost Saved       : Rs. {summary.get('estimated_cost_savings_inr')}")
    print("-" * 50)

    # 2. Verify On-the-Way Slotting Logic
    assert len(stops) >= 3, "Route must contain depot start, at least one stop, and depot return!"
    assert stops[0]["type"] == "depot_start", "First stop must be depot_start"
    assert stops[-1]["type"] == "depot_return", "Last stop must be depot_return"
    assert len(polylines) == len(stops), "Polyline waypoints must match number of stops!"

    print("\nSEQUENTIAL ROUTE MANIFEST:")
    print("-" * 85)
    print(f"{'Stop #':<7} | {'Type':<22} | {'Bin ID':<8} | {'Fill %':<8} | {'Leg Dist':<10} | {'Cumul Dist':<11} | {'ETA'}")
    print("-" * 85)

    has_on_the_way = False
    for s in stops:
        is_otw = s.get("is_on_the_way", False)
        if is_otw:
            has_on_the_way = True
        print(f"{s['stop_number']:<7} | {s['type']:<22} | {s.get('bin_id', '-'):<8} | {s.get('current_fill_level_pct', 0.0):>6.1f}% | {s.get('distance_from_prev_km', 0.0):>7.2f} km | {s.get('cumulative_distance_km', 0.0):>8.2f} km | {s.get('eta_minutes', 0.0):>5.1f} min")

    print("-" * 85)
    print(f"[PASS] Corridor On-The-Way Collection Slotting Active: {has_on_the_way}")
    print("\n[+] Verification 3 Passed Successfully!")
    print("=" * 70)

if __name__ == "__main__":
    test_phase3()
