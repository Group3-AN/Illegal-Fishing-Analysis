import os
import json # used to get geo data
from neo4j import GraphDatabase
import networkx as nx
import dash
from dash import html, dcc
import dash_cytoscape as cyto
import pandas as pd
import geopandas as gpd
from statsmodels.tsa.seasonal import seasonal_decompose
from dash.dependencies import Input, Output
import plotly.express as px
import plotly.graph_objects as go
from neo4j import GraphDatabase
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import IsolationForest
import numpy as np
import dash_cytoscape as cyto
import logging 
from shapely.geometry import Point, Polygon, MultiPolygon, shape
from datetime import datetime, timedelta

# Get project root map
base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# create filepath to geojson
file_path_geojson = os.path.join(base_dir,"backend", "ETL_data", "Oceanus Geography.geojson")
# create filepath to Nodes json
file_path_nodesjson = os.path.join(base_dir,"backend", "ETL_data", "Oceanus Geography Nodes.json")

# Neo4j connection details
uri = "bolt://localhost:7687"
username = "neo4j"
password = "asdf1234"
driver = GraphDatabase.driver(uri, auth=(username, password))

# @Author: Asta Omarsdottir
# @Email: asta.omarsdottir@gmail.com
# @Date: 2024-11-18
# @Last Modified by:   undefined
# @Last Modified time: 2024-12-18
# @Description: get vessels for dropdown filter

def get_vessels():
    query = """
    MATCH (n)
    WHERE n:`Entity.Vessel.CargoVessel` OR n:`Entity.Vessel.FishingVessel`
    RETURN n.id AS id
    ORDER BY id
    """
    with driver.session() as session:
        try:    
            result = session.run(query)
            ids = [record["id"] for record in result]  # extract id:n
            return ids
        except Exception as e:
            print("Error fetching vessels:", e)
            return []  # Return empty list in case of error

# @Author: Asta Omarsdottir
# @Email: asta.omarsdottir@gmail.com
# @Date: 2024-11-18
# @Last Modified by:   undefined
# @Last Modified time: 2024-11-18
# @Description: get cities for dropdown filter

def get_cities():
    query = """
    MATCH (n)
    WHERE n:`Entity.Location.City`    
    RETURN n.id AS id
    ORDER BY id
    """
    with driver.session() as session:
        try: 
            result = session.run(query)
            ids = [record["id"] for record in result]  # Extract id:n
            return ids
        except Exception as e:
            print("Error fetching cities:", e)
            return []  # Return empty list in case of error
        
# @Author: Asta Omarsdottir
# @Email: asta.omarsdottir@gmail.com
# @Date: 2024-11-24
# @Last Modified by:   undefined
# @Last Modified time: 2024-11-24
# @Description: create mapping between {name: id} for geojson and nodes json
        
def get_city_mapping():
    query = """
    MATCH (n:`Entity.Location.City`)
    RETURN n.id AS id, n.Name AS name
    """
    with driver.session() as session:
        try:
            result = session.run(query)
            mapping = {record["name"]: record["id"] for record in result}
            return mapping
        except Exception as e:
            print("Error fetching city mapping:", e)
            return {}  # Return empty dict on error
        
# @Author: Asta Omarsdottir
# @Email: asta.omarsdottir@gmail.com
# @Date: 2024-11-24
# @Last Modified by:   undefined
# @Last Modified time: 2024-11-24
# @Description: get ports for dropdown filter

def get_points():
    query = """
    MATCH (n)
    WHERE n:`Entity.Location.Point`    
    RETURN n.id AS id
    ORDER BY id
    """
    with driver.session() as session:
        try:
            result = session.run(query)
            ids = [record["id"] for record in result]  # Extract id:n
            return ids
        except Exception as e:
            print("Error fetching ports:", e)
            return []  # Return empty list in case of error
        
# @Author: Asta Omarsdottir
# @Email: asta.omarsdottir@gmail.com
# @Date: 2024-11-24
# @Last Modified by:   undefined
# @Last Modified time: 2024-11-24
# @Description: get species for dropdown filter

def get_species():
    query = """
    MATCH (n)
    WHERE n:`Entity.Commodity.Fish`    
    RETURN n.id AS id
    ORDER BY id
    """
    with driver.session() as session:
        try:
            result = session.run(query)
            ids = [record["id"] for record in result]  # Extract id:n
            return ids
        except Exception as e:
            print("Error fetching species:", e)
            return []  # Return empty list in case of error
        
# @Author: Asta Omarsdottir
# @Email: asta.omarsdottir@gmail.com
# @Date: 2024-11-24
# @Last Modified by:   undefined
# @Last Modified time: 2024-11-24
# @Description: get regions for dropdown filter
         
def get_regions():
    query = """
    MATCH (n)
    WHERE n:`Entity.Location.Region`    
    RETURN n.id AS id
    ORDER BY id
    """
    with driver.session() as session:
        try:
            result = session.run(query)
            ids = [record["id"] for record in result]  # Extract ID:n
            return ids
        except Exception as e:
            print("Error fetching regions:", e)
            return []  # Return empty list in case of error
        
# @Author: Asta Omarsdottir
# @Email: asta.omarsdottir@gmail.com
# @Date: 2024-12-19
# @Last Modified by:   undefined
# @Last Modified time: 2024-11-24
# @Description: get companies for dropdown filter
         
def get_companies():
    query = """
    MATCH (n)
    WHERE n:`Entity.Vessel.FishingVessel`    
    RETURN DISTINCT n.company AS company
    ORDER BY company
    """
    with driver.session() as session:
        try:
            result = session.run(query)
            ids = [record["company"] for record in result]  # Extract company as id:n
            return ids
        except Exception as e:
            print("Error fetching regions:", e)
            return []  # Return empty list in case of error
        
# @Author: Nupur Mittal
# @Email: nupurmittal5@gmail.com
# @Date: 2024-11-08
# @Last Modified by:   Asta Omarsdottir
# @Last Modified time: 2024-11-24
# @Last Modified: Moved from dataframetable.py with minor changes
# @Description: clean data, date, qty_tons for seasonal trends
        
def clean_data(data):
    try:
        data = data.copy()
        data.loc[:, 'date'] = pd.to_datetime(data['date'], errors='coerce')
        data = data.dropna(subset=['date'])
        data.loc[:, 'qty_tons'] = pd.to_numeric(data['qty_tons'], errors='coerce')
        data = data.dropna(subset=['qty_tons'])
        data = data[data['qty_tons'] >= 0]
        return data
    except Exception as e:
        print("Error in clean data:", e)
        return []  # Return empty list in case of error
    
# @Author: Nupur Mittal
# @Email: nupurmittal5@gmail.com
# @Date: 2024-11-08
# @Last Modified by:   Asta Omarsdottir 
# @Last Modified time: 2024-11-13
# @Last Modified: Moved from Connection.py with minor changes
# @Description: Query data from Neo4j for Networkx Node-Link Diagram, Fish Delivery Network  
    
def fetch_delivery_data(start_date=None):
    with driver.session() as session:
        try:
            query = """
            MATCH p=(a:`Entity.Document.DeliveryReport`)-[r:`Event.Transaction`]->(c:`Entity.Commodity.Fish`)
            WHERE a.date >= $start_date OR $start_date IS NULL 
            RETURN a.date as delivery_date, a.qty_tons as quantity_delivered, c.name as fish_type
            """
            result = session.run(query, start_date=start_date)
            data = [record for record in result]
            # print("Fetched delivery data:", data)  # Add for testing output
            return data
        except Exception as e:
            print("Error fetching delivery data:", e)
            return []  # Return empty list in case of error
        
# @Author: Nupur Mittal
# @Email: nupurmittal5@gmail.com
# @Date: 2024-11-08
# @Last Modified by:   Asta Omarsdottir # minor changes, error handling and debugging
# @Last Modified time: 2024-11-13
# @Last Modified: Moved from dataframetable.py with minor changes 
# @Description: Get data from DeliveryReport to analyse fish quantity and seasonal trends 
        
def fetch_delivery_qty_data():
    with driver.session() as session:
        try:
            result = session.run("""
            MATCH (d:`Entity.Document.DeliveryReport`)
            RETURN d.date AS date, d.qty_tons AS qty_tons
            """)
            data = result.data()
            df = pd.DataFrame(data)
            
            # Debugging 
            #print("Fetched Data:\n", df)
            
            return df
        except Exception as e:
            print("Error fetching delivery qty data:", e)
            return []  # Return empty list in case of error

# @Author: Nupur Mittal
# @Email: nupurmittal5@gmail.com
# @Date: 2024-11-08
# @Last Modified by:   Asta Omarsdottir 
# @Last Modified time: 2024-11-13
# @Last Modified: Moved from matching vessel cargo.py with some changes
# @Description: Get data from DeliveryReport to analyse fish quantity and seasonal trends 

def fetch_vessel_cargo_data():
    with driver.session() as session:
        try:
            delivery_result = session.run("""
            MATCH (d:`Entity.Document.DeliveryReport`)
            RETURN d.date AS delivery_date, d.qty_tons AS qty_tons
            """)
            
            exit_result = session.run("""
            MATCH p=()-[e:`Event.TransportEvent.TransponderPing`]->()
            RETURN e.time AS exit_date, e.target AS vehicle_id
            """)
            
            deliveries = pd.DataFrame(delivery_result.data())
            exits = pd.DataFrame(exit_result.data())
            return deliveries, exits
        except Exception as e:
            print("Error fetching vessel cargo data:", e)
            return []  # Return empty list in case of error
        
# @Author: Nupur Mittal
# @Email: nupurmittal5@gmail.com
# @Date: 2024-11-08
# @Last Modified by:   Asta Omarsdottir 
# @Last Modified time: 2024-11-13
# @Last Modified: Moved from matching vessel cargo.py with some changes
# @Description: Preprocess data from fetch_vessel_cargo_data to analyse fish quantity and seasonal trends  
        
def normalize_and_cluster(matched_data):
    # Select features
    clustering_data = matched_data[['hour', 'qty_tons']]
    
    # Normalize data
    scaler = StandardScaler()
    scaled_data = scaler.fit_transform(clustering_data)
    
    # Apply KMeans clustering
    kmeans = KMeans(n_clusters=3)
    matched_data['cluster'] = kmeans.fit_predict(scaled_data)
    
    return matched_data
        
# @Author: Nupur Mittal
# @Email: nupurmittal5@gmail.com
# @Date: 2024-11-08
# @Last Modified by:   Asta Omarsdottir 
# @Last Modified time: 2024-11-13
# @Last Modified: Moved from matching vessel cargo.py with some changes
# @Description: Preprocess data from fetch_vessel_cargo_data to analyse fish quantity and seasonal trends  

def preprocess_vessel_cargo_data(threshold_hours=1):
    try:
    
        deliveries, exits = fetch_vessel_cargo_data()
        # Convert dates to datetime
        deliveries['delivery_date'] = pd.to_datetime(deliveries['delivery_date'], errors='coerce')
        exits['exit_date'] = pd.to_datetime(exits['exit_date'], errors='coerce')
        
        # Drop invalid rows
        deliveries.dropna(subset=['delivery_date'], inplace=True)
        exits.dropna(subset=['exit_date'], inplace=True)
        
        # Sort values for merging
        deliveries.sort_values('delivery_date', inplace=True)
        exits.sort_values('exit_date', inplace=True)
        
        # Perform the asof merge with tolerance
        threshold = pd.Timedelta(hours=threshold_hours)
        matched_data = pd.merge_asof(
            deliveries, 
            exits, 
            left_on='delivery_date', 
            right_on='exit_date', 
            tolerance=threshold, 
            direction='nearest'
        )
        
        # Drop unmatched rows and add hour column
        matched_data.dropna(inplace=True)
        matched_data['hour'] = matched_data['exit_date'].dt.hour
        matched_data = normalize_and_cluster(matched_data)
        
        return matched_data
    except Exception as e:
        print("Error preprosessing vessel cargo data:", e) # debug
        return []  # Return empty list in case of error
    
# @Author: Nupur Mittal
# @Email: nupurmittal5@gmail.com
# @Date: 2024-11-15
# @Last Modified by:   Asta Omarsdottir 
# @Last Modified time: 2024-11-13
# @Modified: Moved from network.py with minor changes
# @Description: Fetch data to analyse fish quantity and seasonal trends  

def fetch_temporal_data():
    query = """
    MATCH (a:`Entity.Document.DeliveryReport`)-[r:`Event.Transaction`]->(c:`Entity.Location.City`)
    RETURN a.date AS date, a.qty_tons AS qty, c.id AS city
    ORDER BY date
    """
    with driver.session() as session:
        try:
            results = session.run(query)
            # Convert to a list of dictionaries
            return [dict(record) for record in results]
        except Exception as e:
            # print("Error fetching temporal data:", e) # debug print
            return []  # Return empty list in case of error
        
# @Author: Nupur Mittal
# @Email: nupurmittal5@gmail.com
# @Date: 2024-11-15
# @Last Modified by:   Asta Omarsdottir 
# @Last Modified time: 2024-11-13
# @Last Modified: Moved from network.py with minor changes
# @Description: Prepares temporal data for analysing fish quantity and seasonal trends

def prepare_temporal_dataframe():
    try:
        temporal_data = fetch_temporal_data()
        temporal_df = pd.DataFrame(temporal_data)
        
        # debugging print unique cities in temporal_df
        #print("cities in temporal_df:", temporal_df['city'].unique())

        if 'date' in temporal_df.columns:
            temporal_df['date'] = pd.to_datetime(temporal_df['date'], errors='coerce')
            temporal_df.dropna(subset=['date'], inplace=True)
        else:
            raise ValueError("The 'date' column is missing in the fetched data.")

        return temporal_df
    except Exception as e:
        print("Error in prepare temporal dataframe:", e)
        return []  # Return empty list in case of error
    
# @Author: Asta Omarsdottir
# @Email: asta.omarsdottir@gmail.com
# @Date: 2024-12-01 09:56:32
# @Last Modified by:   undefined
# @Last Modified time: 2024-12-19 09:56:32
# @Description: Fetch data for Geospatial analysis in choropleth and scatter plot
 
def get_geo_data():
    try:
        # Load GeoJSON and nodes JSON
        with open(file_path_geojson, "r") as file:
            geojson_data = json.load(file)
        with open(file_path_nodesjson, "r") as file:
            oceanus_data = json.load(file)

        # Preparing geojson for merge with oceanus_data
        # Extract geometries and properties from GeoJSON
        geometries = []
        properties = []
        for feature in geojson_data["features"]:
            try:
                geom = shape(feature["geometry"])
                geometries.append(geom)
                properties.append(feature["properties"])
            except Exception as e:
                print(f"Error processing feature: {feature['properties'].get('Name', 'Unknown')}, {e}")

        geo_data = gpd.GeoDataFrame(properties, geometry=geometries)
        
        # Ensure required columns exist in geo_data
        if "Activities" not in geo_data.columns:
             geo_data["Activities"] = None
        if "fish_species_present" not in geo_data.columns:
             geo_data["fish_species_present"] = None
        
        # convert list of `Activities` and `fish_species_present` to string data
        for col in ["Activities", "fish_species_present"]:
            if col in geo_data.columns:
                geo_data[col] = geo_data[col].apply(
                    lambda x: ', '.join(x) if isinstance(x, list) else (x if x is not None else "")
                )
        
        # Preparing nodes:df for merge with geo_data  
        # Extract nodes into DataFrame
        nodes = oceanus_data.get("nodes", [])
        nodes_df = pd.DataFrame(nodes)
        
        # Check if nodes_df is DataFrame
        if not isinstance(nodes_df, pd.DataFrame):
            raise ValueError("nodes_df is not a DataFrame")
        
        # Ensure required columns exist in nodes_df
        if "Activities" not in nodes_df.columns:
                nodes_df["Activities"] = None
        if "fish_species_present" not in nodes_df.columns:
             nodes_df["fish_species_present"] = None

        # Process Activities and fish_species_present
        nodes_df["Activities"] = nodes_df["Activities"].fillna("").apply(
             lambda x: ', '.join(x) if isinstance(x, list) else x
        )
        nodes_df["fish_species_present"] = nodes_df["fish_species_present"].fillna("").apply(
             lambda x: ', '.join(x) if isinstance(x, list) else x
         )
        
        # Convert list to string in `nodes_df`
        for col in ["Activities", "fish_species_present"]:
            if col in nodes_df.columns:
                nodes_df[col] = nodes_df[col].apply(
                    lambda x: ', '.join(x) if isinstance(x, list) else (x if x is not None else "")
                )
        
        if 'Name' in nodes_df.columns and 'Name' in geo_data.columns:    
        # Merge geo_data and nodes_df
            merged_geo_data = nodes_df.merge(
                geo_data,
                on="Name",
                how="left"
            )
        else:
            raise ValueError("Column 'Name' missing in nodes_df or geo_data")
        
        # Use mapping to update id-column
        city_mapping = get_city_mapping()
        
        merged_geo_data["id"] = merged_geo_data.apply(
            lambda row: city_mapping.get(row["Name"], row["id"]) 
            if row["type_x"] == "Entity.Location.City" else row["id"],
            axis=1
        )
        return merged_geo_data
    except Exception as e:
        print("Error fetching GeoData:", e) #debug print
        return None
    
# @Author: Asta Omarsdottir
# @Email: asta.omarsdottir@gmail.com
# @Date: 2024-12-10 09:58:52
# @Last Modified by:   undefined
# @Last Modified time: 2024-12-19 09:58:52
# @Description: 
      
def fetch_delivery_intensity_data(start_date=None,end_date=None, city=None):
    query = """
        MATCH (a:`Entity.Document.DeliveryReport`)-[r:`Event.Transaction`]->(c:`Entity.Location.City`)
        WHERE r.date >= $start_date AND r.date <= $end_date
        AND ($city IS NULL OR c.city = $city)
        RETURN c.id AS city, a.date AS delivery_date, COUNT(r) AS transactions, 
        ORDER BY date
    """
    with driver.session() as session:
        try:
            result = session.run(query)
            transaction_events = []
            for record in result:
                transaction_events.append(record.data())
                #debug
                print(pd.DataFrame(transaction_events))
                return pd.DataFrame(transaction_events)
        except Exception as e:
            # print("Error fetching transaction data:", e) # debug print
            return []  # Return empty list in case of error
         
# @Author: Asta Omarsdottir
# @Email: asta.omarsdottir@gmail.com
# @Date: 2024-12-10
# @Last Modified by:   undefined
# @Last Modified time: 2024-12-19
# @Description: Fetch data for heatmap visualizing dwell time in locations over time

def get_transport_movements():
            query = """
            MATCH (start)-[r:`Event.TransportEvent.TransponderPing`]->(end)
            WHERE 
                (start:`Entity.Location.City` OR 
                start:`Entity.Location.Point` OR 
                start:`Entity.Location.Region`) AND 
                (end:`Entity.Vessel.FishingVessel` OR end:`Entity.Vessel.CargoVessel`)
            RETURN 
                start.id AS source_location, 
                start.Name AS source_location_name,
                end.id AS vessel_id, 
                end.Name AS vessel_name,
                labels(end) AS vessel_type,
                r.time AS start_time, 
                r.dwell AS dwell
            """
            with driver.session() as session:
                try:
                    result = session.run(query)
                    transport_events = [record.data() for record in result]
                    return pd.DataFrame(transport_events) if transport_events else pd.DataFrame()
                except Exception as e:
                    # Handle errors gracefully and return an empty DataFrame
                    print("Error fetching transport data:", e)
                    return pd.DataFrame()
                
# @Author: Asta Omarsdottir
# @Email: asta.omarsdottir@gmail.com
# @Date: 2024-12-10 09:58:52
# @Last Modified by:   undefined
# @Last Modified time: 2024-12-19 09:58:52
# @Description: Process data for heatmap visualizing dwell time in locations over time

def process_transport_movements(df):
    transport_movements = []
    if not df.empty:
        df['start_time'] = pd.to_datetime(df['start_time'], errors='coerce')

        # Convert 'dwell' to numeric
        df['dwell'] = pd.to_numeric(df['dwell'], errors='coerce')

        # Calculate end_time
        df['end_time'] = df['start_time'] + pd.to_timedelta(df['dwell'], unit='s')

        for _, row in df.iterrows():
            location_id = row['source_location']
            vessel_id = row['vessel_id']
            start_time = row['start_time']
            end_time = row['end_time']

            current_date = start_time
            while current_date.date() <= end_time.date():
                if current_date.date() == start_time.date():
                    if current_date.date() == end_time.date():
                        dwell = (end_time - start_time).total_seconds()
                    else:
                        dwell = (datetime.combine(current_date.date(), datetime.max.time()) - start_time).total_seconds()
                elif current_date.date() == end_time.date():
                    dwell = (end_time - datetime.combine(current_date.date(), datetime.min.time())).total_seconds()
                else:
                    dwell = 24 * 3600  # Full day in seconds

                transport_movements.append({
                    'date': current_date.strftime("%Y-%m-%d"),
                    'location_id': location_id,
                    'vessel_id': vessel_id,
                    'type': 'transport',
                    'dwell': dwell
                })
                current_date += timedelta(days=1)

    return pd.DataFrame(transport_movements)

# @Author: Asta Omarsdottir
# @Email: asta.omarsdottir@gmail.com
# @Date: 2024-12-26
# @Last Modified by:   undefined
# @Last Modified time: 2024-12-26
# @Description: Treemap to visualyze fish quantity by company and city

def get_treemap_data():
    # Dummy data (To do: replace with real data)
    data = {
        "city_of_arrival": ["City of Paackland", "	City of Himark", "City of Lomark", "City of Haacklee", "City of Port Grove", "City of South Paackland"],
        "vessel_company": ["Parks Ltd", "ScaniaSeafood Holdings Ltd. Liability Co", "SouthSeafood Express Corp", "House Group", "FlounderLeska Marine BV", "Adkins LLC"],
        "qty_tons": [100, 200, 300, 150, 250, 350]
    }
    combined_results_final = pd.DataFrame(data)

    # Create a cross product to include all combinations
    all_cities = combined_results_final["city_of_arrival"].unique()
    all_vessel_companies = combined_results_final["vessel_company"].unique()
    complete_data = pd.DataFrame(
        [(city, company) for city in all_cities for company in all_vessel_companies],
        columns=["city_of_arrival", "vessel_company"]
    )

    # Merge and fill missing values
    merged_data = pd.merge(complete_data, combined_results_final, on=["city_of_arrival", "vessel_company"], how="left")
    merged_data["qty_tons"] = merged_data["qty_tons"].fillna(0)

    # Summarize and normalize data
    treemap_data = (
        merged_data.groupby(["city_of_arrival", "vessel_company"], as_index=False)
        .agg(total_qty_tons=("qty_tons", "sum"))
    )
    
    # Remove data with total_qty_tons less or = 0
    treemap_data = treemap_data[treemap_data['total_qty_tons'] > 0]
    treemap_data["total_qty_tons"] = np.log1p(treemap_data["total_qty_tons"])
    
    #debug
    print("Treemap Data Type:", type(treemap_data))
    print("Treemap Data Content:", treemap_data)
    print("Treemap Data Columns:", treemap_data.columns)
    print("Is Treemap DataFrame Empty?", treemap_data.empty)

    return treemap_data


