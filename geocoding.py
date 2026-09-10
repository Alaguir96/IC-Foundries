"""
Geocoding Module
Handles location geocoding with offline caching.
"""

import json
import os
import hashlib
import random
from typing import Dict, Tuple, Optional
import pandas as pd


# Pre-defined coordinates for major foundry locations
# This serves as an offline cache to avoid API calls
FOUNDRY_COORDINATES = {
    # United States
    'AIM Photonics': (43.0481, -76.1474),  # Rochester, NY
    'Hyperlight': (42.3601, -71.0589),  # Boston, MA area
    'GlobalFoundries': (42.6526, -73.7562),  # Malta, NY
    'TowerSemi.': (32.7767, -96.7970),  # Dallas, TX area
    'Sandia National Lab': (35.0844, -106.6504),  # Albuquerque, NM
    'Skywater Tech.': (44.9778, -93.2650),  # Bloomington, MN
    'Intel Foundry': (45.5152, -122.6784),  # Hillsboro, OR
    
    # Netherlands
    'Aluvia': (52.3700, 4.9050),  # Amsterdam area (offset)
    'LioniX Int.': (52.1350, 6.1960),  # Enschede (offset)
    'Smart Photonics': (51.4430, 5.8000),  # Eindhoven (moved right to fit inside Netherlands)
    
    # Singapore
    'AMF (now GF)': (1.3550, 103.8180),  # Singapore (offset)
    'Compoundtek': (1.6000, 103.8210),  # Singapore (moved further north)
    
    # Germany
    'AMO (GmbH)': (50.7700, 6.5600),  # Aachen (moved east to sit clearly inside Germany)
    'IHP': (52.3400, 13.4000),  # Frankfurt (Oder) (moved west to fit inside Germany)
    'HHI': (52.5100, 13.3200),  # Berlin (more specific)
    
    # Belgium
    'imec': (50.8798, 4.7005),  # Leuven
    
    # China
    'IMECAS': (39.9042, 116.4074),  # Beijing
    'SMIC': (31.2304, 121.4737),  # Shanghai
    'CUMEC': (29.5630, 106.5516),  # Chongqing
    
    # France
    'Leti': (45.1920, 5.7200),  # Grenoble (offset)
    'STMicro': (45.1850, 5.7290),  # Grenoble area (offset)
    
    # Switzerland
    'Ccraft': (46.9500, 6.6400),  # Moved east into Switzerland
    'CSEM': (47.3800, 8.5400),  # Zurich area (offset)
    'LIGENTEC': (47.0000, 8.0000),  # Lausanne area (moved right into Switzerland)
    
    # Canada
    'Applied Nanotools': (53.5461, -113.4938),  # Edmonton
    'C2MI': (45.5050, -73.5650),  # Montreal area (offset)
    'CPFC': (45.4980, -73.5700),  # Montreal area (offset)
    
    # Spain
    'CNM-IMB': (41.3851, 2.1734),  # Barcelona
    
    # United Kingdom
    'Cornerstone': (52.2053, 0.1218),  # Cambridge
    
    # Taiwan
    'TSMC': (24.1500, 120.6700),  # Hsinchu (offset)
    'Win Semi': (24.1450, 120.6770),  # Hsinchu area (offset)
    
    # Finland
    'VTT': (60.1699, 24.9384),  # Espoo
    
    # Austria
    'Silicon Austria Lab': (47.0707, 15.4395),  # Graz
    
    # Denmark
    'SiPhotonIC': (55.6761, 12.2000),  # Moved right to be inside Denmark
    
    # Morocco
    
    # Unknown locations - use country center or major city (with offsets)
    'Luxtelligence': (46.5500, 6.6310),  # Moved down into Switzerland
    'Sivers Photonics': (55.8642, -4.2518),  # Glasgow, Scotland
    'New Origin': (52.3650, 4.9080),  # Assume Netherlands (offset)
    'UMC': (24.1480, 120.6750),  # Assume Taiwan (offset)
    'Fraunhofer': (50.1130, 8.6800),  # Assume Germany/Frankfurt (offset)
    
    # Additional foundries with offsets to prevent overlap
    'Ccraft': (46.9500, 6.6400),  # Moved east into Switzerland
    'CNM-IMB': (41.3880, 2.1700),  # Barcelona (offset)
    'Cornerstone': (52.2080, 0.1200),  # Cambridge (offset)
    'CSEM': (47.3800, 8.5400),  # Zurich (offset)
    'CUMEC': (29.5650, 106.5550),  # Chongqing (offset)
    'Sandia National Lab': (35.0860, -106.6480),  # Albuquerque (offset)
    'Silicon Austria Lab': (47.0720, 15.4370),  # Graz (offset)
    'SiPhotonIC': (55.6761, 12.2000),  # Moved right to be inside Denmark
    'Skywater Tech.': (44.9800, -93.2630),  # Bloomington (offset)
    'VTT': (60.1720, 24.9360),  # Espoo (offset)
}


# Country center coordinates as fallback
COUNTRY_CENTERS = {
    'United States': (39.8283, -98.5795),
    'Netherlands': (52.1326, 5.2913),
    'Singapore': (1.3521, 103.8198),
    'Germany': (51.1657, 10.4515),
    'Belgium': (50.5039, 4.4699),
    'China': (35.8617, 104.1954),
    'France': (46.2276, 2.2137),
    'Switzerland': (46.8182, 8.2275),
    'Canada': (56.1304, -106.3468),
    'Spain': (40.4637, -3.7492),
    'United Kingdom': (55.3781, -3.4360),
    'Taiwan': (23.6978, 120.9605),
    'Finland': (61.9241, 25.7482),
    'Austria': (47.5162, 14.5501),
    'Denmark': (56.2639, 9.5018),
    'Morocco': (31.7917, -7.0926),
    'Unknown': (0, 0),
}


def get_coordinates(foundry_name: str, country: str) -> Tuple[float, float]:
    """
    Get coordinates for a foundry.
    Returns (latitude, longitude).
    """
    # Clean foundry name
    foundry_clean = foundry_name.upper().strip()
    
    # First try exact match
    if foundry_name in FOUNDRY_COORDINATES:
        return FOUNDRY_COORDINATES[foundry_name]
    
    # Try partial match with improved logic
    for key, coords in FOUNDRY_COORDINATES.items():
        key_upper = key.upper().strip()
        # Multiple matching strategies
        if (key_upper in foundry_clean or 
            foundry_clean in key_upper or
            key_upper.replace(' ', '') in foundry_clean.replace(' ', '') or
            foundry_clean.replace(' ', '') in key_upper.replace(' ', '')):
            return coords
    
    # Fall back to country center
    return COUNTRY_CENTERS.get(country, (0, 0))


def add_jitter(lat: float, lon: float, foundry_name: str, index: int) -> Tuple[float, float]:
    """
    Add jitter to coordinates to prevent overlapping markers.
    Uses hash of foundry name for consistent positioning.
    """
    # Create a hash from foundry name for consistent jitter
    name_hash = int(hashlib.md5(foundry_name.encode()).hexdigest()[:8], 16)
    random.seed(name_hash + index)
    
    # Add jitter: ~0.15 to 0.4 degrees (roughly 15-40 km)
    # Larger jitter for world map to prevent overlap
    # Use consistent seed for reproducible positioning
    jitter_lat = random.uniform(-0.25, 0.25)
    jitter_lon = random.uniform(-0.25, 0.25)
    
    return lat + jitter_lat, lon + jitter_lon


def geocode_dataframe(df: pd.DataFrame, use_jitter: bool = True) -> pd.DataFrame:
    """
    Add latitude and longitude columns to DataFrame.
    Adds jitter to prevent overlapping markers.
    """
    coords_list = []
    
    for idx, row in df.iterrows():
        foundry_name = row.get('foundry', '')
        country = row.get('country', 'Unknown')
        
        # Get base coordinates
        base_coords = get_coordinates(foundry_name, country)
        
        # Add jitter to prevent overlap
        if use_jitter:
            final_coords = add_jitter(base_coords[0], base_coords[1], foundry_name, idx)
        else:
            final_coords = base_coords
        
        coords_list.append(final_coords)
    
    df['latitude'] = [c[0] for c in coords_list]
    df['longitude'] = [c[1] for c in coords_list]
    
    return df


def save_coordinates_cache(filepath: str = 'coordinates_cache.json'):
    """Save coordinates cache to file."""
    with open(filepath, 'w') as f:
        json.dump(FOUNDRY_COORDINATES, f, indent=2)


def load_coordinates_cache(filepath: str = 'coordinates_cache.json') -> Dict:
    """Load coordinates cache from file."""
    if os.path.exists(filepath):
        with open(filepath, 'r') as f:
            return json.load(f)
    return {}


if __name__ == '__main__':
    # Test geocoding
    from data_ingestion import load_foundry_data
    
    df = load_foundry_data()
    df = geocode_dataframe(df)
    print(f"Geocoded {len(df)} foundries")
    print(df[['foundry', 'country', 'latitude', 'longitude']].head(10))

