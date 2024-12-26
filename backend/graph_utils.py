import networkx as nx
import pandas as pd
import plotly.express as px
from statsmodels.tsa.seasonal import seasonal_decompose
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import IsolationForest

# @Author: Asta Omarsdottir
# @Email: asta.omarsdottir@gmail.com
# @Date: 2024-12-03
# @Last Modified by:   undefined
# @Last Modified time: 2024-12-03
# @Description: Handles graph design


# @Author: Nupur Mittal
# @Email: nupurmittal5@gmail.com
# @Date: 2024-11-08
# @Last Modified by:   Asta Omarsdottir 
# @Last Modified time: 2024-11-13
# @Last Modified: Moved from Connection.py with minor changes
# @Description: Query data from Neo4j for Networkx Node-Link Diagram, Fish Delivery Network 
# Create NetworkX graph from DeliveryReport, Transaction events and Commodity fish

def create_graph(delivery_data):
    G = nx.Graph()
    for record in delivery_data:
        delivery_node = f"delivery_{record['delivery_date']}_{record['quantity_delivered']}"
        fish_node = record['fish_type']
        
        # Add nodes
        G.add_node(delivery_node, label=f"Delivery on {record['delivery_date']}", type='delivery')
        G.add_node(fish_node, label=fish_node, type='fish')
        
        # Add edge
        G.add_edge(delivery_node, fish_node, quantity=record['quantity_delivered'])
    
    return G

# @Author: Nupur Mittal
# @Email: nupurmittal5@gmail.com
# @Date: 2024-11-08
# @Last Modified by:   Asta Omarsdottir 
# @Last Modified time: 2024-11-13
# @Last Modified: Moved from Connection.py with minor changes
# @Description: Convert NetworkX graph to Cytoscape elements for Networkx Node-Link Diagram, Fish Delivery Network 

def nx_to_cytoscape_elements(G):
    elements = []
    
    # Add nodes
    for node, data in G.nodes(data=True):
        elements.append({'data': {'id': node, 'label': data['label'], 'type': data['type']}})
    
    # Add edges
    for source, target, data in G.edges(data=True):
        elements.append({'data': {'source': source, 'target': target, 'label': f"{data['quantity']} tons"}})
    
    return elements

# @Author: Nupur Mittal
# @Email: nupurmittal5@gmail.com
# @Date: 2024-11-08
# @Last Modified by:   Asta Omarsdottir # minor changes, error handling and debugging
# @Last Modified time: 2024-11-13
# @Last Modified: Moved from dataframetable.py with minor changes 
# @Description: Create decompose time series to analyse fish quantity and seasonal trends 

def decompose_time_series(data):
    data['date'] = pd.to_datetime(data['date'])
    data.set_index('date', inplace=True)
    data = data.resample('D').sum()
    if len(data) < 30:
        raise ValueError("Not enough data points for seasonal decomposition (minimum 30 days required).")
    decomposition = seasonal_decompose(data['qty_tons'], model='additive', period=30)
    return decomposition

# @Author: Nupur Mittal
# @Email: nupurmittal5@gmail.com
# @Date: 2024-11-15
# @Last Modified by:   Asta Omarsdottir 
# @Last Modified time: 2024-11-13
# @Modified: Moved from network.py with minor changes
# @Description: Fetch data to analyse fish quantity and seasonal trends

def detect_anomalies(dataframe):
    # Add a numerical representation of dates for modeling
    dataframe['date_numeric'] = dataframe['date'].map(pd.Timestamp.toordinal)

    # Normalize data for better results with Isolation Forest
    scaler = StandardScaler()
    dataframe[['date_numeric', 'qty']] = scaler.fit_transform(dataframe[['date_numeric', 'qty']])

    # Isolation Forest to identify anomalies
    isolation_forest = IsolationForest(contamination=0.05, random_state=42)
    dataframe['anomaly'] = isolation_forest.fit_predict(dataframe[['date_numeric', 'qty']])

    # Map anomaly values to readable labels
    dataframe['anomaly'] = dataframe['anomaly'].map({1: 'Normal', -1: 'Anomalous'})

    return dataframe

# @Author: Asta Omarsdottir
# @Email: asta.omarsdottir@gmail.com
# @Date: 2024-12-10 09:58:52
# @Last Modified by:   undefined
# @Last Modified time: 2024-12-19 09:58:52
# @Description: Fetch data for heatmap visualizing dwell time in locations over time

def create_heatmap(data, filter_data, calendar_type, single_date, start_date, end_date):
    """
    Create a heatmap showing dwell time by location and date, filtered by vessel.
    """
    # get stored filter data
    selected_vessels = filter_data.get('vessels', [])

    # manage selected date/daterange
    selected_date = None
    if calendar_type == 'single' and single_date:
        selected_date = single_date[0] if single_date else None
    elif calendar_type == 'range' and start_date and end_date:
        selected_date = f"{start_date[0]} to {end_date[0]}" if start_date and end_date else None

    # Filter data based on selected vessels
    if selected_vessels:
        data = data[data['vessel_id'].isin(selected_vessels)]
        
    # Filter data based on selected date
    if selected_date:
       data = data[data['date'] == selected_date]
       
    # # # Handle range selection separately if needed   
    
    # Aggregate dwell time for heatmap
    heatmap_data = data.groupby(['date', 'location_id'])['dwell'].sum().reset_index()
    
    # Create heatmap
    fig = px.density_heatmap(
        heatmap_data,
        x='date',
        y='location_id',
        z='dwell',
        title='Dwell Time by Location and Date',
        labels={'dwell': 'Dwell Time (s)', 'date': 'Date', 'location_id': 'Location'},
        color_continuous_scale='Viridis'
    )
    fig.update_layout(xaxis_title="Date", yaxis_title="Location", coloraxis_colorbar_title="Dwell Time (s)")
    return fig

# @Author: Asta Omarsdottir
# @Email: asta.omarsdottir@gmail.com
# @Date: 2024-12-26
# @Last Modified by:   undefined
# @Last Modified time: 2024-12-26
# @Description: Create treemap

def create_treemap(treemap_data):
    fig = px.treemap(
        treemap_data,
        path=["city_of_arrival", "vessel_company"],
        values="total_qty_tons",
        color="total_qty_tons",
        color_continuous_scale="Viridis",
        title="Treemap of Fish Quantity by Vessel Company and City"
    )
    return fig


