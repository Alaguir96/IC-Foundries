"""
UI Components Module
Dash UI components for the application.
"""

import dash_bootstrap_components as dbc
from dash import html, dcc
import pandas as pd
from typing import List, Dict


def _friendly_tech_label(tech: str) -> str:
    """Shorten technical category names for the UI."""
    mapping = {
        'SiPh (Silicon Photonics)': 'Silicon Photonics',
        'LN (Lithium Niobate)': 'Lithium Niobate',
        'SiN (Silicon Nitride)': 'Silicon Nitride',
        'Hybrid/Multi-platform': 'Hybrid / Multi-platform',
    }
    return mapping.get(tech, tech)


def create_sidebar(df: pd.DataFrame) -> html.Div:
    """
    Create the sidebar with filters and controls.
    """
    countries = sorted(df['country'].unique())
    tech_categories = sorted(df['tech_category'].unique())
    types = sorted(df['type'].unique())
    applications = sorted(set([
        app for apps in df['applications'].str.split(', ')
        for app in apps if app
    ]))

    sidebar = html.Div([
        html.Div([
            html.P("Explore", className="sidebar-kicker"),
            html.H4("Find a foundry", className="sidebar-header"),
            html.P(
                "Filter the map by location, technology, and readiness.",
                className="sidebar-lead",
            ),
        ], className="sidebar-intro"),

        html.Div([
            html.Label("Search", className="filter-label"),
            dcc.Input(
                id='search-input',
                type='text',
                placeholder='Search by foundry name…',
                className='search-input',
                debounce=True,
            ),
        ], className="filter-section"),

        html.Div([
            html.Label("Location", className="filter-label"),
            dcc.Dropdown(
                id='country-filter',
                options=[{'label': country, 'value': country} for country in countries],
                multi=True,
                placeholder='All countries',
                className='filter-dropdown',
            ),
        ], className="filter-section"),

        html.Div([
            html.Label("Technology", className="filter-label"),
            dcc.Dropdown(
                id='tech-filter',
                options=[
                    {'label': _friendly_tech_label(tech), 'value': tech}
                    for tech in tech_categories
                ],
                multi=True,
                placeholder='All platforms',
                className='filter-dropdown',
            ),
        ], className="filter-section"),

        html.Div([
            html.Label("Maturity", className="filter-label"),
            dcc.Checklist(
                id='type-filter',
                options=[{'label': t, 'value': t} for t in types],
                value=types,
                className='filter-checklist',
                inputClassName='filter-check-input',
                labelClassName='filter-check-label',
            ),
        ], className="filter-section"),

        html.Div([
            html.Label("Applications", className="filter-label"),
            dcc.Checklist(
                id='application-filter',
                options=[{'label': app, 'value': app} for app in applications],
                value=applications,
                className='filter-checklist',
                inputClassName='filter-check-input',
                labelClassName='filter-check-label',
            ),
        ], className="filter-section"),

        html.Details([
            html.Summary("More filters & display", className="advanced-summary"),
            html.Div([
                html.Div([
                    html.Label("Budget range (USD)", className="filter-label"),
                    dcc.RangeSlider(
                        id='price-range-filter',
                        min=0,
                        max=50000,
                        step=1000,
                        marks={0: '$0', 25000: '$25K', 50000: '$50K+'},
                        value=[0, 50000],
                        tooltip={"placement": "bottom", "always_visible": False},
                        className="filter-slider",
                    ),
                ], className="filter-section"),

                html.Div([
                    html.Label("Maximum lead time", className="filter-label"),
                    dcc.Slider(
                        id='lead-time-filter',
                        min=0,
                        max=30,
                        step=2,
                        marks={0: 'Any', 15: '15 wks', 30: '30+'},
                        value=30,
                        tooltip={"placement": "bottom", "always_visible": False},
                        className="filter-slider",
                    ),
                ], className="filter-section"),

                html.Div([
                    html.Label("Colour markers by", className="filter-label"),
                    dcc.RadioItems(
                        id='color-by',
                        options=[
                            {'label': 'Maturity', 'value': 'type'},
                            {'label': 'Technology', 'value': 'tech_category'},
                            {'label': 'Access', 'value': 'access'},
                        ],
                        value='type',
                        className='filter-radio',
                        inputClassName='filter-radio-input',
                        labelClassName='filter-radio-label',
                    ),
                ], className="filter-section"),

                html.Div([
                    html.Label("Size markers by", className="filter-label"),
                    dcc.RadioItems(
                        id='size-by',
                        options=[
                            {'label': 'Maturity', 'value': 'type'},
                            {'label': 'Technology breadth', 'value': 'tech_category'},
                            {'label': 'Price', 'value': 'price'},
                        ],
                        value='type',
                        className='filter-radio',
                        inputClassName='filter-radio-input',
                        labelClassName='filter-radio-label',
                    ),
                ], className="filter-section"),

                html.Div([
                    dbc.Checklist(
                        id='heatmap-toggle',
                        options=[{'label': 'Show density overlay', 'value': 'show'}],
                        value=[],
                        className='filter-checklist',
                    ),
                ], className="filter-section"),
            ], className="advanced-body"),
        ], className="advanced-panel"),

        html.Div([
            html.P("At a glance", className="stats-header"),
            html.Div(id='stats-display', className="stats-display"),
        ], className="stats-panel"),

        html.Div([
            dbc.Button(
                "Download results",
                id='export-btn',
                color='primary',
                className='export-button',
                n_clicks=0,
            ),
        ], className="filter-section export-section"),

    ])

    return sidebar


def create_foundry_popup(foundry_data: pd.Series) -> html.Div:
    """
    Create a detailed popup panel for a selected foundry.
    """
    technologies = ', '.join(foundry_data['technologies']) if foundry_data['technologies'] else 'N/A'

    schedule_str = "On request"
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
                html.Span(foundry_data['country'], className="popup-badge"),
                html.Span(foundry_data['type'], className="popup-badge popup-badge-muted"),
            ], className="popup-badges"),

            html.Div([
                html.H6("Technology", className="popup-section-header"),
                html.P(_friendly_tech_label(foundry_data['tech_category'])),
                html.P(f"Substrate · {foundry_data['substrate']}"),
                html.P(f"Wavelength · {foundry_data['wavelength']}"),
                html.P(technologies, className="popup-muted"),
            ], className="popup-section"),

            html.Div([
                html.H6("Access", className="popup-section-header"),
                html.P(foundry_data['access']),
                html.P(f"Focus · {foundry_data['applications']}"),
            ], className="popup-section"),

            html.Div([
                html.H6("Schedule", className="popup-section-header"),
                html.P(schedule_str),
            ], className="popup-section"),

            html.P(
                "Indicative MPW pricing may vary by run and design.",
                className="popup-disclaimer",
            ),
        ]),
        dbc.ModalFooter(
            dbc.Button("Close", id="close-popup", className="ms-auto popup-close-btn", n_clicks=0)
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
            html.Td(_friendly_tech_label(foundry['tech_category'])),
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
                html.Th("Maturity"),
                html.Th("Technology"),
                html.Th("Substrate"),
                html.Th("Wavelength"),
                html.Th("Access"),
            ])
        ]),
        html.Tbody(comparison_rows),
    ], className="comparison-table")

    return html.Div([
        html.H5("Compare foundries", className="comparison-header"),
        comparison_table,
    ], className="comparison-panel")


def create_main_layout() -> html.Div:
    """
    Create the main application layout.
    """
    return html.Div([
        html.Div([
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

        html.Div([
            html.Div([
                dcc.Graph(id='world-map', className="map-graph"),
                dcc.Store(id='selected-foundries', data=[]),
                dcc.Store(id='filtered-data', data=[]),
            ], className="map-container"),
            html.Div(id='comparison-panel', className="comparison-container", style={'display': 'none'}),
        ], className="main-content"),

        html.Div(id='foundry-popup-container'),
        dcc.Loading(id="loading", type="default", children=html.Div(id="loading-output")),

        html.Footer([
            html.Img(
                src="/assets/funding-partners.png?v=2",
                alt="Funding partners",
                className="funding-logo",
            ),
        ], className="app-footer"),
    ], className="app-container")


def create_stats_display(df: pd.DataFrame) -> html.Div:
    """
    Create a compact, readable statistics strip.
    """
    total = len(df)
    countries = df['country'].nunique()
    by_type = df['type'].value_counts().to_dict()

    cards = [
        html.Div([
            html.Span(str(total), className="stat-value"),
            html.Span("Foundries", className="stat-label"),
        ], className="stat-card"),
        html.Div([
            html.Span(str(countries), className="stat-value"),
            html.Span("Countries", className="stat-label"),
        ], className="stat-card"),
        html.Div([
            html.Span(str(by_type.get('Commercial', 0)), className="stat-value"),
            html.Span("Commercial", className="stat-label"),
        ], className="stat-card"),
        html.Div([
            html.Span(str(by_type.get('Pilot', 0) + by_type.get('Pilotline', 0)), className="stat-value"),
            html.Span("Pilot lines", className="stat-label"),
        ], className="stat-card"),
    ]

    def _scalar(value):
        if isinstance(value, pd.Series):
            value = value.dropna()
            return value.iloc[0] if len(value) else None
        return value

    extras = []
    if 'mpw_price_usd' in df.columns:
        avg_price = _scalar(df['mpw_price_usd'].mean())
        if avg_price is not None and pd.notna(avg_price):
            extras.append(
                html.P(
                    f"Typical MPW from about ${float(avg_price):,.0f}",
                    className="stat-footnote",
                )
            )

    if 'lead_time_weeks' in df.columns:
        avg_lead_time = _scalar(df['lead_time_weeks'].mean())
        if avg_lead_time is not None and pd.notna(avg_lead_time):
            extras.append(
                html.P(
                    f"Average lead time · {float(avg_lead_time):.0f} weeks",
                    className="stat-footnote",
                )
            )

    return html.Div([
        html.Div(cards, className="stats-grid"),
        *extras,
    ], className="stats-content")
