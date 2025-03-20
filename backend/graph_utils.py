from pyvis.network import Network
import networkx as nx
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# @Author: Asta Omarsdottir
# @Email: asta.omarsdottir@gmail.com
# @Date: 2024-12-03
# @Last Modified by:   undefined
# @Last Modified time: 2024-12-03
# @Description: Handles graph design

# ***************************************************************************************

# @Author: Asta Omarsdottir
# @Email: asta.omarsdottir@gmail.com
# @Date: 2024-12-10
# @Last Modified by:   undefined
# @Last Modified time: 2024-12-19
# @Description: Fetch data for heatmap visualizing dwell time in locations over time

def create_heatmap(data, filter_data):
    """
    Create a heatmap showing dwell time by vessel and date, with locations as annotations.
    """
    # Create heatmap
    fig = px.density_heatmap(
        data,
        x='date',
        y='location_id',
        z='dwell',
        title='Vessel Dwell Time by location and Date',
        labels={'dwell': 'Dwell Time (s)', 'date': 'Date', 'location_id': 'Location'},
        color_continuous_scale='Viridis'
    )
    fig.update_layout(xaxis_title="Date", yaxis_title="Location", coloraxis_colorbar_title="Dwell Time (s)",
    font=dict(size=8, variant="small-caps"),
    title_font=dict(size=12, variant="small-caps"),
    legend_font=dict(size=8, variant="small-caps")
    )

    return fig

# @Author: Asta Omarsdottir
# @Email: asta.omarsdottir@gmail.com
# @Date: 2024-12-26
# @Last Modified by:   Asta Omarsdottir
# @Last Modified time: 2025-01-14
# @Description: Create treemap

# Create a treemap using Plotly
def create_treemap(treemap_data):
    
    # Remove rows where 'quantity_tons' is zero or missing
    treemap_data = treemap_data[treemap_data['quantity_tons'] > 0]
    
        # Check if the filtered data is empty
    if treemap_data.empty:
        return {}  # Return an empty figure if no valid data is available
    
    fig = px.treemap(
        treemap_data,
        path=["city_of_arrival", "fish_name"],
        values="quantity_tons",
        color="quantity_tons",
        color_continuous_scale="Viridis",
        title="Fish Deliveries Treemap",
    )
    fig.update_layout(
    font=dict(size=8, variant="small-caps"),
    title_font=dict(size=12, variant="small-caps"),
    legend_font=dict(size=8, variant="small-caps")
    )
    return fig

# @Author: Asta Omarsdottir
# @Email: asta.omarsdottir@gmail.com
# @Date: 2025-02-26
# @Last Modified by:   undefined
# @Last Modified time: 2025-02-26
# @Description: Create Network-link graph (pyvis)

def create_interactive_graph(fish_delivery_data):
    G = nx.MultiDiGraph()  # Directed multigraph
    net = Network(notebook=False, directed = True) # Pyvis interactive network 
    net.repulsion()
    
    net.set_options("""
    {
        "layout": {
            "hierarchical": {
                "enabled": false
            }
        },
        "physics": {
            "enabled": true,
            "solver": "forceAtlas2Based",
            "stabilization": {
                "enabled": true,
                "iterations": 300
            }
        },
        "manipulation": {
            "enabled": false
        }
    }
    """)
    
   # net.toggle_physics(False)
   
    for record in fish_delivery_data:
        # Basic info from the cargo report
        delivery_id = record.get("delivery_report_name", "Unknown")
        date_of_arrival = record.get("date_of_arrival", "Unknown")
        city_of_arrival = record.get("city_of_arrival", "Unknown")
        fish = record.get("fish_name", "Unknown")
        qty_tons = float(record.get("quantity_tons", 0.0))  
        
        # Get lists (if no list provided, default to empty list)
        harbor_vessels = record.get("harbor_vessels", [])
        ping_vessels = record.get("ping_vessels", [])

        # Add primary nodes
        net.add_node(
            delivery_id,
            label=delivery_id, 
            title= f"Cargo: {delivery_id}\nArrival: {date_of_arrival}\nCity: {city_of_arrival}\nFish Type: {fish}\nFish qty: {qty_tons}",
            size=30, 
            color="black"
            )
        net.add_node(city_of_arrival, size=30, label=city_of_arrival, color="darkred", title=f"City:{city_of_arrival}")
        net.add_node(fish, label=fish, size=30, color="green", title=f"Fish Type: {fish}")
        
        # Edge between DeliveryReport and City of Arrival
        net.add_edge(
            delivery_id, city_of_arrival, 
            title=f"Delivery: {delivery_id}\nArrival: {date_of_arrival}\nCity: {city_of_arrival}",
            value=3,  # This controls edge thickness in Pyvis
            color="orange"
        )
        
        # Edge between DeliveryReport and Commodity (Fish)
        net.add_edge(
            delivery_id, fish, 
            title=f"Delivery: {delivery_id}\nArrival: {date_of_arrival}\nFish: {fish}\nQty: {qty_tons} tons",
            value=3,  # edge thickness
            color="gray"
        )
        
        # For each harbor vessel, add a node and an edge from fish to harbor vessel
        for hv in harbor_vessels:
            # Ensure hv is a valid string (or int)
            hv = str(hv) if hv is not None else "Unknown"
            net.add_node(hv, label=hv, shape = 'star', size=30, color="blue", title=f"Harbor Vessel: {hv}\nExit: {date_of_arrival}\nCity: {city_of_arrival}\nFish: {fish}\nQty: {qty_tons}")
            net.add_edge(
                fish, hv,
                title=f"Delivery: {delivery_id}\nArrival: {date_of_arrival}\nCity: {city_of_arrival}\nQty: {qty_tons} tons\nHarbor: {hv}\nFish: {fish}",
                value=(qty_tons + 3),
                color="purple"
            )

            # For each ping vessel, add a node and an edge from fish to ping vessel
            for pv in ping_vessels:
                pv = str(pv) if pv is not None else "Unknown"
                net.add_node(pv, label=pv, size=30, color="cyan", title=f"Ping Vessel: {pv}\nDate: {date_of_arrival}\nCity: {city_of_arrival}\nFish: {fish}\nQty: {qty_tons}")
                net.add_edge(
                    fish, pv,
                    title=f"Delivery: {delivery_id}\nArrival: {date_of_arrival}\nCity: {city_of_arrival}\nQty: {qty_tons} tons\nPing: {pv}\nFish: {fish}",
                    value=qty_tons,
                    color="yellow"
                )

    # Generate and return the HTML content
    return net.generate_html()

# def create_interactive_graph(fish_delivery_data):
#     df = preprocess_data_for_clustering(fish_delivery_data)
#     df, kmeans = cluster_deliveries(df, k=4)  # Apply clustering

#     cluster_colors = ["red", "blue", "orange", "purple"]  # Define colors for clusters

#     G = nx.MultiDiGraph()  
#     net = Network(notebook=False, directed=True)  

#     net.set_options("""
#     var options = {
#     "layout": {
#         "hierarchical": {
#         "enabled": true,
#         "direction": "LR",
#         "sortMethod": "hubsize"
#         }
#     },
#     "physics": {
#         "enabled": false
#     }
#     }
#     """)

#     for idx, record in df.iterrows():
#         delivery_id = fish_delivery_data[idx].get("delivery_report_name", "Unknown")
#         city_of_arrival = fish_delivery_data[idx].get("city_of_arrival", "Unknown")
#         fish = fish_delivery_data[idx].get("fish_name", "Unknown")
#         qty_tons = float(fish_delivery_data[idx].get("quantity_tons", 0.0))
#         harbor_vessels = fish_delivery_data[idx].get("harbor_vessels", [])
#         ping_vessels = fish_delivery_data[idx].get("ping_vessels", [])

#         # Get cluster color
#         cluster_id = record["cluster"]
#         cluster_color = cluster_colors[cluster_id]

#         # Add nodes with cluster colors
#         net.add_node(delivery_id, label=delivery_id, color=cluster_color, title=f"Cluster {cluster_id}")
#         net.add_node(city_of_arrival, label=city_of_arrival, color="lightgray")
#         net.add_node(fish, label=fish, color="lightblue")

#         # Edges
#         net.add_edge(delivery_id, city_of_arrival, color="gray")
#         net.add_edge(delivery_id, fish, color="purple")

#         for hv in harbor_vessels:
#             net.add_node(hv, label=hv, color="green")
#             net.add_edge(fish, hv, color="pink")

#         for pv in ping_vessels:
#             net.add_node(pv, label=pv, color="lightgreen")
#             net.add_edge(fish, pv, color="yellow")

#     return net.generate_html()

# @Author: Asta Omarsdottir
# @Email: asta.omarsdottir@gmail.com
# @Date: 2025-02-28
# @Last Modified by:   undefined
# @Last Modified time: 2025-02-28
# @Description: handle empty heatmap

def create_empty_heatmap():
    # Create an empty heatmap figure
    fig = go.Figure()

    # Add empty heatmap data
    fig.add_trace(go.Heatmap(
        z=[],
        x=[],
        y=[],
        colorscale='Viridis'
    ))

    # Update layout with appropriate titles and labels
    fig.update_layout(
        title="Transport Movements Heatmap",
        xaxis_title="Date",
        yaxis_title="Location ID",
        xaxis=dict(type='category', showgrid=True),
        yaxis=dict(type='category', showgrid=True),
        annotations=[
            dict(
                text='No data to display',
                xref='paper', yref='paper',
                showarrow=False,
                font=dict(size=20)
            )
        ]
    )
    fig.update_layout(
    font=dict(size=8, variant="small-caps"),
    title_font=dict(size=12, variant="small-caps"),
    legend_font=dict(size=8, variant="small-caps")
    )

    return fig

def create_empty_treemap():
    # Create an empty figure with a placeholder layout
    fig = go.Figure()

    # Set a title and add a message in the center
    fig.update_layout(
        title="No Data Available",
        annotations=[
            dict(
                text="No data to display",
                x=0.5,
                y=0.5,
                showarrow=False,
                font=dict(size=20, color="gray"),
                xref="paper",
                yref="paper",
            )
        ],
    )

    return fig  # Return the empty figure