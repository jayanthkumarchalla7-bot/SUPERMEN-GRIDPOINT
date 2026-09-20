from __future__ import annotations

from typing import Any

import pandas as pd

from distance import haversine_distance


def simulate_warehouse_failure(
    neighborhoods: pd.DataFrame,
    original_result: dict[str, Any],
    failed_warehouse: str,
    optimizer_function=None,
    **optimizer_kwargs,
) -> dict[str, Any]:
    """Simulate a warehouse failure with constrained reassignment.

    Affected neighborhoods are reassigned only to remaining warehouses from the
    original optimized network. Reassignment respects the configured capacity
    and service-radius constraints when those constraints are supplied.
    The optional optimizer_function argument is retained for API compatibility.
    """

    if neighborhoods is None or neighborhoods.empty:
        raise ValueError("Neighborhood dataset is empty.")

    warehouses = original_result.get("warehouses")
    assignments = original_result.get("assignments")

    if not isinstance(warehouses, pd.DataFrame) or not isinstance(assignments, pd.DataFrame):
        raise ValueError("Original optimization result is missing warehouse or assignment data.")

    failed_rows = warehouses[warehouses["warehouse_id"].astype(str) == str(failed_warehouse)]
    if failed_rows.empty:
        raise ValueError(f"Selected warehouse '{failed_warehouse}' does not exist.")

    failed_assignment = assignments[
        assignments["warehouse"].astype(str) == str(failed_warehouse)
    ].copy()

    affected_orders = float(failed_assignment["daily_orders"].sum())
    affected_neighborhoods = int(len(failed_assignment))

    remaining_warehouses = warehouses[
        warehouses["warehouse_id"].astype(str) != str(failed_warehouse)
    ].copy()

    if remaining_warehouses.empty and affected_neighborhoods:
        return {
            "failed_warehouse": str(failed_warehouse),
            "affected_orders": affected_orders,
            "affected_neighborhoods": affected_neighborhoods,
            "reassignment": pd.DataFrame(),
            "additional_distance": float("nan"),
            "distance_change_percent": float("nan"),
            "remaining_warehouses": remaining_warehouses,
            "feasible": False,
            "reason": "No remaining warehouse is available for reassignment.",
        }

    capacity = optimizer_kwargs.get("warehouse_capacity")
    max_service_radius = optimizer_kwargs.get("max_service_radius")

    remaining_capacity = {}
    for _, warehouse in remaining_warehouses.iterrows():
        wid = str(warehouse["warehouse_id"])
        if capacity is None:
            remaining_capacity[wid] = float("inf")
        else:
            remaining_capacity[wid] = float(capacity) - float(
                assignments.loc[
                    assignments["warehouse"].astype(str) == wid,
                    "daily_orders",
                ].sum()
            )

    # Reassign largest-demand neighborhoods first. This is a deterministic
    # capacity-aware heuristic for resilience analysis, not a replacement for
    # the main MILP optimizer.
    failed_assignment = failed_assignment.sort_values(
        "daily_orders", ascending=False
    )

    reassigned_rows = []
    unassigned = []

    for _, row in failed_assignment.iterrows():
        candidates = []
        for _, warehouse in remaining_warehouses.iterrows():
            wid = str(warehouse["warehouse_id"])
            distance_km = haversine_distance(
                float(row["latitude"]),
                float(row["longitude"]),
                float(warehouse["latitude"]),
                float(warehouse["longitude"]),
            )

            if (
                max_service_radius is not None
                and distance_km > float(max_service_radius) + 1e-9
            ):
                continue

            orders = float(row["daily_orders"])
            if remaining_capacity[wid] + 1e-9 < orders:
                continue

            candidates.append((distance_km, wid, warehouse))

        if not candidates:
            unassigned.append(row["neighborhood"])
            continue

        distance_km, wid, warehouse = min(candidates, key=lambda x: (x[0], x[1]))
        remaining_capacity[wid] -= float(row["daily_orders"])

        reassigned_rows.append(
            {
                "neighborhood": row["neighborhood"],
                "orders": float(row["daily_orders"]),
                "original_warehouse": str(failed_warehouse),
                "recommended_warehouse": wid,
                "original_distance_km": float(row["distance_km"]),
                "estimated_distance_km": float(distance_km),
                "remaining_capacity_after": (
                    None
                    if capacity is None
                    else float(remaining_capacity[wid])
                ),
            }
        )

    reassignment = pd.DataFrame(reassigned_rows)

    original_distance = float(
        (
            failed_assignment["distance_km"].astype(float)
            * failed_assignment["daily_orders"].astype(float)
        ).sum()
    )

    if not reassignment.empty:
        new_distance = float(
            (
                reassignment["estimated_distance_km"].astype(float)
                * reassignment["orders"].astype(float)
            ).sum()
        )
    else:
        new_distance = 0.0

    additional_distance = new_distance - original_distance
    distance_change_percent = (
        additional_distance / original_distance * 100
        if original_distance > 0
        else 0.0
    )

    feasible = len(unassigned) == 0
    reason = (
        "All affected neighborhoods were reassigned within the remaining network."
        if feasible
        else (
            f"{len(unassigned)} affected neighborhood(s) could not be reassigned "
            "within the remaining capacity/service-radius constraints."
        )
    )

    return {
        "failed_warehouse": str(failed_warehouse),
        "affected_orders": affected_orders,
        "affected_neighborhoods": affected_neighborhoods,
        "reassignment": reassignment,
        "additional_distance": additional_distance,
        "distance_change_percent": distance_change_percent,
        "remaining_warehouses": remaining_warehouses,
        "feasible": feasible,
        "unassigned_neighborhoods": unassigned,
        "reason": reason,
    }
