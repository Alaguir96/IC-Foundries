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

# Initialize Dash app
app = dash.Dash(
    __name__,
    external_stylesheets=[
        dbc.themes.DARKLY,
        'https://fonts.googleapis.com/css2?family=Manrope:wght@400;500;600;700&family=Sora:wght@500;600;700&display=swap'
    ],
    suppress_callback_exceptions=True
)

# Custom CSS — PIXSpain brand, product-style shell
app.index_string = '''
<!DOCTYPE html>
<html>
    <head>
        {%metas%}
        <title>PIXSpain · Photonic Foundries Map</title>
        {%favicon%}
        {%css%}
        <style>
            :root {
                --bg: #000000;
                --surface: #3C5460;
                --surface-2: #415569;
                --gold: #FAAA1E;
                --burnt: #EB5523;
                --cream: #FCF0E4;
                --cream-muted: #C8B8A8;
                --line: rgba(252, 240, 228, 0.12);
                --line-strong: rgba(252, 240, 228, 0.22);
                --radius: 14px;
                --shadow: 0 18px 50px rgba(0, 0, 0, 0.35);
            }

            * { margin: 0; padding: 0; box-sizing: border-box; }

            body {
                font-family: 'Manrope', system-ui, sans-serif;
                background:
                    radial-gradient(1200px 600px at 10% -10%, rgba(250, 170, 30, 0.12), transparent 55%),
                    radial-gradient(900px 500px at 100% 0%, rgba(235, 85, 35, 0.10), transparent 50%),
                    var(--bg);
                color: var(--cream);
                -webkit-font-smoothing: antialiased;
            }

            .app-container {
                display: flex;
                flex-direction: column;
                height: 100vh;
                overflow: hidden;
            }

            .app-header {
                display: flex;
                flex-direction: row;
                align-items: center;
                justify-content: space-between;
                gap: 20px;
                padding: 14px 28px;
                background: linear-gradient(135deg, rgba(60, 84, 96, 0.92), rgba(65, 85, 105, 0.88));
                border-bottom: 1px solid var(--line);
                backdrop-filter: blur(12px);
                position: relative;
            }

            .header-brand {
                display: flex;
                align-items: center;
                gap: 16px;
                min-width: 0;
            }

            .brand-logo-wrap {
                display: flex;
                align-items: center;
                justify-content: center;
                background: transparent;
                border: none;
                border-radius: 0;
                padding: 0;
                flex-shrink: 0;
                box-shadow: none;
            }

            .brand-logo {
                height: 44px;
                width: auto;
                max-width: 240px;
                object-fit: contain;
                display: block;
            }

            .header-copy {
                display: flex;
                flex-direction: column;
                gap: 2px;
                min-width: 0;
            }

            .brand-mark {
                font-family: 'Sora', sans-serif;
                font-size: 11px;
                font-weight: 600;
                letter-spacing: 0.18em;
                text-transform: uppercase;
                color: var(--gold);
                margin: 0;
            }

            .app-title {
                font-family: 'Sora', sans-serif;
                font-size: 22px;
                font-weight: 650;
                letter-spacing: -0.02em;
                margin: 0;
                color: var(--cream);
                background: none;
                -webkit-text-fill-color: unset;
            }

            .app-subtitle {
                font-size: 13px;
                color: var(--cream-muted);
                font-weight: 400;
                margin: 0;
            }

            .app-footer {
                display: flex;
                align-items: center;
                justify-content: center;
                padding: 0;
                background: #000000;
                border-top: 1px solid var(--line);
                flex-shrink: 0;
            }

            .funding-logo {
                width: min(1100px, 100%);
                height: auto;
                max-height: 78px;
                object-fit: contain;
                object-position: center;
                display: block;
                padding: 10px 16px;
            }

            .funding-caption {
                display: none;
            }

            .main-content {
                display: flex;
                flex: 1;
                overflow: hidden;
                position: relative;
            }

            .sidebar {
                width: 340px;
                min-width: 300px;
                max-width: 400px;
                background: linear-gradient(180deg, rgba(60, 84, 96, 0.96), rgba(45, 64, 76, 0.98));
                padding: 22px 20px 28px;
                overflow-y: auto;
                border-right: 1px solid var(--line);
                box-shadow: 8px 0 30px rgba(0, 0, 0, 0.2);
                transition: transform 0.3s ease;
                z-index: 1000;
            }

            .sidebar-intro { margin-bottom: 18px; }

            .sidebar-kicker {
                font-size: 11px;
                font-weight: 600;
                letter-spacing: 0.14em;
                text-transform: uppercase;
                color: var(--gold);
                margin-bottom: 6px;
            }

            .sidebar-header {
                font-family: 'Sora', sans-serif;
                font-size: 20px;
                font-weight: 600;
                color: var(--cream);
                margin: 0 0 6px;
            }

            .sidebar-lead {
                font-size: 13px;
                line-height: 1.45;
                color: var(--cream-muted);
                margin: 0;
            }

            .sidebar.hidden { transform: translateX(-100%); }

            .burger-menu {
                display: none;
                position: fixed;
                top: 16px;
                left: 16px;
                z-index: 1001;
                background: var(--surface);
                border: 1px solid var(--line-strong);
                border-radius: 10px;
                padding: 10px;
                cursor: pointer;
                color: var(--cream);
                box-shadow: var(--shadow);
            }

            .burger-menu:hover { background: var(--surface-2); }

            .burger-menu-icon {
                display: flex;
                flex-direction: column;
                gap: 4px;
                width: 22px;
                height: 18px;
            }

            .burger-menu-icon span {
                display: block;
                width: 100%;
                height: 2px;
                background: var(--cream);
                border-radius: 2px;
                transition: all 0.3s ease;
            }

            @media (max-width: 768px) {
                .sidebar {
                    position: fixed;
                    left: 0;
                    top: 0;
                    height: 100vh;
                    width: 300px;
                    max-width: 88vw;
                    transform: translateX(-100%);
                    box-shadow: 12px 0 40px rgba(0, 0, 0, 0.45);
                    z-index: 1000;
                }
                .sidebar.show { transform: translateX(0); }
                .burger-menu { display: block; }
                .app-header {
                    padding-left: 64px;
                    padding-right: 18px;
                    flex-wrap: wrap;
                }
                .brand-logo-wrap { padding: 0; }
                .brand-logo { height: 34px; max-width: 170px; }
                .map-container { width: 100%; margin-left: 0; }
                .app-title { font-size: 18px; }
                .app-subtitle { font-size: 12px; }
                .funding-logo { max-height: 58px; padding: 8px 10px; }
                .app-footer { padding: 0; }
            }

            @media (min-width: 769px) {
                .burger-menu { display: none; }
                .sidebar-overlay { display: none !important; }
            }

            .sidebar-overlay {
                display: none;
                position: fixed;
                inset: 0;
                background: rgba(0, 0, 0, 0.55);
                z-index: 999;
            }
            .sidebar-overlay.show { display: block; }

            .filter-section { margin-bottom: 18px; }

            .filter-label {
                display: block;
                font-size: 11px;
                font-weight: 600;
                color: var(--cream-muted);
                margin-bottom: 8px;
                text-transform: uppercase;
                letter-spacing: 0.08em;
            }

            .search-input {
                width: 100%;
                padding: 12px 14px;
                background: rgba(252, 240, 228, 0.96);
                border: 1px solid transparent;
                border-radius: 10px;
                color: #111;
                font-size: 14px;
                font-family: inherit;
                transition: border-color 0.2s, box-shadow 0.2s;
            }

            .search-input:focus {
                outline: none;
                border-color: var(--gold);
                box-shadow: 0 0 0 3px rgba(250, 170, 30, 0.28);
            }

            .filter-dropdown .Select-control,
            .filter-dropdown .Select-menu-outer,
            .Select-control {
                background: rgba(252, 240, 228, 0.96) !important;
                border-radius: 10px !important;
                border: none !important;
                min-height: 42px !important;
            }

            .filter-dropdown .Select-placeholder,
            .filter-dropdown .Select-value-label,
            .filter-dropdown input,
            .Select-placeholder,
            .Select-value-label,
            .Select-value,
            .Select-input > input,
            div[class*="Select"],
            div[class*="Select"] input,
            #country-filter,
            #tech-filter,
            #country-filter .Select-value-label,
            #tech-filter .Select-value-label,
            #country-filter input,
            #tech-filter input,
            .dash-dropdown {
                color: #111 !important;
            }

            .Select-option {
                color: #111 !important;
                background: #fff !important;
            }
            .Select-option:hover,
            .Select-option.is-focused {
                background: #f3e7d8 !important;
                color: #111 !important;
            }
            .Select-option.is-selected {
                background: var(--gold) !important;
                color: #111 !important;
            }

            .filter-checklist,
            .filter-radio {
                display: flex;
                flex-direction: column;
                gap: 8px;
                font-size: 13px;
                color: var(--cream);
            }

            .filter-check-label,
            .filter-radio-label {
                display: flex;
                align-items: center;
                gap: 8px;
                padding: 6px 8px;
                border-radius: 8px;
                cursor: pointer;
                transition: background 0.15s;
            }

            .filter-check-label:hover,
            .filter-radio-label:hover {
                background: rgba(252, 240, 228, 0.06);
            }

            .advanced-panel {
                margin: 8px 0 20px;
                border: 1px solid var(--line);
                border-radius: var(--radius);
                background: rgba(0, 0, 0, 0.18);
                overflow: hidden;
            }

            .advanced-summary {
                list-style: none;
                cursor: pointer;
                padding: 12px 14px;
                font-size: 13px;
                font-weight: 600;
                color: var(--cream);
                user-select: none;
            }
            .advanced-summary::-webkit-details-marker { display: none; }
            .advanced-summary::before {
                content: '+';
                display: inline-block;
                width: 1.2em;
                color: var(--gold);
                font-weight: 700;
            }
            details[open] > .advanced-summary::before { content: '–'; }
            .advanced-body { padding: 4px 14px 14px; }

            .stats-panel {
                margin-top: 8px;
                padding-top: 8px;
            }

            .stats-header {
                font-size: 11px;
                font-weight: 600;
                letter-spacing: 0.1em;
                text-transform: uppercase;
                color: var(--gold);
                margin-bottom: 12px;
            }

            .stats-grid {
                display: grid;
                grid-template-columns: 1fr 1fr;
                gap: 10px;
            }

            .stat-card {
                background: rgba(0, 0, 0, 0.22);
                border: 1px solid var(--line);
                border-radius: 12px;
                padding: 12px 12px 10px;
                display: flex;
                flex-direction: column;
                gap: 2px;
            }

            .stat-value {
                font-family: 'Sora', sans-serif;
                font-size: 22px;
                font-weight: 650;
                color: var(--cream);
                line-height: 1.1;
            }

            .stat-label {
                font-size: 11px;
                color: var(--cream-muted);
                letter-spacing: 0.02em;
            }

            .stat-footnote {
                margin-top: 10px;
                font-size: 12px;
                color: var(--cream-muted);
                line-height: 1.4;
            }

            .export-button {
                width: 100%;
                margin-top: 4px;
                border: none !important;
                border-radius: 10px !important;
                background: linear-gradient(135deg, var(--gold), var(--burnt)) !important;
                color: #111 !important;
                font-weight: 700 !important;
                letter-spacing: 0.02em;
                padding: 11px 14px !important;
                box-shadow: 0 8px 24px rgba(235, 85, 35, 0.25);
            }
            .export-button:hover {
                filter: brightness(1.05);
            }

            .map-container {
                flex: 1;
                position: relative;
                background: var(--bg);
            }

            .map-graph {
                height: 100%;
                width: 100%;
            }

            .comparison-container {
                position: absolute;
                bottom: 20px;
                left: 20px;
                right: 20px;
                background: rgba(60, 84, 96, 0.96);
                padding: 18px 20px;
                border-radius: var(--radius);
                border: 1px solid var(--line-strong);
                box-shadow: var(--shadow);
                max-height: 280px;
                overflow-y: auto;
                z-index: 1000;
                backdrop-filter: blur(10px);
            }

            .comparison-header {
                font-family: 'Sora', sans-serif;
                font-size: 15px;
                font-weight: 600;
                margin-bottom: 12px;
                color: var(--gold);
            }

            .comparison-table {
                width: 100%;
                font-size: 12px;
                border-collapse: collapse;
            }
            .comparison-table th,
            .comparison-table td {
                padding: 8px 10px;
                text-align: left;
                border-bottom: 1px solid var(--line);
            }
            .comparison-table th {
                background: rgba(250, 170, 30, 0.12);
                font-weight: 600;
                color: var(--gold);
            }

            .popup-section { margin-bottom: 18px; }
            .popup-section-header {
                font-family: 'Sora', sans-serif;
                font-size: 13px;
                font-weight: 600;
                color: var(--gold);
                margin-bottom: 8px;
                letter-spacing: 0.02em;
            }
            .popup-section p {
                font-size: 14px;
                color: var(--cream);
                margin: 4px 0;
                line-height: 1.45;
            }
            .popup-muted { color: var(--cream-muted) !important; font-size: 13px !important; }
            .popup-disclaimer {
                font-size: 12px !important;
                color: var(--cream-muted) !important;
                margin-top: 8px;
            }
            .popup-badges {
                display: flex;
                flex-wrap: wrap;
                gap: 8px;
                margin-bottom: 18px;
            }
            .popup-badge {
                display: inline-flex;
                align-items: center;
                padding: 5px 10px;
                border-radius: 999px;
                font-size: 12px;
                font-weight: 600;
                background: rgba(250, 170, 30, 0.18);
                color: var(--gold);
                border: 1px solid rgba(250, 170, 30, 0.3);
            }
            .popup-badge-muted {
                background: rgba(252, 240, 228, 0.08);
                color: var(--cream);
                border-color: var(--line);
            }

            .modal-content {
                background: #2a3a46 !important;
                border: 1px solid var(--line-strong) !important;
                border-radius: 16px !important;
                color: var(--cream) !important;
            }
            .modal-header, .modal-footer {
                border-color: var(--line) !important;
            }
            .modal-title {
                font-family: 'Sora', sans-serif !important;
                font-weight: 650 !important;
            }

            .rc-slider-track { background-color: var(--gold) !important; }
            .rc-slider-handle {
                border-color: var(--gold) !important;
                background-color: var(--cream) !important;
                opacity: 1 !important;
            }
            .rc-slider-rail { background-color: rgba(252, 240, 228, 0.18) !important; }
            .rc-slider-mark-text { color: var(--cream-muted) !important; font-size: 11px !important; }
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
        html.Div([
            html.Div([
                html.Span(),
                html.Span(),
                html.Span(),
            ], className="burger-menu-icon"),
        ], id="burger-menu", className="burger-menu", n_clicks=0),

        html.Div([
            html.Div([
                html.Img(
                    src="/assets/pixspain-logo.png?v=3",
                    alt="PIXSpain",
                    className="brand-logo",
                ),
            ], className="brand-logo-wrap"),
            html.Div([
                html.H1("Photonic Foundries Map", className="app-title"),
                html.P("Discover MPW partners worldwide", className="app-subtitle"),
            ], className="header-copy"),
        ], className="header-brand"),
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

    # Funding acknowledgement
    html.Footer([
        html.Img(
            src="/assets/funding-partners.png?v=2",
            alt="Co-funded by the European Union, Chips JU, NextGenerationEU, "
                "Ministerio para la Transformación Digital y de la Función Pública, "
                "and Plan de Recuperación, Transformación y Resiliencia",
            className="funding-logo",
        ),
    ], className="app-footer"),
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
    technologies = ', '.join(foundry['technologies']) if foundry['technologies'] else 'Available on request'

    def format_currency(value):
        if pd.isna(value) or value == 0:
            return None
        return f"${value:,.0f}"

    positioning = foundry.get('market_positioning', None)
    payment_terms = foundry.get('payment_terms', None)
    ip_licensing = foundry.get('ip_licensing', None)

    tech_label = foundry['tech_category']
    friendly = {
        'SiPh (Silicon Photonics)': 'Silicon Photonics',
        'LN (Lithium Niobate)': 'Lithium Niobate',
        'SiN (Silicon Nitride)': 'Silicon Nitride',
        'Hybrid/Multi-platform': 'Hybrid / Multi-platform',
    }
    tech_label = friendly.get(tech_label, tech_label)

    detail_rows = []
    if positioning and str(positioning) not in ('N/A', 'nan', ''):
        detail_rows.append(html.P(f"Positioning · {positioning}"))
    if payment_terms and str(payment_terms) not in ('N/A', 'nan', ''):
        detail_rows.append(html.P(f"Payment · {payment_terms}"))
    if ip_licensing and str(ip_licensing) not in ('N/A', 'nan', ''):
        detail_rows.append(html.P(f"IP · {ip_licensing}"))

    popup_content = [
        dbc.ModalHeader(dbc.ModalTitle(foundry['foundry'])),
        dbc.ModalBody([
            html.Div([
                html.Span(foundry['country'], className="popup-badge"),
                html.Span(foundry['type'], className="popup-badge popup-badge-muted"),
            ], className="popup-badges"),

            html.Div([
                html.H6("Technology", className="popup-section-header"),
                html.P(tech_label),
                html.P(f"Substrate · {foundry['substrate']}"),
                html.P(f"Wavelength · {foundry['wavelength']}"),
                html.P(technologies, className="popup-muted"),
            ], className="popup-section"),

            html.Div([
                html.H6("Access & focus", className="popup-section-header"),
                html.P(foundry['access']),
                html.P(f"Applications · {foundry['applications']}"),
            ], className="popup-section"),

            html.Div([
                html.H6("Commercial notes", className="popup-section-header"),
                *detail_rows,
                html.P(
                    "Contact technology@pixspain.es for run details and pricing.",
                    className="popup-muted",
                ),
            ], className="popup-section") if detail_rows else html.Div([
                html.H6("Next step", className="popup-section-header"),
                html.P(
                    "Contact technology@pixspain.es for run details and pricing.",
                    className="popup-muted",
                ),
            ], className="popup-section"),
        ]),
        dbc.ModalFooter(
            dbc.Button("Close", id="close-popup-btn", className="ms-auto export-button", n_clicks=0)
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
    print("PIXSpain · Photonic Foundries Map")
    print("="*60)
    print(f"Loaded {len(df)} foundries across {df['country'].nunique()} countries")
    print("\nStarting server...")
    # Port 8050 is often taken on this machine by AgilentLicenseService
    # (which causes ERR_CONNECTION_RESET in the browser).
    print("Open http://127.0.0.1:8051 in your browser")
    print("="*60 + "\n")
    
    app.run(debug=True, host='127.0.0.1', port=8051)

