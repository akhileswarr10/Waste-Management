"""
SMART WASTE MANAGEMENT
PHASE 4 - ROUTE VISUALIZATION

Creates an interactive HTML map from the optimized routes.

Input:
    data/processed/optimized_routes.csv

Output:
    outputs/route_map.html
"""

import os
import pandas as pd
import folium
from folium.plugins import PolyLineTextPath


# ============================================================
# FILE PATHS
# ============================================================

ROUTE_FILE = "data/processed/optimized_routes.csv"

OUTPUT_DIR = "outputs"

OUTPUT_FILE = os.path.join(
    OUTPUT_DIR,
    "route_map.html"
)


# ============================================================
# SETTINGS
# ============================================================

os.makedirs(
    OUTPUT_DIR,
    exist_ok=True
)


# ============================================================
# HEADER
# ============================================================

print("=" * 70)
print("SMART WASTE MANAGEMENT")
print("PHASE 4 - INTERACTIVE ROUTE VISUALIZATION")
print("=" * 70)


# ============================================================
# STEP 1 - LOAD ROUTES
# ============================================================

print("\n[1/6] Loading optimized routes...")

if not os.path.exists(ROUTE_FILE):

    raise FileNotFoundError(
        f"\nRoute file not found:\n{ROUTE_FILE}\n\n"
        "Run the following first:\n"
        "python src/route_optimizer.py"
    )


routes = pd.read_csv(
    ROUTE_FILE
)


print(
    f"Route records: {routes.shape}"
)


# ============================================================
# STEP 2 - VALIDATE COLUMNS
# ============================================================

print("\n[2/6] Checking route data...")

required_columns = [
    "truck_id",
    "stop_sequence",
    "bin_id",
    "collection_zone",
    "latitude",
    "longitude",
    "risk_level",
    "sensor_fill_level_pct",
    "predicted_fill_6h_pct",
    "raw_predicted_fill_6h_pct",
    "predicted_overflow_pct",
    "overflow_probability",
    "priority_score",
    "route_decision"
]


missing_columns = [
    column
    for column in required_columns
    if column not in routes.columns
]


if missing_columns:

    raise ValueError(
        "Missing columns in optimized_routes.csv:\n"
        + "\n".join(missing_columns)
    )


print("All required columns found.")


# ============================================================
# STEP 3 - PREPARE DATA
# ============================================================

print("\n[3/6] Preparing map data...")


routes = routes.sort_values(
    [
        "truck_id",
        "stop_sequence"
    ]
)


# Convert coordinates to numeric.
routes["latitude"] = pd.to_numeric(
    routes["latitude"],
    errors="coerce"
)

routes["longitude"] = pd.to_numeric(
    routes["longitude"],
    errors="coerce"
)


routes = routes.dropna(
    subset=[
        "latitude",
        "longitude"
    ]
)


# ============================================================
# FIND MAP CENTER
# ============================================================

center_lat = routes[
    "latitude"
].mean()

center_lon = routes[
    "longitude"
].mean()


print(
    f"Map center: "
    f"{center_lat:.6f}, "
    f"{center_lon:.6f}"
)


# ============================================================
# CREATE MAP
# ============================================================

print("\n[4/6] Creating interactive map...")


route_map = folium.Map(
    location=[
        center_lat,
        center_lon
    ],
    zoom_start=13,
    control_scale=True
)


# ============================================================
# COLOR FUNCTIONS
# ============================================================

def get_risk_color(risk):

    risk = str(
        risk
    ).upper()

    if risk == "EMERGENCY":
        return "red"

    if risk == "HIGH":
        return "orange"

    if risk == "MEDIUM":
        return "blue"

    return "green"


def get_route_color(index):

    colors = [
        "blue",
        "red",
        "green",
        "purple",
        "orange",
        "darkred",
        "darkblue",
        "cadetblue",
        "darkgreen",
        "pink"
    ]

    return colors[
        index % len(colors)
    ]


# ============================================================
# CREATE LAYERS
# ============================================================

route_layers = {}


for index, truck_id in enumerate(
    routes["truck_id"].unique()
):

    route_layers[
        truck_id
    ] = folium.FeatureGroup(
        name=f"Truck {truck_id}"
    )

    route_layers[
        truck_id
    ].add_to(
        route_map
    )


# ============================================================
# STEP 5 - ADD ROUTES AND MARKERS
# ============================================================

print("\n[5/6] Drawing truck routes...")


for truck_index, truck_id in enumerate(
    routes["truck_id"].unique()
):

    truck_route = routes[
        routes["truck_id"]
        ==
        truck_id
    ].sort_values(
        "stop_sequence"
    )


    route_color = get_route_color(
        truck_index
    )


    # --------------------------------------------------------
    # Route coordinates
    # --------------------------------------------------------

    coordinates = []

    for row in truck_route.itertuples():

        coordinates.append(
            [
                row.latitude,
                row.longitude
            ]
        )


    # --------------------------------------------------------
    # Draw route line
    # --------------------------------------------------------

    if len(coordinates) >= 2:

        line = folium.PolyLine(
            coordinates,
            color=route_color,
            weight=5,
            opacity=0.8,
            tooltip=f"Truck {truck_id} route"
        )

        line.add_to(
            route_layers[
                truck_id
            ]
        )


    # --------------------------------------------------------
    # Add direction arrows
    # --------------------------------------------------------

    if len(coordinates) >= 2:

        try:

            arrow_line = folium.PolyLine(
                coordinates,
                color=route_color,
                weight=2,
                opacity=0.0
            )

            arrow_line.add_to(
                route_layers[
                    truck_id
                ]
            )


            PolyLineTextPath(
                arrow_line,
                "➤    ",
                repeat=True,
                offset=7,
                attributes={
                    "fill": route_color,
                    "font-weight": "bold",
                    "font-size": "16"
                }
            ).add_to(
                route_layers[
                    truck_id
                ]
            )

        except Exception:

            pass


    # --------------------------------------------------------
    # Add markers
    # --------------------------------------------------------

    for row in truck_route.itertuples():

        risk = str(
            row.risk_level
        ).upper()


        marker_color = get_risk_color(
            risk
        )


        # ----------------------------------------------------
        # Display-safe fill
        # ----------------------------------------------------

        displayed_fill = min(
            max(
                float(
                    row.predicted_fill_6h_pct
                ),
                0
            ),
            100
        )


        raw_prediction = float(
            row.raw_predicted_fill_6h_pct
        )


        overflow_amount = max(
            raw_prediction - 100,
            0
        )


        overflow_probability = float(
            row.overflow_probability
        )


        priority = float(
            row.priority_score
        )


        sensor_fill = float(
            row.sensor_fill_level_pct
        )


        # ----------------------------------------------------
        # Decision text
        # ----------------------------------------------------

        decision = str(
            row.route_decision
        )


        if decision == "OPPORTUNISTIC_ON_WAY":

            decision_text = (
                "Collected opportunistically "
                "while approaching another priority bin."
            )

        elif decision == "EMERGENCY_PRIORITY":

            decision_text = (
                "Emergency collection priority."
            )

        else:

            decision_text = (
                "Selected for route efficiency."
            )


        # ----------------------------------------------------
        # Popup HTML
        # ----------------------------------------------------

        popup_html = f"""
        <div style="
            width: 300px;
            font-family: Arial;
        ">

            <h3 style="margin-bottom: 5px;">
                🗑️ Bin {row.bin_id}
            </h3>

            <hr>

            <b>Truck:</b>
            {row.truck_id}
            <br>

            <b>Route Stop:</b>
            {row.stop_sequence}
            <br>

            <b>Zone:</b>
            {row.collection_zone}
            <br>

            <b>Risk Level:</b>
            {risk}
            <br>

            <b>Priority Score:</b>
            {priority:.2f}
            <br>

            <b>Current Sensor Fill:</b>
            {sensor_fill:.1f}%
            <br>

            <b>Predicted Fill:</b>
            {displayed_fill:.1f}%
            <br>

            <b>Raw ML Prediction:</b>
            {raw_prediction:.1f}%
            <br>

            <b>Predicted Overflow:</b>
            {overflow_amount:.1f}%
            <br>

            <b>Overflow Probability:</b>
            {overflow_probability:.1f}%
            <br>

            <b>Route Decision:</b>
            {decision}
            <br>

            <br>

            <b>Why this stop?</b>
            <br>

            {decision_text}

        </div>
        """


        popup = folium.Popup(
            popup_html,
            max_width=350
        )


        # ----------------------------------------------------
        # Marker
        # ----------------------------------------------------

        folium.Marker(
            location=[
                row.latitude,
                row.longitude
            ],

            popup=popup,

            tooltip=(
                f"Stop {row.stop_sequence} | "
                f"{row.bin_id} | "
                f"{risk}"
            ),

            icon=folium.Icon(
                color=marker_color,
                icon="trash",
                prefix="fa"
            )

        ).add_to(
            route_layers[
                truck_id
            ]
        )


# ============================================================
# LEGEND
# ============================================================

legend_html = """
<div style="
    position: fixed;
    bottom: 30px;
    left: 30px;
    width: 220px;
    z-index: 9999;
    background-color: white;
    border: 2px solid grey;
    border-radius: 8px;
    padding: 12px;
    font-size: 14px;
">

<b>Waste Bin Risk</b>

<br><br>

<span style="
    color:red;
    font-size:18px;
">●</span>
Emergency

<br>

<span style="
    color:orange;
    font-size:18px;
">●</span>
High

<br>

<span style="
    color:blue;
    font-size:18px;
">●</span>
Medium

<br>

<span style="
    color:green;
    font-size:18px;
">●</span>
Low

<br><br>

<b>Route Lines</b>

<br>

Each color represents a truck.

</div>
"""


route_map.get_root().html.add_child(
    folium.Element(
        legend_html
    )
)


# ============================================================
# TITLE
# ============================================================

title_html = """
<div style="
    position: fixed;
    top: 10px;
    left: 50%;
    transform: translateX(-50%);
    z-index: 9999;
    background-color: white;
    padding: 10px 20px;
    border: 2px solid #444;
    border-radius: 8px;
    font-family: Arial;
    font-size: 18px;
    font-weight: bold;
">

Smart Waste Management
<br>

<span style="
    font-size: 13px;
    font-weight: normal;
">

AI-Powered Collection Route

</span>

</div>
"""


route_map.get_root().html.add_child(
    folium.Element(
        title_html
    )
)


# ============================================================
# LAYER CONTROL
# ============================================================

folium.LayerControl(
    collapsed=False
).add_to(
    route_map
)


# ============================================================
# SAVE
# ============================================================

print("\n[6/6] Saving interactive map...")


route_map.save(
    OUTPUT_FILE
)


print(
    "\nMap saved:"
)

print(
    OUTPUT_FILE
)


print(
    "\n" + "=" * 70
)

print(
    "ROUTE VISUALIZATION COMPLETED SUCCESSFULLY"
)

print(
    "=" * 70
)