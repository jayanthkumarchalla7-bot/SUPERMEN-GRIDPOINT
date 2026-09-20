def calculate_savings(
    original_cost,
    optimized_cost
):

    if original_cost == 0:
        return 0

    savings = (
        original_cost
        - optimized_cost
    )

    percentage = (
        savings
        / original_cost
    ) * 100

    return savings, percentage
