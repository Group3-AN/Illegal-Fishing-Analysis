from dash import html, dcc
from config import default_start_date, default_end_date, min_date_allowed

# @Author: Asta Omarsdottir
# @Email: asta.omarsdottir@gmail.com
# @Date: 2024-12-01
# @Last Modified by:   Asta Omarsdottir
# @Last Modified time: 2025-01-08
# @Description: Creates and handles frontend layout

# Layouten
def create_layout():
    return html.Div([
    html.Header(
        className="header",
        children=html.H1("Illegal Fishing Detection Analysis Dashboard")
    ),
    html.Div(
        className="content",
        children=[
            html.Div(
                className="main-content",
                children=[
                    html.Div(
                        id="graph-container-1", 
                        #title= "Node-Link Diagram, Fish Delivery Network with harbor report",
                        className="graph-box",
                        children=[
                            html.H2("Node-Link Diagram, Fish Delivery Network", className="graph-title"),
                            html.Br(),
                            html.Span("Vessels and their Probable Cargos", style={"color": "rgb(42, 63, 95)", "fontSize": "12px", "fontVariant": "small-caps", "font-family": "Verdana"}),
                            html.Div([
                                html.Span("Cargo Report: ", style={"color": "black"}),
                                html.Span("●", style={"color": "black", "fontSize": "20px"}),
                                html.Span("City: ", style={"color": "black"}),
                                html.Span("●", style={"color": "darkred", "fontSize": "20px"}),
                                html.Span("Fish: ", style={"color": "black"}),
                                html.Span("●", style={"color": "green", "fontSize": "20px"}),
                                html.Span("Harbor Vessel: ", style={"color": "black"}),
                                html.Span("●", style={"color": "blue", "fontSize": "20px"}),
                                html.Span("Ping Vessel: ", style={"color": "black"}),
                                html.Span("●", style={"color": "cyan", "fontSize": "20px"}),
                                ], style={"display": "flex", "flexWrap": "wrap", "alignItems": "center"}),
                                html.Div([
                                html.Span("Cargo-City edge: ", style={"color": "black"}),
                                html.Span("──", style={"color": "orange", "fontSize": "20px"}),
                                html.Span("Cargo-Fish edge: ", style={"color": "black"}),
                                html.Span("──", style={"color": "gray", "fontSize": "20px"}),
                                html.Span("Fish-Harbor Vessel edge: ", style={"color": "black"}),
                                html.Span("──", style={"color": "purple", "fontSize": "20px"}),
                                html.Span("Fish-Ping Vessel edge: ", style={"color": "black"}),
                                html.Span("──", style={"color": "yellow", "fontSize": "20px"}),
                                ], style={"display": "flex", "flexWrap": "wrap", "alignItems": "center"}),
                                dcc.Dropdown(
                                id="graph-type",
                                options=[
                                    {"label": "Raw Data", "value": "raw"},
                                    {"label": "Clustered Data", "value": "clustered"}
                                ],
                                value="raw",
                                clearable=False,
                                style={"width": "50%"}
                            ),
                            html.Iframe(
                                id='pyvis-graph',
                                srcDoc="",  # This will be dynamically updated via callback
                                style={'width': '95%', 'height': '80%', 'border': 'none'}
                            )
                        ]
                    ),
                    html.Div(
                        id="graph-container-2", 
                        className="graph-box",
                            children=[
                            html.H2("Geospatial analysis", className="graph-title"),
                            dcc.Graph(
                                id='choropleth-map', 
                                config={"responsive": True}, 
                                style={'flexGrow': "1", 'width': '95%', 'height': '45%'}
                                ),
                            dcc.Graph(
                                id='treemap', 
                                config={"responsive": True}, 
                                style={'flexGrow': "1", 'width': '95%', 'height': '45%'}
                                ),
                        ]
                    ),
                    html.Div(
                        id="graph-container-3", 
                        className="graph-box",
                        children=[
                            html.H2("Transport Movements Heatmap", className="graph-title"),
                            dcc.Graph(id='heatmap-graph', style={'width': '95%', 'height': '90%'},
                            ),
                        ]
                    ),
                    html.Div(
                        id="graph-container-4", 
                        className="graph-box",
                        style={
                            "display": "flex",
                            "flexDirection": "column", 
                            "flexGrow": "1", 
                            "height": "100%",
                        },
                    children=[
                            html.H2("Oceanus Cargo & Vessel Movement Analysis", className="graph-title"),
                            html.Br(),
                            html.Div(
                                dcc.Dropdown(
                                    id="data-toggle",
                                    options=[
                                        {"label": "Cargo Trends", "value": "cargo"},
                                        {"label": "Vessel Movements", "value": "vessels"},
                                        {"label": "Both", "value": "both"}
                                    ],
                                    value="both",
                                    clearable=False,
                                    style={"width": "50%"}
                                ),
                                style={"textAlign": "left", "width": "100%"}
                            ),
                            # Time-series graph for both cargo and vessel data
                            dcc.Graph(id="time-series", config={"displayModeBar": False}, style={"width": "95%", "height": "23%"}),
                            dcc.Graph(id="decomposition-trend", config={"displayModeBar": False}, style={"width": "95%", "height": "23%"}),
                            dcc.Graph(id="decomposition-seasonal", config={"displayModeBar": False}, style={"width": "95%", "height": "23%"}),
                            dcc.Graph(id="decomposition-residual", config={"displayModeBar": False}, style={"width": "95%", "height": "23%"})
                        ]
                    ),
                    html.Div(
                        id="graph-container-5", 
                        className="graph-box",
                        children=[
                            html.H2("Vessel and Cargo Association Analysis", className="graph-title"),
                            # Scatter plot of clusters
                            dcc.Graph(id='cluster-plot', config={'displayModeBar': False}, style={'width': '95%', 'height': '90%'},)  
                        ]
                    ),
                    html.Div(
                        id="graph-container-6", 
                        className="graph-box",
                        children=[
                            html.H2("Fish Delivery Anomaly Detection in Oceanus", className="graph-title"),
                            dcc.Graph(id='anomaly-time-series-graph', style={'width': '95%', 'height': '90%'},)
                        ]
                    ),
                ]
            ),
            html.Div(
                className="filter-container",
                children=[
                    dcc.Store(id='filter-store', data={}),  # store selected filters
                    dcc.Dropdown(
                        id={'type': 'dynamic-dropdown', 'filter': 'companies'}, 
                        options=[], 
                        value=None,
                        multi=True,  # Allow multiple selection
                        placeholder="Company"
                    ),
                    dcc.Dropdown(
                        id={'type': 'dynamic-dropdown', 'filter': 'cities'}, 
                        options=[], 
                        value=None,
                        multi=True,  # Allow multiple selection
                        placeholder="City"
                    ),
                    dcc.Dropdown(
                        id={'type': 'dynamic-dropdown', 'filter': 'ports'},
                        options=[], 
                        value=None,
                        multi=True,  # Allow multiple selection
                        placeholder="Port", 
                    ),                    
                    dcc.Dropdown(
                        id={'type': 'dynamic-dropdown', 'filter': 'regions'},  
                        options=[],
                        value=None,
                        multi=True,  # Allow multiple selection 
                        placeholder="Region", 
                    ),
                    dcc.Dropdown(
                        id={'type': 'dynamic-dropdown', 'filter': 'vessels'}, 
                        options=[],
                        value=None,
                        multi=True,  # Allow multiple selection
                        placeholder="Vessel"
                    ),
                    dcc.Dropdown(
                        id={'type': 'dynamic-dropdown', 'filter': 'species'}, 
                        options=[],
                        value=None,
                        multi=True,  # Allow multiple selection 
                        placeholder="Species", 
                    ),
                    # Dropdown for selecting cargo type (to filter clusters)
                    dcc.Dropdown(
                        id='cargo-selector',
                        #options=[{'label': f"Cluster {i}", 'value': i} for i in matched_data['cluster'].unique()],
                        #value=0,
                        options=[],  # Empty options, will be updated dynamically
                        value=0,  # Default selected value
                        multi=True,
                        placeholder='cargo'
                    ),
                    # Date picker for custom intervals
                    html.Div(
                        dcc.DatePickerRange(
                            id='date-picker',
                            style={'width':'150px'},
                            start_date=default_start_date,  # Default date until updated
                            end_date=default_end_date,    # Default date until updated
                            min_date_allowed=min_date_allowed, # for the VAST challenge
                            display_format='YYYY-MM-DD',
                            clearable=True
                        ),
                    className="date-picker-container",  # Custom class for styling
                    ),
                    # Output container to show the selected dates
                    html.Div(id='output-container', style={'margin-top': '10px'}),
                    # Store to hold the selected calendar data
                    dcc.Store(id='calendar-store', data={}),
                    # Store to hold the selected filtered data
                    dcc.Store(id="processed-data-store", data={}),
                ]
            ),
        ]
    ),  
    html.Footer("© 2025 Illegal Fishing Detection Team, Group 3", className="footer"),
])
    
# Anropa funktionen för att skapa layout
layout = create_layout()