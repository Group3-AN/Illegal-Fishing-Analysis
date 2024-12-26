from dash import html, dcc
import dash_cytoscape as cyto
from backend.dataserver import preprocess_vessel_cargo_data

# @Author: Asta Omarsdottir
# @Email: asta.omarsdottir@gmail.com
# @Date: 2024-12-01
# @Last Modified by:   undefined
# @Last Modified time: 2024-12-01
# @Description: Creates and handles frontend layout


matched_data = preprocess_vessel_cargo_data()

# Layouten
def create_layout(matched_data):
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
                        # title= "Node-Link Diagram, Fish Delivery Network",
                        className="graph-box",
                        children=[
                            html.H2("Node-Link Diagram, Fish Delivery Network", className="graph-title"),
                            cyto.Cytoscape(
                                    id='cytoscape',
                                    elements=[],  # Dynamic data with callback
                                    style={'width': '95%', 'height': '80%'},
                                    layout={'name': 'cose'},  # Force-directed layout
                                    stylesheet=[
                                        {'selector': 'node[type="delivery"]', 'style': {'background-color': '#FF5733', 'label': 'data(label)'}},
                                        {'selector': 'node[type="fish"]', 'style': {'background-color': '#337AB7', 'label': 'data(label)'}},
                                        {'selector': 'edge', 'style': {'line-color': '#B5B5B5', 'label': 'data(label)'}}
                                    ]
                                )
                        ]
                    ),
                    html.Div(
                        id="graph-container-2", 
                        className="graph-box",
                        children=[
                            html.H2("Oceanus Cargo Analysis Dashboard", className="graph-title"),
                                    dcc.Graph(id='time-series', config={'displayModeBar': False}, style={'width': '95%', 'height': '23%'}),
                                    dcc.Graph(id='decomposition-trend', config={'displayModeBar': False}, style={'width': '95%', 'height': '23%'}),
                                    dcc.Graph(id='decomposition-seasonal', config={'displayModeBar': False}, style={'width': '95%', 'height': '23%'}),
                                    dcc.Graph(id='decomposition-residual', config={'displayModeBar': False}, style={'width': '95%', 'height': '23%'})
                        ]
                    ),
                    html.Div(
                        id="graph-container-3", 
                        className="graph-box",
                        children=[
                            html.H2("Transport Movements Heatmap", className="graph-title"),
                            dcc.Graph(id='heatmap-graph', style={'width': '95%', 'height': '80%'},)
                        ]
                    ),
                    html.Div(
                        id="graph-container-4", 
                        className="graph-box",
                        style={
                            "display": "flex",
                            "flexDirection": "column",  # För vertikal layout
                            "flexGrow": "1",  # Gör att den växer när innehållet växer
                            "height": "100%",  # Gör att den fyller hela föräldraelementet
                        },
                        children=[
                            html.H2("Geospatial analys", className="graph-title"),
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
                        id="graph-container-5", 
                        className="graph-box",
                        children=[
                            html.H2("Vessel and Cargo Association Analysis", className="graph-title"),
                            # Scatter plot of clusters
                            dcc.Graph(id='cluster-plot', config={'displayModeBar': False}, style={'width': '95%', 'height': '80%'},)  
                        ]
                    ),
                    html.Div(
                        id="graph-container-6", 
                        className="graph-box",
                        children=[
                            html.H2("Fish Delivery Anomaly Detection in Oceanus", className="graph-title"),
                            dcc.Graph(id='anomaly-time-series-graph', style={'width': '95%', 'height': '80%'},)
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
                        options=[{'label': f"Cluster {i}", 'value': i} for i in matched_data['cluster'].unique()],
                        value=0,
                        multi=True,
                        placeholder='cargo'
                    ),
                    dcc.Dropdown(
                        id='calendar',
                        options=[
                            {'label': 'date', 'value': 'single'},
                            {'label': 'daterange', 'value': 'range'}
                        ],
                        # value='single',  # Standardalternativ
                        placeholder="Select calendar type"
                    ),
                    html.Div(id="calendar-container"),
                    html.Div(id='output-container'),  # show selected date/daterange 
                    dcc.Store(id='calendar-store', data={})
                ]
            ),
        ]
    ),  
    html.Footer("© 2024 Illegal Fishing Detection Team, Group 3", className="footer"),
])
    
# Anropa funktionen för att skapa layout
layout = create_layout(matched_data)