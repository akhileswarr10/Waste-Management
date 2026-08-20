import math
from typing import Dict, List, Any, Tuple
from backend.config import Config
from backend.services.ml_service import MLService
from backend.database.db import db

# System Constants
EARTH_RADIUS_KM = 6371.0
AVERAGE_SPEED_KMPH = 30.0
SERVICE_TIME_MINUTES_PER_STOP = 5.0
FUEL_CONSUMPTION_L_PER_KM = 0.22  # 4.5 km per Liter for collection truck
BASELINE_FIXED_ROUTE_KM = 42.5    # Standard fixed municipal sweep across all 20 bins
FUEL_PRICE_PER_LITER = 100.0      # INR / Liter
CROSS_TRACK_CORRIDOR_KM = 0.60    # 600 meters corridor width along path vector
MAX_ON_THE_WAY_DETOUR_KM = 0.80   # Max 800m extra detour distance

def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculates great-circle distance between two GPS coordinates in kilometers."""
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)

    a = math.sin(dphi / 2.0) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2.0) ** 2
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
    return EARTH_RADIUS_KM * c

def initial_bearing(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculates initial compass bearing from point 1 to point 2 in radians."""
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dlambda = math.radians(lon2 - lon1)
    y = math.sin(dlambda) * math.cos(phi2)
    x = math.cos(phi1) * math.sin(phi2) - math.sin(phi1) * math.cos(phi2) * math.cos(dlambda)
    return math.atan2(y, x)

def cross_track_distance(start_lat: float, start_lon: float, end_lat: float, end_lon: float,
                         point_lat: float, point_lon: float) -> Tuple[float, float]:
    """
    Computes cross-track distance (perpendicular distance to line start->end)
    and along-track distance (distance along segment from start to projected point).
    Returns (cross_track_km, along_track_km).
    """
    d_start_point = haversine_distance(start_lat, start_lon, point_lat, point_lon)
    if d_start_point < 1e-6:
        return 0.0, 0.0

    d_segment = haversine_distance(start_lat, start_lon, end_lat, end_lon)
    if d_segment < 1e-6:
        return d_start_point, 0.0

    theta_segment = initial_bearing(start_lat, start_lon, end_lat, end_lon)
    theta_point = initial_bearing(start_lat, start_lon, point_lat, point_lon)

    # Cross-track distance
    delta_bearing = theta_point - theta_segment
    sin_xt = math.sin(d_start_point / EARTH_RADIUS_KM) * math.sin(delta_bearing)
    xt_dist = math.asin(max(-1.0, min(1.0, sin_xt))) * EARTH_RADIUS_KM

    # Along-track distance
    cos_at = math.cos(d_start_point / EARTH_RADIUS_KM) / math.cos(xt_dist / EARTH_RADIUS_KM)
    at_dist = math.acos(max(-1.0, min(1.0, cos_at))) * EARTH_RADIUS_KM

    return abs(xt_dist), at_dist

class RouteOptimizer:
    @staticmethod
    def calculate_detour(p1: Tuple[float, float], candidate: Tuple[float, float], p2: Tuple[float, float]) -> float:
        direct = haversine_distance(p1[0], p1[1], p2[0], p2[1])
        via = haversine_distance(p1[0], p1[1], candidate[0], candidate[1]) + \
              haversine_distance(candidate[0], candidate[1], p2[0], p2[1])
        return max(0.0, via - direct)

    @classmethod
    def generate_optimized_route(cls) -> Dict[str, Any]:
        """
        Executes Greedy Nearest-Neighbor with corridor detection:
        1. Identifies Primary Targets (Fill >= 80% or Tier IN [HIGH, CRITICAL, EMERGENCY]).
        2. Identifies On-The-Way Candidates (Fill >= 50% and not in primary targets).
        3. Constructs greedy nearest path connecting all primary targets starting & ending at Depot.
        4. Injects on-the-way bins that lie in the corridor along each leg.
        5. Computes route metrics and fuel savings.
        """
        depot_lat = Config.DEPOT_LATITUDE
        depot_lon = Config.DEPOT_LONGITUDE
        depot_pos = (depot_lat, depot_lon)

        # Get latest predictions & fills
        ml_service = MLService.get_instance()
        predictions_data = ml_service.predict_bins()
        predictions = predictions_data.get("predictions", [])

        if not predictions:
            return {"status": "error", "message": "No bins found to route."}

        # -------------------------------------------------------------
        # STEP 1: Segregate Critical Primary Targets & Corridor Candidates
        # -------------------------------------------------------------
        # Primary Targets: Fill >= 80% or Critical/Emergency
        # Corridor Candidates: 50% <= Fill < 80%
        primary_targets = []
        corridor_candidates = []

        for p in predictions:
            curr_fill = float(p["current_fill_level_pct"])
            tier = p.get("urgency_tier", "LOW")
            if curr_fill >= 80.0 or tier in ("EMERGENCY", "CRITICAL"):
                primary_targets.append(p)
            elif curr_fill >= 50.0:
                corridor_candidates.append(p)

        # Fallback: if no bins >= 80%, take top highest fill bins
        if not primary_targets:
            sorted_by_fill = sorted(predictions, key=lambda x: float(x["current_fill_level_pct"]), reverse=True)
            primary_targets = [b for b in sorted_by_fill if float(b["current_fill_level_pct"]) >= 60.0][:3]
            if not primary_targets:
                primary_targets = sorted_by_fill[:1]
            corridor_candidates = [p for p in predictions if p not in primary_targets and float(p["current_fill_level_pct"]) >= 50.0]

        # -------------------------------------------------------------
        # STEP 2: Greedy Nearest-Neighbor Tour for Primary Targets
        # -------------------------------------------------------------
        unvisited_primary = list(primary_targets)
        primary_path: List[Dict[str, Any]] = []
        current_loc = depot_pos

        while unvisited_primary:
            nearest_bin = min(
                unvisited_primary,
                key=lambda b: haversine_distance(current_loc[0], current_loc[1], b["latitude"], b["longitude"])
            )
            primary_path.append(nearest_bin)
            unvisited_primary.remove(nearest_bin)
            current_loc = (nearest_bin["latitude"], nearest_bin["longitude"])

        # -------------------------------------------------------------
        # STEP 3: Inject On-The-Way Corridor Bins (50% - 79%) Strictly Between Consecutive Stops
        # -------------------------------------------------------------
        depot_node_start = {
            "is_depot": True,
            "latitude": depot_lat,
            "longitude": depot_lon,
            "bin_id": "DEPOT_START",
            "name": "Central Operations Depot"
        }
        depot_node_end = {
            "is_depot": True,
            "latitude": depot_lat,
            "longitude": depot_lon,
            "bin_id": "DEPOT_END",
            "name": "Central Operations Depot"
        }

        full_chain = [depot_node_start] + primary_path + [depot_node_end]
        remaining_corridor = list(corridor_candidates)
        final_route_stops: List[Dict[str, Any]] = []

        for i in range(len(full_chain) - 1):
            start_node = full_chain[i]
            end_node = full_chain[i + 1]

            if i == 0:
                final_route_stops.append(start_node)

            s_lat, s_lon = start_node["latitude"], start_node["longitude"]
            e_lat, e_lon = end_node["latitude"], end_node["longitude"]
            seg_len = haversine_distance(s_lat, s_lon, e_lat, e_lon)

            # Strict Bounding Box around segment with small epsilon (~300m)
            min_lat = min(s_lat, e_lat) - 0.003
            max_lat = max(s_lat, e_lat) + 0.003
            min_lon = min(s_lon, e_lon) - 0.003
            max_lon = max(s_lon, e_lon) + 0.003

            leg_corridor_stops: List[Tuple[Dict[str, Any], float]] = []

            for cand in list(remaining_corridor):
                c_lat, c_lon = cand["latitude"], cand["longitude"]

                # 1. Must lie inside the segment's geographical bounding box
                if not (min_lat <= c_lat <= max_lat and min_lon <= c_lon <= max_lon):
                    continue

                # 2. Cross-track (perpendicular distance) and along-track progress
                xt_dist, at_dist = cross_track_distance(s_lat, s_lon, e_lat, e_lon, c_lat, c_lon)
                detour = cls.calculate_detour((s_lat, s_lon), (c_lat, c_lon), (e_lat, e_lon))

                # Strict corridor constraints:
                # - Must be between 15% and 85% of segment progress
                # - Perpendicular cross-track distance <= 0.35 km (350 meters)
                # - Extra detour penalty <= 0.35 km (350 meters)
                if (0.15 * seg_len <= at_dist <= 0.85 * seg_len) and (xt_dist <= 0.35) and (detour <= 0.35):
                    leg_corridor_stops.append((cand, at_dist))

            # Sort inserted corridor bins strictly by along-track progress so vehicle moves forward
            leg_corridor_stops.sort(key=lambda x: x[1])

            for cand_bin, _ in leg_corridor_stops:
                cand_copy = dict(cand_bin)
                cand_copy["is_on_the_way"] = True
                final_route_stops.append(cand_copy)
                if cand_bin in remaining_corridor:
                    remaining_corridor.remove(cand_bin)

            # Append the leg's destination node
            final_route_stops.append(end_node)

        # -------------------------------------------------------------
        # STEP 4: Format Stops, Cumulative Distance & ETAs
        # -------------------------------------------------------------
        formatted_stops = []
        polyline_coords = []
        cumulative_dist = 0.0
        cumulative_time = 0.0
        total_waste_liters = 0.0
        stop_counter = 0

        for idx, stop in enumerate(final_route_stops):
            is_depot = stop.get("is_depot", False)
            is_start = is_depot and idx == 0
            is_end = is_depot and idx == len(final_route_stops) - 1

            if idx == 0:
                dist_from_prev = 0.0
            else:
                prev = final_route_stops[idx - 1]
                dist_from_prev = haversine_distance(prev["latitude"], prev["longitude"], stop["latitude"], stop["longitude"])

            cumulative_dist += dist_from_prev
            # Travel time at 30 km/h
            travel_time_min = (dist_from_prev / AVERAGE_SPEED_KMPH) * 60.0
            cumulative_time += travel_time_min

            if not is_depot:
                stop_counter += 1
                cumulative_time += SERVICE_TIME_MINUTES_PER_STOP
                # Calculate estimated collected waste
                cap = float(stop.get("bin_capacity_liters", 800.0))
                fill = float(stop.get("current_fill_level_pct", 50.0))
                waste_vol = cap * (fill / 100.0)
                total_waste_liters += waste_vol

                stop_type = "on_the_way_collection" if stop.get("is_on_the_way") else "primary_collection"
            else:
                stop_type = "depot_start" if is_start else "depot_return"

            polyline_coords.append([round(stop["latitude"], 6), round(stop["longitude"], 6)])

            formatted_stops.append({
                "stop_number": 0 if is_start else (stop_counter if not is_depot else stop_counter + 1),
                "type": stop_type,
                "is_on_the_way": stop.get("is_on_the_way", False),
                "bin_id": stop.get("bin_id"),
                "name": stop.get("name", f"Bin {stop.get('bin_id')} ({stop.get('area_type', '')})"),
                "latitude": round(stop["latitude"], 6),
                "longitude": round(stop["longitude"], 6),
                "locality": stop.get("locality", "Central"),
                "collection_zone": stop.get("collection_zone", "-"),
                "area_type": stop.get("area_type", "Depot"),
                "current_fill_level_pct": stop.get("current_fill_level_pct", 0.0),
                "predicted_fill_6h_pct": stop.get("predicted_fill_6h_pct", 0.0),
                "priority_score": stop.get("priority_score", 0.0),
                "urgency_tier": stop.get("urgency_tier", "DEPOT"),
                "distance_from_prev_km": round(dist_from_prev, 2),
                "cumulative_distance_km": round(cumulative_dist, 2),
                "eta_minutes": round(cumulative_time, 1)
            })

        # -------------------------------------------------------------
        # STEP 4: Cost & Efficiency Analytics
        # -------------------------------------------------------------
        total_dist = round(cumulative_dist, 2)
        total_duration = round(cumulative_time, 1)

        # Baseline comparison: Static fixed municipal route visiting all 20 bins
        opt_fuel = total_dist * FUEL_CONSUMPTION_L_PER_KM
        base_fuel = BASELINE_FIXED_ROUTE_KM * (FUEL_CONSUMPTION_L_PER_KM * 1.15)
        fuel_saved_l = max(0.0, base_fuel - opt_fuel)
        fuel_savings_pct = (fuel_saved_l / base_fuel) * 100.0 if base_fuel > 0 else 0.0
        cost_saved_inr = fuel_saved_l * FUEL_PRICE_PER_LITER

        primary_count = len(primary_path)
        on_the_way_count = sum(1 for s in formatted_stops if s.get("is_on_the_way"))

        return {
            "status": "success",
            "depot": {
                "latitude": depot_lat,
                "longitude": depot_lon,
                "name": "Central Waste Operations Depot"
            },
            "summary": {
                "total_collection_stops": stop_counter,
                "primary_stops_count": primary_count,
                "on_the_way_stops_count": on_the_way_count,
                "total_route_distance_km": total_dist,
                "estimated_duration_minutes": total_duration,
                "total_waste_collected_liters": round(total_waste_liters, 1),
                "baseline_fixed_route_km": BASELINE_FIXED_ROUTE_KM,
                "distance_saved_km": round(max(0.0, BASELINE_FIXED_ROUTE_KM - total_dist), 2),
                "fuel_consumed_liters": round(opt_fuel, 2),
                "fuel_saved_liters": round(fuel_saved_l, 2),
                "fuel_savings_pct": round(fuel_savings_pct, 1),
                "estimated_cost_savings_inr": round(cost_saved_inr, 2)
            },
            "stops": formatted_stops,
            "polyline_coordinates": polyline_coords
        }
