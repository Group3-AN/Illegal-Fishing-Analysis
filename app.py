from dash import Dash
from frontend.layout import layout
from frontend.callbacks import register_callbacks
from backend.dataserver import fetch_delivery_qty_data, clean_data, normalize_and_cluster, fetch_vessel_cargo_data, preprocess_vessel_cargo_data, prepare_temporal_dataframe, get_transport_movements, process_transport_movements
from backend.graph_utils import decompose_time_series, detect_anomalies

app = Dash(__name__, suppress_callback_exceptions=True)
app.title = "Oceanus Vessel-Cargo Analysis"

# Fetch and process data
data = fetch_delivery_qty_data()
data = clean_data(data)
decomposition = decompose_time_series(data)

# Fetch and process data
deliveries, exits = fetch_vessel_cargo_data()
matched_data = preprocess_vessel_cargo_data()
matched_data = normalize_and_cluster(matched_data)

# Prepare temporal
temporal_df = prepare_temporal_dataframe()
temporal_df = detect_anomalies(temporal_df)

# Debugging: Print the first few rows of temporal_df
# print(temporal_df.head())

# Load and process data
raw_data = get_transport_movements()
#debug
#print("Raw data fetched:", raw_data.head())
processed_data = process_transport_movements(raw_data)

# Ställ in layout
app.layout = layout

# Registrera callbacks
register_callbacks(app, data, decomposition, matched_data, temporal_df, processed_data)

if __name__ == "__main__":
    app.run_server(debug=True)
