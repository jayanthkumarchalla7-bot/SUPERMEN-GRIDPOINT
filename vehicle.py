import math


VEHICLES = {
    "Bike": {
        "capacity": 20,
        "fuel_efficiency": 45,
        "fuel_price": 105,
        "speed": 35
    },

    "Van": {
        "capacity": 100,
        "fuel_efficiency": 12,
        "fuel_price": 105,
        "speed": 40
    },

    "Truck": {
        "capacity": 500,
        "fuel_efficiency": 6,
        "fuel_price": 105,
        "speed": 45
    }
}


def calculate_vehicle_fuel_cost(
    distance_km,
    vehicle_name
):

    vehicle = VEHICLES[vehicle_name]

    fuel_used = (
        distance_km
        / vehicle["fuel_efficiency"]
    )

    fuel_cost = (
        fuel_used
        * vehicle["fuel_price"]
    )

    return fuel_cost


def calculate_trips(
    daily_orders,
    vehicle_name
):

    capacity = VEHICLES[
        vehicle_name
    ]["capacity"]

    return math.ceil(
        daily_orders / capacity
    )


def calculate_delivery_time(
    distance_km,
    vehicle_name,
    traffic_factor
):

    speed = VEHICLES[
        vehicle_name
    ]["speed"]

    normal_time_hours = (
        distance_km / speed
    )

    traffic_time_hours = (
        normal_time_hours
        * traffic_factor
    )

    return traffic_time_hours


def get_vehicle_options():

    return list(
        VEHICLES.keys()
    )