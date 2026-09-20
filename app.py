from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd
import plotly.express as px
import streamlit as st
from streamlit_folium import st_folium

from capacity_recommendation import (
    DEFAULT_BUFFER_PERCENTAGE,
    MAX_BUFFER_PERCENTAGE,
    MIN_BUFFER_PERCENTAGE,
    recommend_warehouse_capacity,
)
from data_loader import load_csv, validate_data
from optimization import optimize_warehouse_locations
from resilience import simulate_warehouse_failure
from scenario import DEMAND_SCENARIOS, TRAFFIC_SCENARIOS, apply_stress_scenario
from vehicle import VEHICLES
from visualization import create_map
from warehouse_analysis import analyze_warehouse_counts, find_best_warehouse_count


BASE_DIR = Path(__file__).resolve().parent
SAMPLE_DATA_PATH = BASE_DIR / "data" / "neighborhoods.csv"

ACCENT = "#2DD4BF"
ACCENT_SOFT = "rgba(45,212,191,0.12)"
BG = "#080C12"
PANEL = "#0E141D"
PANEL_2 = "#121A25"
BORDER = "rgba(148,163,184,0.16)"
TEXT = "#F3F7FA"
MUTED = "#91A0B2"
GOOD = "#34D399"
WARN = "#FBBF24"
BAD = "#FB7185"
BLUE = "#60A5FA"


st.set_page_config(
    page_title="GRIDPOINT | Logistics Made Easy",
    page_icon="L",
    layout="wide",
    initial_sidebar_state="expanded",
)


def inject_css() -> None:
    st.markdown(
        f"""
        <style>
        :root {{
            color-scheme: dark;
        }}

        html, body, [class*="css"] {{
            font-family: Inter, ui-sans-serif, system-ui, -apple-system,
                         BlinkMacSystemFont, "Segoe UI", sans-serif;
        }}

        .stApp {{
            background: {BG};
            color: {TEXT};
        }}

        [data-testid="stHeader"] {{
            background: rgba(8,12,18,0.88);
            border-bottom: 1px solid {BORDER};
        }}

        [data-testid="stSidebar"] {{
            background: #0A1018;
            border-right: 1px solid {BORDER};
        }}

        [data-testid="stSidebarContent"] {{
            padding: 1.15rem 1rem 2rem 1rem;
        }}

        .block-container {{
            max-width: 1500px;
            padding: 1.8rem 2.4rem 4rem 2.4rem;
        }}

        h1, h2, h3, h4 {{
            color: {TEXT} !important;
            letter-spacing: -0.025em;
        }}

        p, label, [data-testid="stMarkdownContainer"] {{
            color: {TEXT};
        }}

        .muted {{
            color: {MUTED};
        }}

        .brand {{
            display: flex;
            align-items: center;
            gap: 12px;
            margin-bottom: 0.8rem;
        }}

        .brand-mark {{
            width: 38px;
            height: 38px;
            border-radius: 9px;
            border: 1px solid rgba(45,212,191,0.30);
            background: rgba(45,212,191,0.08);
            display: grid;
            place-items: center;
            color: {ACCENT};
            font-weight: 850;
            font-size: 16px;
        }}

        .brand-name {{
            font-size: 1.15rem;
            font-weight: 850;
            letter-spacing: 0.04em;
        }}

        .brand-sub {{
            color: {MUTED};
            font-size: 0.72rem;
            margin-top: 1px;
        }}

        .hero {{
            border: 1px solid {BORDER};
            border-radius: 14px;
            background:
                linear-gradient(145deg, rgba(17,26,37,0.98), rgba(10,15,23,0.98));
            padding: 1.35rem 1.5rem 1.25rem 1.5rem;
            box-shadow: 0 20px 60px rgba(0,0,0,0.22);
            margin-bottom: 1rem;
        }}

        .hero-top {{
            display: flex;
            align-items: flex-start;
            justify-content: space-between;
            gap: 18px;
        }}

        .hero-title {{
            font-size: 2.15rem;
            font-weight: 850;
            margin: 0;
        }}

        .hero-description {{
            color: {MUTED};
            margin-top: 0.28rem;
            font-size: 0.92rem;
        }}

        .status-pill {{
            display: inline-flex;
            align-items: center;
            gap: 7px;
            padding: 5px 9px;
            border-radius: 999px;
            border: 1px solid rgba(52,211,153,0.24);
            background: rgba(52,211,153,0.07);
            color: {GOOD};
            font-size: 10px;
            font-weight: 800;
            text-transform: uppercase;
            letter-spacing: 0.09em;
            white-space: nowrap;
        }}

        .status-dot {{
            width: 6px;
            height: 6px;
            border-radius: 50%;
            background: {GOOD};
        }}

        .section-kicker {{
            color: {ACCENT};
            font-size: 10px;
            font-weight: 800;
            text-transform: uppercase;
            letter-spacing: 0.13em;
            margin-bottom: 0.22rem;
        }}

        .section-title {{
            color: {TEXT};
            font-size: 1.13rem;
            font-weight: 760;
            margin-bottom: 0.78rem;
        }}

        .card {{
            border: 1px solid {BORDER};
            background: {PANEL};
            border-radius: 11px;
            padding: 0.9rem 0.95rem;
            min-height: 96px;
            box-shadow: 0 10px 24px rgba(0,0,0,0.13);
        }}

        .card-label {{
            color: {MUTED};
            font-size: 0.70rem;
            font-weight: 750;
            letter-spacing: 0.08em;
            text-transform: uppercase;
        }}

        .card-value {{
            color: {TEXT};
            font-size: 1.42rem;
            font-weight: 830;
            margin-top: 0.28rem;
        }}

        .card-caption {{
            color: {MUTED};
            font-size: 0.75rem;
            margin-top: 0.22rem;
        }}

        .advisor {{
            border: 1px solid rgba(45,212,191,0.22);
            background: linear-gradient(145deg, rgba(45,212,191,0.06), {PANEL});
            border-radius: 13px;
            padding: 1rem;
            box-shadow: 0 14px 30px rgba(0,0,0,0.16);
        }}

        .advisor-head {{
            display: flex;
            align-items: flex-start;
            justify-content: space-between;
            gap: 16px;
        }}

        .advisor-title {{
            font-size: 1.05rem;
            font-weight: 820;
        }}

        .advisor-badge {{
            color: {ACCENT};
            background: rgba(45,212,191,0.07);
            border: 1px solid rgba(45,212,191,0.26);
            padding: 4px 8px;
            border-radius: 6px;
            font-size: 9px;
            font-weight: 820;
            letter-spacing: 0.10em;
            white-space: nowrap;
        }}

        .advisor-grid {{
            display: grid;
            grid-template-columns: repeat(4, minmax(0, 1fr));
            gap: 8px;
            margin-top: 0.85rem;
        }}

        .advisor-stat {{
            background: rgba(4,8,13,0.40);
            border: 1px solid {BORDER};
            border-radius: 8px;
            padding: 0.7rem;
        }}

        .advisor-stat .label {{
            color: {MUTED};
            font-size: 0.67rem;
        }}

        .advisor-stat .value {{
            color: {TEXT};
            font-size: 1.08rem;
            font-weight: 820;
            margin-top: 0.20rem;
        }}

        .callout {{
            border-left: 3px solid {ACCENT};
            border-top: 1px solid {BORDER};
            border-right: 1px solid {BORDER};
            border-bottom: 1px solid {BORDER};
            background: rgba(45,212,191,0.045);
            border-radius: 0 8px 8px 0;
            padding: 0.67rem 0.8rem;
            color: {MUTED};
            font-size: 0.80rem;
        }}

        .health {{
            border: 1px solid {BORDER};
            background: {PANEL};
            border-radius: 12px;
            padding: 0.95rem 1rem;
            margin-top: 1rem;
        }}

        .health-top {{
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 12px;
        }}

        .health-state {{
            font-size: 0.76rem;
            font-weight: 850;
            letter-spacing: 0.10em;
        }}

        .health-detail {{
            color: {MUTED};
            font-size: 0.80rem;
            margin-top: 0.40rem;
        }}

        .info-strip {{
            border: 1px solid {BORDER};
            background: {PANEL};
            border-radius: 9px;
            padding: 0.65rem 0.8rem;
            color: {MUTED};
            font-size: 0.76rem;
        }}

        .stButton > button {{
            border-radius: 8px;
            border: 1px solid rgba(45,212,191,0.30);
            background: rgba(45,212,191,0.08);
            color: {TEXT};
            font-weight: 730;
            min-height: 38px;
        }}

        .stButton > button:hover {{
            border-color: rgba(45,212,191,0.62);
            background: rgba(45,212,191,0.14);
            color: {TEXT};
        }}

        .stButton > button[kind="primary"] {{
            background: {ACCENT};
            border-color: {ACCENT};
            color: #06110F;
            font-weight: 820;
        }}

        .stButton > button[kind="primary"]:hover {{
            background: #5EEAD4;
            border-color: #5EEAD4;
            color: #06110F;
        }}

        [data-baseweb="tab-list"] {{
            gap: 3px;
            border-bottom: 1px solid {BORDER};
        }}

        [data-baseweb="tab"] {{
            color: {MUTED};
            padding: 0.65rem 0.85rem;
        }}

        [aria-selected="true"][data-baseweb="tab"] {{
            color: {TEXT} !important;
        }}

        [data-testid="stMetric"] {{
            background: {PANEL};
            border: 1px solid {BORDER};
            border-radius: 10px;
            padding: 0.8rem 0.9rem;
        }}

        [data-testid="stMetricLabel"] {{
            color: {MUTED};
        }}

        [data-testid="stMetricValue"] {{
            color: {TEXT};
        }}

        div[data-baseweb="select"] > div,
        div[data-baseweb="input"] > div {{
            background: #0B121B;
            border-color: {BORDER};
        }}

        [data-testid="stDataFrame"] {{
            border: 1px solid {BORDER};
            border-radius: 9px;
        }}

        hr {{
            border-color: {BORDER};
        }}

        @media (max-width: 900px) {{
            .block-container {{
                padding-left: 1rem;
                padding-right: 1rem;
            }}

            .advisor-grid {{
                grid-template-columns: repeat(2, minmax(0, 1fr));
            }}

            .hero-top {{
                flex-direction: column;
            }}

            .hero-title {{
                font-size: 1.75rem;
            }}
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )


def safe_float(value: Any, default: float = 0.0) -> float:
    try:
        value = float(value)
        return value if pd.notna(value) else default
    except (TypeError, ValueError):
        return default


def card(label: str, value: str, caption: str = "") -> None:
    st.markdown(
        f"""
        <div class="card">
            <div class="card-label">{label}</div>
            <div class="card-value">{value}</div>
            <div class="card-caption">{caption}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def section_heading(kicker: str, title: str) -> None:
    st.markdown(
        f"""
        <div class="section-kicker">{kicker}</div>
        <div class="section-title">{title}</div>
        """,
        unsafe_allow_html=True,
    )


def render_hero() -> None:
    st.markdown(
        """
        <div class="hero">
            <div class="hero-top">
                <div>
                    <div class="brand">
                        <div class="brand-mark">G</div>
                        <div>
                            <div class="brand-name">GRIDPOINT</div>
                            <div class="brand-sub">LOGISTICS MADE EASY</div>
                        </div>
                    </div>
                    <div class="hero-title">Adaptive Warehouse & Urban Delivery Network Simulator</div>
                    <div class="hero-description">
                        Model warehouse placement, demand coverage, capacity utilization,
                        delivery economics and network resilience in one planning workspace.
                    </div>
                </div>
                <div class="status-pill">
                    <span class="status-dot"></span>
                    Optimization Engine · Ready
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def load_data(input_method: str, uploaded_file) -> pd.DataFrame | None:
    try:
        if input_method == "Sample Data":
            if not SAMPLE_DATA_PATH.exists():
                st.error(
                    f"Sample data not found at {SAMPLE_DATA_PATH}. "
                    "Use Upload CSV or restore the bundled sample file."
                )
                return None
            return validate_data(pd.read_csv(SAMPLE_DATA_PATH))

        if uploaded_file is None:
            return None

        return load_csv(uploaded_file)
    except Exception as error:
        st.error(f"Data loading failed: {error}")
        return None


def apply_recommended_capacity(
    recommendation: dict[str, Any],
) -> None:
    value = int(recommendation["recommended_capacity_per_warehouse"])
    st.session_state["warehouse_capacity"] = max(1, value)


def make_signature(
    df: pd.DataFrame,
    input_method: str,
    uploaded_file,
    demand_scenario: str,
    number_of_warehouses: int,
    warehouse_capacity,
    max_service_radius,
    traffic_level: str,
    optimization_mode: str,
    selected_vehicles: list[str],
    warehouse_fixed_cost: float,
) -> tuple:
    upload_meta = (
        getattr(uploaded_file, "name", None),
        getattr(uploaded_file, "size", None),
    )
    return (
        input_method,
        upload_meta,
        demand_scenario,
        int(number_of_warehouses),
        None if warehouse_capacity is None else float(warehouse_capacity),
        None if max_service_radius is None else float(max_service_radius),
        traffic_level,
        optimization_mode,
        tuple(selected_vehicles),
        float(warehouse_fixed_cost),
        round(safe_float(df["daily_orders"].sum()), 4),
        len(df),
    )


def style_plotly(fig, height: int = 360):
    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color=TEXT, size=12),
        title=dict(font=dict(color=TEXT, size=15)),
        legend=dict(
            bgcolor="rgba(0,0,0,0)",
            font=dict(color=MUTED),
        ),
        margin=dict(l=10, r=10, t=46, b=10),
        height=height,
    )
    fig.update_xaxes(
        gridcolor="rgba(148,163,184,0.08)",
        linecolor="rgba(148,163,184,0.12)",
        zerolinecolor="rgba(148,163,184,0.06)",
    )
    fig.update_yaxes(
        gridcolor="rgba(148,163,184,0.08)",
        linecolor="rgba(148,163,184,0.12)",
        zerolinecolor="rgba(148,163,184,0.06)",
    )
    return fig


def render_capacity_advisor(
    advisor_df: pd.DataFrame,
    number_of_warehouses: int,
    buffer_percentage: float,
    warehouse_capacity,
    recommendation: dict[str, Any],
) -> None:
    """Render the capacity advisor using native Streamlit components."""
    del advisor_df  # Kept in the signature for compatibility with the existing app flow.

    total_demand = safe_float(recommendation["total_demand"])
    average_demand = safe_float(recommendation["average_demand_per_warehouse"])
    recommended_total = int(recommendation["recommended_total_capacity"])
    recommended_per = int(recommendation["recommended_capacity_per_warehouse"])
    planned_buffer = safe_float(recommendation["planning_buffer_orders"])
    largest_neighborhood = safe_float(
        recommendation.get("largest_neighborhood_demand", 0)
    )
    raw_buffered_target = safe_float(
        recommendation.get("buffered_demand_target", recommended_total)
    )

    section_heading("CAPACITY ADVISOR", "Warehouse Capacity Recommendation")
    st.caption(
        "Planning-only estimate based on baseline neighborhood demand, warehouse "
        f"count and a {buffer_percentage:.0f}% operational buffer."
    )

    with st.container():
        first_row = st.columns(4)
        first_row[0].metric(
            "Baseline demand", f"{total_demand:,.0f}", "orders/day"
        )
        first_row[1].metric("Warehouses", f"{number_of_warehouses}")
        first_row[2].metric(
            "Avg demand / warehouse", f"{average_demand:,.0f}", "orders/day"
        )
        first_row[3].metric("Operational buffer", f"{buffer_percentage:.0f}%")

        second_row = st.columns(4)
        second_row[0].metric(
            "Buffered demand target", f"{raw_buffered_target:,.0f}", "before rounding"
        )
        second_row[1].metric(
            "Recommended / warehouse", f"{recommended_per:,.0f}", "orders/day"
        )
        second_row[2].metric(
            "Recommended installed total", f"{recommended_total:,.0f}", "orders/day"
        )
        second_row[3].metric(
            "Largest neighborhood", f"{largest_neighborhood:,.0f}", "orders/day"
        )

    if warehouse_capacity is None:
        st.info(
            "Warehouse capacity is currently disabled in the optimizer. "
            "The advisor remains available as a planning reference."
        )
    else:
        current = safe_float(warehouse_capacity)
        gap = recommended_per - current
        if gap > 0:
            st.warning(
                f"Configured capacity is {gap:,.0f} orders/warehouse/day below the "
                "planning recommendation."
            )
        elif gap < 0:
            st.success(
                f"Configured capacity is {abs(gap):,.0f} orders/warehouse/day above the "
                "planning recommendation."
            )
        else:
            st.success("Configured capacity matches the planning recommendation.")

    st.caption(
        f"Calculation: {total_demand:,.0f} × (1 + {buffer_percentage:.0f}% buffer) = "
        f"{raw_buffered_target:,.0f} orders/day. "
        f"The network plan uses {recommended_per:,.0f} orders/day per warehouse "
        f"({recommended_total:,.0f} installed total)."
    )
    st.caption(
        "Traffic, vehicle selection, delivery cost and service radius are not used "
        "by the Capacity Advisor."
    )
def render_preflight(
    df: pd.DataFrame,
    recommendation: dict[str, Any],
    number_of_warehouses: int,
    warehouse_capacity,
    max_service_radius,
    optimization_mode: str,
    max_utilization,
) -> None:
    total_demand = safe_float(df["daily_orders"].sum())

    if warehouse_capacity is None:
        capacity_state = "Unconstrained"
        effective_total_capacity = None
    else:
        raw_capacity = float(number_of_warehouses) * float(warehouse_capacity)
        effective_multiplier = (
            safe_float(max_utilization, 1.0)
            if optimization_mode == "Resilience-Aware Optimization"
            and max_utilization is not None
            else 1.0
        )
        effective_total_capacity = raw_capacity * effective_multiplier
        capacity_state = (
            "Sufficient" if effective_total_capacity >= total_demand else "Insufficient"
        )

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        card("Scenario demand", f"{total_demand:,.0f}", "orders/day")
    with c2:
        card(
            "Advisor capacity",
            f"{int(recommendation['recommended_total_capacity']):,.0f}",
            f"{recommendation['buffer_percentage']:.0f}% planning buffer",
        )
    with c3:
        card(
            "Configured capacity",
            (
                f"{effective_total_capacity:,.0f}"
                if effective_total_capacity is not None
                else "Unconstrained"
            ),
            (
                f"{capacity_state} · effective ceiling"
                if optimization_mode == "Resilience-Aware Optimization"
                and warehouse_capacity is not None
                else capacity_state
            ),
        )
    with c4:
        card(
            "Service radius",
            f"{max_service_radius:.1f} km"
            if max_service_radius is not None
            else "Disabled",
            "straight-line Haversine model",
        )


def render_network_health(
    df: pd.DataFrame,
    warehouses: pd.DataFrame,
    assignments: pd.DataFrame,
    warehouse_capacity,
    max_service_radius,
) -> None:
    total_demand = safe_float(df["daily_orders"].sum())
    assigned_demand = (
        safe_float(assignments["daily_orders"].sum())
        if not assignments.empty and "daily_orders" in assignments.columns
        else 0.0
    )
    coverage = (
        len(assignments) / len(df) * 100.0
        if len(df) else 0.0
    )

    utilization = None
    if "utilization_percent" in warehouses.columns and not warehouses.empty:
        utilization = safe_float(warehouses["utilization_percent"].max())
    elif warehouse_capacity is not None and not warehouses.empty:
        total_capacity = len(warehouses) * float(warehouse_capacity)
        utilization = (
            assigned_demand / total_capacity * 100.0
            if total_capacity > 0 else 0.0
        )

    radius_violations = 0
    if (
        max_service_radius is not None
        and not assignments.empty
        and "distance_km" in assignments.columns
    ):
        radius_violations = int(
            (assignments["distance_km"].astype(float) > float(max_service_radius) + 1e-9).sum()
        )

    reasons = []
    if abs(assigned_demand - total_demand) > 1e-6:
        reasons.append("not all demand is represented in assignments")
    if coverage < 100:
        reasons.append("network coverage is incomplete")
    if radius_violations:
        reasons.append(f"{radius_violations} assignment(s) exceed the service radius")
    if utilization is not None and utilization > 100:
        reasons.append("at least one warehouse exceeds its configured effective capacity")
    elif utilization is not None and utilization >= 90:
        reasons.append("at least one warehouse is operating near its capacity ceiling")

    if any("exceed" in x or "not all" in x for x in reasons):
        state, color = "CRITICAL", BAD
    elif reasons:
        state, color = "WATCH", WARN
    else:
        state, color = "HEALTHY", GOOD

    detail = (
        "All current assignments satisfy the visible network checks."
        if not reasons
        else "; ".join(reasons).capitalize() + "."
    )

    st.markdown(
        f"""
        <div class="health">
            <div class="health-top">
                <div>
                    <div class="section-kicker">Network Health</div>
                    <div style="font-weight:760;">Current optimized network assessment</div>
                </div>
                <div class="health-state" style="color:{color};">{state}</div>
            </div>
            <div class="health-detail">{detail}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    hc1, hc2, hc3, hc4 = st.columns(4)
    hc1.metric("Coverage", f"{coverage:.1f}%")
    hc2.metric(
        "Peak utilization",
        f"{utilization:.1f}%" if utilization is not None else "N/A",
    )
    hc3.metric("Assigned demand", f"{assigned_demand:,.0f}")
    hc4.metric(
        "Avg. distance",
        (
            f"{safe_float(assignments['distance_km'].mean()):.2f} km"
            if not assignments.empty and "distance_km" in assignments.columns
            else "N/A"
        ),
    )


def render_capacity_chart(
    assignments: pd.DataFrame,
    warehouses: pd.DataFrame,
    warehouse_capacity,
) -> None:
    if assignments.empty:
        st.info("No assignments available.")
        return

    summary = (
        assignments.groupby("warehouse", as_index=False)
        .agg(
            assigned_demand=("daily_orders", "sum"),
            neighborhoods=("neighborhood", "count"),
        )
    )

    if warehouse_capacity is not None:
        summary["capacity"] = float(warehouse_capacity)
        summary["utilization"] = (
            summary["assigned_demand"] / summary["capacity"] * 100.0
        )
    elif "utilization_percent" in warehouses.columns:
        util_map = warehouses.set_index("warehouse_id")["utilization_percent"].to_dict()
        summary["capacity"] = None
        summary["utilization"] = summary["warehouse"].map(util_map)
    else:
        summary["capacity"] = None
        summary["utilization"] = None

    if warehouse_capacity is not None:
        chart_df = summary.melt(
            id_vars=["warehouse"],
            value_vars=["assigned_demand", "capacity"],
            var_name="Metric",
            value_name="Orders",
        )
        fig = px.bar(
            chart_df,
            x="warehouse",
            y="Orders",
            color="Metric",
            barmode="group",
            title="Assigned demand vs configured capacity",
            color_discrete_map={
                "assigned_demand": ACCENT,
                "capacity": "rgba(148,163,184,0.38)",
            },
        )
        style_plotly(fig)
        st.plotly_chart(fig, use_container_width=True)

    display = summary.rename(
        columns={
            "warehouse": "Warehouse",
            "assigned_demand": "Assigned Demand",
            "capacity": "Capacity",
            "utilization": "Utilization %",
            "neighborhoods": "Neighborhoods",
        }
    )
    st.dataframe(
        display.round(
            {"Assigned Demand": 0, "Capacity": 0, "Utilization %": 1}
        ),
        use_container_width=True,
        hide_index=True,
    )


def render_warehouse_rationale(
    warehouses: pd.DataFrame,
    assignments: pd.DataFrame,
    warehouse_capacity,
) -> None:
    for _, warehouse in warehouses.iterrows():
        warehouse_id = str(warehouse["warehouse_id"])
        local = assignments[assignments["warehouse"].astype(str) == warehouse_id]

        orders = safe_float(local["daily_orders"].sum())
        count = len(local)
        avg_distance = (
            safe_float(local["distance_km"].mean()) if not local.empty else 0.0
        )
        max_distance = (
            safe_float(local["distance_km"].max()) if not local.empty else 0.0
        )
        util_text = ""
        if warehouse_capacity:
            util_text = f" Utilization: {orders / float(warehouse_capacity) * 100:.1f}%."

        st.markdown(
            f"""
            <div class="card" style="min-height:0; margin-bottom:8px;">
                <div class="card-label">{warehouse_id}</div>
                <div class="card-value" style="font-size:1.02rem;">
                    {warehouse["neighborhood"]}
                </div>
                <div class="card-caption">
                    {count} neighborhoods · {orders:,.0f} orders/day ·
                    average {avg_distance:.2f} km · maximum {max_distance:.2f} km.
                    {util_text}
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )


inject_css()
render_hero()


if "warehouse_capacity" not in st.session_state:
    st.session_state["warehouse_capacity"] = 4000

# Sidebar controls
with st.sidebar:
    st.markdown("### Network Configuration")
    st.caption("Set the planning inputs, then execute the deterministic MILP.")

    st.markdown("**01 · DATA**")
    input_method = st.radio(
        "Data source",
        ["Sample Data", "Upload CSV"],
        key="input_method",
    )

    uploaded_file = None
    if input_method == "Upload CSV":
        uploaded_file = st.file_uploader(
            "Neighborhood CSV",
            type=["csv"],
            key="uploaded_neighborhood_file",
        )

    st.markdown("**02 · DEMAND**")
    demand_scenario = st.selectbox(
        "Demand scenario",
        list(DEMAND_SCENARIOS.keys()),
        key="demand_scenario",
    )

    st.markdown("**03 · NETWORK SIZE**")
    number_of_warehouses = int(
        st.number_input(
            "Number of warehouses",
            min_value=1,
            max_value=20,
            value=2,
            step=1,
            key="number_of_warehouses",
        )
    )

    warehouse_fixed_cost = float(
        st.number_input(
            "Infrastructure cost / warehouse / day",
            min_value=0.0,
            value=10000.0,
            step=1000.0,
            key="warehouse_fixed_cost",
        )
    )

df = load_data(input_method, uploaded_file)

if df is None:
    st.markdown(
        '<div class="info-strip">Load a neighborhood CSV to unlock the optimizer. '
        'The bundled sample dataset is available under Data Source → Sample Data.</div>',
        unsafe_allow_html=True,
    )
    st.stop()

df = df.copy()
df["base_orders"] = pd.to_numeric(df["daily_orders"], errors="coerce")
if df["base_orders"].isna().any():
    st.error("Neighborhood demand contains invalid numeric values.")
    st.stop()

# Advisor deliberately uses raw neighborhood data only.
advisor_df = df.copy()

# The optimization scenario uses the selected demand multiplier.
df["daily_orders"] = df["base_orders"] * DEMAND_SCENARIOS[demand_scenario]

if number_of_warehouses > len(df):
    st.error(
        f"Number of warehouses ({number_of_warehouses}) cannot exceed "
        f"the number of neighborhoods ({len(df)})."
    )
    st.stop()

with st.sidebar:
    st.markdown("**04 · CAPACITY PLANNING**")

    buffer_percentage = st.slider(
        "Operational capacity buffer",
        min_value=int(MIN_BUFFER_PERCENTAGE),
        max_value=int(MAX_BUFFER_PERCENTAGE),
        value=int(DEFAULT_BUFFER_PERCENTAGE),
        step=5,
        format="%d%%",
        key="capacity_buffer_percentage",
        help="Planning-only buffer used by the Capacity Advisor. Default is 15%.",
    )

recommendation = recommend_warehouse_capacity(
    neighborhoods=advisor_df,
    number_of_warehouses=number_of_warehouses,
    buffer_percentage=buffer_percentage,
)

# The callback fires before the capacity widget is created during the rerun.
with st.sidebar:
    st.caption(
        f"Advisor: {int(recommendation['recommended_capacity_per_warehouse']):,.0f} "
        "orders/day per warehouse."
    )
    st.button(
        "Apply Recommended Capacity",
        key="apply_recommended_capacity",
        on_click=apply_recommended_capacity,
        args=(recommendation,),
        use_container_width=True,
    )

    current_capacity = max(
        1,
        int(st.session_state.get("warehouse_capacity", 4000)),
    )

    enable_capacity = st.checkbox(
        "Enable warehouse capacity",
        value=True,
        key="enable_capacity",
    )

    if enable_capacity:
        warehouse_capacity = int(
            st.number_input(
                "Warehouse capacity (orders/day)",
                min_value=1,
                value=current_capacity,
                step=50,
                key="warehouse_capacity",
            )
        )
    else:
        warehouse_capacity = None

    st.markdown("**05 · SERVICE CONSTRAINTS**")
    enable_radius = st.checkbox(
        "Enable maximum service radius",
        value=True,
        key="enable_radius",
    )

    if enable_radius:
        max_service_radius = float(
            st.number_input(
                "Maximum service radius (km)",
                min_value=0.1,
                value=15.0,
                step=0.5,
                key="max_service_radius",
            )
        )
    else:
        max_service_radius = None

    st.markdown("**06 · DELIVERY ECONOMICS**")
    delivery_cost_per_order_km = float(
        st.number_input(
            "Base delivery cost / order / km",
            min_value=0.0,
            value=2.0,
            step=0.5,
            key="delivery_cost_per_order_km",
        )
    )
    traffic_level = st.selectbox(
        "Traffic condition",
        list(TRAFFIC_SCENARIOS.keys()),
        index=1,
        key="sidebar_traffic_level",
    )
    selected_traffic_factor = TRAFFIC_SCENARIOS[traffic_level]
    time_cost_per_hour = float(
        st.number_input(
            "Delivery time cost / hour",
            min_value=0.0,
            value=100.0,
            step=10.0,
            key="time_cost_per_hour",
        )
    )

    st.markdown("**07 · FLEET**")
    selected_vehicles = st.multiselect(
        "Available vehicles",
        list(VEHICLES.keys()),
        default=list(VEHICLES.keys()),
        key="selected_vehicles",
    )

    st.markdown("**08 · OPTIMIZATION**")
    optimization_mode = st.radio(
        "Strategy",
        ["Cost Optimization", "Resilience-Aware Optimization"],
        key="optimization_mode",
    )

    max_utilization = None
    if optimization_mode == "Resilience-Aware Optimization":
        max_utilization = (
            st.slider(
                "Maximum effective utilization",
                min_value=50,
                max_value=100,
                value=80,
                step=5,
                key="max_utilization_percent",
            )
            / 100.0
        )

    solver_time = int(
        st.number_input(
            "Solver time limit (seconds)",
            min_value=10,
            max_value=600,
            value=120,
            step=10,
            key="solver_time",
        )
    )

# Planning workspace
section_heading("01 · Planning", "Network planning snapshot")
st.caption(
    f"Scenario: {demand_scenario} · Warehouses: {number_of_warehouses} · "
    "Distance model: straight-line Haversine approximation"
)

render_preflight(
    df=df,
    recommendation=recommendation,
    number_of_warehouses=number_of_warehouses,
    warehouse_capacity=warehouse_capacity,
    max_service_radius=max_service_radius,
    optimization_mode=optimization_mode,
    max_utilization=max_utilization,
)

section_heading("02 · Capacity Planning", "Warehouse Capacity Advisor")
render_capacity_advisor(
    advisor_df=advisor_df,
    number_of_warehouses=number_of_warehouses,
    buffer_percentage=buffer_percentage,
    warehouse_capacity=warehouse_capacity,
    recommendation=recommendation,
)

st.markdown(
    '<div class="info-strip">The Capacity Advisor is intentionally independent from '
    'the MILP. It uses only baseline neighborhood demand, the selected warehouse count '
    'and the user-configured planning buffer. The optimizer remains the network decision engine.</div>',
    unsafe_allow_html=True,
)

section_heading("03 · Demand", "Scenario demand distribution")

demand_table = df[
    ["neighborhood", "latitude", "longitude", "base_orders", "daily_orders"]
].rename(
    columns={
        "neighborhood": "Neighborhood",
        "latitude": "Latitude",
        "longitude": "Longitude",
        "base_orders": "Baseline Orders",
        "daily_orders": "Scenario Orders",
    }
)

d1, d2 = st.columns([1.3, 1])
with d1:
    fig_demand = px.bar(
        df.sort_values("daily_orders", ascending=False),
        x="neighborhood",
        y="daily_orders",
        title="Scenario demand by neighborhood",
        color_discrete_sequence=[ACCENT],
    )
    style_plotly(fig_demand, height=350)
    fig_demand.update_layout(xaxis_title="", yaxis_title="Orders / day")
    st.plotly_chart(fig_demand, use_container_width=True)

with d2:
    st.dataframe(
        demand_table.sort_values("Scenario Orders", ascending=False),
        use_container_width=True,
        height=350,
        hide_index=True,
    )

# Initial map is always available before optimization.
section_heading("03 · Network Map", "Neighborhood demand topology")
try:
    base_map = create_map(advisor_df, map_mode="Demand View")
    st_folium(base_map, height=430, width=None, key="base_neighborhood_map")
except Exception as error:
    st.error(f"Could not render the neighborhood map: {error}")

# Optimization execution
st.markdown("---")
run_col1, run_col2, run_col3 = st.columns([1.45, 1, 1])

with run_col1:
    st.markdown("### Execute Network Optimization")
    st.caption(
        "Solve the capacitated warehouse-location MILP using the current planning configuration."
    )
    optimize_clicked = st.button(
        "Optimize Warehouse Network",
        type="primary",
        key="optimize_network",
        use_container_width=True,
    )

with run_col2:
    if warehouse_capacity is not None:
        headroom = (
            number_of_warehouses * warehouse_capacity
            - safe_float(df["daily_orders"].sum())
        )
        st.metric("Configured headroom", f"{headroom:,.0f}", "orders/day")
    else:
        st.metric("Configured capacity", "Unconstrained", "capacity disabled")

with run_col3:
    st.metric("Advisor buffer", f"{buffer_percentage:.0f}%", "planning only")

current_signature = make_signature(
    df,
    input_method,
    uploaded_file,
    demand_scenario,
    number_of_warehouses,
    warehouse_capacity,
    max_service_radius,
    traffic_level,
    optimization_mode,
    selected_vehicles,
    warehouse_fixed_cost,
)

if optimize_clicked:
    if not selected_vehicles:
        st.error("Select at least one vehicle type before running the optimizer.")
    else:
        try:
            with st.spinner("Solving the LOGITWIN MILP..."):
                result = optimize_warehouse_locations(
                    neighborhoods=df,
                    number_of_warehouses=number_of_warehouses,
                    delivery_cost_per_order_km=delivery_cost_per_order_km,
                    warehouse_fixed_cost=warehouse_fixed_cost,
                    warehouse_capacity=warehouse_capacity,
                    max_service_radius=max_service_radius,
                    traffic_factor=selected_traffic_factor,
                    time_cost_per_hour=time_cost_per_hour,
                    selected_vehicles=selected_vehicles,
                    time_limit=solver_time,
                    optimization_mode=optimization_mode,
                    max_utilization=max_utilization,
                )

            if not isinstance(result, dict):
                raise TypeError("Optimization engine returned an invalid result.")

            if not isinstance(result.get("warehouses"), pd.DataFrame):
                raise TypeError("Optimization result is missing warehouse data.")
            if not isinstance(result.get("assignments"), pd.DataFrame):
                raise TypeError("Optimization result is missing assignment data.")

            st.session_state["optimization_result"] = result
            st.session_state["optimization_signature"] = current_signature
            st.session_state.pop("warehouse_analysis", None)
            st.success("Optimization completed successfully.")
        except Exception as error:
            st.error(f"Optimization failed: {error}")

result = st.session_state.get("optimization_result")

if result is None:
    st.markdown(
        '<div class="info-strip">No optimized network is loaded yet. '
        'Run the optimizer to unlock network health, assignments, detailed maps, '
        'stress testing, resilience analysis and warehouse-count analysis.</div>',
        unsafe_allow_html=True,
    )
    st.stop()

warehouses = result.get("warehouses", pd.DataFrame())
assignments = result.get("assignments", pd.DataFrame())

if not isinstance(warehouses, pd.DataFrame) or not isinstance(assignments, pd.DataFrame):
    st.error("The saved optimization result is invalid. Run the optimizer again.")
    st.stop()

if warehouses.empty:
    st.error("The optimizer returned no warehouse locations. Run it again with feasible settings.")
    st.stop()

saved_signature = st.session_state.get("optimization_signature")
if saved_signature != current_signature:
    st.warning(
        "Planning inputs have changed since the last optimization. "
        "The result shown below is retained for reference until you run the optimizer again."
    )

section_heading("04 · Results", "Optimized network command center")

total_demand = safe_float(df["daily_orders"].sum())
average_distance = (
    safe_float(assignments["distance_km"].mean())
    if not assignments.empty and "distance_km" in assignments.columns
    else 0.0
)

if warehouse_capacity is not None:
    total_capacity = len(warehouses) * warehouse_capacity
    peak_utilization = (
        safe_float(warehouses["utilization_percent"].max())
        if "utilization_percent" in warehouses.columns
        else (total_demand / total_capacity * 100 if total_capacity else 0)
    )
else:
    total_capacity = None
    peak_utilization = None

r1, r2, r3, r4, r5, r6 = st.columns(6)
with r1:
    card("Active warehouses", f"{len(warehouses)}", "selected locations")
with r2:
    card("Scenario demand", f"{total_demand:,.0f}", "orders/day")
with r3:
    card(
        "Total capacity",
        f"{total_capacity:,.0f}" if total_capacity is not None else "Unconstrained",
        "configured",
    )
with r4:
    card(
        "Peak utilization",
        f"{peak_utilization:.1f}%" if peak_utilization is not None else "N/A",
        "across selected warehouses",
    )
with r5:
    card("Avg. distance", f"{average_distance:.2f} km", "straight-line estimate")
with r6:
    card(
        "Network cost",
        f"₹{safe_float(result.get('total_cost', 0)):,.0f}",
        "per planning day",
    )

render_network_health(
    df=df,
    warehouses=warehouses,
    assignments=assignments,
    warehouse_capacity=warehouse_capacity,
    max_service_radius=max_service_radius,
)

tabs = st.tabs(
    [
        "Overview",
        "Optimization",
        "Network Map",
        "Stress Test",
        "Resilience",
        "Warehouse Analysis",
    ]
)

tab_overview, tab_optimize, tab_map, tab_stress, tab_resilience, tab_analysis = tabs

with tab_overview:
    section_heading("Overview", "Network economics and rationale")

    cost_df = pd.DataFrame(
        {
            "Cost Type": ["Distance", "Fuel", "Time", "Infrastructure"],
            "Cost": [
                safe_float(result.get("distance_cost", 0)),
                safe_float(result.get("fuel_cost", 0)),
                safe_float(result.get("time_cost", 0)),
                safe_float(result.get("infrastructure_cost", 0)),
            ],
        }
    )

    oc1, oc2 = st.columns([1.15, 1])
    with oc1:
        fig_cost = px.bar(
            cost_df,
            x="Cost Type",
            y="Cost",
            title="Daily network cost breakdown",
            color_discrete_sequence=[ACCENT],
        )
        style_plotly(fig_cost, height=350)
        st.plotly_chart(fig_cost, use_container_width=True)

    with oc2:
        st.markdown(
            '<div class="callout"><b>Why these locations?</b><br>'
            "The MILP evaluates candidate neighborhood points, selects the requested "
            "number of facilities, assigns every neighborhood exactly once, enforces "
            "capacity and service-radius constraints when enabled, and chooses one "
            "vehicle for each assignment.</div>",
            unsafe_allow_html=True,
        )
        st.markdown("")
        render_warehouse_rationale(
            warehouses,
            assignments,
            warehouse_capacity,
        )

with tab_optimize:
    section_heading("Optimization", "MILP solution detail")

    solver_status = str(result.get("solver_status", "Unknown"))
    if solver_status in {"Optimal", "Feasible"}:
        st.success(f"Solver status: {solver_status}")
    else:
        st.warning(f"Solver status: {solver_status}")

    o1, o2, o3 = st.columns(3)
    o1.metric(
        "Weighted delivery distance",
        f"{safe_float(result.get('weighted_distance', 0)):,.0f}",
    )
    o2.metric(
        "Delivery cost",
        f"₹{safe_float(result.get('delivery_cost', 0)):,.0f}",
    )
    o3.metric(
        "Total delivery time",
        f"{safe_float(result.get('total_delivery_time', 0)):.2f} h",
    )

    st.subheader("Warehouse utilization")
    render_capacity_chart(
        assignments=assignments,
        warehouses=warehouses,
        warehouse_capacity=warehouse_capacity,
    )

    st.subheader("Neighborhood assignments")
    st.dataframe(assignments, use_container_width=True, hide_index=True)

    if not assignments.empty and "vehicle" in assignments.columns:
        vehicle_summary = (
            assignments.groupby("vehicle", as_index=False)
            .agg(
                neighborhoods=("neighborhood", "count"),
                daily_orders=("daily_orders", "sum"),
                trips=("trips", "sum"),
                fuel_liters=("fuel_liters", "sum"),
                fuel_cost=("fuel_cost", "sum"),
                delivery_time_hours=("delivery_time_hours", "sum"),
            )
        )
        st.subheader("Vehicle mix")
        st.dataframe(vehicle_summary, use_container_width=True, hide_index=True)

with tab_map:
    section_heading("Network Map", "Interactive logistics topology")
    map_mode = st.selectbox(
        "Map view",
        [
            "Demand View",
            "Warehouse Assignment",
            "Delivery Distance",
            "Capacity Utilization",
            "Risk View",
        ],
        key="map_mode_tab",
    )

    try:
        optimized_map = create_map(
            df,
            warehouses,
            assignments,
            map_mode=map_mode,
        )
        st_folium(
            optimized_map,
            height=650,
            width=None,
            key="optimized_network_map",
        )
    except Exception as error:
        st.error(f"Could not render the optimized map: {error}")

with tab_stress:
    section_heading("Stress Test", "Test the network under demand and traffic shocks")
    s1, s2 = st.columns(2)

    with s1:
        demand_change = st.slider(
            "Demand increase (%)",
            min_value=0,
            max_value=100,
            value=35,
            step=5,
            key="tab_stress_demand",
        )
        fuel_change = st.slider(
            "Fuel price increase (%)",
            min_value=0,
            max_value=100,
            value=20,
            step=5,
            key="tab_stress_fuel",
        )

    with s2:
        stress_traffic = st.selectbox(
            "Traffic condition",
            list(TRAFFIC_SCENARIOS.keys()),
            index=2,
            key="tab_stress_traffic",
        )
        spike_area = st.selectbox(
            "Neighborhood demand spike",
            ["None"] + df["neighborhood"].tolist(),
            key="tab_stress_neighborhood",
        )

    if st.button("Run Stress Test", key="tab_run_stress_test"):
        if not selected_vehicles:
            st.error("Select at least one vehicle type before running a stress test.")
        else:
            try:
                stress_df = apply_stress_scenario(
                    df,
                    demand_increase=demand_change / 100.0,
                    neighborhood=None if spike_area == "None" else spike_area,
                    neighborhood_spike=1.0,
                )
                with st.spinner("Re-solving the network under stress..."):
                    stress_result = optimize_warehouse_locations(
                        neighborhoods=stress_df,
                        number_of_warehouses=number_of_warehouses,
                        delivery_cost_per_order_km=delivery_cost_per_order_km,
                        warehouse_fixed_cost=warehouse_fixed_cost,
                        warehouse_capacity=warehouse_capacity,
                        max_service_radius=max_service_radius,
                        traffic_factor=TRAFFIC_SCENARIOS[stress_traffic],
                        time_cost_per_hour=time_cost_per_hour,
                        selected_vehicles=selected_vehicles,
                        time_limit=solver_time,
                        optimization_mode=optimization_mode,
                        max_utilization=max_utilization,
                    )

                normal_cost = safe_float(result.get("total_cost", 0))
                stress_cost = safe_float(stress_result.get("total_cost", 0))
                normal_fuel = safe_float(result.get("fuel_cost", 0))
                stress_fuel = safe_float(stress_result.get("fuel_cost", 0))
                adjusted_stress_fuel = stress_fuel * (1 + fuel_change / 100.0)
                adjusted_total_cost = (
                    stress_cost - stress_fuel + adjusted_stress_fuel
                )

                comparison = pd.DataFrame(
                    {
                        "Metric": [
                            "Orders",
                            "Delivery Cost",
                            "Fuel Cost",
                            "Total Cost",
                        ],
                        "Normal": [
                            safe_float(df["daily_orders"].sum()),
                            safe_float(result.get("delivery_cost", 0)),
                            normal_fuel,
                            normal_cost,
                        ],
                        "Stress": [
                            safe_float(stress_df["daily_orders"].sum()),
                            safe_float(stress_result.get("delivery_cost", 0)),
                            adjusted_stress_fuel,
                            adjusted_total_cost,
                        ],
                    }
                )
                st.dataframe(comparison, use_container_width=True, hide_index=True)

                sc1, sc2, sc3 = st.columns(3)
                sc1.metric(
                    "Order increase",
                    f"{safe_float(stress_df['daily_orders'].sum() - df['daily_orders'].sum()):,.0f}",
                )
                sc2.metric(
                    "Stress total cost",
                    f"₹{adjusted_total_cost:,.0f}",
                    f"₹{adjusted_total_cost - normal_cost:,.0f}",
                )
                sc3.metric(
                    "Stress solver",
                    str(stress_result.get("solver_status", "Unknown")),
                )
            except Exception as error:
                st.error(f"Stress test failed: {error}")

with tab_resilience:
    section_heading("Resilience", "Warehouse failure simulation")

    warehouse_ids = warehouses["warehouse_id"].astype(str).tolist()
    failed_warehouse = st.selectbox(
        "Warehouse to fail",
        warehouse_ids,
        key="tab_failure_warehouse",
    )

    if st.button("Simulate Warehouse Failure", key="tab_simulate_failure"):
        try:
            failure = simulate_warehouse_failure(
                neighborhoods=df,
                original_result=result,
                failed_warehouse=failed_warehouse,
                optimizer_function=optimize_warehouse_locations,
                warehouse_capacity=warehouse_capacity,
                max_service_radius=max_service_radius,
            )

            fc1, fc2, fc3 = st.columns(3)
            fc1.metric(
                "Affected orders",
                f"{safe_float(failure.get('affected_orders', 0)):,.0f}",
            )
            fc2.metric(
                "Affected neighborhoods",
                int(failure.get("affected_neighborhoods", 0)),
            )
            fc3.metric(
                "Distance change",
                f"{safe_float(failure.get('distance_change_percent', 0)):+.1f}%",
            )

            if failure.get("feasible"):
                st.success(failure.get("reason", "Reassignment proposal generated."))
            else:
                st.warning(failure.get("reason", "Reassignment is incomplete."))

            reassignment = failure.get("reassignment", pd.DataFrame())
            if isinstance(reassignment, pd.DataFrame) and not reassignment.empty:
                st.dataframe(
                    reassignment,
                    use_container_width=True,
                    hide_index=True,
                )
            else:
                st.info("No valid reassignment rows were generated.")
        except Exception as error:
            st.error(f"Failure simulation failed: {error}")

with tab_analysis:
    section_heading("Warehouse Analysis", "Compare network scale options")

    an1, an2 = st.columns(2)
    with an1:
        min_warehouses = st.number_input(
            "Minimum warehouses",
            min_value=1,
            max_value=len(df),
            value=1,
            step=1,
            key="analysis_min_warehouses",
        )
    with an2:
        max_warehouses = st.number_input(
            "Maximum warehouses",
            min_value=1,
            max_value=len(df),
            value=min(5, len(df)),
            step=1,
            key="analysis_max_warehouses",
        )

    if min_warehouses > max_warehouses:
        st.error("Minimum warehouses cannot exceed maximum warehouses.")
    elif st.button("Run Warehouse Count Analysis", key="run_count_analysis"):
        if not selected_vehicles:
            st.error("Select at least one vehicle type before running the analysis.")
        else:
            try:
                with st.spinner("Testing warehouse configurations..."):
                    analysis = analyze_warehouse_counts(
                        neighborhoods=df,
                        optimizer_function=optimize_warehouse_locations,
                        min_warehouses=int(min_warehouses),
                        max_warehouses=int(max_warehouses),
                        delivery_cost_per_order_km=delivery_cost_per_order_km,
                        warehouse_fixed_cost=warehouse_fixed_cost,
                        warehouse_capacity=warehouse_capacity,
                        max_service_radius=max_service_radius,
                        traffic_factor=selected_traffic_factor,
                        time_cost_per_hour=time_cost_per_hour,
                        selected_vehicles=selected_vehicles,
                        time_limit=solver_time,
                        optimization_mode=optimization_mode,
                        max_utilization=max_utilization,
                    )
                st.session_state["warehouse_analysis"] = analysis
            except Exception as error:
                st.error(f"Warehouse analysis failed: {error}")

    analysis = st.session_state.get("warehouse_analysis")
    if isinstance(analysis, pd.DataFrame):
        best = find_best_warehouse_count(analysis)
        if best is not None:
            st.info(
                f"Lowest total network cost among feasible tested configurations: "
                f"{best} warehouse(s)."
            )
        else:
            st.warning(
                "No feasible warehouse configuration was found in the tested range."
            )

        feasible = analysis[analysis["total_cost"].notna()].copy()
        if not feasible.empty:
            fig_scale = px.line(
                feasible,
                x="warehouses",
                y="total_cost",
                markers=True,
                title="Total network cost vs warehouse count",
                color_discrete_sequence=[ACCENT],
            )
            style_plotly(fig_scale, height=360)
            fig_scale.update_layout(
                xaxis_title="Number of warehouses",
                yaxis_title="Total cost",
            )
            st.plotly_chart(fig_scale, use_container_width=True)

        st.dataframe(
            analysis,
            use_container_width=True,
            hide_index=True,
        )
        st.caption(
            "Infeasible configurations remain visible with their solver/error status."
        )

    st.markdown("---")
    section_heading("Warehouse Rationale", "Service footprint by selected warehouse")
    render_warehouse_rationale(
        warehouses,
        assignments,
        warehouse_capacity,
    )

# Export
st.markdown("---")
section_heading("05 · Export", "Save the optimized network")

st.download_button(
    "Download Optimized Assignments",
    assignments.to_csv(index=False),
    "logitwin_optimized_assignments.csv",
    "text/csv",
    key="download_assignments",
    use_container_width=True,
)

with st.expander("Model notes"):
    st.write(
        "Distance values use Haversine straight-line geography, not live road distance."
    )
    st.write(
        "Vehicle trip calculations are planning-level estimates rather than a full "
        "vehicle-routing problem."
    )
    st.write(
        "The Capacity Advisor is independent of the MILP and uses baseline neighborhood "
        "demand, warehouse count and a configurable planning buffer."
    )
