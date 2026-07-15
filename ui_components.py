"""
UI Components Module
Dash UI components for the application.
"""

import dash_bootstrap_components as dbc
from dash import html, dcc
import pandas as pd
from typing import List, Dict


def create_sidebar(df: pd.DataFrame) -> html.Div:
    """
    Create the sidebar with filters and controls.
    """
    # Get unique values for filters
    countries = sorted(df['country'].unique())
    tech_categories = sorted(df['tech_category'].unique())
    types = sorted(df['type'].unique())
    applications = sorted(set([app for apps in df['applications'].str.split(', ') 
                               for app in apps if app]))
    
    sidebar = html.Div([
        html.H4("Filters", className="sidebar-header"),
        html.Hr(className="sidebar-divider"),
        
        # Search bar
        html.Div([
            html.Label("Search Foundries", className="filter-label"),
            dcc.Input(
                id='search-input',
                type='text',
                placeholder='Type to search...',
                className='search-input',
                debounce=True,
            ),
        ], className="filter-section"),
        
        # Country filter
        html.Div([
            html.Label("Country / Region", className="filter-label"),
            dcc.Dropdown(
                id='country-filter',
                options=[{'label': country, 'value': country} for country in countries],
                multi=True,
                placeholder='Select countries...',
                className='filter-dropdown',
            ),
        ], className="filter-section"),
        
        # Technology filter
        html.Div([
            html.Label("Technology Category", className="filter-label"),
            dcc.Dropdown(
                id='tech-filter',
                options=[{'label': tech, 'value': tech} for tech in tech_categories],
                multi=True,
                placeholder='Select technologies...',
                className='filter-dropdown',
            ),
        ], className="filter-section"),
        
        # Type filter
        html.Div([
            html.Label("Production Maturity", className="filter-label"),
            dcc.Checklist(
                id='type-filter',
                options=[{'label': t, 'value': t} for t in types],
                value=types,  # All selected by default
                className='filter-checklist',
            ),
        ], className="filter-section"),
        
        # Application filter
        html.Div([
            html.Label("Application Domain", className="filter-label"),
            dcc.Checklist(
                id='application-filter',
                options=[{'label': app, 'value': app} for app in applications],
                value=applications,  # All selected by default
                className='filter-checklist',
            ),
        ], className="filter-section"),
        
        # Price range filter
        html.Div([
            html.Label("MPW Price Range (USD)", className="filter-label"),
            dcc.RangeSlider(
                id='price-range-filter',
                min=0,
                max=50000,
                step=1000,
                marks={0: '$0', 10000: '$10K', 20000: '$20K', 30000: '$30K', 40000: '$40K', 50000: '$50K+'},
                value=[0, 50000],
                tooltip={"placement": "bottom", "always_visible": False},
            ),
        ], className="filter-section"),
        
        # Lead time filter
        html.Div([
            html.Label("Max Lead Time (weeks)", className="filter-label"),
            dcc.Slider(
                id='lead-time-filter',
                min=0,
                max=30,
                step=2,
                marks={0: '0', 10: '10', 20: '20', 30: '30+'},
                value=30,
                tooltip={"placement": "bottom", "always_visible": False},
            ),
        ], className="filter-section"),
        
        # Color by selector
        html.Div([
            html.Label("Color By", className="filter-label"),
            dcc.RadioItems(
                id='color-by',
                options=[
                    {'label': 'Type', 'value': 'type'},
                    {'label': 'Technology', 'value': 'tech_category'},
                    {'label': 'Access Model', 'value': 'access'},
                ],
                value='type',
                className='filter-radio',
            ),
        ], className="filter-section"),
        
        # Size by selector
        html.Div([
            html.Label("Size By", className="filter-label"),
            dcc.RadioItems(
                id='size-by',
                options=[
                    {'label': 'Type', 'value': 'type'},
                    {'label': 'Technology Count', 'value': 'tech_category'},
                    {'label': 'MPW Price', 'value': 'price'},
                ],
                value='type',
                className='filter-radio',
            ),
        ], className="filter-section"),
        
        # Heatmap toggle
        html.Div([
            dbc.Checklist(
                id='heatmap-toggle',
                options=[{'label': 'Show Density Heatmap', 'value': 'show'}],
                value=[],
                className='filter-checklist',
            ),
        ], className="filter-section"),
        
        html.Hr(className="sidebar-divider"),
        
        # Statistics
        html.Div([
            html.H5("Statistics", className="stats-header"),
            html.Div(id='stats-display', className="stats-display"),
        ], className="filter-section"),
        
        # Export button
        html.Div([
            dbc.Button(
                "Export to CSV",
                id='export-btn',
                color='primary',
                className='export-button',
                n_clicks=0,
            ),
        ], className="filter-section"),
        
    ])
    
    return sidebar


def create_foundry_popup(foundry_data: pd.Series) -> html.Div:
    """
    Create a detailed popup panel for a selected foundry.
    """
    technologies = ', '.join(foundry_data['technologies']) if foundry_data['technologies'] else 'N/A'
    
    # Parse schedule
    schedule_str = "N/A"
    if isinstance(foundry_data.get('schedule'), dict):
        schedule_items = []
        for month, value in foundry_data['schedule'].items():
            if value and value not in ['TBA', 'Unknown', 'On-demand', 'Dedicated']:
                schedule_items.append(f"{month}: {value}")
        if schedule_items:
            schedule_str = "; ".join(schedule_items)
        elif 'all' in foundry_data['schedule']:
            schedule_str = foundry_data['schedule']['all']
    
    popup = dbc.Modal([
        dbc.ModalHeader(dbc.ModalTitle(foundry_data['foundry'])),
        dbc.ModalBody([
            html.Div([
                html.H6("Location", className="popup-section-header"),
                html.P(f"Country: {foundry_data['country']} ({foundry_data['country_code']})"),
                html.P(f"Coordinates: {foundry_data['latitude']:.4f}, {foundry_data['longitude']:.4f}"),
            ], className="popup-section"),
            
            html.Div([
                html.H6("Technology Profile", className="popup-section-header"),
                html.P(f"Category: {foundry_data['tech_category']}"),
                html.P(f"Substrate: {foundry_data['substrate']}"),
                html.P(f"Technologies: {technologies}"),
                html.P(f"Wavelength: {foundry_data['wavelength']}"),
            ], className="popup-section"),
            
            html.Div([
                html.H6("Business Model", className="popup-section-header"),
                html.P(f"Type: {foundry_data['type']}"),
                html.P(f"Access: {foundry_data['access']}"),
                html.P(f"Applications: {foundry_data['applications']}"),
            ], className="popup-section"),
            
            html.Div([
                html.H6("Schedule", className="popup-section-header"),
                html.P(schedule_str),
            ], className="popup-section"),
            
        ]),
        dbc.ModalFooter(
            dbc.Button("Close", id="close-popup", className="ms-auto", n_clicks=0)
        ),
    ], id="foundry-popup", is_open=False, size="lg")
    
    return popup


def create_comparison_panel(selected_foundries: List[pd.Series]) -> html.Div:
    """
    Create a comparison panel for selected foundries.
    """
    if not selected_foundries:
        return html.Div()
    
    comparison_rows = []
    for foundry in selected_foundries:
        row = html.Tr([
            html.Td(foundry['foundry']),
            html.Td(foundry['country']),
            html.Td(foundry['type']),
            html.Td(foundry['tech_category']),
            html.Td(foundry['substrate']),
            html.Td(foundry['wavelength']),
            html.Td(foundry['access']),
        ])
        comparison_rows.append(row)
    
    comparison_table = html.Table([
        html.Thead([
            html.Tr([
                html.Th("Foundry"),
                html.Th("Country"),
                html.Th("Type"),
                html.Th("Technology"),
                html.Th("Substrate"),
                html.Th("Wavelength"),
                html.Th("Access"),
            ])
        ]),
        html.Tbody(comparison_rows),
    ], className="comparison-table")
    
    return html.Div([
        html.H5("Comparison", className="comparison-header"),
        comparison_table,
    ], className="comparison-panel")


def create_main_layout() -> html.Div:
    """
    Create the main application layout.
    """
    return html.Div([
        # Header
        html.Div([
            html.H1("Integrated Optical Foundries 2026", className="app-title"),
            html.P("Interactive World Map & Analytics", className="app-subtitle"),
        ], className="app-header"),
        
        # Main content area
        html.Div([
            # Map container
            html.Div([
                dcc.Graph(id='world-map', className="map-graph"),
                dcc.Store(id='selected-foundries', data=[]),
                dcc.Store(id='filtered-data', data=[]),
            ], className="map-container"),
            
            # Comparison panel (hidden by default)
            html.Div(id='comparison-panel', className="comparison-container", style={'display': 'none'}),
        ], className="main-content"),
        
        # Foundry popup
        html.Div(id='foundry-popup-container'),
        
        # Loading indicator
        dcc.Loading(id="loading", type="default", children=html.Div(id="loading-output")),
    ], className="app-container")


def create_stats_display(df: pd.DataFrame) -> html.Div:
    """
    Create statistics display component.
    """
    import pandas as pd
    
    total = len(df)
    by_type = df['type'].value_counts().to_dict()
    by_tech = df['tech_category'].value_counts().to_dict()
    countries = df['country'].nunique()
    
    # Economic statistics
    if 'mpw_price_usd' in df.columns:
        avg_price = df['mpw_price_usd'].mean()
        min_price = df['mpw_price_usd'].min()
        max_price = df['mpw_price_usd'].max()
        
        if pd.notna(avg_price):
            price_stats = [
                html.P(f"Avg. MPW Price: ${avg_price:,.0f}", className="stat-item"),
                html.P(f"Price Range: ${min_price:,.0f} - ${max_price:,.0f}", className="stat-item"),
            ]
        else:
            price_stats = []
    else:
        price_stats = []
    
    if 'lead_time_weeks' in df.columns:
        avg_lead_time = df['lead_time_weeks'].mean()
        if pd.notna(avg_lead_time):
            lead_time_stat = html.P(f"Avg. Lead Time: {avg_lead_time:.1f} weeks", className="stat-item")
        else:
            lead_time_stat = None
    else:
        lead_time_stat = None
    
    stats_items = [
        html.P(f"Total Foundries: {total}", className="stat-item"),
        html.P(f"Countries: {countries}", className="stat-item"),
        html.P(f"Commercial: {by_type.get('Commercial', 0)}", className="stat-item"),
        html.P(f"Pilot: {by_type.get('Pilot', 0)}", className="stat-item"),
        html.P(f"R&D: {by_type.get('R&D', 0)}", className="stat-item"),
    ]
    
    stats_items.extend(price_stats)
    if lead_time_stat:
        stats_items.append(lead_time_stat)
    
    stats = html.Div(stats_items, className="stats-content")
    
    return stats

