import os
import json # used to get geo data
from neo4j import GraphDatabase
import networkx as nx
import dash
from dash import html, dcc
import dash_cytoscape as cyto
import pandas as pd
import geopandas as gpd
from dash.dependencies import Input, Output
import plotly.express as px
import plotly.graph_objects as go
from neo4j import GraphDatabase
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.ensemble import IsolationForest
import numpy as np
import dash_cytoscape as cyto
import logging 
from shapely.geometry import Point, Polygon, MultiPolygon, shape
from datetime import datetime, timedelta

# @Author: Asta Omarsdottir
# @Email: asta.omarsdottir@gmail.com
# @Date: 2024-11-08
# @Last Modified by:   undefined
# @Last Modified time: 2024-12-19
# @Description: Handles data fetching and processing for the backend

# ***************************************************************************************

# @Author: Asta Omarsdottir
# @Email: asta.omarsdottir@gmail.com
# @Date: 2024-11-08
# @Last Modified by:   undefined
# @Last Modified time: 2024-12-19
# @Description: Connection to Neo4j database, file paths and data fetching

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
# @Last Modified by:   Asta Omarsdottir
# @Last Modified time: 2024-01-05
# @Description: get vessels for dropdown filter
# 2024-01-05 Each dropdown dynamically updates based on selected values in other dropdowns. 

def get_vessels(company=None, city=None, port=None, region=None, species=None):
    filters = []
    if company:
        if isinstance(company, list):
            company_filter = ", ".join(f"'{c}'" for c in company)
            filters.append(f"n.company IN [{company_filter}]")
        else:
            filters.append(f"n.company = '{company}'")
    if city:
        filters.append(f"n.city = '{city}'")
    filter_query = " AND ".join(filters)
    if port:
        filters.append(f"n.port = '{port}'")
    filter_query = " AND ".join(filters)
    if region:
        filters.append(f"n.region = '{region}'")
    filter_query = " AND ".join(filters)
    if species:
        filters.append(f"n.species = '{species}'")
    filter_query = " AND ".join(filters)
    
    
    query = f"""
    MATCH (n)
    WHERE (n:`Entity.Vessel.CargoVessel` OR n:`Entity.Vessel.FishingVessel`)
    {f'AND {filter_query}' if filters else ''}
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
# @Last Modified by:   Asta Omarsdottir
# @Last Modified time: 2024-01-05
# @Description: get cities for dropdown filter
# 2024-01-05 Each dropdown dynamically updates based on selected values in other dropdowns.

def get_cities(company=None, vessel=None, port=None, region=None, species=None):
    filters = []
    if company:
        filters.append(f"n.company = '{company}'")
    if vessel:
        filters.append(f"n.vessel = '{vessel}'")
    filter_query = " AND ".join(filters)
    if port:
        filters.append(f"n.port = '{port}'")
    filter_query = " AND ".join(filters)
    if region:
        filters.append(f"n.region = '{region}'")
    filter_query = " AND ".join(filters)
    if species:
        filters.append(f"n.species = '{species}'")
    filter_query = " AND ".join(filters)
    
    query = f"""
    MATCH (n)
    WHERE n:`Entity.Location.City`
    {f'AND {filter_query}' if filters else ''}    
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
# @Last Modified by:
# @Last Modified time: 
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
# @Last Modified by:   Asta Omarsdottir
# @Last Modified time: 2024-01-05
# @Description: get ports for dropdown filter
# 2024-01-05 Each dropdown dynamically updates based on selected values in other dropdowns.

def get_points(company=None, city=None, vessel=None, region=None, species=None):
    filters = []
    if company:
        filters.append(f"n.company = '{company}'")
    if city:
        filters.append(f"n.city = '{city}'")
    filter_query = " AND ".join(filters)
    if vessel:
        filters.append(f"n.vessel = '{vessel}'")
    filter_query = " AND ".join(filters)
    if region:
        filters.append(f"n.region = '{region}'")
    filter_query = " AND ".join(filters)
    if species:
        filters.append(f"n.species = '{species}'")
    filter_query = " AND ".join(filters)
    
    query = f"""
    MATCH (n)
    WHERE n:`Entity.Location.Point` 
    {f'AND {filter_query}' if filters else ''}   
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
# @Last Modified by:   Asta Omarsdottir
# @Last Modified time: 2024-01-05
# @Description: get species for dropdown filter
# 2024-01-05 Each dropdown dynamically updates based on selected values in other dropdowns.

def get_species(company=None, city=None, port=None, region=None, vessel=None):
    filters = []
    if company:
        filters.append(f"n.company = '{company}'")
    if city:
        filters.append(f"n.city = '{city}'")
    filter_query = " AND ".join(filters)
    if port:
        filters.append(f"n.port = '{port}'")
    filter_query = " AND ".join(filters)
    if region:
        filters.append(f"n.region = '{region}'")
    filter_query = " AND ".join(filters)
    if vessel:
        filters.append(f"n.vessel = '{vessel}'")
    filter_query = " AND ".join(filters)
    
    query = f"""
    MATCH (n)
    WHERE n:`Entity.Commodity.Fish` 
    {f'AND {filter_query}' if filters else ''}   
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
# @Last Modified by:   Asta Omarsdottir
# @Last Modified time: 2024-01-05
# @Description: get regions for dropdown filter
# 2024-01-05 Each dropdown dynamically updates based on selected values in other dropdowns.
         
def get_regions(company=None, city=None, port=None, vessel=None, species=None):
    filters = []
    if company:
        filters.append(f"n.company = '{company}'")
    if city:
        filters.append(f"n.city = '{city}'")
    filter_query = " AND ".join(filters)
    if port:
        filters.append(f"n.port = '{port}'")
    filter_query = " AND ".join(filters)
    if vessel:
        filters.append(f"n.vessel = '{vessel}'")
    filter_query = " AND ".join(filters)
    if species:
        filters.append(f"n.species = '{species}'")
    filter_query = " AND ".join(filters)
    
    query = f"""
    MATCH (n)
    WHERE n:`Entity.Location.Region` 
    {f'AND {filter_query}' if filters else ''}   
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
# @Last Modified by:   Asta Omarsdottir
# @Last Modified time: 2024-01-05
# @Description: get companies for dropdown filter
# 2024-01-05 Each dropdown dynamically updates based on selected values in other dropdowns.
         
def get_companies(vessel=None, city=None, port=None, region=None, species=None):
    filters = []
    if vessel:
        if isinstance(vessel, list):
            vessel_filter = ", ".join(f"'{v}'" for v in vessel)
            filters.append(f"n.id IN [{vessel_filter}]")
        else:
            filters.append(f"n.id = '{vessel}'")
    filter_query = " AND ".join(filters)
    if city:
        filters.append(f"n.city = '{city}'")
    filter_query = " AND ".join(filters)
    if port:
        filters.append(f"n.port = '{port}'")
    filter_query = " AND ".join(filters)
    if region:
        filters.append(f"n.region = '{region}'")
    filter_query = " AND ".join(filters)
    if species:
        filters.append(f"n.species = '{species}'")
    filter_query = " AND ".join(filters)
    
    query = f"""
    MATCH (n)
    WHERE (n:`Entity.Vessel.CargoVessel` OR n:`Entity.Vessel.FishingVessel`)
    {f'AND {filter_query}' if filters else ''}
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
        
# @Author: Asta Omarsdottir
# @Email: asta.omarsdottir@gmail.com
# @Date: 2025-03-04
# @Last Modified by:   undefined
# @Last Modified time: 2025-03-04
# @Description: Fetches the data for the treemap visualization

def get_fish_distribution_data():
    with driver.session() as session:
        try:
            query = """
            MATCH (l:`Entity.Location.Region`)
            WITH l, 
                [f IN split(replace(replace(l.fish_species_present, "[", ""), "]", ""), ",") | trim(replace(f, "'", ""))] AS fish_list
            RETURN l.id AS location, l.kind AS type, fish_list AS fish_species_present
            """
            result = session.run(query)
            data = [record.data() for record in result]
            
            # Ensure fish_species_present is always a list
            for location in data:
                if isinstance(location["fish_species_present"], str):
                    location["fish_species_present"] = [
                        fish.strip().replace("'", "") 
                        for fish in location["fish_species_present"].strip("[]").split(",")
                    ]
            
            return data
        except Exception as e:
            print("Error fetching fish distribution data:", e)
            return []
    
# @Author: Asta Omarsdottir
# @Email: asta.omarsdottir@gmail.com
# @Date: 2025-01-18
# @Last Modified by:   undefined
# @Last Modified time: 2025-01-18
# @Description: Fetch fish deliveries from the database for Network-Link graph (pyvis)

def get_fish_deliveries(start_date, end_date):

    # Ensure date-only format for start_date
    if start_date:
        start_date = datetime.strptime(start_date.split(" ")[0], '%Y-%m-%d').strftime('%Y-%m-%d')
    if end_date:
        # Add one day to make the range inclusive for the upper bound
        end_date = datetime.strptime(end_date.split(" ")[0], '%Y-%m-%d') + timedelta(days=1)
        end_date = end_date.strftime('%Y-%m-%d')
   
    with driver.session() as session:
        try:
            query = """
            MATCH 
            (cargo:`Entity.Document.DeliveryReport`)-[:`Event.Transaction`]->(targetEntity)
            WHERE 
            ((cargo.date >= $start_date OR $start_date IS NULL) AND (cargo.date < $end_date OR $end_date IS NULL)) AND
            (targetEntity:`Entity.Commodity.Fish` OR targetEntity:`Entity.Location.City`)
            WITH 
            cargo, 
            cargo.id AS deliveryreport_name,
            COLLECT(CASE WHEN targetEntity:`Entity.Location.City` THEN targetEntity.id ELSE null END)[0] AS city_of_arrival,
            COLLECT(CASE WHEN targetEntity:`Entity.Commodity.Fish` THEN targetEntity.id ELSE null END)[0] AS fish_name,
            cargo.date AS date_of_arrival,
            cargo.qty_tons AS qty_tons
            OPTIONAL MATCH 
            (vessel)-[harbor:`Event.HarborReport`]->(city:`Entity.Location.City`)
            WHERE
            (vessel:`Entity.Vessel.FishingVessel` OR vessel:`Entity.Vessel.CargoVessel`) AND
            harbor.target = city_of_arrival AND
            (date(cargo.date) = date(harbor.date) OR date(cargo.date) + duration('P1D') = date(harbor.date))
            WITH
            cargo, deliveryreport_name, date_of_arrival, city_of_arrival, fish_name, qty_tons,
            COLLECT(harbor.source) AS harbor_vessels
            OPTIONAL MATCH 
                (city:`Entity.Location.City`)-[ping:`Event.TransportEvent.TransponderPing`]->(vessel)
            WHERE
                (vessel:`Entity.Vessel.FishingVessel` OR vessel:`Entity.Vessel.CargoVessel`) AND
                ping.source = city_of_arrival AND
                (date(cargo.date) = date(substring(ping.time, 0, 10)))
            WITH
            cargo, deliveryreport_name, date_of_arrival, city_of_arrival, fish_name, qty_tons, harbor_vessels,
            COLLECT(ping.target) AS ping_vessels
            RETURN 
            deliveryreport_name, date_of_arrival, city_of_arrival, fish_name, qty_tons,
            harbor_vessels, ping_vessels
        
        """
            result = session.run(query, start_date=start_date, end_date=end_date)
            data = [record.data() for record in result]
            # print("Fetched fish delivery data:", data)  # Add for testing output
            return data
        except Exception as e:
            print("Error fetching delivery data:", e)
            return []  # Return empty list in case of error
        
# @Author: Asta Omarsdottir
# @Email: asta.omarsdottir@gmail.com
# @Date: 2025-02-25
# @Last Modified by:   undefined
# @Last Modified time: 2025-02-25
# @Description: Ensure that the item is a list

def ensure_list(item):
    # If it's already a list, return it; otherwise, wrap it in a list.
    return item if isinstance(item, list) else [item]
        
# @Author: Asta Omarsdottir
# @Email: asta.omarsdottir@gmail.com
# @Date: 2025-01-18
# @Last Modified by:   undefined
# @Last Modified time: 2025-01-18
# @Description: Process fish deliveries from the database for Network-Link graph (pyvis)

def process_fish_deliveries(raw_data):
    processed_data = []
    for record in raw_data:
        qty_tons = record.get("qty_tons", "0")  # Default to "0" if missing
        
        # Normalize the qty_tons value
        try:
            # Replace comma with a dot for decimal parsing
            qty_tons = qty_tons.replace(",", ".") if isinstance(qty_tons, str) else qty_tons
            # Convert to float
            qty_tons = float(qty_tons)
        except (ValueError, AttributeError):
            # Handle any unexpected format
            qty_tons = 0.0
            
        # Ensure no negative weights
        if qty_tons < 0:
            print(f"Warning: Negative qty_tons value encountered ({qty_tons}). Setting to 0.")
            qty_tons = 0.0
            
        # Use ensure_list to avoid double-wrapping
        harbor_vessels = ensure_list(record.get("harbor_vessels", "Unknown"))
        ping_vessels = ensure_list(record.get("ping_vessels", "Unknown"))
        
        processed_record = {
            "delivery_report_name": record.get("deliveryreport_name", "Unknown"),
            "date_of_arrival": record.get("date_of_arrival"),
            "city_of_arrival": record.get("city_of_arrival", "Unknown"),
            "fish_name": record.get("fish_name", "Unknown"),
            "quantity_tons": qty_tons, # Normalized value
            
            # Wrap these in lists for multiple values later on.
            "harbor_vessels": harbor_vessels,
            "ping_vessels": ping_vessels,
        }
        # Ensure date format consistency if needed
        if processed_record["date_of_arrival"]:
            processed_record["date_of_arrival"] = datetime.strptime(
                processed_record["date_of_arrival"], "%Y-%m-%d"
            ).strftime("%Y-%m-%d")
        processed_data.append(processed_record)
        
        #print("processed fish delivery data:", processed_data)  # Add for testing output
    return processed_data
        
# @Author: Nupur Mittal
# @Email: nupurmittal5@gmail.com
# @Date: 2024-11-08
# @Last Modified by:   Asta Omarsdottir # minor changes, error handling and debugging
# @Last Modified time: 2024-11-13
# @Last Modified: Moved from dataframetable.py with minor changes 
# @Last Modified by:   Asta Omarsdottir
# @Last Modified time: 2025-03-01
# @Last Modified: Added dates
# @Description: Get data from DeliveryReport to analyse fish quantity and seasonal trends in temporal and seasonal graph
        
def fetch_delivery_qty_data(start_date, end_date):

    # Ensure date-only format for start_date
    if start_date:
        start_date = datetime.strptime(start_date.split(" ")[0], '%Y-%m-%d').strftime('%Y-%m-%d')
    if end_date:
        # Add one day to make the range inclusive for the upper bound
        end_date = datetime.strptime(end_date.split(" ")[0], '%Y-%m-%d') + timedelta(days=1)
        end_date = end_date.strftime('%Y-%m-%d')

    with driver.session() as session:
        try:
            query = """
            MATCH (d:`Entity.Document.DeliveryReport`)
            WHERE (d.date >= $start_date OR $start_date IS NULL)
            AND (d.date < $end_date OR $end_date IS NULL)
            RETURN d.date AS date, d.qty_tons AS qty_tons
            """
            result = session.run(query, start_date=start_date, end_date=end_date)
            data = [record.data() for record in result]
            
            return data
        except Exception as e:
            print("Error fetching delivery qty data:", e)
            return []  # Return empty list in case of error
        
# @Author: Nupur Mittal
# @Email: nupurmittal5@gmail.com
# @Date: 2024-11-08
# @Last Modified by:   Asta Omarsdottir 
# @Last Modified time: 2024-11-13
# @Last Modified: Moved from matching vessel cargo.py with some changes
# @Description: Get data from DeliveryReport and TransponderPing to analyse vessel, cargo data in for cluster-plot graph

def fetch_vessel_cargo_data(start_date, end_date):
         # Ensure date-only format for start_date
    if start_date:
        start_date = datetime.strptime(start_date.split(" ")[0], '%Y-%m-%d').strftime('%Y-%m-%d')
    if end_date:
        # Add one day to make the range inclusive for the upper bound
        end_date = datetime.strptime(end_date.split(" ")[0], '%Y-%m-%d') + timedelta(days=1)
        end_date = end_date.strftime('%Y-%m-%d')
    
    with driver.session() as session:
        try:
            delivery_result = session.run("""
            MATCH (d:`Entity.Document.DeliveryReport`)
            WHERE d.date >= $start_date AND d.date < $end_date
            RETURN d.date AS delivery_date, d.qty_tons AS qty_tons
            """, start_date=start_date, end_date=end_date)
            
            exit_result = session.run("""
            MATCH p=()-[e:`Event.TransportEvent.TransponderPing`]->()
            WHERE e.time >= $start_date AND e.time < $end_date
            RETURN e.time AS exit_date, e.target AS vessel_id
            """, start_date=start_date, end_date=end_date)
            
            deliveries = pd.DataFrame(delivery_result.data())
            exits = pd.DataFrame(exit_result.data())
            # print("Fetched vessel cargo data:", deliveries, exits)  # Debug
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
# @Description: Call from Preprocess_fetch_vessel_cargo_data to normalize and cluster data for analysis 
        
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

def preprocess_vessel_cargo_data(deliveries, exits, threshold_hours=24):
    try:
    
        # deliveries, exits = fetch_vessel_cargo_data()
        # Convert dates to datetime
        deliveries['delivery_date'] = pd.to_datetime(deliveries['delivery_date'], errors='coerce')
        exits['exit_date'] = pd.to_datetime(exits['exit_date'], errors='coerce')
        
        # Drop invalid rows
        deliveries = deliveries.dropna(subset=['delivery_date'])
        exits = exits.dropna(subset=['exit_date'])
        
        # Sort values for merging
        deliveries = deliveries.sort_values('delivery_date')
        exits = exits.sort_values('exit_date')
        
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
        
        # Drop unmatched rows and add hour column if needed
        matched_data = matched_data.dropna()
        matched_data['hour'] = matched_data['exit_date'].dt.hour if 'exit_date' in matched_data else None
       
        # Convert exit_date (and other datetimes) to strings for JSON serialization
        matched_data['exit_date'] = matched_data['exit_date'].dt.strftime('%Y-%m-%dT%H:%M:%S')
        matched_data['delivery_date'] = matched_data['delivery_date'].dt.strftime('%Y-%m-%dT%H:%M:%S')
        
        matched_data = normalize_and_cluster(matched_data)
        
        return matched_data
    except Exception as e:
        print("Error preprosessing vessel cargo data:", e)
        return []  # Return empty list in case of error
    
        
# @Author: Nupur Mittal
# @Email: nupurmittal5@gmail.com
# @Date: 2024-11-15
# @Last Modified by:   Asta Omarsdottir 
# @Last Modified time: 2024-11-13
# @Last Modified: Moved from network.py with minor changes
# @Last Modified by:   Asta Omarsdottir 
# @Last Modified time: 2025-03-02
# @Last Modified: prepares the temporal data by combining the delivery_qty_data and vessel_count_data
# @Description: Prepares temporal data for analysing fish quantity and seasonal trends

def prepare_temporal_dataframe(delivery_qty_data, vessel_count_data):
    try:
        # Convert delivery_qty_data and vessel_count_data to DataFrames
        delivery_df = pd.DataFrame(delivery_qty_data)
        vessel_df = pd.DataFrame(vessel_count_data)

        # Convert 'date' in delivery data
        if 'date' in delivery_df.columns:
            delivery_df['date'] = pd.to_datetime(delivery_df['date'], format="mixed", errors="coerce")
            delivery_df = delivery_df.dropna(subset=['date'])
            
        # Ensure 'qty_tons' exists in delivery_df and handle it
        if 'qty_tons' in delivery_df.columns:
            # Normalize qty_tons (check and process each row)
            for index, row in delivery_df.iterrows():
                qty_tons = row['qty_tons']
                
                # Handle missing or incorrect 'qty_tons'
                if pd.isna(qty_tons):  # If missing, set to 0
                    qty_tons = 0.0
                
                try:
                    # If it's a string, replace comma with a dot for decimal parsing
                    if isinstance(qty_tons, str):
                        qty_tons = qty_tons.replace(",", ".")
                    
                    # Convert to float
                    qty_tons = float(qty_tons)
                except (ValueError, AttributeError):
                    # Handle any unexpected format, set to 0
                    qty_tons = 0.0
                    
                # Ensure no negative values
                if qty_tons < 0:
                    print(f"Warning: Negative qty_tons value encountered ({qty_tons}). Setting to 0.")
                    qty_tons = 0.0

                # Update the DataFrame with the processed qty_tons value
                delivery_df.at[index, 'qty_tons'] = qty_tons
            
        # Convert 'date/timestamp' in vessel data
        if 'date' in vessel_df.columns:
            vessel_df['date'] = pd.to_datetime(vessel_df['date'], format="mixed", errors="coerce")
            vessel_df = vessel_df.dropna(subset=['date'])
            
         # Drop rows with missing values in the 'num_vessels' column
        vessel_df = vessel_df.dropna(subset=['num_vessels'])
        
        # Merge the two DataFrames on 'date'
        temporal_df = pd.merge(delivery_df, vessel_df, on='date', how='outer')
        
       # Opt into future behavior (only needs to be set once per session)
        pd.set_option('future.no_silent_downcasting', True)
        
        # Fill missing values if necessary
        temporal_df = temporal_df.ffill()
        # Infer proper types for object dtype columns
        temporal_df = temporal_df.infer_objects(copy=False)
        
        # Sort the dataframe by date
        temporal_df = temporal_df.sort_values(by='date')
        
        # Set the 'date' column as the index
        temporal_df = temporal_df.set_index('date')
        
        # Reset index before any operation that accesses 'date' column
        temporal_df = temporal_df.reset_index()
        
        return temporal_df
    
    except Exception as e:
        print("Error in prepare temporal dataframe:", e)
        return pd.DataFrame()  # Return empty dataframe in case of error
    
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
        print("Error fetching GeoData:", e)
        return None
         
# @Author: Asta Omarsdottir
# @Email: asta.omarsdottir@gmail.com
# @Date: 2024-12-10
# @Last Modified by:   undefined
# @Last Modified time: 2024-12-19
# @Description: Fetch data for heatmap visualizing dwell time in locations over time

def get_transport_movements(start_date, end_date):
     # Ensure date-only format for start_date
    if start_date:
        start_date = datetime.strptime(start_date.split(" ")[0], '%Y-%m-%d').strftime('%Y-%m-%d')
    if end_date:
        # Add one day to make the range inclusive for the upper bound
        end_date = datetime.strptime(end_date.split(" ")[0], '%Y-%m-%d') + timedelta(days=1)
        end_date = end_date.strftime('%Y-%m-%d')
    
    query = """
    MATCH (start)-[r:`Event.TransportEvent.TransponderPing`]->(end)
    WHERE 
        ((r.time >= $start_date OR $start_date IS NULL) AND (r.time < $end_date OR $end_date IS NULL))
        AND (start:`Entity.Location.City` OR 
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
            result = session.run(query, start_date=start_date, end_date=end_date)
            transport_events = [record.data() for record in result]
            df = pd.DataFrame(transport_events) if transport_events else pd.DataFrame()
            return df
        except Exception as e:
            # Handle errors gracefully and return an empty DataFrame
            print("Error fetching transport data:", e)
            return pd.DataFrame()
                
# @Author: Asta Omarsdottir
# @Email: asta.omarsdottir@gmail.com
# @Date: 2024-12-10
# @Last Modified by:   undefined
# @Last Modified time: 2024-12-19
# @Last Modified time: 2025-02-28
# @Description: Process data for heatmap visualizing dwell time per vessel at specific location at selected calendar_date intervall.

def process_transport_movements(df):
    transport_movements = []
    if not df.empty:
        df['start_time'] = pd.to_datetime(df['start_time'], errors='coerce')
        
        # Convert 'dwell' to numeric
        df['dwell'] = pd.to_numeric(df['dwell'], errors='coerce')
        
        # Calculate end_time
        df['end_time'] = df['start_time'] + pd.to_timedelta(df['dwell'], unit='s')

        for _, row in df.iterrows():
            if pd.isna(row['start_time']) or pd.isna(row['end_time']):
                continue
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
# @Date: 2025-03-01
# @Last Modified by:   undefined
# @Last Modified time: 2025-03-01
# @Description: Fetch vessel data for temporal and seasonal graph

def get_vessel_counts(start_date, end_date):
    # Ensure date-only format for start_date
    if start_date:
        start_date = datetime.strptime(start_date.split(" ")[0], '%Y-%m-%d').strftime('%Y-%m-%d')
    if end_date:
        # Add one day to make the range inclusive for the upper bound
        end_date = datetime.strptime(end_date.split(" ")[0], '%Y-%m-%d') + timedelta(days=1)
        end_date = end_date.strftime('%Y-%m-%d')
        
    query = """
    MATCH (start)-[r:`Event.TransportEvent.TransponderPing`]->(end)
    WHERE 
        ((r.time >= $start_date OR $start_date IS NULL) AND (r.time < $end_date OR $end_date IS NULL))
        AND (start:`Entity.Location.City` OR 
        start:`Entity.Location.Point` OR 
        start:`Entity.Location.Region`) AND 
        (end:`Entity.Vessel.FishingVessel` OR end:`Entity.Vessel.CargoVessel`)
    RETURN 
        r.time AS date,
        COUNT(DISTINCT end) AS num_vessels
    """
    with driver.session() as session:
        try:
            result = session.run(query, start_date=start_date, end_date=end_date)
            vessel_counts = [record.data() for record in result]
            df = pd.DataFrame(vessel_counts) if vessel_counts else pd.DataFrame()
            return df
        except Exception as e:
            print("Error fetching vessel count data:", e)
            return pd.DataFrame()
                
# @Author: Asta Omarsdottir
# @Email: asta.omarsdottir@gmail.com
# @Date: 2025-03-02
# @Last Modified by:   undefined
# @Last Modified time: 2025-03-02
# @Description: detect anomalies for temporal and seasonal graph
     
def detect_anomalies(temporal_df):
    try:
       # Ensure numerical columns
        temporal_df['qty_tons'] = pd.to_numeric(temporal_df['qty_tons'], errors='coerce')
        temporal_df['num_vessels'] = pd.to_numeric(temporal_df['num_vessels'], errors='coerce')

        # Rolling mean & standard deviation for qty_tons
        temporal_df['rolling_mean_qty'] = temporal_df['qty_tons'].rolling(window=7, min_periods=1).mean()
        temporal_df['rolling_std_qty'] = temporal_df['qty_tons'].rolling(window=7, min_periods=1).std()

        # Rolling mean & standard deviation for num_vessels
        temporal_df['rolling_mean_vessels'] = temporal_df['num_vessels'].rolling(window=7, min_periods=1).mean()
        temporal_df['rolling_std_vessels'] = temporal_df['num_vessels'].rolling(window=7, min_periods=1).std()

        # Z-score calculation for both metrics
        temporal_df['z_score_qty'] = (temporal_df['qty_tons'] - temporal_df['rolling_mean_qty']) / temporal_df['rolling_std_qty']
        temporal_df['z_score_vessels'] = (temporal_df['num_vessels'] - temporal_df['rolling_mean_vessels']) / temporal_df['rolling_std_vessels']

        # Detect anomalies: If either Z-score is above threshold (e.g., 2)
        temporal_df['anomaly'] = temporal_df.apply(
            lambda row: 'Anomaly' if abs(row['z_score_qty']) > 2 or abs(row['z_score_vessels']) > 2 else 'Normal',
            axis=1
        )     
        
        return temporal_df
    
    except Exception as e:
        print("Error in anomaly detection:", e)
        return temporal_df  # Return original dataframe in case of error

# @Author: Asta Omarsdottir
# @Email: asta.omarsdottir@gmail.com
# @Date: 2025-03-02
# @Last Modified by:   undefined
# @Last Modified time: 2025-03-02
# @Description: Detect fish delivery anomalies using Isolation Forest

def detect_fish_delivery_anomalies(store_data):
    
        # Ensure store_data is parsed as a dictionary
        if isinstance(store_data, str):
            try:
                store_data = json.loads(store_data)
            except json.JSONDecodeError:
                print("Error: Failed to decode JSON data!")
                return "<h3 style='color:white;'>Error: Invalid Data</h3>"

        # Extract fish delivery data
        fish_delivery_data = store_data.get("fish_deliveries", [])
        
        df = pd.DataFrame(fish_delivery_data)
    
        # Convert date_of_arrival to datetime (without time)
        df["date_of_arrival"] = pd.to_datetime(df["date_of_arrival"], format="%Y-%m-%d", errors="coerce")
       
        # Remove rows where date_of_arrival is NaT
        df = df.dropna(subset=["date_of_arrival"])

        # Label encode categorical variables (city and fish type)
        le_city = LabelEncoder()
        le_fish = LabelEncoder()
        df["city_encoded"] = le_city.fit_transform(df["city_of_arrival"])
        df["fish_encoded"] = le_fish.fit_transform(df["fish_name"])

        # Replace missing vessel data with 0
        df["harbor_vessels"] = df["harbor_vessels"].fillna(0)
        df["ping_vessels"] = df["ping_vessels"].fillna(0)

        # Normalize numerical features
        scaler = StandardScaler()

        # Convert vessel lists to counts
        df["harbor_vessels_count"] = df["harbor_vessels"].apply(lambda x: len(x) if isinstance(x, list) else 0)
        df["ping_vessels_count"] = df["ping_vessels"].apply(lambda x: len(x) if isinstance(x, list) else 0)

        # Select numerical features
        numeric_cols = ["quantity_tons", "harbor_vessels_count", "ping_vessels_count"]
        df[numeric_cols] = scaler.fit_transform(df[numeric_cols])

        # Apply Isolation Forest
        iso_forest = IsolationForest(contamination=0.05, random_state=42)
        df["anomaly"] = iso_forest.fit_predict(df[["quantity_tons", "harbor_vessels_count", "ping_vessels_count"]])

        # Convert anomaly labels (-1 = anomaly, 1 = normal) to binary (1 = anomaly, 0 = normal)
        df["anomaly"] = df["anomaly"].map({1: 0, -1: 1})

        return df

        # Usage
        anomalies_df = detect_fish_delivery_anomalies(processed_fish_data)
        

# @Author: Asta Omarsdottir
# @Email: asta.omarsdottir@gmail.com
# @Date: 2025-02-27
# @Last Modified by:   undefined
# @Last Modified time: 2025-02-27
# @Description: cluster deliveries based on timing and location using K-Means

def apply_kmeans_clustering(fish_delivery_data, num_clusters=5):
    """Clusters deliveries based on timing & location using K-Means."""

    # Create unique city mapping
    unique_cities = list(set(record["city_of_arrival"] for record in fish_delivery_data))
    city_map = {city: i for i, city in enumerate(unique_cities)}

    # Extract features
    delivery_features = []
    delivery_ids = []

    for record in fish_delivery_data:
        delivery_ids.append(record["delivery_report_name"])
        
        try:
            timestamp = int(datetime.strptime(record["date_of_arrival"], "%Y-%m-%d").timestamp())
        except ValueError:
            timestamp = 0  # Default to 0 if the date is missing or invalid
            
        # Convert city to a unique numeric ID
        location_id = city_map.get(record["city_of_arrival"], -1)  # Default to -1 if city is missing

        delivery_features.append([timestamp, location_id])

    # Convert to NumPy array and handle NaN values
    delivery_features = np.array(delivery_features, dtype=np.float64)
    delivery_features = np.nan_to_num(delivery_features)  # Replace NaN with 0

    print(delivery_features[:10])  # Check the first 10 feature rows

    # Apply K-Means
    kmeans = KMeans(n_clusters=num_clusters, random_state=42, n_init=10)
    clusters = kmeans.fit_predict(delivery_features)

    # Assign clusters
    for i, record in enumerate(fish_delivery_data):
        record["cluster"] = f"Cluster {clusters[i]}"

    return fish_delivery_data