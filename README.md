# GRIDPOINT — Logistics Made Easy

Run:

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Fixes in this build

- Capacity Advisor uses native Streamlit components, so its HTML markup is never displayed as plain text.
- Capacity recommendation uses baseline neighborhood demand, warehouse count, and the configurable planning buffer only.
- Default buffer: 15%; configurable range: 0%–50%.
- OpenStreetMap is used as the Folium basemap; no Google, Mapbox, or CartoDB API key is required.
- Existing PuLP/CBC MILP optimization is retained.
- Existing stress, resilience, fleet, warehouse-count, and map functionality is retained.

For a dataset with 6,120 baseline orders/day, 2 warehouses, and a 15% buffer, the advisor returns 3,519 orders/day per warehouse and 7,038 orders/day installed total.
