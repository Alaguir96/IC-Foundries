"""
Main Application
Interactive World Map of Integrated Optical Foundries 2026
"""

import dash
from dash import html, dcc, Input, Output, State, callback_context, dash_table, no_update
import dash_bootstrap_components as dbc
import pandas as pd
import json
from typing import List, Dict

# Import custom modules
from data_ingestion import load_foundry_data
from geocoding import geocode_dataframe
from map_view import create_scatter_map, create_heatmap
from ui_components import (
    create_sidebar, create_foundry_popup, create_comparison_panel,
    create_main_layout, create_stats_display
)

# Initialize Dash app with dark theme
app = dash.Dash(
    __name__,
    external_stylesheets=[
        dbc.themes.DARKLY,
        'https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap'
    ],
    suppress_callback_exceptions=True
)

# Custom CSS
app.index_string = '''
<!DOCTYPE html>
<html>
    <head>
        {%metas%}
        <title>Integrated Optical Foundries 2026</title>
        {%favicon%}
        {%css%}
        <style>
            * {
                margin: 0;
                padding: 0;
                box-sizing: border-box;
            }
            
            body {
                font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
                background-color: #0a0a14;
                color: #ffffff;
            }
            
            .app-container {
                display: flex;
                flex-direction: column;
                height: 100vh;
                overflow: hidden;
            }
            
            .app-header {
                background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
                padding: 20px 30px;
                border-bottom: 1px solid rgba(255, 255, 255, 0.1);
                box-shadow: 0 2px 10px rgba(0, 0, 0, 0.3);
            }
            
            .app-title {
                font-size: 28px;
                font-weight: 700;
                margin-bottom: 5px;
                background: linear-gradient(90deg, #4facfe 0%, #00f2fe 100%);
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
            }
            
            .app-subtitle {
                font-size: 14px;
                color: #a0a0a0;
                font-weight: 300;
            }
            
            .main-content {
                display: flex;
                flex: 1;
                overflow: hidden;
                position: relative;
            }
            
            .sidebar {
                width: 320px;
                min-width: 280px;
                max-width: 400px;
                background: #1a1a2e;
                padding: 20px;
                overflow-y: auto;
                border-right: 1px solid rgba(255, 255, 255, 0.1);
                box-shadow: 2px 0 10px rgba(0, 0, 0, 0.2);
                transition: transform 0.3s ease-in-out;
                z-index: 1000;
            }
            
            .sidebar.hidden {
                transform: translateX(-100%);
            }
            
            /* Burger menu button */
            .burger-menu {
                display: none;
                position: fixed;
                top: 20px;
                left: 20px;
                z-index: 1001;
                background: #1a1a2e;
                border: 1px solid rgba(255, 255, 255, 0.2);
                border-radius: 6px;
                padding: 10px;
                cursor: pointer;
                color: #ffffff;
                font-size: 20px;
                box-shadow: 0 2px 10px rgba(0, 0, 0, 0.3);
            }
            
            .burger-menu:hover {
                background: #2a2a3e;
            }
            
            .burger-menu-icon {
                display: flex;
                flex-direction: column;
                gap: 4px;
                width: 24px;
                height: 24px;
            }
            
            .burger-menu-icon span {
                display: block;
                width: 100%;
                height: 2px;
                background: #ffffff;
                transition: all 0.3s ease;
            }
            
            /* Responsive design */
            @media (max-width: 768px) {
                .sidebar {
                    position: fixed;
                    left: 0;
                    top: 0;
                    height: 100vh;
                    width: 280px;
                    max-width: 85vw;
                    transform: translateX(-100%);
                    box-shadow: 4px 0 20px rgba(0, 0, 0, 0.5);
                    z-index: 1000;
                    padding: 15px;
                    overflow-y: auto;
                    overflow-x: hidden;
                }
                
                .sidebar.show {
                    transform: translateX(0);
                }
                
                .burger-menu {
                    display: block;
                }
                
                .app-header {
                    padding-left: 60px;
                    padding-right: 20px;
                    position: relative;
                }
                
                .map-container {
                    width: 100%;
                    margin-left: 0;
                }
                
                .app-title {
                    font-size: 20px;
                }
                
                .app-subtitle {
                    font-size: 12px;
                }
                
                .filter-section {
                    margin-bottom: 15px;
                }
                
                .filter-label {
                    font-size: 11px;
                }
                
                .search-input {
                    padding: 8px;
                    font-size: 13px;
                }
            }
            
            @media (min-width: 769px) and (max-width: 1024px) {
                .sidebar {
                    width: 280px;
                    min-width: 250px;
                }
                
                .burger-menu {
                    display: none;
                }
            }
            
            @media (min-width: 1025px) {
                .burger-menu {
                    display: none;
                }
                
                .sidebar-overlay {
                    display: none !important;
                }
            }
            
            /* Overlay for mobile when sidebar is open */
            .sidebar-overlay {
                display: none;
                position: fixed;
                top: 0;
                left: 0;
                width: 100%;
                height: 100%;
                background: rgba(0, 0, 0, 0.5);
                z-index: 999;
            }
            
            .sidebar-overlay.show {
                display: block;
            }
            
            @media (max-width: 768px) {
                .sidebar-overlay.show {
                    display: block;
                }
            }
            
            .sidebar-header {
                font-size: 18px;
                font-weight: 600;
                margin-bottom: 10px;
                color: #4facfe;
            }
            
            .sidebar-divider {
                border-color: rgba(255, 255, 255, 0.1);
                margin: 15px 0;
            }
            
            .filter-section {
                margin-bottom: 20px;
            }
            
            .filter-label {
                font-size: 12px;
                font-weight: 500;
                color: #a0a0a0;
                margin-bottom: 8px;
                text-transform: uppercase;
                letter-spacing: 0.5px;
            }
            
            .search-input {
                width: 100%;
                padding: 10px;
                background: #ffffff;
                border: 1px solid rgba(255, 255, 255, 0.1);
                border-radius: 6px;
                color: #000000;
                font-size: 14px;
            }
            
            .search-input:focus {
                outline: none;
                border-color: #4facfe;
                box-shadow: 0 0 0 2px rgba(79, 172, 254, 0.2);
            }
            
            .filter-dropdown {
                background: #ffffff;
            }
            
            /* Dash Dropdown styling */
            .filter-dropdown .Select-control,
            .filter-dropdown .Select-input,
            .filter-dropdown .Select-placeholder,
            .filter-dropdown .Select-value-label,
            .filter-dropdown input {
                color: #000000 !important;
                background: #ffffff !important;
            }
            
            .filter-dropdown .Select-menu-outer {
                background: #ffffff !important;
            }
            
            .filter-dropdown .Select-option {
                color: #000000 !important;
                background: #ffffff !important;
            }
            
            .filter-dropdown .Select-option:hover {
                background: #e0e0e0 !important;
            }
            
            /* Additional Dash dropdown styling */
            div[class*="Select"] {
                color: #000000 !important;
            }
            
            div[class*="Select"] input {
                color: #000000 !important;
            }
            
            /* Target Dash dcc.Dropdown specifically */
            #country-filter,
            #tech-filter {
                color: #000000 !important;
            }
            
            #country-filter .Select-value-label,
            #tech-filter .Select-value-label,
            #country-filter input,
            #tech-filter input {
                color: #000000 !important;
            }
            
            .filter-checklist {
                font-size: 13px;
            }
            
            .filter-radio {
                font-size: 13px;
            }
            
            .map-container {
                flex: 1;
                position: relative;
                background: #0a0a14;
            }
            
            .map-graph {
                height: 100%;
                width: 100%;
            }
            
            .stats-header {
                font-size: 14px;
                font-weight: 600;
                margin-bottom: 10px;
                color: #4facfe;
            }
            
            .stats-display {
                font-size: 12px;
                color: #c0c0c0;
            }
            
            .stats-content {
                margin-top: 10px;
            }
            
            .stat-item {
                margin: 5px 0;
                padding: 5px 0;
                border-bottom: 1px solid rgba(255, 255, 255, 0.05);
            }
            
            .export-button {
                width: 100%;
                margin-top: 10px;
            }
            
            .comparison-container {
                position: absolute;
                bottom: 20px;
                left: 20px;
                right: 20px;
                background: rgba(26, 26, 46, 0.95);
                padding: 20px;
                border-radius: 8px;
                border: 1px solid rgba(255, 255, 255, 0.1);
                box-shadow: 0 4px 20px rgba(0, 0, 0, 0.5);
                max-height: 300px;
                overflow-y: auto;
                z-index: 1000;
            }
            
            .comparison-header {
                font-size: 16px;
                font-weight: 600;
                margin-bottom: 15px;
                color: #4facfe;
            }
            
            .comparison-table {
                width: 100%;
                font-size: 12px;
                border-collapse: collapse;
            }
            
            .comparison-table th,
            .comparison-table td {
                padding: 8px 12px;
                text-align: left;
                border-bottom: 1px solid rgba(255, 255, 255, 0.1);
            }
            
            .comparison-table th {
                background: rgba(79, 172, 254, 0.1);
                font-weight: 600;
                color: #4facfe;
            }
            
            .popup-section {
                margin-bottom: 20px;
            }
            
            .popup-section-header {
                font-size: 14px;
                font-weight: 600;
                color: #4facfe;
                margin-bottom: 8px;
            }
            
            .popup-section p {
                font-size: 13px;
                color: #c0c0c0;
                margin: 5px 0;
            }
            
            /* Additional styling for Dash dropdowns - ensure black text */
            .dash-dropdown {
                color: #000000 !important;
            }
            
            /* React-Select component styling */
            .Select-control {
                background-color: #ffffff !important;
                color: #000000 !important;
            }
            
            .Select-input > input {
                color: #000000 !important;
            }
            
            .Select-placeholder,
            .Select-value-label,
            .Select-value {
                color: #000000 !important;
            }
            
            .Select-menu-outer {
                background-color: #ffffff !important;
            }
            
            .Select-option {
                color: #000000 !important;
                background-color: #ffffff !important;
            }
            
            .Select-option:hover,
            .Select-option.is-focused {
                background-color: #e0e0e0 !important;
                color: #000000 !important;
            }
            
            .Select-option.is-selected {
                background-color: #4facfe !important;
                color: #ffffff !important;
            }
        </style>
    </head>
    <body>
        {%app_entry%}
        <footer>
            {%config%}
            {%scripts%}
            {%renderer%}
        </footer>
    </body>
</html>
'''

# Load and prepare data
print("Loading foundry data...")
df = load_foundry_data()
df = geocode_dataframe(df)
print(f"Loaded {len(df)} foundries")

# Create app layout
app.layout = html.Div([
    dcc.Store(id='full-data', data=df.to_dict('records')),
    dcc.Store(id='selected-foundries-store', data=[]),
    dcc.Store(id='filtered-data', data=df.to_dict('records')),
    
    # Header
    html.Div([
        # Burger menu button
        html.Div([
            html.Div([
                html.Span(),
                html.Span(),
                html.Span(),
            ], className="burger-menu-icon"),
        ], id="burger-menu", className="burger-menu", n_clicks=0),
        
        html.H1("Integrated Optical Foundries 2026", className="app-title"),
        html.P("Interactive World Map & Analytics", className="app-subtitle"),
    ], className="app-header"),
    
    # Sidebar overlay (for mobile)
    html.Div(id="sidebar-overlay", className="sidebar-overlay", n_clicks=0),
    
    # Main content with sidebar and map
    html.Div([
        # Sidebar
        html.Div(
            create_sidebar(df).children,
            id="sidebar-container",
            className="sidebar"
        ),
        
        # Map container
        html.Div([
            dcc.Graph(id='world-map', className="map-graph"),
            html.Div(id='comparison-panel', className="comparison-container", style={'display': 'none'}),
        ], className="map-container"),
    ], className="main-content", style={'display': 'flex', 'flex': '1', 'overflow': 'hidden'}),
    
    # Foundry popup
    dbc.Modal(id="foundry-popup-modal", is_open=False),
    
    # Loading indicator
    dcc.Loading(id="loading", type="default", children=html.Div(id="loading-output")),
], className="app-container")


# Callbacks
@app.callback(
    [Output('world-map', 'figure'),
     Output('filtered-data', 'data'),
     Output('stats-display', 'children')],
    [Input('search-input', 'value'),
     Input('country-filter', 'value'),
     Input('tech-filter', 'value'),
     Input('type-filter', 'value'),
     Input('application-filter', 'value'),
     Input('price-range-filter', 'value'),
     Input('lead-time-filter', 'value'),
     Input('color-by', 'value'),
     Input('size-by', 'value'),
     Input('heatmap-toggle', 'value'),
     Input('full-data', 'data')]
)
def update_map(search, countries, techs, types, applications, price_range, max_lead_time, 
               color_by, size_by, heatmap, full_data):
    """Update map based on filters."""
    df_filtered = pd.DataFrame(full_data)
    
    # Apply filters
    if search:
        mask = df_filtered['foundry'].str.contains(search, case=False, na=False)
        df_filtered = df_filtered[mask]
    
    if countries:
        df_filtered = df_filtered[df_filtered['country'].isin(countries)]
    
    if techs:
        df_filtered = df_filtered[df_filtered['tech_category'].isin(techs)]
    
    if types:
        df_filtered = df_filtered[df_filtered['type'].isin(types)]
    
    if applications:
        app_mask = df_filtered['applications'].apply(
            lambda x: any(app in str(x) for app in applications)
        )
        df_filtered = df_filtered[app_mask]
    
    # Apply price range filter
    if price_range and len(price_range) == 2:
        price_min, price_max = price_range
        if 'mpw_price_usd' in df_filtered.columns:
            price_mask = (
                (df_filtered['mpw_price_usd'] >= price_min) & 
                (df_filtered['mpw_price_usd'] <= price_max)
            ) | df_filtered['mpw_price_usd'].isna()
            df_filtered = df_filtered[price_mask]
    
    # Apply lead time filter
    if max_lead_time and max_lead_time < 30:
        if 'lead_time_weeks' in df_filtered.columns:
            lead_time_mask = (
                (df_filtered['lead_time_weeks'] <= max_lead_time) |
                df_filtered['lead_time_weeks'].isna()
            )
            df_filtered = df_filtered[lead_time_mask]
    
    # Create map
    fig = create_scatter_map(df_filtered, color_by=color_by, size_by=size_by)
    
    # Add heatmap if requested
    if heatmap and 'show' in heatmap:
        # Note: Heatmap overlay would require additional implementation
        pass
    
    # Update stats
    stats = create_stats_display(df_filtered)
    
    return fig, df_filtered.to_dict('records'), stats


@app.callback(
    [Output('foundry-popup-modal', 'is_open'),
     Output('foundry-popup-modal', 'children')],
    Input('world-map', 'clickData'),
    State('filtered-data', 'data'),
    prevent_initial_call=True
)
def open_popup(click_data, filtered_data):
    """Handle foundry popup on marker click."""
    if not click_data or not click_data.get('points'):
        return False, []
    
    # Get foundry data from click
    point_data = click_data['points'][0]
    customdata = point_data.get('customdata', [])
    
    if not customdata or len(customdata) < 2:
        return False, []
    
    foundry_nr = customdata[0]
    df = pd.DataFrame(filtered_data)
    
    if df.empty or foundry_nr not in df['nr'].values:
        return False, []
    
    foundry = df[df['nr'] == foundry_nr].iloc[0]
    
    # Create popup content
    technologies = ', '.join(foundry['technologies']) if foundry['technologies'] else 'N/A'
    
    # Format economic data
    def format_currency(value):
        if pd.isna(value) or value == 0:
            return 'N/A'
        return f"${value:,.0f}"
    
    mpw_price = format_currency(foundry.get('mpw_price_usd', 0))
    nre_cost = format_currency(foundry.get('nre_cost_usd', 0))
    setup_cost = format_currency(foundry.get('setup_cost_usd', 0))
    min_order = foundry.get('min_order_qty', 'N/A')
    lead_time = foundry.get('lead_time_weeks', 'N/A')
    capacity = foundry.get('capacity_wafers_month', 'N/A')
    volume_threshold = foundry.get('volume_threshold', 'N/A')
    volume_discount = foundry.get('volume_discount_percent', 'N/A')
    per_unit = format_currency(foundry.get('per_unit_price_usd_per_mm2', 0))
    positioning = foundry.get('market_positioning', 'N/A')
    payment_terms = foundry.get('payment_terms', 'N/A')
    ip_licensing = foundry.get('ip_licensing', 'N/A')
    
    popup_content = [
        dbc.ModalHeader(dbc.ModalTitle(foundry['foundry'])),
        dbc.ModalBody([
            html.Div([
                html.H6("Location", className="popup-section-header"),
                html.P(f"Country: {foundry['country']} ({foundry['country_code']})"),
                html.P(f"Coordinates: {foundry['latitude']:.4f}°, {foundry['longitude']:.4f}°"),
            ], className="popup-section"),
            
            html.Div([
                html.H6("Technology Profile", className="popup-section-header"),
                html.P(f"Category: {foundry['tech_category']}"),
                html.P(f"Substrate: {foundry['substrate']}"),
                html.P(f"Technologies: {technologies}"),
                html.P(f"Wavelength: {foundry['wavelength']}"),
            ], className="popup-section"),
            
            html.Div([
                html.H6("Business Model", className="popup-section-header"),
                html.P(f"Type: {foundry['type']}"),
                html.P(f"Access: {foundry['access']}"),
                html.P(f"Applications: {foundry['applications']}"),
                html.P(f"Market Positioning: {positioning}"),
            ], className="popup-section"),
            
            html.Div([
                html.H6("💰 Pricing & Economics", className="popup-section-header"),
                html.P([
                    html.Strong("MPW Price: "), mpw_price, " per wafer"
                ]),
                html.P([
                    html.Strong("NRE Cost: "), nre_cost
                ]),
                html.P([
                    html.Strong("Setup Cost: "), setup_cost
                ]),
                html.P([
                    html.Strong("Per Unit: "), per_unit, " per mm²"
                ]),
                html.P([
                    html.Strong("Min. Order: "), f"{min_order} wafer(s)"
                ]),
            ], className="popup-section"),
            
            html.Div([
                html.H6("📊 Volume & Capacity", className="popup-section-header"),
                html.P([
                    html.Strong("Capacity: "), f"{capacity} wafers/month"
                ]),
                html.P([
                    html.Strong("Volume Discount: "), f"{volume_discount}% off at {volume_threshold}+ wafers"
                ]),
                html.P([
                    html.Strong("Lead Time: "), f"{lead_time} weeks"
                ]),
            ], className="popup-section"),
            
            html.Div([
                html.H6("📋 Terms & Conditions", className="popup-section-header"),
                html.P([
                    html.Strong("Payment Terms: "), payment_terms
                ]),
                html.P([
                    html.Strong("IP/Licensing: "), ip_licensing
                ]),
            ], className="popup-section"),
        ]),
        dbc.ModalFooter(
            dbc.Button("Close", id="close-popup-btn", className="ms-auto", n_clicks=0)
        ),
    ]
    
    return True, popup_content


@app.callback(
    Output('foundry-popup-modal', 'is_open', allow_duplicate=True),
    Input('close-popup-btn', 'n_clicks'),
    prevent_initial_call=True
)
def close_popup(n_clicks):
    """Close popup when close button is clicked."""
    if n_clicks and n_clicks > 0:
        return False
    return no_update


@app.callback(
    [Output('sidebar-container', 'className'),
     Output('sidebar-overlay', 'className')],
    [Input('burger-menu', 'n_clicks'),
     Input('sidebar-overlay', 'n_clicks')],
    State('sidebar-container', 'className')
)
def toggle_sidebar(burger_clicks, overlay_clicks, current_class):
    """Toggle sidebar visibility on mobile/tablet."""
    ctx = callback_context
    if not ctx.triggered:
        return current_class, "sidebar-overlay"
    
    trigger_id = ctx.triggered[0]['prop_id'].split('.')[0]
    
    # Toggle sidebar
    if 'show' in current_class:
        new_class = current_class.replace(' show', '').strip()
        overlay_class = "sidebar-overlay"
    else:
        new_class = f"{current_class} show".strip()
        overlay_class = "sidebar-overlay show"
    
    return new_class, overlay_class


@app.callback(
    Output('export-btn', 'n_clicks'),
    Input('export-btn', 'n_clicks'),
    State('filtered-data', 'data'),
    prevent_initial_call=True
)
def export_to_csv(n_clicks, filtered_data):
    """Export filtered data to CSV."""
    if n_clicks and filtered_data:
        df = pd.DataFrame(filtered_data)
        filename = 'foundries_export.csv'
        df.to_csv(filename, index=False)
        print(f"Exported {len(df)} foundries to {filename}")
    return 0


if __name__ == '__main__':
    print("\n" + "="*60)
    print("Integrated Optical Foundries 2026 - Interactive Map")
    print("="*60)
    print(f"Loaded {len(df)} foundries from {df['country'].nunique()} countries")
    print("\nStarting server...")
    print("Open http://127.0.0.1:8050 in your browser")
    print("="*60 + "\n")
    
    app.run(debug=True, host='127.0.0.1', port=8050)

