import pandas as pd


def analyze_warehouse_counts(
    neighborhoods,
    optimizer_function,
    min_warehouses,
    max_warehouses,
    **optimizer_kwargs
):

    results = []

    for warehouse_count in range(
        min_warehouses,
        max_warehouses + 1
    ):

        try:

            result = optimizer_function(
                neighborhoods=neighborhoods,
                number_of_warehouses=warehouse_count,
                **optimizer_kwargs
            )

            warehouses = result["warehouses"]

            if (
                "orders_served" in warehouses.columns
                and "remaining_capacity"
                in warehouses.columns
            ):

                capacity = (
                    warehouses["orders_served"]
                    + warehouses["remaining_capacity"]
                )

                utilization = (
                    warehouses["orders_served"]
                    / capacity
                ).mean() * 100

            else:
                utilization = None

            results.append({
                "warehouses": warehouse_count,
                "delivery_cost":
                    result["delivery_cost"],
                "fuel_cost":
                    result["fuel_cost"],
                "time_cost":
                    result["time_cost"],
                "infrastructure_cost":
                    result["infrastructure_cost"],
                "total_cost":
                    result["total_cost"],
                "weighted_distance":
                    result["weighted_distance"],
                "utilization":
                    utilization,
                "status":
                    result["solver_status"]
            })

        except Exception as error:

            results.append({
                "warehouses": warehouse_count,
                "delivery_cost": None,
                "fuel_cost": None,
                "time_cost": None,
                "infrastructure_cost": None,
                "total_cost": None,
                "weighted_distance": None,
                "utilization": None,
                "status": f"Infeasible: {error}"
            })

    return pd.DataFrame(results)


def find_best_warehouse_count(results):

    feasible = results[
        results["total_cost"].notna()
    ]

    if feasible.empty:
        return None

    best_row = feasible.loc[
        feasible["total_cost"].idxmin()
    ]

    return int(
        best_row["warehouses"]
    )