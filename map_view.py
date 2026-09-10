"""
Map View Module
Creates interactive Plotly map visualizations.
"""

import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
from typing import Dict, List, Optional
import numpy as np


# PIXSpain MMCPGI palette (sampled from brand slide):
# Motivation #D87878 | Market #FCCC84 | Competition #C00000
# Proposal #3C5460 | Go-to-Market #FCA818 | Impact #FCF0E4
# Primary brand: Gold #FAAA1E | Burnt #EB5523 | Slate #415569 | Black #000000
COLOR_SCHEME = {
    'type': {
        'Commercial': '#C00000',       # Competition
        'Pilot': '#D87878',            # Motivation
        'R&D': '#FCCC84',              # Market
        'Pilotline': '#FCA818',        # Go-to-Market
        'Research Center': '#3C5460',  # Proposal
        'Unknown': '#FCF0E4',          # Impact
    },
    'tech_category': {
        'SiPh (Silicon Photonics)': '#D87878',  # Motivation
        'InP': '#FCCC84',                       # Market
        'LN (Lithium Niobate)': '#C00000',      # Competition
        'SiN (Silicon Nitride)': '#3C5460',     # Proposal
        'AlN/AlO': '#FCA818',                   # Go-to-Market
        'Hybrid/Multi-platform': '#FCF0E4',     # Impact
    },
    'access': {
        'Open + PDK': '#D87878',                    # Motivation
        'OPEN + PDK': '#D87878',
        'Open': '#FCCC84',                          # Market
        'OPEN': '#FCCC84',
        'MIX': '#FCA818',                           # Go-to-Market
        'Bilateral + PDK': '#3C5460',               # Proposal
        'Bilateral + PDI': '#3C5460',
        'Dedicated Engineering Runs Only': '#C00000',  # Competition
        'Unknown': '#FCF0E4',                       # Impact
        '??': '#FCF0E4',
        '???': '#FCF0E4',
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
            paper_bgcolor='#000000',
            plot_bgcolor='#000000',
            font=dict(color='#FCF0E4'),
        )
        return fig
    
    # Filter data if needed
    plot_df = df.copy()
    
    # Create hover text
    def create_hover_text(row):
        return (
            f"<b>{row['foundry']}</b><br>"
            f"{row['country']} · {row['type']}<br>"
            f"{row['tech_category']}<br>"
            f"<span style='opacity:0.75'>Click for details</span>"
        )
    
    plot_df['hover_text'] = plot_df.apply(create_hover_text, axis=1)
    plot_df['marker_size'] = plot_df.apply(lambda r: get_marker_size(r, size_by), axis=1)
    
    # Get color mapping
    color_map = COLOR_SCHEME.get(color_by, COLOR_SCHEME['type'])
    plot_df['color'] = plot_df[color_by].map(color_map).fillna('#3C5460')
    
    # Highlight selected foundries
    if selected_foundries:
        plot_df['selected'] = plot_df['nr'].isin(selected_foundries)
        plot_df.loc[plot_df['selected'], 'marker_size'] *= 1.5
        plot_df.loc[plot_df['selected'], 'color'] = '#FAAA1E'  # Brand gold for selected
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
    
    # Add a masking line to hide the Morocco–Western Sahara border (best-effort)
    # This draws a thick line colored the same as the land to visually mask the disputed border.
    try:
        mask_lons = [-8.5, -9.0, -10.0, -11.0, -12.0, -13.0, -14.0, -15.5, -16.0]
        mask_lats = [29.0, 28.5, 27.8, 27.0, 26.0, 25.0, 24.0, 23.0, 22.0]
        fig.add_trace(go.Scattergeo(
            lon=mask_lons,
            lat=mask_lats,
            mode='lines',
            hoverinfo='none',
            showlegend=False,
            line=dict(width=8, color='#3C5460')
        ))
    except Exception:
        # If masking fails, continue without stopping the map creation
        pass

    # Update layout
    fig.update_layout(
        title=dict(
            text='Photonic foundries offering MPW services',
            x=0.5,
            y=0.96,
            yanchor='top',
            font=dict(size=16, color='#FCF0E4', family='Sora, Arial')
        ),
        geo=dict(
            projection_type='natural earth',
            showland=True,
            landcolor='#3C5460',
            coastlinecolor='#415569',
            showocean=True,
            oceancolor='#000000',
            showlakes=True,
            lakecolor='#000000',
            showcountries=True,
            countrycolor='#415569',
            bgcolor='#000000',
            lonaxis=dict(range=[-180, 180]),
            lataxis=dict(range=[-90, 90]),
        ),
        paper_bgcolor='#000000',
        plot_bgcolor='#000000',
        font=dict(color='#FCF0E4', family='Arial'),
        height=700,
        margin=dict(l=0, r=0, t=56, b=0),
        legend=dict(
            bgcolor='rgba(60, 84, 96, 0.92)',
            bordercolor='rgba(250, 170, 30, 0.28)',
            borderwidth=1,
            font=dict(color='#FCF0E4', size=11, family='Manrope, Arial'),
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
                marker=dict(size=20, color='#FAAA1E'),
                name=foundry['foundry'],
                showlegend=False,
            ),
            row=1, col=idx+1
        )
    
    fig.update_geos(
        projection_type='natural earth',
        showland=True,
        landcolor='#3C5460',
        bgcolor='#000000',
    )
    
    fig.update_layout(
        title='Foundry Comparison',
        paper_bgcolor='#000000',
        plot_bgcolor='#000000',
        font=dict(color='#FCF0E4'),
        height=400,
    )
    
    return fig

