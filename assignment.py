import pandas as pd


def calculate_assignment_summary(
    assignments
):

    summary = (
        assignments
        .groupby("warehouse")
        .agg(
            neighborhoods=(
                "neighborhood",
                "count"
            ),
            daily_orders=(
                "daily_orders",
                "sum"
            ),
            total_distance=(
                "distance_km",
                "sum"
            ),
            delivery_cost=(
                "delivery_cost",
                "sum"
            )
        )
        .reset_index()
    )

    return summary