import json
import networkx as nx
import pandas as pd
from neo4j import GraphDatabase
import dash
from dash import dcc, html
from dash.dependencies import Input, Output
import plotly.express as px
import plotly.graph_objects as go
from statsmodels.tsa.seasonal import seasonal_decompose

# Step 1: Connect to local db and investigate whats in it - Extract
uri = "bolt://localhost:7687"
username = "neo4j"
password = "asdf1234"

try:
    driver = GraphDatabase.driver(uri, auth=(username, password))
except Exception as e:
    print(f"Anslutning misslyckades: {e}")

# Get all nodes and print out types and number of nodes of each type   
def fetch_node_types():
    query = """
    MATCH (n)
    WHERE n.type IS NOT NULL
    RETURN n.type AS node_type, count(*) AS count
    ORDER BY count DESC
    """
    with driver.session() as session:
        results = session.run(query)
        for record in results:
            print(f"Type: {record['node_type']}, Count: {record['count']}")
            
# Get all links and print out types and number of each type
def fetch_link_types():
    query = """
     MATCH ()-[r]->()
    WHERE r.type IS NOT NULL
    RETURN r.type AS link_type, count(*) AS count
    ORDER BY count DESC
    """
    with driver.session() as session:
        results = session.run(query)
        for record in results:
            print(f"Type: {record['link_type']}, Count: {record['count']}")
            
# Get node type DeliveryReport         
def fetch_delivery_reports():
    query = """
    MATCH (n:Entity.Document.DeliveryReport)
    WHERE n.type = "Entity.Document.DeliveryReport"
    RETURN n
    """
    with driver.session() as session:
        results = session.run(query)
        # for record in results:
        #     print(record['n'])  # Skriver ut noderna
        DeliveryData = results.data()
        return pd.DataFrame(DeliveryData)

# def decompose_time_series(data):
#     data['date'] = pd.to_datetime(data['date'])
#     data.set_index('date', inplace=True)
#     data = data.resample('D').sum()  # Daily resampling to ensure continuous time series
    
#     # Decompose the time series
#     decomposition = seasonal_decompose(data['qty_tons'], model='additive', period=30)
#     return decomposition

           
# functions call
fetch_node_types()
fetch_link_types()
# fetch_delivery_reports()



   
# # JSON-data to pandas DataFrame (flatten nested json)
# df_nodes = pd.json_normalize(driver['nodes'])

# # Count unique node types and their occurances
# node_type_counts = df_nodes['type'].value_counts()

# # List unique node types and their counts 
# print(f"Number of unique node types: {len(node_type_counts)}") 
# print("Unique node types and their counts:") 
# for node_type, count in node_type_counts.items(): 
#     print(f"{node_type}: {count}")

# Total number of nodes: 5637
# Total number of edges: 271643
# Number of unique node types: 12
# Unique node types and their counts:
# Entity.Document.DeliveryReport: 5307
# Entity.Vessel.FishingVessel: 178
# Entity.Vessel.CargoVessel: 100
# Entity.Location.Point: 12
# Entity.Commodity.Fish: 10
# Entity.Location.City: 6
# Entity.Vessel.Tour: 6
# Entity.Location.Region: 6
# Entity.Vessel.Other: 5
# Entity.Vessel.Ferry.Passenger: 3
# Entity.Vessel.Ferry.Cargo: 2
# Entity.Vessel.Research: 2

# JSON-data to pandas DataFrame  (flatten nested json)
# df_links = pd.json_normalize(data['links'])

# # Count unique link types and their occurances
# link_type_counts = df_links['type'].value_counts()

# # List unique link types and their counts 
# print(f"Number of unique link types: {len(link_type_counts)}") 
# print("Unique link types and their counts:") 
# for link_type, count in link_type_counts.items(): 
#     print(f"{link_type}: {count}")

# Number of unique link types: 3
# Unique link types and their counts:
# Event.TransportEvent.TransponderPing: 258542
# Event.Transaction: 10614
# Event.HarborReport: 2487

    #   {
    #      "type": "Event.TransportEvent.TransponderPing",
    #      "time": "2035-09-16T04:06:48.185987",
    #      "dwell": 115074.790577,
    #      "_last_edited_by": "Olokun Daramola",
    #      "_date_added": "2035-09-16T00:59:46.300100",
    #      "_last_edited_date": "2035-09-16T00:59:46.300100",
    #      "_raw_source": "Oceanus Vessel Locator System",
    #      "_algorithm": "OVLS-Catch&Hook",
    #      "source": "City of Haacklee",
    #      "target": "perchplundererbc0",
    #      "key": 0
    #   },

    #   {
    #      "date": "2035-11-03",
    #      "type": "Event.Transaction",
    #      "_last_edited_by": "Junior Shurdlu",
    #      "_date_added": "2035-11-04",
    #      "_last_edited_date": "2035-11-06",
    #      "_raw_source": "Oceanus Centralized Export/Import Archive and Notatification Service (OCEANS)",
    #      "_algorithm": "CatchMate ('arrrr' edition)",
    #      "source": "cargo_2035_2394778c",
    #      "target": "gadusnspecificatae4ba",
    #      "key": 0
    #   },
    
    #       {
    #      "date": "2035-09-14",
    #      "type": "Event.HarborReport",
    #      "data_author": "Portmaster of Haacklee",
    #      "_raw_source": "Haacklee harbor reports",
    #      "_algorithm": "HarborReportMaster 3.11",
    #      "_date_added": "2035-09-21",
    #      "_last_edited_date": "2035-09-28",
    #      "_last_edited_by": "Junior Shurdlu",
    #      "aphorism": "The sea-shore is a sort of neutral ground, a most advantageous point from which to contemplate the world.",
    #      "holiday_greeting": "What are you doing for Saw Appreciation Day this year?",
    #      "wisdom": "Boats, like whiskey, are all good.",
    #      "saying of the sea": "An island is a world apart.",
    #      "source": "wavewranglerc2d",
    #      "target": "City of Haacklee",
    #      "key": 0
    #   },
    
# Step 2 Cleaning data
# df_nodes - dataframe with nodes already normalized
# Drop any rows with missing 'id' or 'type' 
# df_nodes = df_nodes.dropna(subset=['id', 'type'])
# print("Unique node types and their counts after cleaning missing rows:") 
# for node_type, count in node_type_counts.items(): 
#     print(f"{node_type}: {count}")
    
# # Convert date strings to datetime objects for easier manipulation
# df_nodes['details.time'] = pd.to_datetime(df_nodes['details.time'], errors='coerce')
# df_nodes['details.date'] = pd.to_datetime(df_nodes['details.date'], errors='coerce')

# # Fill missing values in specific columns if needed
# df_nodes['name'] = df_nodes['name'].fillna('Unknown')

# # Remove duplicates based on 'id'
# df_nodes = df_nodes.drop_duplicates(subset=['id'])
# print("Unique node types and their counts after removing duplicates:") 
# for node_type, count in node_type_counts.items(): 
#     print(f"{node_type}: {count}")


# df_links - dataframe with links already normalized



# # Step 2 preprocessing data

#     # Function to get deliveryReport
#     def fetch_delivery_report(data):
#         delivery_report = []
#         nodes = data.get("nodes", [])  # try to get "nodes" from data
#         print(f"Nodes extracted: {len(nodes)}")  # Show number of nodes extracted (5637)
#         for item in nodes:
#             if item.get("type") == "Entity.Document.DeliveryReport":
#             # print(f"Processing Delivery Report: {item}")
#                 for transaction in item.get("relations", []):
#                     print(f"Processing relation: {transaction}")
#                     if transaction.get("type") == "Event.Transaction":
#                         target_id = transaction.get("target")
#                         target_node = next((x for x in nodes if x.get("id") == target_id), None)
#                         print(f"Target Node: {target_node}")
#                     if target_node and target_node.get("type") == "Entity.Commodity.Fish":
#                         delivery_report.append({
#                             "delivery_date": item.get("properties", {}).get("date"),
#                             "quantity_delivered": item.get("properties", {}).get("qty_tons"),
#                             "fish_type": target_node.get("properties", {}).get("name")
#                         })
#     # print(f"Delivery data extracted: {len(delivery_data)} records")  # Antal hittade poster
#     return delivery_report

# # Kontrollera leveransdata
# print("Delivery Data:", data)

# close connection
driver.close()


