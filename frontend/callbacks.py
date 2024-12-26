from dash.dependencies import Input, Output, State, ALL
from dash import dcc
from dash import no_update
from backend.dataserver import get_geo_data, get_companies, get_vessels, get_cities, get_points, get_species, get_regions, fetch_delivery_data, fetch_delivery_qty_data, clean_data, fetch_temporal_data, get_treemap_data
from backend.graph_utils import create_graph, nx_to_cytoscape_elements, decompose_time_series, create_heatmap, create_treemap
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import json
from shapely.geometry import Point, MultiPoint
from shapely.geometry import Polygon, MultiPolygon
from shapely.geometry.polygon import orient
import geopandas as gpd

# @Author: Asta Omarsdottir
# @Email: asta.omarsdottir@gmail.com
# @Date: 2024-11-08
# @Last Modified by:   undefined
# @Last Modified time: 2024-12-19
# @Description: Handles callback between frontend and backend

def register_callbacks(app, data, decomposition, matched_data, temporal_df, processed_data):
    
# @Author: Asta Omarsdottir
# @Email: asta.omarsdottir@gmail.com
# @Date: 2024-12-08
# @Last Modified by:   undefined
# @Last Modified time: 2024-12-08
# @Description: Callback function to dynamically populate dropdown menus based on user selections.
    
    @app.callback(
    Output({'type': 'dynamic-dropdown', 'filter': ALL}, 'options'),
    Input({'type': 'dynamic-dropdown', 'filter': ALL}, 'value')
    )
    def populate_dynamic_dropdowns(selected_values):
        
        # debug
        print("Selected values:", selected_values) 
        
        # Check which selections have been made
        selected_filters = {
            'companies': selected_values[0] if len(selected_values) > 0 else None,
            'cities': selected_values[0] if len(selected_values) > 0 else None,
            'ports': selected_values[1] if len(selected_values) > 1 else None,
            'regions': selected_values[2] if len(selected_values) > 2 else None,
            'vessels': selected_values[3] if len(selected_values) > 3 else None,
            'species': selected_values[4] if len(selected_values) > 4 else None,
        }
    
        # Fill dropdowns with standard data, no filters selected
        dropdown_data = {
            'companies': [{'label': company, 'value': company} for company in get_companies()],
            'cities': [{'label': city, 'value': city} for city in get_cities()],
            'ports': [{'label': port, 'value': port} for port in get_points()],
            'regions': [{'label': region, 'value': region} for region in get_regions()],
            'vessels': [{'label': vessel, 'value': vessel} for vessel in get_vessels()],
            'species': [{'label': species, 'value': species} for species in get_species()],
        }
        
        # To do
        # Update dropdown_data based on selected_filters
        
        # Return selected values
        result = [dropdown_data.get(filter_key, []) for filter_key in ['companies','cities', 'ports', 'regions', 'vessels', 'species']]
        # debug
        #print("Returning options:", result)
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
        [State('filter-store', 'data')]  # earlier selected filters
    )
    def update_filter_store(values, current_data):
        # Identify which dropdowns are involved
        filter_types = ['companies', 'cities', 'ports', 'regions', 'vessels', 'species']
        
        # Update filtered data
        for i, value in enumerate(values):
            current_data[filter_types[i]] = value  # Save values from selected dropdown
        # debug
        # print('filter store updated: ')
        return current_data  # Return updated values
    
# @Author: Asta Omarsdottir
# @Email: asta.omarsdottir@gmail.com
# @Date: 2024-11-13
# @Last Modified by: 
# @Last Modified time: 2024-11-13
# @Last Modified:
# @Description: Update the graph elements in a Cytoscape component based on data filtered by the user's 
# selected date or date range for Networkx Node-Link Diagram, Fish Delivery Network

    @app.callback(
        Output('cytoscape', 'elements'),
        [
            Input('calendar', 'value')
        ],
        [
            State({'type': 'date-picker', 'index': ALL}, 'date'),
            State({'type': 'date-picker-range', 'index': ALL}, 'start_date'),
            State({'type': 'date-picker-range', 'index': ALL}, 'end_date')   
        ]
    )
    def update_graph(calendar_type, single_date, start_date, end_date):
        
        # manage selected date/daterange
        if calendar_type == 'single' and single_date:
            start_date = single_date[0] if single_date else None
        elif calendar_type == 'range' and start_date and end_date:
            start_date = f"{start_date[0]} to {end_date[0]}" if start_date and end_date else None
        else:
            start_date = "2035-11-01"
        # fetch data and create graph
        # start_date = "2035-11-01" if not selected_date else selected_date
        delivery_data = fetch_delivery_data(start_date=start_date)
        
        G = create_graph(delivery_data)
        elements = nx_to_cytoscape_elements(G)
        return elements   
    
# @Author: Asta Omarsdottir
# @Email: asta.omarsdottir@gmail.com
# @Date: 2024-12-10
# @Last Modified by:   undefined
# @Last Modified time: 2024-12-19
# @Description: Handles callback with users filter selections for heatmap visualizing dwell time in locations over time
      
    @app.callback(
    Output('heatmap-graph', 'figure'),
    [
        Input('filter-store', 'data'),
        Input('calendar', 'value')],
    [
        State({'type': 'date-picker', 'index': ALL}, 'date'),
        State({'type': 'date-picker-range', 'index': ALL}, 'start_date'),
        State({'type': 'date-picker-range', 'index': ALL}, 'end_date')   
    ]
    )
    def update_heatmap(filter_data, calendar_type, single_date, start_date, end_date):
        # Debugging information
        print("Filter Data:", filter_data)
        print("Calendar Type:", calendar_type)
        print("Single Date:", single_date)
        print("Start Date:", start_date, "End Date:", end_date)
        #print("Processed Data:", processed_data.head())
        return create_heatmap(processed_data,filter_data, calendar_type, single_date, start_date, end_date)

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
            print("No GeoData available or GeoData empty.")  # debug print, change to log
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
    
        # selected_cities = filter_data.get("cities", []) if filter_data else []

        # if selected_cities:
        #     geo_data = geo_data[geo_data['id'].isin(selected_cities)]

        # if geo_data.empty:
        #     #print("No data for selected cities.") # debug print
        #     empty_figure = go.Figure().update_layout(
        #         title="No data for selected cities",
        #         geo=dict(showframe=False, showcoastlines=False)
        #     )
        #     return empty_figure, empty_figure
        
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
            marker=dict(size=10, color='purple'),
            text=polygons_data['id'],
            textposition="top center",
        )
        
        # Scatter for points
        scatter_points = go.Scattermapbox(
            lat=points_data['centroid_lat'],
            lon=points_data['centroid_lon'],
            mode='markers+text',
            marker=dict(size=10, color='blue'),
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
# @Last Modified by:   undefined
# @Last Modified time: 2024-11-27
# @Description: Callback to Update the Calendar Component.
# ## This callback dynamically creates a calendar based on the selection of single or range

    @app.callback(
        Output('calendar-container', 'children'),  # Update calendar
        Input('calendar', 'value')  # listen to dropdown-value
    )
    def update_calendar(selected_option):
        if selected_option == 'single':
            # Single datepicker
            return dcc.DatePickerSingle(
                id={'type': 'date-picker', 'index': 0},  # Dynamic ID
                min_date_allowed="2022-01-01",
                max_date_allowed="2040-12-31",
                initial_visible_month="2035-11-01",
                date="2035-11-01",
                placeholder="Select a date"
            )
        elif selected_option == 'range':
            # Daterange
            return dcc.DatePickerRange(
                id={'type': 'date-picker-range', 'index': 0},  # Dynamic ID
                min_date_allowed="2022-01-01",
                max_date_allowed="2040-12-31",
                initial_visible_month="2035-11-01",
                start_date="2035-11-01",
                end_date="2035-11-30"
            )
        return None  # If nothing selected
    
# @Author: Asta Omarsdottir
# @Email: asta.omarsdottir@gmail.com
# @Date: 2024-11-27
# @Last Modified by:   undefined
# @Last Modified time: 2024-11-27
# @Description: Callback to Update the Backend.
# This callback listens to selections from DatePickerSingle or DatePickerRange and stores them in the calendar-store

    @app.callback(
        Output('calendar-store', 'data'),
        [
            Input({'type': 'date-picker', 'index': ALL}, 'date'),
            Input({'type': 'date-picker-range', 'index': ALL}, 'start_date'),
            Input({'type': 'date-picker-range', 'index': ALL}, 'end_date')
        ]
    )
    def update_calendar_store(single_date, start_date, end_date):
        # Kontrollera om single_date är valt
        if single_date and single_date[0]:
            return {'type': 'single', 'date': single_date[0]}
        # Kontrollera om daterange är valt
        elif start_date and start_date[0] and end_date and end_date[0]:
            return {'type': 'range', 'start_date': start_date[0], 'end_date': end_date[0]}
        return {}
    
# @Author: Asta Omarsdottir
# @Email: asta.omarsdottir@gmail.com
# @Date: 2024-11-27
# @Last Modified by:   undefined
# @Last Modified time: 2024-11-27
# @Description: Callback to display selected dates on the site.  
    
    @app.callback(
        Output('output-container', 'children'),
        Input('calendar-store', 'data')
    ) 
    def display_selected_dates(data):
        if not data:
            return "No dates selected"
        if data['type'] == 'single':
            return f"Selected Date: {data['date']}"
        elif data['type'] == 'range':
            return f"Selected Range: {data['start_date']} to {data['end_date']}"
        return "Invalid selection"
    
# @Author: Nupur Mittal
# @Email: nupurmittal5@gmail.com
# @Date: 2024-11-08
# @Last Modified by:   Asta Omarsdottir
# @Last Modified time: 2024-11-24
# @Last Modified: Moved from dataframetable.py with minor changes
# @Description: Generates and updates four different graphs based on time series analysis.
          
    @app.callback(
        [Output('time-series', 'figure'),
         Output('decomposition-trend', 'figure'),
         Output('decomposition-seasonal', 'figure'),
         Output('decomposition-residual', 'figure')],
        Input('time-series', 'id')
    )   
    def update_graphs(_):
        fig_time_series = px.line(data, x=data.index, y='qty_tons', title='Cargo Quantity Over Time')
        fig_time_series.update_layout(font=dict(size=8, variant="small-caps"), margin=dict(t=40, b=5, l=40, r=10),)
        fig_trend = go.Figure(go.Scatter(x=decomposition.trend.index, y=decomposition.trend, mode='lines', name='Trend'))
        fig_trend.update_layout(title='Trend Component',font=dict(size=8,variant="small-caps"), margin=dict(t=40, b=20, l=40, r=10),)
        fig_seasonal = go.Figure(go.Scatter(x=decomposition.seasonal.index, y=decomposition.seasonal, mode='lines', name='Seasonality'))
        fig_seasonal.update_layout(title='Seasonal Component',font=dict(size=8,variant="small-caps"), margin=dict(t=40, b=20, l=40, r=10),)
        fig_residual = go.Figure(go.Scatter(x=decomposition.resid.index, y=decomposition.resid, mode='lines', name='Residuals'))
        fig_residual.update_layout(title='Residuals (Anomalies',font=dict(size=8,variant="small-caps"), margin=dict(t=40, b=20, l=40, r=10),)

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
        Input('cargo-selector', 'value')
    )
    def update_cluster_plot(selected_clusters):
        # Ensure `selected_clusters` is a list
        if not isinstance(selected_clusters, list):
            selected_clusters = [selected_clusters]
        
        # Filter data based on selected clusters
        filtered_data = matched_data[matched_data['cluster'].isin(selected_clusters)]
        
        # Create scatter plot
        fig = px.scatter(filtered_data, x='exit_date', y='qty_tons', color='cluster', template='plotly',
                         title='Clustered Port Exits by Cargo Volume and Time',
                         labels={'exit_date': 'Exit Date and Time', 'qty_tons': 'Quantity (Tons)'},
                         hover_data=['vehicle_id']
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
# @Description: Handles user filter selections and create/updates graph to analyse fish quantity and seasonal trends 
    
    # temporal
    @app.callback(
    Output('anomaly-time-series-graph', 'figure'),
    Input('filter-store', 'data')  # Listening to multiple selections
    )
    def update_anomaly_time_series(filter_data):
        
        selected_cities = filter_data.get("cities", []) if filter_data else []
        
        # If no cities are selected, return an empty graph
        if not selected_cities:
            fig = px.scatter(
                title="No data to display",
                labels={'qty': 'Quantity (Tons)', 'date': 'Date'}
            )
            fig.update_layout(
            font=dict(size=8, variant="small-caps"),
            title_font=dict(size=12, variant="small-caps")
            )
            return fig
        
        # Debug
        #print(f"Selected cities: {selected_cities}")

        # Filter data for the selected cities
        filtered_df = temporal_df[temporal_df['city'].isin(selected_cities)]
        
        # Debug
        #print(f"Filtered data: {filtered_df.head()}")

        if filtered_df.empty:
            fig = px.scatter(
                title="No data for selected cities",
                labels={'qty': 'Quantity (Tons)', 'date': 'Date'}
            )
            fig.update_layout(
            font=dict(size=8, variant="small-caps"),
            title_font=dict(size=12, variant="small-caps")
            )
            return fig

        # Create a scatter plot with color based on 'anomaly'
        fig = px.scatter(
        filtered_df,
        x='date',
        y='qty',
        color='anomaly',
        title="Delivery Quantities and Anomalies Over Time",
        labels={'qty': 'Quantity (Tons)', 'date': 'Date'},
        color_discrete_map={'Normal': 'blue', 'Anomalous': 'red'},
        hover_data=['city']  # show city in hover-data
    )
        fig.update_traces(mode='markers+lines')
        fig.update_layout(
        font=dict(size=8, variant="small-caps"),
        title_font=dict(size=12, variant="small-caps"),
        xaxis_title_font=dict(size=8, variant="small-caps"),
        yaxis_title_font=dict(size=8, variant="small-caps")
    )
        return fig
    
# @Author: Asta Omarsdottir
# @Email: asta.omarsdottir@gmail.com
# @Date: 2024-12-26
# @Last Modified by:   undefined
# @Last Modified time: 2024-12-26
# @Description: Handles callback for treemap
   
    @app.callback(
            Output('treemap', 'figure'),
            Input('filter-store', 'data')
        )
    def update_treemap(filter_value):
        # Get data for treemap
        treemap_data = get_treemap_data()
        
        # Create treemap
        fig = create_treemap(treemap_data)
        return fig