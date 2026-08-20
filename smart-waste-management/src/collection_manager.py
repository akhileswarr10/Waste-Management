"""
SMART WASTE MANAGEMENT
PHASE 5 - DRIVER COLLECTION MANAGEMENT

Purpose:
    Simulate the operational workflow used by truck drivers.

Workflow:

ASSIGNED
    ↓
IN PROGRESS
    ↓
COLLECTION COMPLETED
    ↓
BIN RESET
    ↓
NEXT BIN

Important:
    This module NEVER modifies the ML training dataset.

    It creates/updates:
        data/processed/operational_bin_state.csv

This represents the live operational state of the bins.
"""

import os
import pandas as pd
from datetime import datetime


# ============================================================
# PATHS
# ============================================================

DATA_DIR = "data/processed"

ROUTE_FILE = os.path.join(
    DATA_DIR,
    "optimized_routes.csv"
)

PRIORITY_FILE = os.path.join(
    DATA_DIR,
    "priority_predictions.csv"
)

STATE_FILE = os.path.join(
    DATA_DIR,
    "operational_bin_state.csv"
)


# ============================================================
# CONSTANTS
# ============================================================

RESET_FILL_LEVEL = 0.0


# ============================================================
# LOAD CURRENT BIN STATE
# ============================================================

def create_initial_state():

    print(
        "\nCreating operational bin state..."
    )


    priority_df = pd.read_csv(
        PRIORITY_FILE
    )


    priority_df["timestamp"] = pd.to_datetime(
        priority_df["timestamp"]
    )


    # Get latest observation for every bin.
    latest = (
        priority_df
        .sort_values("timestamp")
        .groupby(
            "bin_id",
            as_index=False
        )
        .tail(1)
        .copy()
    )


    state = latest[
        [
            "bin_id",
            "timestamp",
            "sensor_fill_level_pct",
            "predicted_fill_6h_pct",
            "risk_level"
        ]
    ].copy()


    state[
        "operational_fill_level_pct"
    ] = state[
        "sensor_fill_level_pct"
    ]


    state[
        "collection_status"
    ] = "PENDING"


    state[
        "assigned_truck"
    ] = ""


    state[
        "collection_started_at"
    ] = ""


    state[
        "collection_completed_at"
    ] = ""


    state[
        "last_reset_at"
    ] = ""


    state[
        "collection_count"
    ] = 0


    state.to_csv(
        STATE_FILE,
        index=False
    )


    print(
        f"Created: {STATE_FILE}"
    )


    return state


# ============================================================
# LOAD STATE
# ============================================================

def load_state():

    if not os.path.exists(
        STATE_FILE
    ):

        return create_initial_state()


    return pd.read_csv(
        STATE_FILE
    )


# ============================================================
# LOAD ROUTES
# ============================================================

def load_routes():

    if not os.path.exists(
        ROUTE_FILE
    ):

        raise FileNotFoundError(
            "optimized_routes.csv not found. "
            "Run route_optimizer.py first."
        )


    return pd.read_csv(
        ROUTE_FILE
    )


# ============================================================
# ASSIGN ROUTES
# ============================================================

def apply_assignments(
    state,
    routes
):

    for row in routes.itertuples(
        index=False
    ):

        mask = (
            state["bin_id"]
            ==
            row.bin_id
        )


        state.loc[
            mask,
            "assigned_truck"
        ] = row.truck_id


        state.loc[
            mask,
            "collection_status"
        ] = "ASSIGNED"


    return state


# ============================================================
# SHOW TRUCK ROUTE
# ============================================================

def show_truck_route(
    truck_id
):

    state = load_state()

    routes = load_routes()


    route = routes[
        routes["truck_id"]
        ==
        truck_id
    ].sort_values(
        "stop_sequence"
    )


    if route.empty:

        print(
            f"\nNo route found for {truck_id}."
        )

        return


    print(
        "\n============================================="
    )

    print(
        f"DRIVER ROUTE - {truck_id}"
    )

    print(
        "============================================="
    )


    for row in route.itertuples():

        current = state[
            state["bin_id"]
            ==
            row.bin_id
        ]


        if current.empty:

            status = "UNKNOWN"

        else:

            status = current[
                "collection_status"
            ].iloc[0]


        print(
            f"\nStop {row.stop_sequence}"
        )

        print(
            f"Bin       : {row.bin_id}"
        )

        print(
            f"Risk      : {row.risk_level}"
        )

        print(
            f"Predicted : "
            f"{row.predicted_fill_6h_pct:.1f}%"
        )

        print(
            f"Overflow  : "
            f"{row.overflow_probability:.1f}%"
        )

        print(
            f"Status    : {status}"
        )


# ============================================================
# START COLLECTION
# ============================================================

def start_collection(
    truck_id,
    bin_id
):

    state = load_state()


    mask = (
        (state["bin_id"] == bin_id)
        &
        (
            state[
                "assigned_truck"
            ]
            ==
            truck_id
        )
    )


    if not mask.any():

        print(
            "This bin is not assigned "
            f"to {truck_id}."
        )

        return


    state.loc[
        mask,
        "collection_status"
    ] = "IN PROGRESS"


    state.loc[
        mask,
        "collection_started_at"
    ] = datetime.now().isoformat(
        timespec="seconds"
    )


    state.to_csv(
        STATE_FILE,
        index=False
    )


    print(
        f"\nCollection started: "
        f"{bin_id}"
    )


# ============================================================
# COMPLETE COLLECTION
# ============================================================

def complete_collection(
    truck_id,
    bin_id
):

    state = load_state()


    mask = (
        (state["bin_id"] == bin_id)
        &
        (
            state[
                "assigned_truck"
            ]
            ==
            truck_id
        )
    )


    if not mask.any():

        print(
            "Invalid truck/bin assignment."
        )

        return


    # --------------------------------------------------------
    # Mark collection completed.
    # --------------------------------------------------------

    state.loc[
        mask,
        "collection_status"
    ] = "COLLECTED"


    state.loc[
        mask,
        "collection_completed_at"
    ] = datetime.now().isoformat(
        timespec="seconds"
    )


    # --------------------------------------------------------
    # RESET LIVE BIN LEVEL
    # --------------------------------------------------------

    state.loc[
        mask,
        "operational_fill_level_pct"
    ] = RESET_FILL_LEVEL


    state.loc[
        mask,
        "collection_count"
    ] += 1


    state.loc[
        mask,
        "last_reset_at"
    ] = datetime.now().isoformat(
        timespec="seconds"
    )


    state.to_csv(
        STATE_FILE,
        index=False
    )


    print(
        "\n============================================="
    )

    print(
        "COLLECTION COMPLETED"
    )

    print(
        "============================================="
    )

    print(
        f"Truck : {truck_id}"
    )

    print(
        f"Bin   : {bin_id}"
    )

    print(
        "Status: COLLECTED"
    )

    print(
        "Fill level reset to: 0%"
    )


# ============================================================
# DRIVER MODE
# ============================================================

def driver_mode(
    truck_id
):

    state = load_state()

    routes = load_routes()


    route = routes[
        routes["truck_id"]
        ==
        truck_id
    ].sort_values(
        "stop_sequence"
    )


    if route.empty:

        print(
            f"No route found for {truck_id}."
        )

        return


    print(
        "\n============================================="
    )

    print(
        f"DRIVER MODE - {truck_id}"
    )

    print(
        "============================================="
    )


    while True:

        # ----------------------------------------------------
        # Find first incomplete stop.
        # ----------------------------------------------------

        current_stop = None


        for row in route.itertuples():

            status = state[
                state["bin_id"]
                ==
                row.bin_id
            ][
                "collection_status"
            ].iloc[0]


            if status != "COLLECTED":

                current_stop = row

                break


        # ----------------------------------------------------
        # Route completed.
        # ----------------------------------------------------

        if current_stop is None:

            print(
                "\nALL COLLECTIONS COMPLETED!"
            )

            break


        print(
            "\n---------------------------------------------"
        )

        print(
            f"NEXT STOP: "
            f"{current_stop.bin_id}"
        )

        print(
            "---------------------------------------------"
        )

        print(
            f"Stop       : "
            f"{current_stop.stop_sequence}"
        )

        print(
            f"Risk       : "
            f"{current_stop.risk_level}"
        )

        print(
            f"Predicted  : "
            f"{current_stop.predicted_fill_6h_pct:.1f}%"
        )

        print(
            f"Overflow   : "
            f"{current_stop.overflow_probability:.1f}%"
        )


        print(
            "\n1. Start Collection"
        )

        print(
            "2. Collection Completed"
        )

        print(
            "3. Show Route"
        )

        print(
            "4. Exit Driver Mode"
        )


        choice = input(
            "\nChoose: "
        ).strip()


        if choice == "1":

            start_collection(
                truck_id,
                current_stop.bin_id
            )


            state = load_state()


        elif choice == "2":

            complete_collection(
                truck_id,
                current_stop.bin_id
            )


            state = load_state()


        elif choice == "3":

            show_truck_route(
                truck_id
            )


        elif choice == "4":

            print(
                "\nExiting driver mode."
            )

            break


        else:

            print(
                "Invalid choice."
            )


# ============================================================
# MAIN MENU
# ============================================================

def main():

    state = load_state()

    routes = load_routes()


    # Apply current route assignments.
    state = apply_assignments(
        state,
        routes
    )


    state.to_csv(
        STATE_FILE,
        index=False
    )


    while True:

        print(
            "\n============================================="
        )

        print(
            "SMART WASTE MANAGEMENT"
        )

        print(
            "DRIVER COLLECTION MANAGEMENT"
        )

        print(
            "============================================="
        )

        print(
            "1. Show truck route"
        )

        print(
            "2. Start driver mode"
        )

        print(
            "3. Complete a collection"
        )

        print(
            "4. Show operational bin state"
        )

        print(
            "5. Exit"
        )


        choice = input(
            "\nChoose: "
        ).strip()


        if choice == "1":

            truck_id = input(
                "Enter truck ID: "
            ).strip().upper()


            show_truck_route(
                truck_id
            )


        elif choice == "2":

            truck_id = input(
                "Enter truck ID: "
            ).strip().upper()


            driver_mode(
                truck_id
            )


        elif choice == "3":

            truck_id = input(
                "Truck ID: "
            ).strip().upper()


            bin_id = input(
                "Bin ID: "
            ).strip().upper()


            complete_collection(
                truck_id,
                bin_id
            )


        elif choice == "4":

            current_state = load_state()

            print(
                "\nCURRENT OPERATIONAL STATE"
            )

            print(
                current_state[
                    [
                        "bin_id",
                        "operational_fill_level_pct",
                        "collection_status",
                        "assigned_truck",
                        "collection_count"
                    ]
                ].to_string(
                    index=False
                )
            )


        elif choice == "5":

            print(
                "\nExiting."
            )

            break


        else:

            print(
                "Invalid choice."
            )


# ============================================================
# RUN
# ============================================================

if __name__ == "__main__":

    main()