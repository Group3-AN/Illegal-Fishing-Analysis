from dash.dependencies import Input, Output, State, ALL
from dash import dcc
from dash import no_update
from dash import ctx
from backend.dataserver import ( get_geo_data, get_companies, get_vessels, get_cities, get_points, get_species, 
    get_regions, fetch_delivery_qty_data, 
    get_transport_movements, process_transport_movements, get_fish_deliveries, 
    process_fish_deliveries, get_vessel_counts, prepare_temporal_dataframe, detect_anomalies, detect_fish_delivery_anomalies,
    get_fish_distribution_data, fetch_vessel_cargo_data, preprocess_vessel_cargo_data) #, apply_kmeans_clustering
from backend.graph_utils import ( create_empty_heatmap, create_interactive_graph, create_heatmap, create_treemap, create_empty_treemap)
import plotly.express as px
import plotly.graph_objects as go
import json
from shapely.geometry import Point, MultiPoint
from shapely.geometry import Polygon, MultiPolygon
from shapely.geometry.polygon import orient
import geopandas as gpd
from datetime import datetime, timedelta
import pandas as pd
from statsmodels.tsa.seasonal import seasonal_decompose

# @Author: Asta Omarsdottir
# @Email: asta.omarsdottir@gmail.com
# @Date: 2024-11-08
# @Last Modified by:   undefined
# @Last Modified time: 2024-12-19
# @Description: Handles callback between frontend and backend

def register_callbacks(app):
    
#**********************************************************************************************    
    
# @Author: Asta Omarsdottir
# @Email: asta.omarsdottir@gmail.com
# @Date: 2024-12-08
# @Last Modified by:   undefined
# @Last Modified time: 2024-12-08
# @Description: Callback function to dynamically populate dropdown menus based on user selections.
    
    @app.callback(
    Output({'type': 'dynamic-dropdown', 'filter': ALL}, 'options'),
    Input({'type': 'dynamic-dropdown', 'filter': ALL}, 'value'),
    State('filter-store', 'data')
    )
    def populate_dynamic_dropdowns(selected_values, filter_store):
        # Update dropdown_data based on selected_filters
        # Extract current filter selections
        filter_mapping = ['companies', 'cities', 'ports', 'regions', 'vessels', 'species']
        filters = {key: selected_values[i] if i < len(selected_values) and selected_values[i] else None
                for i, key in enumerate(filter_mapping)}

        # Update filter-store dynamically
        for key, value in filters.items():
            filter_store[key] = value

        # Fetch updated data for each dropdown based on the current filter state
        dropdown_data = {
            'companies': [
                {'label': str(company), 'value': str(company)}
                for company in get_companies(vessel=filters['vessels'])
                if company is not None
            ] if filters['vessels'] else [
                {'label': str(company), 'value': str(company)}
                for company in get_companies()
                if company is not None
            ],
            'cities': [{'label': city, 'value': city} for city in get_cities()],
            'ports': [{'label': port, 'value': port} for port in get_points()],
            'regions': [{'label': region, 'value': region} for region in get_regions()],
            'vessels': [
                {'label': str(vessel), 'value': str(vessel)}
                for vessel in get_vessels(company=filters['companies'])
                if vessel is not None
            ] if filters['companies'] else [
                {'label': str(vessel), 'value': str(vessel)}
                for vessel in get_vessels()
                if vessel is not None
            ],
            'species': [{'label': species, 'value': species} for species in get_species()]
        } 
        # Return selected values
        result = [dropdown_data.get(filter_key, []) for filter_key in filter_mapping]
        return result
    
# @Author: Asta Omarsdottir
# @Email: asta.omarsdottir@gmail.com
# @Date: 2024-12-08
# @Last Modified by:   undefined
# @Last Modified time: 2024-12-08
# @Description: Handles updating stored filter data (in filter-store) based on user selections in dynamic dropdown menus
    
    @app.callback(
        Output('filter-store', 'data'),  # Update stored filters
        [
            Input({'type': 'dynamic-dropdown', 'filter': ALL}, 'value')  # Gets all selected values in dynamic dropdowns
        ],
        [State('filter-store', 'data')]  # current selected filters
    )
    def update_filter_store(values, current_data):
        filter_mapping = ['companies', 'cities', 'ports', 'regions', 'vessels', 'species']
        for i, filter_type in enumerate(filter_mapping):
            current_data[filter_type] = values[i] if i < len(values) else None
        return current_data
    
# @Author: Asta Omarsdottir
# @Email: asta.omarsdottir@gmail.com
# @Date: 2025-03-16
# @Last Modified by:   undefined
# @Last Modified time: 2025-03-16
# @Description: Handles callback to update the processed data store based on user cargo filter selections
 
    @app.callback(
        [Output('cargo-selector', 'options'),
        Output('cargo-selector', 'value')],
        Input('processed-data-store', 'data')  # Listening to changes in processed data
    )
    def update_cargo_selector(processed_data):
        if not processed_data:
            # If no data is present, return an empty list of options
            return [], None

        # Load and parse the processed data (if it's stored as a JSON string)
        processed_data = json.loads(processed_data)
        
        # Extract matched_data and ensure 'cluster' is present
        matched_data = processed_data.get('matched_data', [])
        if not matched_data:
            return [], None

        # Create unique clusters for the dropdown
        clusters = sorted(set(item.get('cluster') for item in matched_data if 'cluster' in item))
        if not clusters:
            # Handle case where no clusters are available
            return [], None
        
        # Generate options for the dropdown
        options = [{'label': f"Cluster {i}", 'value': i} for i in clusters]

        # Default value is the first cluster (e.g., cluster `0`)
        default_value = 0 if 0 in clusters else clusters[0]  # Fallback to the first cluster if `0` is not available
        
        return options, default_value
 
    
# @Author: Asta Omarsdottir
# @Email: asta.omarsdottir@gmail.com
# @Date: 2024-12-10
# @Last Modified by:   Asta Omarsdottir
# @Last Modified time: 2024-12-19
# @Last Modified time: 2025-03-01
# @Description: Handles callback with users filter selections for heatmap visualizing dwell time in locations over time
      
    @app.callback(
    Output('heatmap-graph', 'figure'),
    [
        Input('filter-store', 'data'),
        Input('processed-data-store', 'data')
        ]
    )
    def update_heatmap(filter_data, store_data):
        if not store_data:
            return {}  # Return an empty figure if no data
        
        # Convert JSON string back into a dictionary
        store_data_dict = json.loads(store_data)
    
        # Get transport movement data
        transport_data = store_data_dict.get("transport_movements", [])
        
        if not transport_data:
            return create_empty_heatmap()  # Handle the case when no data is available

        # Convert list of dictionaries to DataFrame
        if transport_data:
            transport_df = pd.DataFrame(transport_data)
        else:
            transport_df = pd.DataFrame()
            
         # Apply filters
        if filter_data:
            selected_vessels = filter_data.get('vessels', [])
            selected_cities = filter_data.get('cities', [])
            selected_points = filter_data.get('points', [])
            selected_regions = filter_data.get('regions', [])
        
         # Filter by selected vessels
        if selected_vessels:
            transport_df = transport_df[transport_df['vessel_id'].isin(selected_vessels)]
         # Filter by cities, points, or regions (location-based filters)
        if selected_cities:
            transport_df = transport_df[transport_df['location_id'].isin(selected_cities)]
        elif selected_points:
            transport_df = transport_df[transport_df['location_id'].isin(selected_points)]
        elif selected_regions:
            transport_df = transport_df[transport_df['location_id'].isin(selected_regions)]   
        
        # Check if DataFrame is not empty
        if transport_df.empty:
            return create_empty_heatmap()
        
        # Create the heatmap with filtered data
        return create_heatmap(transport_df, filter_data)
            
# @Author: Asta Omarsdottir
# @Email: asta.omarsdottir@gmail.com
# @Date: 2024-12-01
# @Last Modified by:   undefined
# @Last Modified time: 2024-12-19
# @Description: Create choropleth-map and scatter-plot for Geospatial analysis in choropleth and scatter plot

    @app.callback(
    Output('choropleth-map', 'figure'),
    Input('filter-store', 'data')
    )
    def update_choropleth_and_scatter(filter_data):
        geo_data = get_geo_data()
        
        if geo_data is None or geo_data.empty:
            empty_figure = go.Figure().update_layout(
                title="No data available",
                geo=dict(showframe=False, showcoastlines=False)
            )
            return empty_figure, empty_figure
        
        # Ensure geo_data is a GeoDataFrame
        if not isinstance(geo_data, gpd.GeoDataFrame):
             geo_data = gpd.GeoDataFrame(geo_data, geometry='geometry')
             
        # Correct orientation for each polygon
        def correct_orientation(geometry):
            if geometry.geom_type == 'Polygon':
                return orient(geometry, sign=1.0)  # Counterclockwise for outer rings
            elif geometry.geom_type == 'MultiPolygon':
                return MultiPolygon([orient(poly, sign=1.0) for poly in geometry.geoms])
            return geometry

        geo_data['geometry'] = geo_data['geometry'].apply(correct_orientation)     

        # Remove invalid or missing geometry types
        geo_data = geo_data[geo_data.geometry.notnull() & geo_data.geometry.is_valid]
        geo_data['geometry'] = geo_data['geometry'].apply(lambda geom: geom.buffer(0) if not geom.is_valid else geom)
        
        # Calculate centroids for alla geometries
        geo_data['centroid_lat'] = geo_data.geometry.centroid.y
        geo_data['centroid_lon'] = geo_data.geometry.centroid.x

        # Separate points for scatter plot
        points_data = geo_data.loc[geo_data['geometry'].geom_type == 'Point'].copy()
        polygons_data = geo_data.loc[geo_data['geometry'].geom_type == 'Polygon'].copy()
            
        # Mapping type and type_x from the merged data
        points_data['type'] = points_data['type_x']
        polygons_data['type'] = polygons_data['type_x']
        
        # Calculate bounding box and zoom
        points = geo_data['geometry'].centroid
        multi_point = MultiPoint(list(points))
        minx, miny, maxx, maxy = multi_point.bounds
        center_lat, center_lon = (miny + maxy) / 2, (minx + maxx) / 2
        zoom = 7
        
        # Specify z-values based on the kind of region
        # Define groups and colors
        ecological_preserve = ['Nemo Reef', 'Ghoti Preserve', 'Don Limpet Preserve']
        fishing_ground = ['Wrasse Beds', 'Cod Table', 'Tuna Shelf']

        # Add a column for color values in polygons_data
        polygons_data['group'] = polygons_data['id'].apply(
            lambda x: 'Ecological Preserve' if x in ecological_preserve else 
                    'Fishing Ground' if x in fishing_ground else 'Others'
        )

        # Create z-col for colorindex
        polygons_data['z_value'] = polygons_data['group'].apply(
            lambda x: 0 if x == 'Ecological Preserve' else 
                    1 if x == 'Fishing Ground' else 2
        )

        # Define colorindex for the groups
        colorscale = [
            [0, '#FFCCCC'],  # Light Red (Ecological Preserve)
            [0.33, '#FFCCCC'],
            [0.34, '#CCE5FF'],  # Light Blue (Fishing Ground)
            [0.66, '#CCE5FF'],
            [0.67, '#CCFFCC'],  # Light Green (Others)
            [1, '#CCFFCC']
        ]

        # Scatter plot for points_data (ports and cities)
        scatter_fig = px.scatter_mapbox(
            points_data,
            lat='centroid_lat',
            lon='centroid_lon',
            text='Name',
            color='type',
            title="Scatter Plot of Centroids",
            zoom=zoom,
            height=600
        )
        scatter_fig.update_layout(
            mapbox=dict(
                style="white-bg",
                center={"lat": center_lat, "lon":  center_lon},
                zoom=7,
            ),
            margin={"r": 0, "t": 0, "l": 0, "b": 0}
        )
       
       # Choropleth map 
        if polygons_data.empty:
            print("No polygons available for choropleth.")
            choropleth_fig = go.Figure().update_layout(
                title="No polygons available",
                geo=dict(showframe=False, showcoastlines=False)
            )
        else:
            # Create GeoJSON-object
            polygons_data['geojson'] = polygons_data['geometry'].apply(lambda geom: geom.__geo_interface__)
            geojson_object = {
                "type": "FeatureCollection",
                "features": [
                    {
                        "type": "Feature",
                        "geometry": row['geometry'].__geo_interface__,
                        "properties": {"id": row['id'], "type": row['type'], "Name": row['Name']},
                    }
                    for _, row in polygons_data.iterrows()
                ],
            }
            
        #Choropleth map
        # Choropleth for polygons
        choropleth = go.Choroplethmapbox(
            geojson=geojson_object,
            locations=polygons_data['id'],
            featureidkey="properties.id",
            # z=[1] * len(polygons_data),
            # colorscale=[[0, 'gray'], [1, 'gray']],
            z=polygons_data['z_value'],
            colorscale=colorscale,
            marker_opacity=0.8,
            marker_line_width=2,
         )
        
        # Scatter for polygons points
        scatter_polygons = go.Scattermapbox(
            lat=polygons_data['centroid_lat'],
            lon=polygons_data['centroid_lon'],
            mode='markers+text',
            marker=dict(size=6, color='purple'),
            text=polygons_data['id'],
            textposition="top center",
        )
        
        # Scatter for points
        scatter_points = go.Scattermapbox(
            lat=points_data['centroid_lat'],
            lon=points_data['centroid_lon'],
            mode='markers+text',
            marker=dict(size=6, color='blue'),
            text=points_data['id'],
            textposition="top center",
        )
        
        # Add all to the map
        choropleth_fig = go.Figure(data=[choropleth, scatter_polygons, scatter_points])
        
        # Layout for Choroplethmap
        choropleth_fig.update_layout(
            mapbox=dict(
                style="white-bg",
                center={"lat": center_lat, "lon": center_lon},
                zoom=zoom,
            ),
            margin={"r": 0, "t": 0, "l": 0, "b": 0},
        )
        
        return choropleth_fig
    
# @Author: Asta Omarsdottir
# @Email: asta.omarsdottir@gmail.com
# @Date: 2024-11-27
# @Last Modified by:   Asta Omarsdottir
# @Last Modified time: 2024-01-06
# @Description: Callback to Update the Backend.
# This callback listens to selections from DatePickerRange and stores dates in the calendar-store
# Simplified the functionality

    # Callback to handle date selection and store interval in calendar-store
    @app.callback(
        Output('calendar-store', 'data'),
        [
            Input('date-picker', 'start_date'),
            Input('date-picker', 'end_date')
        ]
    )
    def update_calendar_store(start_date, end_date): 
        # Define default dates
        start_datetime = datetime.strptime('2035-01-01 00:00:00', '%Y-%m-%d %H:%M:%S')
        end_datetime = datetime.strptime('2035-02-28 23:59:59', '%Y-%m-%d %H:%M:%S')
        
        if start_date:
            start_datetime = datetime.strptime(start_date, '%Y-%m-%d')
        if end_date:
            end_datetime = datetime.strptime(end_date, '%Y-%m-%d')
            
            # Ensure the start date is earlier than the end date
        if start_datetime >= end_datetime:
            print(f"Invalid date range: start_datetime={start_datetime}, end_datetime={end_datetime}")
            return {
                'start_datetime': start_datetime.strftime('%Y-%m-%d %H:%M:%S'),
                'end_datetime': (start_datetime + timedelta(days=1)).strftime('%Y-%m-%d %H:%M:%S'),
            }
        
        # Convert to string format for consistency
        return {
            'start_datetime': start_datetime.strftime('%Y-%m-%d %H:%M:%S'),
            'end_datetime': end_datetime.strftime('%Y-%m-%d %H:%M:%S')
        }

# @Author: Asta Omarsdottir
# @Email: asta.omarsdottir@gmail.com
# @Date: 2024-11-27
# @Last Modified by:   Asta Omarsdottir
# @Last Modified time: 2025-01-06
# @Description: Callback to display selected dates on the site.
# User friendly messages when no dates selected 
    
    # Callback to display selected interval
    @app.callback(
        Output('output-container', 'children'),
        Input('calendar-store', 'data')
    )
    def display_selected_interval(data):
        if not data or not data.get('start_datetime') or not data.get('end_datetime'):
            return "No selected interval"  # Display this when no dates are selected
        
        start_date = datetime.strptime(data['start_datetime'], '%Y-%m-%d %H:%M:%S').date()
        end_date = datetime.strptime(data['end_datetime'], '%Y-%m-%d %H:%M:%S').date()
        
        return f"Dates: {start_date} to {end_date}"
    
# @Author: Nupur Mittal
# @Email: nupurmittal5@gmail.com
# @Date: 2024-11-08
# @Last Modified by:   Asta Omarsdottir
# @Last Modified time: 2024-11-24
# @Last Modified: Moved from dataframetable.py with minor changes
# @Last Modified by:   Asta Omarsdottir
# @Last Modified time: 2025-03-01
# @Last Modified: Added transport movements to this graph
# @Description: Generates and updates four different graphs based on time series analysis.
 
    @app.callback(
        [Output('time-series', 'figure'),
        Output('decomposition-trend', 'figure'),
        Output('decomposition-seasonal', 'figure'),
        Output('decomposition-residual', 'figure')],
        [Input("data-toggle", "value"),  # Dropdown selection
        Input("processed-data-store", "data")]  # Stored processed data
    )
    def update_graphs(data_type, store_data):
        if not store_data:
            return go.Figure(), go.Figure(), go.Figure(), go.Figure()

        # Convert JSON string to Python dictionary
        if isinstance(store_data, str):  
            store_data = json.loads(store_data)

        temporal_data = store_data.get("temporal_data", [])
        
        # Ensure temporal data exists
        if not temporal_data:
            return go.Figure(), go.Figure(), go.Figure(), go.Figure()

        # Convert temporal data into DataFrame
        temporal_df = pd.DataFrame(temporal_data)

        # Ensure the 'date' column is datetime
        temporal_df["date"] = pd.to_datetime(temporal_df["date"])

        # Time-series Figure
        fig_time_series = go.Figure()

        # Plot Cargo Data (Fish Deliveries)
        if data_type in ["cargo", "both"] and "qty_tons" in temporal_df.columns:
            fig_time_series.add_trace(go.Scatter(
                x=temporal_df["date"],  
                y=temporal_df["qty_tons"],  
                mode="lines",
                name="Cargo Quantity (tons)",
                line=dict(color="blue")
            ))

        # Plot Vessel Data
        if data_type in ["vessels", "both"] and "num_vessels" in temporal_df.columns:
            fig_time_series.add_trace(go.Scatter(
                x=temporal_df["date"],  
                y=temporal_df["num_vessels"],  
                mode="lines",
                name="Vessel Count",
                line=dict(color="red", dash="dash")
            ))
            fig_time_series.update_layout(title="Time Serie Component",font=dict(size=8,variant="small-caps"), margin=dict(t=40, b=20, l=40, r=10),)

        # Perform Time Series Decomposition
        if len(temporal_df) >= 30:
            # Ensure there are no missing values in 'qty_tons' and 'num_vessels' columns
            temporal_df['qty_tons']= temporal_df['qty_tons'].fillna(0)
            temporal_df['num_vessels'] = temporal_df['num_vessels'].fillna(0)
            
            decomposition = seasonal_decompose(temporal_df.set_index("date")["qty_tons"], model="additive", period=30)
            vessel_decomposition = seasonal_decompose(temporal_df.set_index("date")["num_vessels"], model="additive", period=30)

            # Trend Component
            fig_trend = go.Figure(go.Scatter(
                x=decomposition.trend.index, 
                y=decomposition.trend, 
                mode="lines", 
                name="Trend (Cargo)"
            ))
            fig_trend.add_trace(go.Scatter(
                x=vessel_decomposition.trend.index, 
                y=vessel_decomposition.trend, 
                mode="lines", 
                name="Trend (Vessels)",
                line=dict(dash="dash", color="red")
            ))
            fig_trend.update_layout(title="Trend Component",font=dict(size=8,variant="small-caps"), margin=dict(t=40, b=20, l=40, r=10),)

            # Seasonal Component
            fig_seasonal = go.Figure(go.Scatter(
                x=decomposition.seasonal.index, 
                y=decomposition.seasonal, 
                mode="lines", 
                name="Seasonality (Cargo)"
            ))
            fig_seasonal.add_trace(go.Scatter(
                x=vessel_decomposition.seasonal.index, 
                y=vessel_decomposition.seasonal, 
                mode="lines", 
                name="Seasonality (Vessels)",
                line=dict(dash="dash", color="red")
            ))
            fig_seasonal.update_layout(title="Seasonal Component",font=dict(size=8,variant="small-caps"), margin=dict(t=40, b=20, l=40, r=10),)
            
            # Residual Component (Anomalies)
            fig_residual = go.Figure(go.Scatter(
                x=decomposition.resid.index, 
                y=decomposition.resid, 
                mode="lines", 
                name="Residuals (Cargo)"
            ))
            fig_residual.add_trace(go.Scatter(
                x=vessel_decomposition.resid.index, 
                y=vessel_decomposition.resid, 
                mode="lines", 
                name="Residuals (Vessels)",
                line=dict(dash="dash", color="red")
            ))
            fig_residual.update_layout(title='Residuals Anomalies',font=dict(size=8,variant="small-caps"), margin=dict(t=40, b=20, l=40, r=10),)
            
        else:
            # Not enough data for decomposition
            fig_trend, fig_seasonal, fig_residual = go.Figure(), go.Figure(), go.Figure()

        return fig_time_series, fig_trend, fig_seasonal, fig_residual

# @Author: Nupur Mittal
# @Email: nupurmittal5@gmail.com
# @Date: 2024-11-08
# @Last Modified by:   Asta Omarsdottir 
# @Last Modified time: 2024-11-13
# @Last Modified: Moved from matching vessel cargo.py with some changes
# @Description: Handles users cluster selection and generates and updates the cluster graph based on filter selections. 
    
    @app.callback(
        Output('cluster-plot', 'figure'),
        [ 
        Input('cargo-selector', 'value'),
        Input('processed-data-store', 'data')
        ]
        
    )
    def update_cluster_plot(selected_clusters, store_data):    
        if not store_data:
        # Return an empty Plotly figure if no data is available
            return px.scatter(
                title="No Data Available",
                labels={'x': 'Exit Date', 'y': 'Quantity (Tons)'}
            )
        
        # Ensure `selected_clusters` is a list
        if not isinstance(selected_clusters, list):
            selected_clusters = [selected_clusters]
            
        # Check if store_data is a string and parse it
        if isinstance(store_data, str):
            store_data = json.loads(store_data)  # Convert JSON string to dictionary    
            
        # Extract matched_data and use it in your layout
        matched_data = store_data.get("matched_data", [])
        
        if not matched_data:
            # Return a placeholder figure if matched_data is empty
            return px.scatter(
                title="No matched data found",
                labels={'x': 'Exit Date', 'y': 'Quantity (Tons)'}
            )
        
        # Convert matched_data to a pandas DataFrame
        matched_data = pd.DataFrame(matched_data)
    
        # Ensure 'cluster' column exists
        if 'cluster' not in matched_data.columns:
            return px.scatter(
                title="Cluster column not found in matched data.",
                labels={'x': 'Exit Date', 'y': 'Quantity (Tons)'}
            )
                
        # Filter data based on selected clusters
        filtered_data = matched_data[matched_data['cluster'].isin(selected_clusters)]
        
        # Create scatter plot
        fig = px.scatter(filtered_data, x='exit_date', y='qty_tons', color='cluster', template='plotly',
                         title='Clustered Port Exits by Cargo Volume and Date',
                         labels={'exit_date': 'Exit Date', 'qty_tons': 'Quantity (Tons)'},
                         hover_data=['vessel_id']
                         )
        fig.update_layout(
            font=dict(size=8, variant="small-caps"),
            title_font=dict(size=12, variant="small-caps"),
            legend_font=dict(size=8, variant="small-caps")
            )
        return fig
    
# @Author: Nupur Mittal
# @Email: nupurmittal5@gmail.com
# @Date: 2024-11-15
# @Last Modified by:   Asta Omarsdottir 
# @Last Modified time: 2024-11-18
# @Modified: Moved from network.py with minor changes
# @Last Modified by:   Asta Omarsdottir 
# @Last Modified time: 2025-03-02
# @Modified: Added filter data to the function and updated the function to handle the filter data
# @Modified: Added store_data as an input to the function
# @Description: Handles user filter selections and create/updates graph to analyse fish quantity and seasonal trends 
    
    @app.callback(
        Output('anomaly-time-series-graph', 'figure'),
        [Input('filter-store', 'data'),
        Input('processed-data-store', 'data')]
    )
    def update_anomaly_time_series(filter_data, store_data):
        if not store_data:
            return px.scatter(
                title="No data available",
                labels={'qty_tons': 'Quantity (Tons)', 'date_of_arrival': 'Date'}
            )
            
        if isinstance(store_data, str):
            try:
                store_data = json.loads(store_data)
            except json.JSONDecodeError:
                print("Error: Failed to decode JSON data!")
                return px.scatter(
                    title="Error: Invalid Data",
                    labels={'qty_tons': 'Quantity (Tons)', 'date_of_arrival': 'Date'}
                )  
            
        # Check if 'fish_deliveries' exists in store_data
        if "fish_deliveries" not in store_data or not store_data["fish_deliveries"]:
            return px.scatter(
                title="No fish deliveries available",
                labels={'qty_tons': 'Quantity (Tons)', 'date_of_arrival': 'Date'}
            )
            
        # Apply anomaly detection function
        fish_df = detect_fish_delivery_anomalies(store_data)
        if fish_df.empty:
            return px.scatter(
            title="No fish deliveries available",
            labels={'qty_tons': 'Quantity (Tons)', 'date_of_arrival': 'Date'}
        )

        # Apply filters dynamically
        selected_cities = filter_data.get("cities", []) if filter_data else []
        selected_fish = filter_data.get("species", []) if filter_data else []
        selected_vessels = filter_data.get("vessels", []) if filter_data else []

        if selected_cities:
            fish_df = fish_df[fish_df["city_of_arrival"].isin(selected_cities)]
        if selected_fish:
            fish_df = fish_df[fish_df["fish_name"].isin(selected_fish)]
        if selected_vessels:
            fish_df = fish_df[
                fish_df["harbor_vessels"].apply(lambda x: any(v in x for v in selected_vessels) if isinstance(x, list) else False) |
                fish_df["ping_vessels"].apply(lambda x: any(v in x for v in selected_vessels) if isinstance(x, list) else False)
    ]

        # If no data remains after filtering, return an empty plot
        if fish_df.empty:
            return px.scatter(
                title="No data after filtering",
                labels={'qty_tons': 'Quantity (Tons)', 'date_of_arrival': 'Date'}
            )

        # Create the Scatter Plot**
        fig = px.scatter(
            fish_df,
            x="date_of_arrival",
            y="quantity_tons",
            color="anomaly",
            title="Fish Delivery Anomalies Over Time",
            labels={'quantity_tons': 'Quantity (Tons)', 'date_of_arrival': 'Date'},
            color_discrete_map={0: "blue", 1: "red"},  # 0 = Normal, 1 = Anomalous
            hover_data=["city_of_arrival", "fish_name"]
        )

        fig.update_traces(mode="markers+lines")
        fig.update_layout(
            font=dict(size=10),
            title_font=dict(size=12),
            xaxis_title_font=dict(size=10),
            yaxis_title_font=dict(size=10)
        )
        
        return fig
   
# @Author: Asta Omarsdottir
# @Email: asta.omarsdottir@gmail.com
# @Date: 2024-12-26
# @Last Modified by:   undefined
# @Last Modified time: 2024-12-26
# @Description: Handles callback for Treemap showing fish quantity by city, fish or vessel
   
    @app.callback(
        Output('treemap', 'figure'),
        [Input('filter-store', 'data'),  # Selected city, fish, vessel
        Input('processed-data-store', 'data')]  # Fetched fish deliveries
    )
    def update_treemap(filter_data, store_data):
        if not store_data:
            return {}  # Return an empty figure if no data

        # Convert JSON string back into a dictionary
        store_data_dict = json.loads(store_data)
        
        # Get treemap data
        treemap_data = store_data_dict.get("fish_deliveries", [])

        if not treemap_data:
            return create_empty_treemap()  # Handle the case when no data is available

        # Convert list of dictionaries to DataFrame
        treemap_df = pd.DataFrame(treemap_data) if treemap_data else pd.DataFrame()

        # Ensure 'harbor_vessels' and 'ping_vessels' are lists, avoiding NaN issues
        treemap_df["harbor_vessels"] = treemap_df["harbor_vessels"].apply(lambda x: x if isinstance(x, list) else [])
        treemap_df["ping_vessels"] = treemap_df["ping_vessels"].apply(lambda x: x if isinstance(x, list) else [])

        # Merge vessel lists and explode them
        treemap_df["vessel_id"] = treemap_df["harbor_vessels"] + treemap_df["ping_vessels"]
        treemap_df = treemap_df.explode("vessel_id")

        # Apply filters if data exists
        if filter_data:
            selected_vessels = filter_data.get('vessels', [])
            selected_cities = filter_data.get('cities', [])
            selected_species = filter_data.get('species', [])

            # Filter by selected vessels
            if selected_vessels:
                treemap_df = treemap_df[treemap_df['vessel_id'].isin(selected_vessels)]

            # Filter by cities, points, or regions (location-based filters)
            if selected_cities:
                treemap_df = treemap_df[treemap_df['city_of_arrival'].isin(selected_cities)]
            
            # Filter by species
            if selected_species:  # Corrected from `elif selected_regions`
                treemap_df = treemap_df[treemap_df['fish_name'].isin(selected_species)]

        # Ensure DataFrame is valid and contains necessary columns
        required_columns = {"city_of_arrival", "fish_name", "date_of_arrival", "quantity_tons"}
        if treemap_df.empty or not required_columns.issubset(treemap_df.columns):
            return create_empty_treemap()

        # Ensure 'date_of_arrival' is a valid datetime format
        treemap_df["date_of_arrival"] = pd.to_datetime(treemap_df["date_of_arrival"], errors="coerce")

        # Ensure 'quantity_tons' is numeric to avoid aggregation issues
        treemap_df["quantity_tons"] = pd.to_numeric(treemap_df["quantity_tons"], errors="coerce")

        # Aggregate data by city, fish type, and date
        aggregated_data = (
            treemap_df.groupby(["city_of_arrival", "fish_name", "date_of_arrival"])["quantity_tons"]
            .sum()
            .reset_index()
        )

        # Fill NaN values and avoid division by zero
        aggregated_data["quantity_tons"] = aggregated_data["quantity_tons"].fillna(1)
        if aggregated_data["quantity_tons"].sum() == 0:
            aggregated_data["quantity_tons"] = 1  # Avoid division by zero

        # Create the treemap with filtered data
        return create_treemap(aggregated_data)

# @Author: Asta Omarsdottir
# @Email: asta.omarsdottir@gmail.com
# @Date: 2025-01-16
# @Last Modified by:   undefined
# @Last Modified time: 2025-01-16
# @Description: Load and process data dynamically when date range changes
    
    # Callback to load and process data dynamically
    @app.callback(
        Output("processed-data-store", "data"),
        [Input("calendar-store", "data")]
    )
    def load_and_process_data(calendar_data):
        if not calendar_data:
            return json.dumps({})

        # Extract dates from the calendar store
        start_date = calendar_data.get("start_datetime")
        end_date = calendar_data.get("end_datetime")
        
        # Fetch and process transport movement data for heatmap
        raw_transport_data = get_transport_movements(start_date, end_date)
        processed_transport_data = process_transport_movements(raw_transport_data) 
    
        # Fetch and process fish delivery data for Network-Link graph (pyvis)
        raw_fish_data = get_fish_deliveries(start_date, end_date)
        processed_fish_data = process_fish_deliveries(raw_fish_data)
        
        # Fetch and process delivery qty data for temporal and seasonal graph
        delivery_qty_data = fetch_delivery_qty_data(start_date, end_date)
        
        # Fetch and process vessel data for temporal and seasonal graph  
        vessel_count_data = get_vessel_counts(start_date, end_date)
        
        # Prepare temporal data (combined delivery_qty_data and vessel_count_data)
        temporal_df = prepare_temporal_dataframe(delivery_qty_data, vessel_count_data)
        
        # Detect anomalies in temporal data (combined fish deliveries and vessel counts)
        temporal_df = detect_anomalies(temporal_df)
        
        # Convert datetime columns to string to make them JSON serializable
        if 'date' in temporal_df.columns:
            temporal_df['date'] = temporal_df['date'].astype(str)
            
        # Fetch and process fish distribution data for treemap
        fish_distribution_data = get_fish_distribution_data()
        
        # Fetch and process data for cluster-plot
        deliveries, exits = fetch_vessel_cargo_data(start_date, end_date)
        matched_data = preprocess_vessel_cargo_data(deliveries, exits)
        
        # Convert matched_data to a DataFrame if necessary and handle empty cases
        if isinstance(matched_data, list):
            if matched_data: 
                matched_data = pd.DataFrame(matched_data)
            else:
                matched_data = pd.DataFrame()

        # Store all datasets in a dictionary
        processed_data = {
            "transport_movements": processed_transport_data.to_dict("records") if isinstance(processed_transport_data, pd.DataFrame) else [],
            "fish_deliveries": processed_fish_data,
            "temporal_data": temporal_df.to_dict("records") if isinstance(temporal_df, pd.DataFrame) else [],
            "fish_distribution": fish_distribution_data,
            "matched_data": matched_data.to_dict("records") if not matched_data.empty else []
        }
        return json.dumps(processed_data)
    
# @Author: Asta Omarsdottir
# @Email: asta.omarsdottir@gmail.com
# @Date: 2025-03-01
# @Last Modified by:   undefined
# @Last Modified time: 2025-03-01
# @Description: Callback to update the pyvis graph based on selected filters and graph type

    @app.callback(
        Output('pyvis-graph', 'srcDoc'),
        [
            Input('filter-store', 'data'),
            Input('calendar-store', 'data'),
            Input('graph-type', 'value'),
            Input('processed-data-store', 'data')
        ]
    )
    def update_interactive_graph(filter_data, calendar_data, selected_graph, store_data):
        if not selected_graph:
            print("graph_type not selected, returning empty graph.")
            return "<h3 style='color:white;'>Waiting for selecting graph type...</h3>"
        
        # Ensure store_data is parsed as a dictionary
        if isinstance(store_data, str):
            try:
                store_data = json.loads(store_data)
            except json.JSONDecodeError:
                print("Error: Failed to decode JSON data!")
                return "<h3 style='color:white;'>Error: Invalid Data</h3>"
            
        # Extract start and end datetime safely
        start_datetime = datetime.strptime(calendar_data.get('start_datetime', '2035-01-01 00:00:00'), '%Y-%m-%d %H:%M:%S')
        end_datetime = datetime.strptime(calendar_data.get('end_datetime', '2035-02-28 23:59:59'), '%Y-%m-%d %H:%M:%S')

        # Extract fish delivery data
        fish_delivery_data = store_data.get("fish_deliveries", [])
        
        if not fish_delivery_data:
            print("No fish deliveries found in processed data!")
            return ""

        # Extract filter options
        selected_cities = filter_data.get('cities', []) if filter_data else []
        selected_vessels = filter_data.get('vessels', []) if filter_data else []
        selected_fish_types = filter_data.get('species', []) if filter_data else []

        # Ensure both are date objects
        start_date = start_datetime.date()
        end_date = end_datetime.date()

        filtered_data = [
            record for record in fish_delivery_data
            if (not selected_cities or record.get("city_of_arrival") in selected_cities)
            and (not selected_vessels or any(vessel in selected_vessels for vessel in record.get("harbor_vessels", [])) 
                or any(vessel in selected_vessels for vessel in record.get("ping_vessels", [])))
            and (not selected_fish_types or record.get("fish_name") in selected_fish_types)
        ]
        
        # To do: Implement the selected graph type
        #Apply clustering if "clustered" is selected
        # if selected_graph == "clustered":
        #     clustered_data = apply_kmeans_clustering(filtered_data)  # Apply clustering
        #     print(f"Clustered Data: {clustered_data[:5]}")  # Debug first few records
        #     graph_html = create_interactive_graph(clustered_data)
        # else:        
            # Generate the filtered graph
        graph_html = create_interactive_graph(filtered_data)

        return graph_html
    
