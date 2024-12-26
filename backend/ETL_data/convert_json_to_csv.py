# Create CSV files from json file, and import to neo4j using ne4j-admin
# neo4j-admin database import full neo4j --nodes=import/nodes.csv --relationships=import/ relationships.csv --overwrite-destination

import json
import pandas as pd

# Load JSON-file
with open(r'C:\RepositoryData\mc2.json', "r") as file:
    data = json.load(file)

# Extract nodes
nodes = pd.DataFrame(data["nodes"])

# Add :LABEL column if not existing
if ':LABEL' not in nodes.columns:
    nodes[':LABEL'] = nodes['type']  # Use 'type' column as :LABEL

# Add :ID from id-column (if not already existing)
if ':ID' not in nodes.columns:
    nodes[':ID'] = nodes['id']  # :ID to id-column

# Prepare columns in correct order
nodes = nodes[[":ID", ":LABEL"] + [col for col in nodes.columns if col not in [":ID", ":LABEL"]]]

# print out CSV
nodes.to_csv("nodes.csv", index=False)

# Extract relationes
links = pd.DataFrame(data["links"])

# Add :TYPE column
if ':TYPE' not in links.columns:
    links[':TYPE'] = links['type']  # Use 'type' column as :TYPE

# Create :START_ID och :END_ID (if not already existing)
links[':START_ID'] = links['source']
links[':END_ID'] = links['target']

# Prepare columns in correct order
links = links[[":START_ID", ":END_ID", ":TYPE"] + [col for col in links.columns if col not in [":START_ID", ":END_ID", ":TYPE"]]]

# Print out CSV
links.to_csv("relationships.csv", index=False)

print("JSON-converting to CSV done!")
