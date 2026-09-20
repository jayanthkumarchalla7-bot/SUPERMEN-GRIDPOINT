import pandas as pd


REQUIRED_COLUMNS = [
    "neighborhood",
    "latitude",
    "longitude",
    "daily_orders"
]


def validate_data(df):

    df = df.copy()

    # Check required columns
    missing = [
        column
        for column in REQUIRED_COLUMNS
        if column not in df.columns
    ]

    if missing:
        raise ValueError(
            "Missing columns: " + ", ".join(missing)
        )

    # Convert numeric columns
    df["latitude"] = pd.to_numeric(
        df["latitude"],
        errors="coerce"
    )

    df["longitude"] = pd.to_numeric(
        df["longitude"],
        errors="coerce"
    )

    df["daily_orders"] = pd.to_numeric(
        df["daily_orders"],
        errors="coerce"
    )

    # Check missing values
    if df[REQUIRED_COLUMNS].isnull().any().any():
        raise ValueError(
            "Latitude, longitude and daily_orders "
            "cannot contain empty or invalid values."
        )

    # Geographic validation
    if not df["latitude"].between(-90, 90).all():
        raise ValueError(
            "Latitude must be between -90 and 90."
        )

    if not df["longitude"].between(-180, 180).all():
        raise ValueError(
            "Longitude must be between -180 and 180."
        )

    # Demand validation
    if (df["daily_orders"] <= 0).any():
        raise ValueError(
            "daily_orders must be greater than zero."
        )

    # Remove duplicate neighborhood names
    if df["neighborhood"].duplicated().any():
        raise ValueError(
            "Neighborhood names must be unique."
        )

    return df.reset_index(drop=True)


def load_csv(file):

    df = pd.read_csv(file)

    return validate_data(df)