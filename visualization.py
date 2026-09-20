from __future__ import annotations

import math
from typing import Optional

import folium
from folium.plugins import MarkerCluster


ACCENT = "#38bdf8"
TEXT = "#e5e7eb"
MUTED = "#94a3b8"
GOOD = "#34d399"
WARN = "#fbbf24"
BAD = "#fb7185"


def _safe_float(value, default=0.0):
    try:
        value = float(value)
        if math.isfinite(value):
            return value
    except (TypeError, ValueError):
        pass
    return default


def _blend_color(value: float, low=0.0, high=100.0) -> str:
    ratio = 0.0 if high <= low else (value - low) / (high - low)
    ratio = max(0.0, min(1.0, ratio))
    r = int(52 + ratio * 199)
    g = int(211 - ratio * 120)
    b = int(153 - ratio * 72)
    return f"#{r:02x}{g:02x}{b:02x}"


def create_map(
    neighborhoods,
    warehouses=None,
    assignments=None,
    map_mode="Demand View",
):
    if neighborhoods is None or neighborhoods.empty:
        raise ValueError("Neighborhood dataset is empty.")

    center_lat = _safe_float(neighborhoods["latitude"].mean())
    center_lon = _safe_float(neighborhoods["longitude"].mean())

    map_object = folium.Map(
        location=[center_lat, center_lon],
        zoom_start=11,
        tiles="OpenStreetMap",
        control_scale=True,
        prefer_canvas=True,
    )

    assignment_by_neighborhood = {}
    warehouse_by_id = {}
    warehouse_utilization = {}

    if warehouses is not None and not warehouses.empty:
        warehouse_by_id = warehouses.set_index("warehouse_id").to_dict("index")
        if (
            "utilization_percent" in warehouses.columns
        ):
            warehouse_utilization = {
                str(row["warehouse_id"]): _safe_float(
                    row.get("utilization_percent", 0)
                )
                for _, row in warehouses.iterrows()
            }

    if assignments is not None and not assignments.empty:
        assignment_by_neighborhood = (
            assignments.set_index("neighborhood").to_dict("index")
        )

    cluster = MarkerCluster(
        name="Neighborhoods",
        show=True,
        options={"disableClusteringAtZoom": 13},
    )

    max_demand = max(
        1.0,
        _safe_float(neighborhoods["daily_orders"].max()),
    )

    for _, row in neighborhoods.iterrows():
        name = str(row["neighborhood"])
        demand = _safe_float(row["daily_orders"])
        assignment = assignment_by_neighborhood.get(name, {})

        distance = _safe_float(assignment.get("distance_km", 0))
        warehouse_id = str(assignment.get("warehouse", "Unassigned"))

        if map_mode == "Delivery Distance" and warehouse_id != "Unassigned":
            color = _blend_color(
                min(100.0, distance / max(1.0, 25.0) * 100.0),
                0,
                100,
            )
            popup_body = (
                f"<b>{name}</b><br>"
                f"Warehouse: {warehouse_id}<br>"
                f"Delivery distance: {distance:.2f} km<br>"
                f"Daily orders: {demand:,.0f}"
            )
        elif map_mode == "Capacity Utilization" and warehouse_id != "Unassigned":
            utilization = warehouse_utilization.get(warehouse_id, 0.0)
            color = (
                BAD if utilization > 100
                else WARN if utilization >= 80
                else GOOD
            )
            popup_body = (
                f"<b>{name}</b><br>"
                f"Warehouse: {warehouse_id}<br>"
                f"Warehouse utilization: {utilization:.1f}%<br>"
                f"Daily orders: {demand:,.0f}"
            )
        elif map_mode == "Risk View":
            utilization = warehouse_utilization.get(warehouse_id, 0.0)
            if utilization >= 90 or distance >= 15:
                color = BAD
                risk = "High"
            elif utilization >= 75 or distance >= 10:
                color = WARN
                risk = "Moderate"
            else:
                color = GOOD
                risk = "Low"
            popup_body = (
                f"<b>{name}</b><br>"
                f"Risk: {risk}<br>"
                f"Warehouse: {warehouse_id}<br>"
                f"Daily orders: {demand:,.0f}"
            )
        else:
            intensity = min(1.0, demand / max_demand)
            color = ACCENT
            radius = 5 + int(8 * intensity)
            popup_body = (
                f"<b>{name}</b><br>"
                f"Daily orders: {demand:,.0f}<br>"
                f"Warehouse: {warehouse_id}"
            )
            folium.CircleMarker(
                location=[row["latitude"], row["longitude"]],
                radius=radius,
                popup=folium.Popup(popup_body, max_width=280),
                tooltip=name,
                color=color,
                fill=True,
                fill_color=color,
                fill_opacity=0.72,
                opacity=0.9,
                weight=1,
            ).add_to(cluster)
            continue

        radius = 7
        folium.CircleMarker(
            location=[row["latitude"], row["longitude"]],
            radius=radius,
            popup=folium.Popup(popup_body, max_width=280),
            tooltip=name,
            color=color,
            fill=True,
            fill_color=color,
            fill_opacity=0.72,
            opacity=0.9,
            weight=1,
        ).add_to(cluster)

    cluster.add_to(map_object)

    if warehouses is not None and not warehouses.empty:
        for _, row in warehouses.iterrows():
            warehouse_id = str(row["warehouse_id"])
            utilization = warehouse_utilization.get(warehouse_id, 0.0)
            util_text = (
                f"{utilization:.1f}%"
                if "utilization_percent" in warehouses.columns
                else "N/A"
            )

            popup_body = (
                f"<b>{warehouse_id}</b><br>"
                f"Candidate location: {row['neighborhood']}<br>"
                f"Orders served: {_safe_float(row.get('orders_served', 0)):,.0f}"
                f"<br>Utilization: {util_text}"
            )

            folium.Marker(
                location=[row["latitude"], row["longitude"]],
                popup=folium.Popup(popup_body, max_width=300),
                tooltip=f"{warehouse_id} • {row['neighborhood']}",
                icon=folium.Icon(
                    color="blue",
                    icon="home",
                    prefix="glyphicon",
                ),
            ).add_to(map_object)

    if (
        assignments is not None
        and not assignments.empty
        and warehouses is not None
        and not warehouses.empty
    ):
        for _, row in assignments.iterrows():
            warehouse = warehouse_by_id.get(str(row["warehouse"]))
            if warehouse is None:
                continue

            line_color = ACCENT
            if map_mode == "Risk View":
                util = warehouse_utilization.get(str(row["warehouse"]), 0)
                line_color = BAD if util >= 90 else WARN if util >= 75 else ACCENT

            folium.PolyLine(
                locations=[
                    [row["latitude"], row["longitude"]],
                    [warehouse["latitude"], warehouse["longitude"]],
                ],
                color=line_color,
                weight=1.5,
                opacity=0.35,
                tooltip=(
                    f"{row['neighborhood']} → {row['warehouse']} "
                    f"({row['distance_km']:.2f} km)"
                ),
            ).add_to(map_object)

    legend_html = """
    <div style="
        position: fixed;
        bottom: 24px;
        left: 24px;
        z-index: 9999;
        background: rgba(15,23,42,0.92);
        border: 1px solid rgba(148,163,184,0.25);
        color: #e5e7eb;
        padding: 10px 12px;
        border-radius: 8px;
        font-size: 12px;
        line-height: 1.6;
        box-shadow: 0 8px 25px rgba(0,0,0,0.28);
    ">
      <b>MAP LEGEND</b><br>
      <span style="color:#38bdf8;">●</span> Neighborhood demand<br>
      <span style="color:#60a5fa;">◆</span> Warehouse<br>
      <span style="color:#34d399;">●</span> Healthy / low risk<br>
      <span style="color:#fbbf24;">●</span> Watch / moderate risk<br>
      <span style="color:#fb7185;">●</span> Critical / high risk
    </div>
    """
    map_object.get_root().html.add_child(folium.Element(legend_html))

    return map_object
