"""
SMART WASTE MANAGEMENT
PHASE 4 - SMART ROUTE & COST OPTIMIZATION V6

V6 improvements:
    1. Physical fill display is capped at 100%.
    2. Raw prediction is preserved internally.
    3. Overflow amount is calculated separately.
    4. Emergency bins have response constraints.
    5. Nearby bins can be collected opportunistically.
    6. Route considers distance, urgency, fuel and cost.
    7. Truck capacity is respected.
    8. Truck consolidation is encouraged.
"""

import os
import math
import pandas as pd


# ============================================================
# FILES
# ============================================================

DATA_DIR = "data/processed"
RAW_DIR = "data/raw"

PRIORITY_FILE = os.path.join(
    DATA_DIR,
    "priority_predictions.csv"
)

TRUCK_FILE = os.path.join(
    RAW_DIR,
    "trucks.csv"
)

ROUTE_FILE = os.path.join(
    DATA_DIR,
    "optimized_routes.csv"
)

ASSIGNMENT_FILE = os.path.join(
    DATA_DIR,
    "collection_assignments.csv"
)

COMPARISON_FILE = os.path.join(
    DATA_DIR,
    "route_comparison.csv"
)

SUMMARY_FILE = os.path.join(
    DATA_DIR,
    "optimization_summary.csv"
)


# ============================================================
# SYSTEM PARAMETERS
# ============================================================

MAX_COLLECTION_CANDIDATES = 8

OVERFLOW_THRESHOLD = 62.0

WASTE_DENSITY_KG_PER_LITER = 0.55

AVERAGE_SPEED_KMPH = 30.0

SERVICE_TIME_MINUTES = 5

# Emergency response target.
# This is a simulation parameter.
EMERGENCY_RESPONSE_HOURS = 1.0

# Maximum extra travel distance allowed to collect
# an opportunistic bin while heading toward an emergency.
OPPORTUNISTIC_DETOUR_KM = 1.5

# A nearby bin is considered "on the way" when the extra
# distance is small.
MAX_ON_WAY_DETOUR_KM = 0.8

# Cost assumptions for the simulation.
FUEL_PRICE_PER_LITER = 100.0

VEHICLE_COST_PER_KM = 15.0

TRUCK_DISPATCH_COST = 500.0


# ============================================================
# RISK ORDER
# ============================================================

RISK_ORDER = {
    "EMERGENCY": 0,
    "HIGH": 1,
    "MEDIUM": 2,
    "LOW": 3
}


# ============================================================
# HAVERSINE DISTANCE
# ============================================================

def haversine_distance(
    lat1,
    lon1,
    lat2,
    lon2
):
    earth_radius = 6371.0

    lat1 = math.radians(float(lat1))
    lat2 = math.radians(float(lat2))

    delta_lat = lat2 - lat1

    delta_lon = math.radians(
        float(lon2) - float(lon1)
    )

    a = (
        math.sin(delta_lat / 2) ** 2
        +
        math.cos(lat1)
        * math.cos(lat2)
        * math.sin(delta_lon / 2) ** 2
    )

    c = (
        2
        * math.atan2(
            math.sqrt(a),
            math.sqrt(1 - a)
        )
    )

    return earth_radius * c


# ============================================================
# ROUTE DISTANCE
# ============================================================

def calculate_route_distance(points):

    if len(points) < 2:
        return 0.0

    total = 0.0

    for i in range(len(points) - 1):

        total += haversine_distance(
            points[i][0],
            points[i][1],
            points[i + 1][0],
            points[i + 1][1]
        )

    return total


# ============================================================
# POINT-TO-SEGMENT DETOUR
# ============================================================

def calculate_detour(
    current,
    candidate,
    target
):
    """
    Approximate extra distance if we visit candidate
    before target.

    Direct:
        current -> target

    With candidate:
        current -> candidate -> target

    Detour:
        extra distance caused by candidate.
    """

    direct = haversine_distance(
        current[0],
        current[1],
        target[0],
        target[1]
    )

    via_candidate = (
        haversine_distance(
            current[0],
            current[1],
            candidate[0],
            candidate[1]
        )
        +
        haversine_distance(
            candidate[0],
            candidate[1],
            target[0],
            target[1]
        )
    )

    return max(
        0.0,
        via_candidate - direct
    )


# ============================================================
# URGENCY SCORE
# ============================================================

def calculate_urgency(row):

    priority = (
        float(
            row["priority_score"]
        )
        / 100
    )

    overflow = (
        float(
            row["overflow_probability"]
        )
        / 100
    )

    current_fill = min(
        max(
            float(
                row["sensor_fill_level_pct"]
            ),
            0
        ),
        100
    ) / 100

    predicted_fill = min(
        max(
            float(
                row["predicted_fill_6h_pct"]
            ),
            0
        ),
        110
    ) / 110

    return (
        0.40 * priority
        +
        0.30 * overflow
        +
        0.15 * current_fill
        +
        0.15 * predicted_fill
    )


# ============================================================
# HEADER
# ============================================================

print("=" * 70)
print("SMART WASTE MANAGEMENT")
print("PHASE 4 - SMART ROUTE & COST OPTIMIZATION V6")
print("=" * 70)


# ============================================================
# STEP 1 - LOAD DATA
# ============================================================

print(
    "\n[1/12] Loading data..."
)

priority_df = pd.read_csv(
    PRIORITY_FILE
)

trucks_df = pd.read_csv(
    TRUCK_FILE
)

priority_df["timestamp"] = pd.to_datetime(
    priority_df["timestamp"]
)

print(
    f"Priority records : "
    f"{priority_df.shape}"
)

print(
    f"Truck records    : "
    f"{trucks_df.shape}"
)

print(
    f"Unique bins       : "
    f"{priority_df['bin_id'].nunique()}"
)

print(
    f"Available trucks  : "
    f"{trucks_df['truck_id'].nunique()}"
)


# ============================================================
# STEP 2 - LATEST BIN STATE
# ============================================================

print(
    "\n[2/12] Building latest bin state..."
)

priority_df = priority_df.sort_values(
    "timestamp"
)

latest_bins = (
    priority_df
    .groupby(
        "bin_id",
        as_index=False
    )
    .tail(1)
    .copy()
)

print(
    f"Current bins: "
    f"{len(latest_bins)}"
)


# ============================================================
# STEP 3 - PHYSICAL FILL NORMALIZATION
# ============================================================

print(
    "\n[3/12] Normalizing physical fill values..."
)


# Preserve raw ML prediction.
latest_bins[
    "raw_predicted_fill_6h_pct"
] = latest_bins[
    "predicted_fill_6h_pct"
]


# Physical fill cannot exceed 100%.
latest_bins[
    "displayed_predicted_fill_6h_pct"
] = latest_bins[
    "predicted_fill_6h_pct"
].clip(
    upper=100
)


# Calculate overflow amount separately.
latest_bins[
    "predicted_overflow_pct"
] = (
    latest_bins[
        "predicted_fill_6h_pct"
    ]
    - 100
).clip(
    lower=0
)


print(
    "Physical fill values normalized."
)


# ============================================================
# STEP 4 - COLLECTION CANDIDATES
# ============================================================

print(
    "\n[4/12] Selecting collection candidates..."
)


latest_bins[
    "collection_candidate_score"
] = (

    0.45
    * latest_bins[
        "priority_score"
    ]

    +

    0.30
    * latest_bins[
        "overflow_probability"
    ]

    +

    0.15
    * latest_bins[
        "sensor_fill_level_pct"
    ]

    +

    0.10
    * latest_bins[
        "predicted_fill_6h_pct"
    ]
)


mandatory = latest_bins[
    (
        latest_bins[
            "predicted_fill_6h_pct"
        ]
        >= 100
    )
    |
    (
        latest_bins[
            "overflow_probability"
        ]
        >= OVERFLOW_THRESHOLD
    )
    |
    (
        latest_bins[
            "sensor_fill_level_pct"
        ]
        >= 95
    )
].copy()


additional = latest_bins[
    (
        latest_bins[
            "sensor_fill_level_pct"
        ]
        >= 60
    )
    |
    (
        latest_bins[
            "priority_score"
        ]
        >= 30
    )
].copy()


candidates = pd.concat(
    [
        mandatory,
        additional
    ],
    ignore_index=True
)


candidates = candidates.drop_duplicates(
    subset=["bin_id"]
)


candidates = candidates.sort_values(
    "collection_candidate_score",
    ascending=False
)


candidates = candidates.head(
    MAX_COLLECTION_CANDIDATES
).copy()


candidates[
    "urgency_score"
] = candidates.apply(
    calculate_urgency,
    axis=1
)


candidates[
    "risk_rank"
] = candidates[
    "risk_level"
].map(
    RISK_ORDER
).fillna(4)


print(
    f"Collection candidates: "
    f"{len(candidates)}"
)


print(
    "\nSelected candidates:"
)


display_columns = [
    "bin_id",
    "collection_zone",
    "sensor_fill_level_pct",
    "displayed_predicted_fill_6h_pct",
    "predicted_overflow_pct",
    "overflow_probability",
    "priority_score",
    "risk_level"
]


print(
    candidates[
        display_columns
    ].to_string(
        index=False
    )
)


# ============================================================
# STEP 5 - ESTIMATE WASTE
# ============================================================

print(
    "\n[5/12] Estimating collection loads..."
)


candidates[
    "estimated_waste_liters"
] = (

    candidates[
        "predicted_fill_6h_pct"
    ]
    .clip(
        lower=0
    )
    / 100
    *
    candidates[
        "bin_capacity_liters"
    ]
)


candidates[
    "estimated_waste_kg"
] = (

    candidates[
        "estimated_waste_liters"
    ]
    *
    WASTE_DENSITY_KG_PER_LITER
)


print(
    f"Estimated total waste: "
    f"{candidates['estimated_waste_kg'].sum():.2f} kg"
)


# ============================================================
# STEP 6 - PREPARE TRUCK FLEET
# ============================================================

print(
    "\n[6/12] Preparing truck fleet..."
)


truck_data = {}


for row in trucks_df.itertuples(
    index=False
):

    truck_data[
        row.truck_id
    ] = {

        "truck_id":
            row.truck_id,

        "home_zone":
            row.home_zone,

        "capacity":
            float(
                row.truck_capacity_kg
            ),

        "fuel_efficiency":
            float(
                row.fuel_efficiency_km_per_liter
            ),

        "depot_lat":
            float(
                row.depot_latitude
            ),

        "depot_lon":
            float(
                row.depot_longitude
            )
    }


print(
    f"Fleet size: "
    f"{len(truck_data)} trucks"
)


# ============================================================
# STEP 7 - TRUCK/BIN DISTANCE MATRIX
# ============================================================

print(
    "\n[7/12] Building distance matrix..."
)


truck_bin_distance = {}


for truck_id, truck in truck_data.items():

    truck_bin_distance[
        truck_id
    ] = {}


    for row in candidates.itertuples(
        index=False
    ):

        truck_bin_distance[
            truck_id
        ][
            row.bin_id
        ] = haversine_distance(
            truck["depot_lat"],
            truck["depot_lon"],
            row.latitude,
            row.longitude
        )


# ============================================================
# STEP 8 - FLEET ASSIGNMENT
# ============================================================

print(
    "\n[8/12] Optimizing fleet assignment..."
)


truck_bins = {
    truck_id: []
    for truck_id in truck_data
}


truck_loads = {
    truck_id: 0.0
    for truck_id in truck_data
}


assignment_candidates = (
    candidates
    .sort_values(
        [
            "risk_rank",
            "urgency_score"
        ],
        ascending=[
            True,
            False
        ]
    )
    .to_dict(
        "records"
    )
)


for item in assignment_candidates:

    bin_id = item[
        "bin_id"
    ]

    waste = float(
        item[
            "estimated_waste_kg"
        ]
    )


    best_truck = None

    best_score = float(
        "inf"
    )


    for truck_id, truck in truck_data.items():

        remaining_capacity = (
            truck["capacity"]
            -
            truck_loads[
                truck_id
            ]
        )


        if remaining_capacity < waste:

            continue


        distance = (
            truck_bin_distance[
                truck_id
            ][
                bin_id
            ]
        )


        same_zone = (
            truck[
                "home_zone"
            ]
            ==
            item[
                "collection_zone"
            ]
        )


        zone_penalty = (
            0
            if same_zone
            else 2
        )


        if truck_bins[
            truck_id
        ]:

            activation_penalty = 0

            consolidation_bonus = 5

        else:

            activation_penalty = (
                TRUCK_DISPATCH_COST
                / 100
            )

            consolidation_bonus = 0


        utilization = (
            truck_loads[
                truck_id
            ]
            /
            truck[
                "capacity"
            ]
        )


        score = (

            distance

            +

            zone_penalty

            +

            activation_penalty

            +

            utilization * 5

            -

            consolidation_bonus
        )


        if score < best_score:

            best_score = score

            best_truck = truck_id


    if best_truck is None:

        raise RuntimeError(
            f"No truck has enough "
            f"capacity for {bin_id}"
        )


    truck_bins[
        best_truck
    ].append(
        bin_id
    )


    truck_loads[
        best_truck
    ] += waste


used_trucks = [
    truck_id
    for truck_id in truck_bins
    if truck_bins[
        truck_id
    ]
]


print(
    f"Bins assigned: "
    f"{len(assignment_candidates)}"
)

print(
    f"Trucks dispatched: "
    f"{len(used_trucks)}"
)


# ============================================================
# STEP 9 - SMART ROUTE CONSTRUCTION
# ============================================================

print(
    "\n[9/12] Building emergency-aware "
    "opportunistic routes..."
)


optimized_routes = []


for truck_id in used_trucks:

    truck = truck_data[
        truck_id
    ]


    assigned_ids = truck_bins[
        truck_id
    ]


    remaining = (
        candidates[
            candidates[
                "bin_id"
            ].isin(
                assigned_ids
            )
        ]
        .copy()
        .to_dict(
            "records"
        )
    )


    current_lat = truck[
        "depot_lat"
    ]

    current_lon = truck[
        "depot_lon"
    ]


    route_points = [
        (
            current_lat,
            current_lon
        )
    ]


    elapsed_hours = 0.0

    sequence = 1


    while remaining:

        current_point = (
            current_lat,
            current_lon
        )


        # ----------------------------------------------------
        # Find emergency bins.
        # ----------------------------------------------------

        emergency_bins = [
            item
            for item in remaining
            if item[
                "risk_level"
            ] == "EMERGENCY"
        ]


        # ----------------------------------------------------
        # If there are emergency bins, find the most urgent.
        # ----------------------------------------------------

        if emergency_bins:

            emergency_bins.sort(
                key=lambda x:
                    (
                        -float(
                            x[
                                "overflow_probability"
                            ]
                        ),
                        -float(
                            x[
                                "priority_score"
                            ]
                        )
                    )
            )


            emergency = emergency_bins[
                0
            ]


            emergency_point = (
                float(
                    emergency[
                        "latitude"
                    ]
                ),
                float(
                    emergency[
                        "longitude"
                    ]
                )
            )


            direct_distance = (
                haversine_distance(
                    current_point[0],
                    current_point[1],
                    emergency_point[0],
                    emergency_point[1]
                )
            )


            direct_time = (
                direct_distance
                /
                AVERAGE_SPEED_KMPH
            )


            # ------------------------------------------------
            # We need to determine whether another bin can
            # be collected before the emergency.
            # ------------------------------------------------

            best_opportunistic = None

            best_detour = float(
                "inf"
            )


            for candidate in remaining:

                if candidate[
                    "bin_id"
                ] == emergency[
                    "bin_id"
                ]:

                    continue


                candidate_point = (
                    float(
                        candidate[
                            "latitude"
                        ]
                    ),
                    float(
                        candidate[
                            "longitude"
                        ]
                    )
                )


                detour = calculate_detour(
                    current_point,
                    candidate_point,
                    emergency_point
                )


                candidate_distance = (
                    haversine_distance(
                        current_point[0],
                        current_point[1],
                        candidate_point[0],
                        candidate_point[1]
                    )
                )


                candidate_time = (
                    candidate_distance
                    /
                    AVERAGE_SPEED_KMPH
                )


                # ------------------------------------------------
                # Candidate is allowed before emergency only if:
                #
                # 1. It is very close to the emergency path.
                # 2. It does not cause excessive delay.
                # 3. Emergency remains within response target.
                # ------------------------------------------------

                resulting_time = (
                    elapsed_hours
                    +
                    (
                        candidate_distance
                        +
                        haversine_distance(
                            candidate_point[0],
                            candidate_point[1],
                            emergency_point[0],
                            emergency_point[1]
                        )
                    )
                    /
                    AVERAGE_SPEED_KMPH
                )


                response_safe = (
                    resulting_time
                    <=
                    EMERGENCY_RESPONSE_HOURS
                )


                if (
                    detour
                    <=
                    MAX_ON_WAY_DETOUR_KM
                    and
                    response_safe
                    and
                    detour
                    < best_detour
                ):

                    best_opportunistic = (
                        candidate
                    )

                    best_detour = (
                        detour
                    )


            # ------------------------------------------------
            # If a nearby bin is genuinely on the way,
            # collect it before the emergency.
            # ------------------------------------------------

            if best_opportunistic is not None:

                selected = (
                    best_opportunistic
                )

                decision_reason = (
                    "OPPORTUNISTIC_ON_WAY"
                )

            else:

                selected = emergency

                decision_reason = (
                    "EMERGENCY_PRIORITY"
                )


        else:

            # ------------------------------------------------
            # No emergency bins remain.
            #
            # Choose next bin based on:
            # distance + urgency.
            # ------------------------------------------------

            best_score = float(
                "inf"
            )

            selected = None

            decision_reason = (
                "COST_OPTIMIZED"
            )


            for candidate in remaining:

                point = (
                    float(
                        candidate[
                            "latitude"
                        ]
                    ),
                    float(
                        candidate[
                            "longitude"
                        ]
                    )
                )


                distance = (
                    haversine_distance(
                        current_point[0],
                        current_point[1],
                        point[0],
                        point[1]
                    )
                )


                urgency = float(
                    candidate[
                        "urgency_score"
                    ]
                )


                score = (
                    distance
                    -
                    urgency * 4
                )


                if score < best_score:

                    best_score = score

                    selected = candidate


        # ----------------------------------------------------
        # Add selected stop.
        # ----------------------------------------------------

        remaining.remove(
            selected
        )


        selected_point = (
            float(
                selected[
                    "latitude"
                ]
            ),
            float(
                selected[
                    "longitude"
                ]
            )
        )


        travel_distance = (
            haversine_distance(
                current_point[0],
                current_point[1],
                selected_point[0],
                selected_point[1]
            )
        )


        travel_time = (
            travel_distance
            /
            AVERAGE_SPEED_KMPH
        )


        elapsed_hours += (
            travel_time
            +
            SERVICE_TIME_MINUTES / 60
        )


        optimized_routes.append(
            {
                "truck_id":
                    truck_id,

                "stop_sequence":
                    sequence,

                "bin_id":
                    selected[
                        "bin_id"
                    ],

                "collection_zone":
                    selected[
                        "collection_zone"
                    ],

                "latitude":
                    selected[
                        "latitude"
                    ],

                "longitude":
                    selected[
                        "longitude"
                    ],

                "priority_score":
                    selected[
                        "priority_score"
                    ],

                "risk_level":
                    selected[
                        "risk_level"
                    ],

                "sensor_fill_level_pct":
                    selected[
                        "sensor_fill_level_pct"
                    ],

                # Display-safe value.
                "predicted_fill_6h_pct":
                    selected[
                        "displayed_predicted_fill_6h_pct"
                    ],

                # Preserve original model output.
                "raw_predicted_fill_6h_pct":
                    selected[
                        "raw_predicted_fill_6h_pct"
                    ],

                "predicted_overflow_pct":
                    selected[
                        "predicted_overflow_pct"
                    ],

                "overflow_probability":
                    selected[
                        "overflow_probability"
                    ],

                "urgency_score":
                    selected[
                        "urgency_score"
                    ],

                "estimated_waste_kg":
                    selected[
                        "estimated_waste_kg"
                    ],

                "route_decision":
                    decision_reason,

                "travel_distance_to_stop_km":
                    travel_distance
            }
        )


        current_lat = (
            selected_point[0]
        )

        current_lon = (
            selected_point[1]
        )


        route_points.append(
            selected_point
        )


        sequence += 1


    # --------------------------------------------------------
    # Return to depot.
    # --------------------------------------------------------

    route_points.append(
        (
            truck[
                "depot_lat"
            ],
            truck[
                "depot_lon"
            ]
        )
    )


    total_distance = (
        calculate_route_distance(
            route_points
        )
    )


    total_fuel = (
        total_distance
        /
        truck[
            "fuel_efficiency"
        ]
    )


    total_time = (
        total_distance
        /
        AVERAGE_SPEED_KMPH
        +
        len(assigned_ids)
        *
        SERVICE_TIME_MINUTES
        /
        60
    )


    # Add route-level information.
    for route in optimized_routes:

        if route[
            "truck_id"
        ] == truck_id:

            route[
                "route_distance_km"
            ] = total_distance

            route[
                "route_fuel_liters"
            ] = total_fuel

            route[
                "route_time_hours"
            ] = total_time

            route[
                "truck_capacity_kg"
            ] = truck[
                "capacity"
            ]

            route[
                "truck_load_kg"
            ] = truck_loads[
                truck_id
            ]


optimized_df = pd.DataFrame(
    optimized_routes
)


# ============================================================
# STEP 10 - SMART COST
# ============================================================

print(
    "\n[10/12] Calculating smart route costs..."
)


smart_rows = []


for truck_id in used_trucks:

    route = optimized_df[
        optimized_df[
            "truck_id"
        ] == truck_id
    ]


    distance = float(
        route[
            "route_distance_km"
        ].iloc[0]
    )


    fuel = float(
        route[
            "route_fuel_liters"
        ].iloc[0]
    )


    fuel_cost = (
        fuel
        *
        FUEL_PRICE_PER_LITER
    )


    distance_cost = (
        distance
        *
        VEHICLE_COST_PER_KM
    )


    dispatch_cost = (
        TRUCK_DISPATCH_COST
    )


    total_cost = (
        fuel_cost
        +
        distance_cost
        +
        dispatch_cost
    )


    smart_rows.append(
        {
            "truck_id":
                truck_id,

            "stops":
                len(route),

            "waste_kg":
                route[
                    "estimated_waste_kg"
                ].sum(),

            "distance_km":
                distance,

            "fuel_liters":
                fuel,

            "fuel_cost":
                fuel_cost,

            "distance_cost":
                distance_cost,

            "dispatch_cost":
                dispatch_cost,

            "total_cost":
                total_cost
        }
    )


smart_cost_df = pd.DataFrame(
    smart_rows
)


# ============================================================
# STEP 11 - BASELINE
# ============================================================

print(
    "\n[11/12] Creating conventional baseline..."
)


baseline_truck_bins = {
    truck_id: []
    for truck_id in truck_data
}


zone_trucks = {}


for truck_id, truck in truck_data.items():

    zone = truck[
        "home_zone"
    ]

    zone_trucks.setdefault(
        zone,
        []
    ).append(
        truck_id
    )


for item in candidates.to_dict(
    "records"
):

    zone = item[
        "collection_zone"
    ]


    if zone in zone_trucks:

        selected_truck = zone_trucks[
            zone
        ][0]

    else:

        selected_truck = min(
            truck_data.keys(),
            key=lambda tid:
                haversine_distance(
                    truck_data[
                        tid
                    ][
                        "depot_lat"
                    ],
                    truck_data[
                        tid
                    ][
                        "depot_lon"
                    ],
                    item[
                        "latitude"
                    ],
                    item[
                        "longitude"
                    ]
                )
        )


    baseline_truck_bins[
        selected_truck
    ].append(
        item[
            "bin_id"
        ]
    )


baseline_rows = []


for truck_id, bin_ids in baseline_truck_bins.items():

    if not bin_ids:

        continue


    truck = truck_data[
        truck_id
    ]


    bin_ids = sorted(
        bin_ids
    )


    points = [
        (
            truck[
                "depot_lat"
            ],
            truck[
                "depot_lon"
            ]
        )
    ]


    for bin_id in bin_ids:

        item = candidates[
            candidates[
                "bin_id"
            ]
            ==
            bin_id
        ].iloc[0]


        points.append(
            (
                item[
                    "latitude"
                ],
                item[
                    "longitude"
                ]
            )
        )


    points.append(
        (
            truck[
                "depot_lat"
            ],
            truck[
                "depot_lon"
            ]
        )
    )


    distance = (
        calculate_route_distance(
            points
        )
    )


    fuel = (
        distance
        /
        truck[
            "fuel_efficiency"
        ]
    )


    fuel_cost = (
        fuel
        *
        FUEL_PRICE_PER_LITER
    )


    distance_cost = (
        distance
        *
        VEHICLE_COST_PER_KM
    )


    dispatch_cost = (
        TRUCK_DISPATCH_COST
    )


    total_cost = (
        fuel_cost
        +
        distance_cost
        +
        dispatch_cost
    )


    baseline_rows.append(
        {
            "truck_id":
                truck_id,

            "stops":
                len(bin_ids),

            "waste_kg":
                candidates[
                    candidates[
                        "bin_id"
                    ].isin(
                        bin_ids
                    )
                ][
                    "estimated_waste_kg"
                ].sum(),

            "distance_km":
                distance,

            "fuel_liters":
                fuel,

            "fuel_cost":
                fuel_cost,

            "distance_cost":
                distance_cost,

            "dispatch_cost":
                dispatch_cost,

            "total_cost":
                total_cost
        }
    )


baseline_df = pd.DataFrame(
    baseline_rows
)


# ============================================================
# STEP 12 - FINAL RESULTS
# ============================================================

print(
    "\n[12/12] Calculating final savings..."
)


baseline_distance = (
    baseline_df[
        "distance_km"
    ].sum()
)


smart_distance = (
    smart_cost_df[
        "distance_km"
    ].sum()
)


baseline_fuel = (
    baseline_df[
        "fuel_liters"
    ].sum()
)


smart_fuel = (
    smart_cost_df[
        "fuel_liters"
    ].sum()
)


baseline_cost = (
    baseline_df[
        "total_cost"
    ].sum()
)


smart_cost = (
    smart_cost_df[
        "total_cost"
    ].sum()
)


baseline_trucks = len(
    baseline_df
)


smart_trucks = len(
    smart_cost_df
)


distance_saved = (
    baseline_distance
    -
    smart_distance
)


fuel_saved = (
    baseline_fuel
    -
    smart_fuel
)


cost_saved = (
    baseline_cost
    -
    smart_cost
)


distance_pct = (
    distance_saved
    /
    baseline_distance
    *
    100
    if baseline_distance > 0
    else 0
)


fuel_pct = (
    fuel_saved
    /
    baseline_fuel
    *
    100
    if baseline_fuel > 0
    else 0
)


cost_pct = (
    cost_saved
    /
    baseline_cost
    *
    100
    if baseline_cost > 0
    else 0
)


truck_reduction = (
    baseline_trucks
    -
    smart_trucks
)


truck_pct = (
    truck_reduction
    /
    baseline_trucks
    *
    100
    if baseline_trucks > 0
    else 0
)


# ============================================================
# PRINT RESULTS
# ============================================================

print(
    "\n============================================="
)

print(
    "FLEET-LEVEL OPTIMIZATION RESULTS"
)

print(
    "============================================="
)


print(
    f"Bins evaluated       : "
    f"{len(latest_bins)}"
)

print(
    f"Collection candidates: "
    f"{len(candidates)}"
)


print(
    "\nTRUCKS"
)

print(
    f"Baseline : "
    f"{baseline_trucks}"
)

print(
    f"Smart    : "
    f"{smart_trucks}"
)

print(
    f"Reduction: "
    f"{truck_reduction} "
    f"({truck_pct:.2f}%)"
)


print(
    "\nDISTANCE"
)

print(
    f"Baseline : "
    f"{baseline_distance:.2f} km"
)

print(
    f"Smart    : "
    f"{smart_distance:.2f} km"
)

print(
    f"Saved    : "
    f"{distance_saved:.2f} km"
)

print(
    f"Savings  : "
    f"{distance_pct:.2f}%"
)


print(
    "\nFUEL"
)

print(
    f"Baseline : "
    f"{baseline_fuel:.2f} L"
)

print(
    f"Smart    : "
    f"{smart_fuel:.2f} L"
)

print(
    f"Saved    : "
    f"{fuel_saved:.2f} L"
)

print(
    f"Savings  : "
    f"{fuel_pct:.2f}%"
)


print(
    "\nOPERATING COST"
)

print(
    f"Baseline : "
    f"Rs. {baseline_cost:.2f}"
)

print(
    f"Smart    : "
    f"Rs. {smart_cost:.2f}"
)

print(
    f"Saved    : "
    f"Rs. {cost_saved:.2f}"
)

print(
    f"Savings  : "
    f"{cost_pct:.2f}%"
)


# ============================================================
# ROUTES
# ============================================================

print(
    "\n============================================="
)

print(
    "SMART COLLECTION ROUTES"
)

print(
    "============================================="
)


for truck_id in sorted(
    optimized_df[
        "truck_id"
    ].unique()
):

    route = optimized_df[
        optimized_df[
            "truck_id"
        ]
        ==
        truck_id
    ].sort_values(
        "stop_sequence"
    )


    print(
        f"\nTruck {truck_id}"
    )

    print(
        "-" * 65
    )


    for row in route.itertuples():

        print(
            f"{row.stop_sequence}. "
            f"{row.bin_id} | "
            f"{row.risk_level} | "
            f"Fill="
            f"{row.predicted_fill_6h_pct:.1f}% | "
            f"Overflow="
            f"{row.predicted_overflow_pct:.1f}% | "
            f"Decision="
            f"{row.route_decision}"
        )


# ============================================================
# SAVE ASSIGNMENTS
# ============================================================

assignment_map = {}


for truck_id in used_trucks:

    for bin_id in truck_bins[
        truck_id
    ]:

        assignment_map[
            bin_id
        ] = truck_id


assignment_df = candidates[
    [
        "bin_id",
        "collection_zone",
        "sensor_fill_level_pct",
        "displayed_predicted_fill_6h_pct",
        "raw_predicted_fill_6h_pct",
        "predicted_overflow_pct",
        "overflow_probability",
        "priority_score",
        "risk_level",
        "urgency_score",
        "estimated_waste_kg"
    ]
].copy()


assignment_df[
    "truck_id"
] = assignment_df[
    "bin_id"
].map(
    assignment_map
)


assignment_df.to_csv(
    ASSIGNMENT_FILE,
    index=False
)


# ============================================================
# SAVE COMPARISON
# ============================================================

comparison_df = pd.DataFrame(
    {
        "metric": [
            "trucks_dispatched",
            "distance_km",
            "fuel_liters",
            "operating_cost"
        ],

        "baseline": [
            baseline_trucks,
            baseline_distance,
            baseline_fuel,
            baseline_cost
        ],

        "smart": [
            smart_trucks,
            smart_distance,
            smart_fuel,
            smart_cost
        ],

        "saved": [
            truck_reduction,
            distance_saved,
            fuel_saved,
            cost_saved
        ],

        "savings_percent": [
            truck_pct,
            distance_pct,
            fuel_pct,
            cost_pct
        ]
    }
)


comparison_df.to_csv(
    COMPARISON_FILE,
    index=False
)


# ============================================================
# SAVE SUMMARY
# ============================================================

summary_df = pd.DataFrame(
    [
        {
            "metric":
                "bins_evaluated",
            "value":
                len(latest_bins)
        },

        {
            "metric":
                "collection_candidates",
            "value":
                len(candidates)
        },

        {
            "metric":
                "baseline_trucks",
            "value":
                baseline_trucks
        },

        {
            "metric":
                "smart_trucks",
            "value":
                smart_trucks
        },

        {
            "metric":
                "distance_savings_percent",
            "value":
                distance_pct
        },

        {
            "metric":
                "fuel_savings_percent",
            "value":
                fuel_pct
        },

        {
            "metric":
                "cost_savings_percent",
            "value":
                cost_pct
        }
    ]
)


summary_df.to_csv(
    SUMMARY_FILE,
    index=False
)


optimized_df.to_csv(
    ROUTE_FILE,
    index=False
)


# ============================================================
# FINAL
# ============================================================

print(
    "\nSaved:"
)

print(
    ROUTE_FILE
)

print(
    ASSIGNMENT_FILE
)

print(
    COMPARISON_FILE
)

print(
    SUMMARY_FILE
)


print(
    "\n" + "=" * 70
)

print(
    "ROUTE OPTIMIZATION V6 COMPLETED SUCCESSFULLY"
)

print(
    "=" * 70
)