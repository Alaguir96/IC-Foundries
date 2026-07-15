"""
Map View Module
Creates interactive Plotly map visualizations.
"""

import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
from typing import Dict, List, Optional
import numpy as np


# Color scheme for different categories
COLOR_SCHEME = {
    'type': {
        'Commercial': '#2E86AB',  # Blue
        'Pilot': '#A23B72',  # Purple
        'R&D': '#F18F01',  # Orange
        'Pilotline': '#C73E1D',  # Red
        'Unknown': '#6C757D',  # Gray
    },
    'tech_category': {
        'SiPh (Silicon Photonics)': '#1f77b4',
        'InP': '#ff7f0e',
        'LN (Lithium Niobate)': '#2ca02c',
        'SiN (Silicon Nitride)': '#d62728',
        'AlN/AlO': '#9467bd',
        'Hybrid/Multi-platform': '#8c564b',
    },
    'access': {
        'Open + PDK': '#28a745',
        'OPEN + PDK': '#28a745',
        'Open': '#17a2b8',
        'OPEN': '#17a2b8',
        'MIX': '#ffc107',
        'Bilateral + PDK': '#6c757d',
        'Bilateral + PDI': '#6c757d',
        'Dedicated Engineering Runs Only': '#dc3545',
        'Unknown': '#6c757d',
        '??': '#6c757d',
        '???': '#6c757d',
    }
}


def get_marker_size(row: pd.Series, size_by: str = 'type') -> float:
    """
    Calculate marker size based on selected attribute.
    """
    base_size = 8
    
    if size_by == 'type':
        size_map = {
            'Commercial': 15,
            'Pilot': 12,
            'R&D': 10,
            'Pilotline': 12,
            'Unknown': 8,
        }
        return size_map.get(row['type'], base_size)
    
    elif size_by == 'tech_category':
        # Count number of technologies
        tech_count = len(row['technologies']) if row['technologies'] else 1
        return base_size + (tech_count * 2)
    
    elif size_by == 'price':
        # Size by MPW price
        mpw_price = row.get('mpw_price_usd', 0)
        if pd.notna(mpw_price) and mpw_price > 0:
            # Scale price to marker size (8-25 range)
            # Assuming price range 0-50000
            normalized = min(mpw_price / 50000, 1.0)
            return base_size + (normalized * 17)  # 8 to 25
        return base_size
    
    return base_size


def create_scatter_map(df: pd.DataFrame, 
                       color_by: str = 'type',
                       size_by: str = 'type',
                       selected_foundries: Optional[List[int]] = None) -> go.Figure:
    """
    Create an interactive scatter map of foundries.
    
    Parameters:
    -----------
    df : pd.DataFrame
        Foundry data with latitude, longitude columns
    color_by : str
        Column to color markers by ('type', 'tech_category', 'access')
    size_by : str
        Column to size markers by ('type', 'tech_category')
    selected_foundries : List[int], optional
        List of foundry numbers to highlight
    """
    
    # Handle empty dataframe
    if df.empty:
        # Return empty map
        fig = go.Figure()
        fig.update_layout(
            title='No foundries match the selected filters',
            geo=dict(projection_type='natural earth'),
            paper_bgcolor='rgb(10, 10, 20)',
            plot_bgcolor='rgb(10, 10, 20)',
            font=dict(color='white'),
        )
        return fig
    
    # Filter data if needed
    plot_df = df.copy()
    
    # Create hover text
    def create_hover_text(row):
        tech_str = ', '.join(row['technologies']) if row['technologies'] else 'N/A'
        
        # Format pricing
        mpw_price = row.get('mpw_price_usd', 0)
        if pd.notna(mpw_price) and mpw_price > 0:
            price_str = f"${mpw_price:,.0f}/wafer"
        else:
            price_str = "N/A"
        
        lead_time = row.get('lead_time_weeks', 'N/A')
        if pd.notna(lead_time) and lead_time != 'N/A':
            lead_str = f"{lead_time} weeks"
        else:
            lead_str = "N/A"
        
        return (
            f"<b>{row['foundry']}</b><br>"
            f"Country: {row['country']}<br>"
            f"Type: {row['type']}<br>"
            f"Technology: {row['tech_category']}<br>"
            f"💰 MPW Price: {price_str}<br>"
            f"⏱️ Lead Time: {lead_str}<br>"
            f"Substrate: {row['substrate']}<br>"
            f"Wavelength: {row['wavelength']}<br>"
            f"Access: {row['access']}<br>"
            f"Click for full details"
        )
    
    plot_df['hover_text'] = plot_df.apply(create_hover_text, axis=1)
    plot_df['marker_size'] = plot_df.apply(lambda r: get_marker_size(r, size_by), axis=1)
    
    # Get color mapping
    color_map = COLOR_SCHEME.get(color_by, COLOR_SCHEME['type'])
    plot_df['color'] = plot_df[color_by].map(color_map).fillna('#6c757d')
    
    # Highlight selected foundries
    if selected_foundries:
        plot_df['selected'] = plot_df['nr'].isin(selected_foundries)
        plot_df.loc[plot_df['selected'], 'marker_size'] *= 1.5
        plot_df.loc[plot_df['selected'], 'color'] = '#FFD700'  # Gold for selected
    else:
        plot_df['selected'] = False
    
    # Create the map
    fig = go.Figure()
    
    # Add markers for each category (for legend grouping)
    for category in plot_df[color_by].unique():
        category_df = plot_df[plot_df[color_by] == category]
        
        # Ensure we have all required columns for customdata
        customdata_cols = ['nr', 'foundry', 'country', 'type', 'tech_category', 
                          'substrate', 'wavelength', 'access', 'technologies_str', 
                          'applications']
        
        # Filter to only columns that exist
        available_cols = [col for col in customdata_cols if col in category_df.columns]
        customdata_values = category_df[available_cols].values
        
        fig.add_trace(go.Scattergeo(
            lon=category_df['longitude'],
            lat=category_df['latitude'],
            text=None,  # Don't show text labels to reduce clutter
            hovertext=category_df['hover_text'],
            hoverinfo='text',
            mode='markers',  # Only markers
            name=category,
            marker=dict(
                size=category_df['marker_size'],
                color=category_df['color'],
                line=dict(width=1, color='white'),
                opacity=0.8,
                sizemode='diameter',
            ),
            customdata=customdata_values,
        ))
    
    # Update layout
    fig.update_layout(
        title=dict(
            text='Integrated Optical Foundries 2026 - World Map',
            x=0.5,
            font=dict(size=24, color='white')
        ),
        geo=dict(
            projection_type='natural earth',
            showland=True,
            landcolor='rgb(30, 30, 30)',
            coastlinecolor='rgb(100, 100, 100)',
            showocean=True,
            oceancolor='rgb(20, 20, 40)',
            showlakes=True,
            lakecolor='rgb(20, 40, 60)',
            showcountries=True,
            countrycolor='rgb(80, 80, 80)',
            bgcolor='rgb(10, 10, 20)',
            lonaxis=dict(range=[-180, 180]),
            lataxis=dict(range=[-90, 90]),
        ),
        paper_bgcolor='rgb(10, 10, 20)',
        plot_bgcolor='rgb(10, 10, 20)',
        font=dict(color='white', family='Arial'),
        height=700,
        margin=dict(l=0, r=0, t=50, b=0),
        legend=dict(
            bgcolor='rgba(30, 30, 30, 0.8)',
            bordercolor='rgba(255, 255, 255, 0.2)',
            borderwidth=1,
            font=dict(color='white', size=12),
            x=0.02,
            y=0.98,
            yanchor='top',
        ),
    )
    
    return fig


def create_heatmap(df: pd.DataFrame) -> go.Figure:
    """
    Create a heatmap overlay showing foundry density.
    """
    # Create density grid
    lat_bins = np.linspace(df['latitude'].min(), df['latitude'].max(), 20)
    lon_bins = np.linspace(df['longitude'].min(), df['longitude'].max(), 20)
    
    # Count foundries in each bin
    density = np.zeros((len(lat_bins)-1, len(lon_bins)-1))
    
    for _, row in df.iterrows():
        lat_idx = np.digitize(row['latitude'], lat_bins) - 1
        lon_idx = np.digitize(row['longitude'], lon_bins) - 1
        if 0 <= lat_idx < len(lat_bins)-1 and 0 <= lon_idx < len(lon_bins)-1:
            density[lat_idx, lon_idx] += 1
    
    fig = go.Figure(data=go.Heatmap(
        z=density,
        x=lon_bins[:-1],
        y=lat_bins[:-1],
        colorscale='Viridis',
        opacity=0.3,
        showscale=True,
    ))
    
    return fig


def create_comparison_view(foundries: List[pd.Series]) -> go.Figure:
    """
    Create a side-by-side comparison view for selected foundries.
    """
    if len(foundries) == 0:
        return go.Figure()
    
    # Create subplot with comparison
    from plotly.subplots import make_subplots
    
    fig = make_subplots(
        rows=1, cols=len(foundries),
        subplot_titles=[f['foundry'] for f in foundries],
        specs=[[{'type': 'scattergeo'} for _ in foundries]]
    )
    
    for idx, foundry in enumerate(foundries):
        fig.add_trace(
            go.Scattergeo(
                lon=[foundry['longitude']],
                lat=[foundry['latitude']],
                mode='markers',
                marker=dict(size=20, color='#FFD700'),
                name=foundry['foundry'],
                showlegend=False,
            ),
            row=1, col=idx+1
        )
    
    fig.update_geos(
        projection_type='natural earth',
        showland=True,
        landcolor='rgb(30, 30, 30)',
        bgcolor='rgb(10, 10, 20)',
    )
    
    fig.update_layout(
        title='Foundry Comparison',
        paper_bgcolor='rgb(10, 10, 20)',
        plot_bgcolor='rgb(10, 10, 20)',
        font=dict(color='white'),
        height=400,
    )
    
    return fig

