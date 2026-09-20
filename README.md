GRIDPOINT
Logistics Made Easy

GRIDPOINT is a warehouse and urban delivery network simulator that helps optimize warehouse locations, customer assignments, capacity, delivery cost, and network resilience.

How It Works
1. Load Data

Upload a neighborhood CSV containing:

Neighborhood
Latitude
Longitude
Daily Orders
2. Configure Network

Set:

Number of warehouses
Warehouse capacity
Service radius
Traffic conditions
Delivery cost
Vehicle types
Demand scenario
3. Capacity Advisor

GRIDPOINT estimates the required warehouse capacity using:

Total neighborhood demand
Number of warehouses
Configurable operational buffer
4. Optimization

The system uses Mixed Integer Linear Programming (MILP) with PuLP/CBC to:

Select warehouse locations
Assign neighborhoods to warehouses
Respect capacity and service-radius constraints
Select suitable delivery vehicles
Minimize network cost
5. Network Analysis

The dashboard shows:

Capacity utilization
Delivery distance
Cost breakdown
Warehouse performance
Network health
6. Map Visualization

Interactive maps display:

Demand distribution
Warehouse locations
Neighborhood assignments
Delivery distances
Capacity utilization
Network risk
7. Stress Testing

Simulate changes such as:

Demand increases
Traffic changes
Local demand spikes
Fuel-price changes
8. Resilience Testing

Simulate a warehouse failure and analyze:

Affected neighborhoods
Affected orders
Possible reassignment
Additional delivery distance
Remaining network capacity
Core Algorithm
Neighborhood Data
       ↓
Demand & Capacity Analysis
       ↓
Distance Matrix (Haversine)
       ↓
MILP Optimization
       ↓
Warehouse Selection
       ↓
Neighborhood Assignment
       ↓
Vehicle Selection
       ↓
Cost & Capacity Analysis
       ↓
Visualization & Resilience Testing
Optimization Objective

GRIDPOINT minimizes:

Delivery Cost + Fuel Cost + Time Cost + Infrastructure Cost

subject to warehouse count, capacity, assignment, vehicle, and service-radius constraints.

UI

The application uses a clean dark logistics-control-center interface with:

Network overview
Capacity Advisor
Optimization results
Interactive network map
Stress testing
Resilience analysis
Warehouse-count analysis
Tech Stack

Python · Streamlit · Pandas · NumPy · Plotly · Folium · PuLP/CBC

Run Locally
pip install -r requirements.txt
streamlit run app.py

GRIDPOINT turns complex warehouse planning into a simple visual decision-support system for urban logistics.
