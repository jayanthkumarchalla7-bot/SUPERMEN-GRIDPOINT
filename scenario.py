import pandas as pd


DEMAND_SCENARIOS = {
    "Current": 1.00,
    "Weekend": 1.15,
    "Festival": 1.35,
    "Peak": 1.60
}


TRAFFIC_SCENARIOS = {
    "Low": 0.85,
    "Normal": 1.00,
    "Heavy": 1.35,
    "Severe": 1.70
}


def apply_demand_scenario(
    df,
    scenario_name,
    neighborhood=None,
    neighborhood_spike=0.0
):
    result = df.copy()

    multiplier = DEMAND_SCENARIOS[
        scenario_name
    ]

    result["base_orders"] = result[
        "daily_orders"
    ]

    result["daily_orders"] = (
        result["base_orders"]
        * multiplier
    )

    # Optional localized demand shock
    if neighborhood is not None:
        mask = (
            result["neighborhood"]
            == neighborhood
        )

        result.loc[
            mask,
            "daily_orders"
        ] *= (1 + neighborhood_spike)

    return result


def apply_stress_scenario(
    df,
    demand_increase=0.0,
    neighborhood=None,
    neighborhood_spike=0.0
):
    result = df.copy()

    result["base_orders"] = (
        result["daily_orders"]
    )

    result["daily_orders"] = (
        result["daily_orders"]
        * (1 + demand_increase)
    )

    if neighborhood is not None:
        mask = (
            result["neighborhood"]
            == neighborhood
        )

        result.loc[
            mask,
            "daily_orders"
        ] *= (1 + neighborhood_spike)

    return result