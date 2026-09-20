import math
import pandas as pd
import pulp

from distance import create_distance_matrix
from vehicle import VEHICLES


def _normalise_utilization(max_utilization):
    if max_utilization is None:
        return 1.0
    value = float(max_utilization)
    if value > 1:
        value /= 100.0
    if not 0 < value <= 1:
        raise ValueError("max_utilization must be between 0 and 1 or 1 and 100.")
    return value


def _infeasibility_message(
    neighborhoods,
    distances,
    number_of_warehouses,
    warehouse_capacity,
    max_service_radius,
    effective_capacity,
):
    demand = neighborhoods["daily_orders"].astype(float)
    total_demand = float(demand.sum())
    details = []

    if effective_capacity is not None:
        total_capacity = number_of_warehouses * float(effective_capacity)
        if total_capacity + 1e-9 < total_demand:
            details.append(
                f"capacity is insufficient: demand={total_demand:.1f}, "
                f"available capacity={total_capacity:.1f}"
            )

    if max_service_radius is not None:
        reachable = (distances <= float(max_service_radius) + 1e-9).sum(axis=1)
        unreachable = [
            neighborhoods.iloc[i]["neighborhood"]
            for i, count in enumerate(reachable)
            if count == 0
        ]
        if unreachable:
            preview = ", ".join(map(str, unreachable[:5]))
            suffix = "..." if len(unreachable) > 5 else ""
            details.append(
                f"{len(unreachable)} neighborhood(s) have no candidate warehouse "
                f"within {max_service_radius:g} km: {preview}{suffix}"
            )

    if not details:
        details.append(
            "the combination of assignment, capacity, radius, or warehouse-count "
            "constraints is infeasible"
        )

    return (
        "No feasible solution found. "
        + "; ".join(details)
        + ". Increase capacity/radius, choose more warehouses, or disable the "
          "corresponding constraint."
    )


def optimize_warehouse_locations(
    neighborhoods,
    number_of_warehouses,
    delivery_cost_per_order_km,
    warehouse_fixed_cost,
    warehouse_capacity=None,
    max_service_radius=None,
    traffic_factor=1.0,
    time_cost_per_hour=0.0,
    selected_vehicles=None,
    time_limit=120,
    optimization_mode="Cost Optimization",
    max_utilization=None,
):
    """Solve the LOGITWIN capacitated warehouse-location MILP.

    The model uses candidate neighborhoods as warehouse locations, binary
    opening/assignment variables, optional capacity and service-radius
    constraints, and one vehicle choice for every assigned neighborhood.
    Distances are straight-line Haversine distances, not road distances.
    """

    if neighborhoods is None or len(neighborhoods) == 0:
        raise ValueError("Neighborhood dataset is empty.")

    required = {"neighborhood", "latitude", "longitude", "daily_orders"}
    missing = required - set(neighborhoods.columns)
    if missing:
        raise ValueError("Missing columns: " + ", ".join(sorted(missing)))

    data = neighborhoods.copy().reset_index(drop=True)
    for col in ["latitude", "longitude", "daily_orders"]:
        data[col] = pd.to_numeric(data[col], errors="coerce")
    if data[list(required)].isnull().any().any():
        raise ValueError("Neighborhood data contains invalid numeric values.")
    if (data["daily_orders"] <= 0).any():
        raise ValueError("daily_orders must be greater than zero.")

    n = len(data)
    number_of_warehouses = int(number_of_warehouses)
    if not 1 <= number_of_warehouses <= n:
        raise ValueError(
            f"number_of_warehouses must be between 1 and {n}."
        )

    if selected_vehicles is None:
        selected_vehicles = list(VEHICLES.keys())
    selected_vehicles = list(dict.fromkeys(selected_vehicles))
    unknown = [v for v in selected_vehicles if v not in VEHICLES]
    if unknown:
        raise ValueError("Unknown vehicle type(s): " + ", ".join(unknown))
    if not selected_vehicles:
        raise ValueError("At least one vehicle type must be selected.")

    effective_capacity = warehouse_capacity
    if (
        optimization_mode == "Resilience-Aware Optimization"
        and warehouse_capacity is not None
        and max_utilization is not None
    ):
        effective_capacity = float(warehouse_capacity) * _normalise_utilization(
            max_utilization
        )

    candidates = data[
        ["neighborhood", "latitude", "longitude"]
    ].copy().reset_index(drop=True)

    distances = create_distance_matrix(data, candidates)

    # Fail early with a useful diagnosis instead of exposing a generic CBC error.
    if effective_capacity is not None:
        total_capacity = number_of_warehouses * float(effective_capacity)
        if total_capacity + 1e-9 < float(data["daily_orders"].sum()):
            raise ValueError(
                _infeasibility_message(
                    data, distances, number_of_warehouses,
                    warehouse_capacity, max_service_radius, effective_capacity
                )
            )

    if max_service_radius is not None:
        reachable = (distances <= float(max_service_radius) + 1e-9).sum(axis=1)
        if (reachable == 0).any():
            raise ValueError(
                _infeasibility_message(
                    data, distances, number_of_warehouses,
                    warehouse_capacity, max_service_radius, effective_capacity
                )
            )

    model = pulp.LpProblem("LOGITWIN_Warehouse_Optimization", pulp.LpMinimize)

    open_var = {
        j: pulp.LpVariable(f"open_{j}", cat="Binary")
        for j in range(n)
    }
    assign_var = {
        (i, j): pulp.LpVariable(f"assign_{i}_{j}", cat="Binary")
        for i in range(n)
        for j in range(n)
    }
    vehicle_var = {
        (i, j, vehicle): pulp.LpVariable(
            f"vehicle_{i}_{j}_{vehicle}", cat="Binary"
        )
        for i in range(n)
        for j in range(n)
        for vehicle in selected_vehicles
    }

    objective_terms = []

    for i in range(n):
        demand = float(data.iloc[i]["daily_orders"])
        for j in range(n):
            distance = float(distances[i, j])
            for vehicle in selected_vehicles:
                vehicle_data = VEHICLES[vehicle]
                trips = demand / vehicle_data["capacity"]
                fuel_cost = (
                    trips
                    * distance
                    / vehicle_data["fuel_efficiency"]
                    * vehicle_data["fuel_price"]
                )
                distance_cost = (
                    demand * distance * float(delivery_cost_per_order_km)
                )
                travel_time = (
                    distance / vehicle_data["speed"] * float(traffic_factor)
                )
                time_cost = (
                    travel_time
                    * float(time_cost_per_hour)
                    * trips
                )
                objective_terms.append(
                    (fuel_cost + distance_cost + time_cost)
                    * vehicle_var[i, j, vehicle]
                )

    infrastructure = pulp.lpSum(
        float(warehouse_fixed_cost) * open_var[j] for j in range(n)
    )

    # Both supported modes remain deterministic. Resilience mode uses the
    # capacity ceiling as its explicit resilience mechanism.
    model += pulp.lpSum(objective_terms) + infrastructure

    # Every neighborhood is served exactly once.
    for i in range(n):
        model += (
            pulp.lpSum(assign_var[i, j] for j in range(n)) == 1,
            f"assign_once_{i}",
        )

    # Exactly the requested number of warehouses is opened.
    model += (
        pulp.lpSum(open_var[j] for j in range(n)) == number_of_warehouses,
        "warehouse_count",
    )

    for i in range(n):
        for j in range(n):
            model += (
                assign_var[i, j] <= open_var[j],
                f"open_link_{i}_{j}",
            )
            model += (
                pulp.lpSum(
                    vehicle_var[i, j, vehicle]
                    for vehicle in selected_vehicles
                )
                == assign_var[i, j],
                f"vehicle_link_{i}_{j}",
            )

            if (
                max_service_radius is not None
                and float(distances[i, j]) > float(max_service_radius) + 1e-9
            ):
                model += (
                    assign_var[i, j] == 0,
                    f"radius_{i}_{j}",
                )

    if effective_capacity is not None:
        cap = float(effective_capacity)
        for j in range(n):
            model += (
                pulp.lpSum(
                    float(data.iloc[i]["daily_orders"]) * assign_var[i, j]
                    for i in range(n)
                )
                <= cap * open_var[j],
                f"capacity_{j}",
            )

    solver = pulp.PULP_CBC_CMD(
        msg=False,
        timeLimit=max(1, int(time_limit)),
    )
    model.solve(solver)

    status = pulp.LpStatus.get(model.status, str(model.status))
    if status not in {"Optimal", "Feasible"}:
        raise ValueError(
            _infeasibility_message(
                data, distances, number_of_warehouses,
                warehouse_capacity, max_service_radius, effective_capacity
            )
            + f" Solver status: {status}."
        )

    selected_indices = [
        j for j in range(n)
        if pulp.value(open_var[j]) is not None
        and pulp.value(open_var[j]) > 0.5
    ]
    if len(selected_indices) != number_of_warehouses:
        raise ValueError(
            "Solver returned an invalid warehouse selection. "
            f"Expected {number_of_warehouses}, got {len(selected_indices)}."
        )

    warehouse_mapping = {
        original_index: position
        for position, original_index in enumerate(selected_indices)
    }

    warehouses = candidates.iloc[selected_indices].copy().reset_index(drop=True)
    warehouses["warehouse_id"] = [
        f"W{i + 1}" for i in range(len(warehouses))
    ]
    warehouses = warehouses[
        ["warehouse_id", "neighborhood", "latitude", "longitude"]
    ]

    rows = []
    for i in range(n):
        chosen_j = next(
            (
                j for j in selected_indices
                if pulp.value(assign_var[i, j]) is not None
                and pulp.value(assign_var[i, j]) > 0.5
            ),
            None,
        )
        if chosen_j is None:
            raise ValueError(
                f"Solver returned no assignment for "
                f"{data.iloc[i]['neighborhood']}."
            )

        chosen_vehicle = next(
            (
                vehicle for vehicle in selected_vehicles
                if pulp.value(vehicle_var[i, chosen_j, vehicle]) is not None
                and pulp.value(vehicle_var[i, chosen_j, vehicle]) > 0.5
            ),
            None,
        )
        if chosen_vehicle is None:
            raise ValueError(
                f"No vehicle was selected for {data.iloc[i]['neighborhood']}."
            )

        demand = float(data.iloc[i]["daily_orders"])
        distance = float(distances[i, chosen_j])
        vehicle_data = VEHICLES[chosen_vehicle]
        trips = demand / vehicle_data["capacity"]
        fuel_liters = (
            distance / vehicle_data["fuel_efficiency"] * trips
        )
        fuel_cost = fuel_liters * vehicle_data["fuel_price"]
        delivery_time = (
            distance / vehicle_data["speed"] * float(traffic_factor)
        )
        time_cost = delivery_time * float(time_cost_per_hour) * trips
        distance_cost = (
            demand * distance * float(delivery_cost_per_order_km)
        )
        total_delivery_cost = distance_cost + fuel_cost + time_cost

        rows.append(
            {
                "neighborhood": data.iloc[i]["neighborhood"],
                "latitude": float(data.iloc[i]["latitude"]),
                "longitude": float(data.iloc[i]["longitude"]),
                "daily_orders": demand,
                "warehouse": f"W{warehouse_mapping[chosen_j] + 1}",
                "distance_km": distance,
                "vehicle": chosen_vehicle,
                "trips": trips,
                "fuel_liters": fuel_liters,
                "fuel_cost": fuel_cost,
                "traffic_factor": float(traffic_factor),
                "delivery_time_hours": delivery_time,
                "time_cost": time_cost,
                "distance_cost": distance_cost,
                "delivery_cost": total_delivery_cost,
            }
        )

    assignments = pd.DataFrame(rows)

    warehouse_load = (
        assignments.groupby("warehouse", as_index=False)
        .agg(
            neighborhoods=("neighborhood", "count"),
            orders_served=("daily_orders", "sum"),
            delivery_cost=("delivery_cost", "sum"),
        )
    )

    warehouses = warehouses.merge(
        warehouse_load,
        left_on="warehouse_id",
        right_on="warehouse",
        how="left",
    ).drop(columns=["warehouse"])

    warehouses["orders_served"] = warehouses["orders_served"].fillna(0)
    warehouses["neighborhoods"] = warehouses["neighborhoods"].fillna(0).astype(int)
    warehouses["delivery_cost"] = warehouses["delivery_cost"].fillna(0)

    if effective_capacity is not None:
        warehouses["remaining_capacity"] = (
            float(effective_capacity) - warehouses["orders_served"]
        )
        warehouses["utilization_percent"] = (
            warehouses["orders_served"] / float(effective_capacity) * 100
        )
    else:
        warehouses["remaining_capacity"] = float("nan")
        warehouses["utilization_percent"] = float("nan")

    distance_cost = float(assignments["distance_cost"].sum())
    fuel_cost = float(assignments["fuel_cost"].sum())
    time_cost = float(assignments["time_cost"].sum())
    delivery_cost = float(assignments["delivery_cost"].sum())
    infrastructure_cost = (
        number_of_warehouses * float(warehouse_fixed_cost)
    )
    total_cost = delivery_cost + infrastructure_cost

    weighted_distance = float(
        (assignments["distance_km"] * assignments["daily_orders"]).sum()
    )

    return {
        "warehouses": warehouses,
        "assignments": assignments,
        "weighted_distance": weighted_distance,
        "distance_cost": distance_cost,
        "fuel_cost": fuel_cost,
        "time_cost": time_cost,
        "delivery_cost": delivery_cost,
        "infrastructure_cost": infrastructure_cost,
        "total_cost": total_cost,
        "total_fuel": float(assignments["fuel_liters"].sum()),
        "total_delivery_time": float(
            assignments["delivery_time_hours"].sum()
        ),
        "solver_status": status,
    }
