GRIDPOINT: Logistics Made Easy

GRIDPOINT is a warehouse and urban delivery network optimization project. I built it to make logistics planning easier to understand and play around with. You can find good warehouse locations, assign neighborhoods to them, plan capacity, estimate delivery costs, and see how the network holds up when conditions change.

We used mostly CHAT-GPT for the code and have done some changes in code manually.
We used VS-CODE for code editor .
And as we used "streamlit" as our website hosting, so we ran it on local host


How it works-------------

1. Add your neighborhood data

Upload a CSV with these columns:

Neighborhood, Latitude, Longitude, Daily Orders

Everything else in the app is calculated from this file.

2. Set up the network

Pick your main planning parameters:

Number of warehouses

Warehouse capacity

Maximum service radius

Demand scenario

Traffic condition

Delivery cost

Available vehicle types

3. Check capacity

The Capacity Advisor gives a simple capacity recommendation based on neighborhood demand and the number of warehouses. It also adds an operational buffer, which is 15% by default but you can change it.

4. Optimize the network

GRIDPOINT uses Mixed Integer Linear Programming (MILP) with PuLP/CBC to find a good warehouse network. The optimizer decides:

Which warehouse locations to use

Which warehouse serves each neighborhood

Which vehicle is used

How much capacity is used

What the final network cost is

5. Analyze the results

Once optimization finishes, the dashboard shows the key numbers: total demand, warehouse utilization, delivery distance, cost breakdown, warehouse performance, and overall network health.

6. View the network on a map

The interactive map shows neighborhood demand, warehouse locations, delivery assignments, delivery distance, capacity utilization, and network risk.

7. Stress-test it

The stress-testing section lets you simulate:

Higher demand

Heavy traffic

Local demand spikes

Fuel price changes

That way you can see how the network behaves when things don't go as planned.

8. Test warehouse failures

The resilience section lets you temporarily remove a warehouse from the network. The system then checks:

Which neighborhoods and orders are affected

Whether they can be reassigned

How much extra delivery distance that adds

How much capacity the remaining warehouses have left

Optimization flow-------------

Neighborhood Data → Demand Analysis → Capacity Planning → Distance Calculation → MILP Optimization → Warehouse Selection → Neighborhood Assignment → Vehicle Selection → Cost & Capacity Analysis → Map & Dashboard → Stress and Resilience Testing

Optimization model-------------

The main goal is to bring down the overall network cost:

Total Cost = Delivery Cost + Fuel Cost + Time Cost + Infrastructure Cost

The model also takes into account the number of warehouses, warehouse capacity, service radius, neighborhood assignments, and vehicle selection.

Distances use the Haversine formula, which gives the straight-line distance between two locations.

Dashboard-------------

The dashboard is dark-themed and built around the main logistics workflow:

Network Overview: a quick look at demand, warehouses, capacity, cost, and network health

Capacity Advisor: shows the recommended warehouse capacity and compares it with what you configured

Optimization Results: warehouse selections, neighborhood assignments, vehicle choices, distances, and costs

Interactive Map: a geographical view of the whole network

Stress Testing: how the network changes under different operating conditions

Resilience Analysis: what happens to the rest of the network when a warehouse fails

Warehouse Analysis: compares different warehouse-count setups

Tech stack-------------

Python, Streamlit, Pandas, NumPy, PuLP / CBC, Plotly, Folium


Running the project-------------

Clone the repo and install the requirements:

bash
pip install -r requirements.txt

Then start the app:

bash
streamlit run app.py

It should open in your browser automatically.

Key features-------------

Warehouse location optimization

Neighborhood assignment

Warehouse capacity planning

Configurable capacity buffer

Vehicle selection

Delivery cost calculation

Traffic and demand scenarios

Interactive network map

Stress testing

Warehouse failure analysis

Resilience analysis

Warehouse-count comparison


Why GRIDPOINT?

The idea is simple: take a complicated logistics problem and make it easier to see, understand, and experiment with. Instead of just staring at optimization numbers, GRIDPOINT puts the model, maps, capacity analysis, stress testing, and resilience analysis all in one place.

GRIDPOINT: Logistics Made Easy
