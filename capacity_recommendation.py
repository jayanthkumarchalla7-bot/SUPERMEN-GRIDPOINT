from __future__ import annotations

import math
from typing import Any

import pandas as pd


DEFAULT_BUFFER_PERCENTAGE = 15.0
MIN_BUFFER_PERCENTAGE = 0.0
MAX_BUFFER_PERCENTAGE = 50.0


def _validate_inputs(
    neighborhoods: pd.DataFrame,
    number_of_warehouses: int,
    buffer_percentage: float,
) -> None:
    if neighborhoods is None or neighborhoods.empty:
        raise ValueError("Neighborhood dataset is empty.")
    if "daily_orders" not in neighborhoods.columns:
        raise ValueError("Neighborhood data is missing the 'daily_orders' column.")
    warehouse_count = int(number_of_warehouses)
    if warehouse_count <= 0:
        raise ValueError("number_of_warehouses must be greater than zero.")
    buffer = float(buffer_percentage)
    if not MIN_BUFFER_PERCENTAGE <= buffer <= MAX_BUFFER_PERCENTAGE:
        raise ValueError(
            f"buffer_percentage must be between {MIN_BUFFER_PERCENTAGE:.0f}% and "
            f"{MAX_BUFFER_PERCENTAGE:.0f}%."
        )


def _round_up(value: float, step: int = 1) -> int:
    if step <= 0:
        raise ValueError("step must be greater than zero.")
    return int(math.ceil(value / step) * step)


def recommend_warehouse_capacity(
    neighborhoods: pd.DataFrame,
    number_of_warehouses: int,
    buffer_percentage: float = DEFAULT_BUFFER_PERCENTAGE,
    rounding: int = 1,
) -> dict[str, Any]:
    """Return a transparent capacity-planning recommendation.

    Only baseline neighborhood demand, warehouse count and the configurable
    operational buffer are used. The recommendation is not an optimizer constraint.
    """
    _validate_inputs(neighborhoods, number_of_warehouses, buffer_percentage)
    demand = pd.to_numeric(neighborhoods["daily_orders"], errors="coerce")
    if demand.isna().any() or (demand <= 0).any():
        raise ValueError("daily_orders must contain positive numeric values.")

    warehouse_count = int(number_of_warehouses)
    total_demand = float(demand.sum())
    average_demand = total_demand / warehouse_count
    largest_neighborhood = float(demand.max())
    buffered_target = total_demand * (1.0 + float(buffer_percentage) / 100.0)

    # The per-warehouse recommendation must cover both the buffered network
    # average and any single neighborhood demand.
    recommended_per = max(buffered_target / warehouse_count, largest_neighborhood)
    recommended_per = _round_up(recommended_per, int(rounding))
    recommended_total = recommended_per * warehouse_count

    return {
        "total_demand": total_demand,
        "number_of_warehouses": warehouse_count,
        "average_demand_per_warehouse": average_demand,
        "buffer_percentage": float(buffer_percentage),
        "buffered_demand_target": buffered_target,
        "recommended_total_capacity": int(recommended_total),
        "recommended_capacity_per_warehouse": int(recommended_per),
        "planning_buffer_orders": float(recommended_total - total_demand),
        "largest_neighborhood_demand": largest_neighborhood,
    }
