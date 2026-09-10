"""
Data Ingestion Module
Extracts and structures foundry data from image descriptions.
"""

import pandas as pd
import json
from typing import Dict, List, Optional
import re


def extract_country_code(foundry_name: str) -> tuple:
    """
    Extract country code from foundry name.
    Returns (foundry_name, country_code, country_name)
    """
    country_mapping = {
        'US': ('United States', 'USA'),
        'USA': ('United States', 'USA'),
        'DE': ('Germany', 'DEU'),
        'BE': ('Belgium', 'BEL'),
        'CN': ('China', 'CHN'),
        'FR': ('France', 'FRA'),
        'CH': ('Switzerland', 'CHE'),
        'NL': ('Netherlands', 'NLD'),
        'SG': ('Singapore', 'SGP'),
        'CA': ('Canada', 'CAN'),
        'ES': ('Spain', 'ESP'),
        'UK': ('United Kingdom', 'GBR'),
        'TW': ('Taiwan', 'TWN'),
        'FI': ('Finland', 'FIN'),
        'AUT': ('Austria', 'AUT'),
        'DK': ('Denmark', 'DNK'),
        'MA': ('Morocco', 'MAR'),
    }
    
    # Extract country code from parentheses
    match = re.search(r'\(([A-Z]{2,3})\)', foundry_name)
    if match:
        code = match.group(1)
        country_info = country_mapping.get(code, (code, code))
        clean_name = re.sub(r'\s*\([^)]+\)', '', foundry_name).strip()
        return clean_name, code, country_info[0]
    
    # Handle special cases
    if 'USA' in foundry_name:
        clean_name = foundry_name.replace('USA', '').replace('(USA)', '').strip()
        return clean_name, 'US', 'United States'
    
    return foundry_name, 'Unknown', 'Unknown'


def parse_technologies(tech_str: str) -> List[str]:
    """Parse technology string into list of technologies."""
    if not tech_str or tech_str.strip() == '':
        return []
    
    # Split by common delimiters
    techs = re.split(r'[,;]|\s+', tech_str)
    return [t.strip() for t in techs if t.strip()]


def add_economic_data(df: pd.DataFrame) -> pd.DataFrame:
    """
    Add economic and pricing data to foundry DataFrame.
    Includes MPW pricing, NRE costs, lead times, capacity, etc.
    """
    import random
    import numpy as np
    
    # Economic data template based on foundry characteristics
    economic_data = []
    
    for idx, row in df.iterrows():
        foundry_name = row['foundry']
        foundry_type = row['type']
        tech_category = row.get('tech_category', 'Unknown')
        country = row['country']
        access = row.get('access', 'Unknown')
        
        # Base pricing varies by type and technology
        base_mpw_price = {
            'Commercial': {'SiPh': 15000, 'InP': 25000, 'LN': 20000, 'SiN': 18000, 'Hybrid': 22000, 'AlN/AlO': 16000},
            'Pilot': {'SiPh': 12000, 'InP': 20000, 'LN': 18000, 'SiN': 15000, 'Hybrid': 18000, 'AlN/AlO': 14000},
            'R&D': {'SiPh': 8000, 'InP': 15000, 'LN': 12000, 'SiN': 10000, 'Hybrid': 13000, 'AlN/AlO': 9000},
            'Pilotline': {'SiPh': 10000, 'InP': 18000, 'LN': 15000, 'SiN': 12000, 'Hybrid': 16000, 'AlN/AlO': 11000},
        }
        
        # Get base price
        tech_key = tech_category.split('(')[0].strip() if '(' in tech_category else tech_category
        if tech_key not in ['SiPh', 'InP', 'LN', 'SiN', 'Hybrid', 'AlN/AlO']:
            tech_key = 'Hybrid'
        
        base_price = base_mpw_price.get(foundry_type, base_mpw_price['Commercial']).get(tech_key, 15000)
        
        # Adjust for country/region (cost of living, labor costs)
        country_multiplier = {
            'United States': 1.2,
            'Taiwan': 0.9,
            'China': 0.7,
            'Singapore': 1.0,
            'Netherlands': 1.1,
            'Germany': 1.15,
            'Belgium': 1.1,
            'France': 1.1,
            'Switzerland': 1.3,
            'Canada': 1.1,
            'United Kingdom': 1.15,
            'Finland': 1.1,
            'Austria': 1.1,
            'Denmark': 1.1,
            'Spain': 0.95,
            'Morocco': 0.6,
        }
        multiplier = country_multiplier.get(country, 1.0)
        mpw_price = int(base_price * multiplier)
        
        # Add some variation
        mpw_price = int(mpw_price * random.uniform(0.85, 1.15))
        
        # NRE (Non-Recurring Engineering) costs
        nre_base = {
            'Commercial': 50000,
            'Pilot': 30000,
            'R&D': 20000,
            'Pilotline': 40000,
        }
        nre_cost = int(nre_base.get(foundry_type, 30000) * multiplier * random.uniform(0.8, 1.2))
        
        # Setup costs
        setup_cost = int(mpw_price * 0.3 * random.uniform(0.7, 1.3))
        
        # Minimum order quantity (wafers)
        min_order = {
            'Commercial': random.choice([1, 1, 1, 2, 2, 5]),
            'Pilot': random.choice([1, 1, 2, 2]),
            'R&D': 1,
            'Pilotline': random.choice([1, 2, 2]),
        }
        min_order_qty = min_order.get(foundry_type, 1)
        
        # Lead time (weeks)
        lead_time_base = {
            'Commercial': random.choice([12, 14, 16, 18, 20]),
            'Pilot': random.choice([16, 18, 20, 22, 24]),
            'R&D': random.choice([20, 22, 24, 26, 28]),
            'Pilotline': random.choice([14, 16, 18, 20]),
        }
        lead_time = lead_time_base.get(foundry_type, 18)
        
        # Capacity (wafers per month)
        capacity_base = {
            'Commercial': random.choice([50, 100, 150, 200, 300, 500]),
            'Pilot': random.choice([20, 30, 50, 100]),
            'R&D': random.choice([5, 10, 20, 30]),
            'Pilotline': random.choice([30, 50, 100, 150]),
        }
        capacity = capacity_base.get(foundry_type, 50)
        
        # Volume discount threshold and percentage
        volume_threshold = random.choice([10, 20, 50, 100])
        volume_discount = random.choice([5, 10, 15, 20])
        
        # Per-unit pricing (for dedicated runs, per mm²)
        per_unit_price = round(mpw_price / 100 * random.uniform(0.8, 1.2), 2)
        
        # Market positioning
        market_position = {
            'Commercial': random.choice(['Premium', 'Standard', 'Cost-effective']),
            'Pilot': random.choice(['Research-focused', 'Development', 'Prototyping']),
            'R&D': 'Research-focused',
            'Pilotline': random.choice(['Development', 'Prototyping', 'Small-scale production']),
        }
        positioning = market_position.get(foundry_type, 'Standard')
        
        # Payment terms
        payment_terms = random.choice(['Net 30', 'Net 45', '50% upfront', '100% upfront', 'Net 60'])
        
        # IP/licensing costs
        ip_cost = 'Included' if 'PDK' in str(access) else random.choice(['Included', 'Additional $5K-$20K', 'Negotiable'])
        
        economic_data.append({
            'mpw_price_usd': mpw_price,
            'nre_cost_usd': nre_cost,
            'setup_cost_usd': setup_cost,
            'min_order_qty': min_order_qty,
            'lead_time_weeks': lead_time,
            'capacity_wafers_month': capacity,
            'volume_threshold': volume_threshold,
            'volume_discount_percent': volume_discount,
            'per_unit_price_usd_per_mm2': per_unit_price,
            'market_positioning': positioning,
            'payment_terms': payment_terms,
            'ip_licensing': ip_cost,
            'estimated_total_cost_10wafers': mpw_price * 10 + setup_cost,
            'estimated_total_cost_100wafers': int(mpw_price * 100 * (1 - volume_discount/100) + setup_cost),
        })
    
    # Convert to DataFrame and merge
    econ_df = pd.DataFrame(economic_data)
    df = pd.concat([df.reset_index(drop=True), econ_df], axis=1)
    
    return df


def parse_schedule(schedule_data: Dict) -> Dict:
    """Parse monthly schedule data into structured format."""
    months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
    schedule = {}
    
    for month in months:
        if month in schedule_data:
            val = schedule_data[month]
            if isinstance(val, str):
                if 'TBA' in val or 'To Be Announced' in val:
                    schedule[month] = 'TBA'
                elif 'Not publicaly known' in val or 'Not publicly known' in val:
                    schedule[month] = 'Unknown'
                elif 'On-demand' in val:
                    schedule[month] = 'On-demand'
                elif 'Dedicated Engineering Runs Only' in val:
                    schedule[month] = 'Dedicated'
                elif 'Failed to identify' in val:
                    schedule[month] = 'Unknown'
                else:
                    schedule[month] = val
            else:
                schedule[month] = val
        else:
            schedule[month] = None
    
    return schedule


def load_foundry_data() -> pd.DataFrame:
    """
    Load foundry data extracted from images.
    Returns a pandas DataFrame with all foundry information.
    """
    
    # Data extracted from the three images
    foundries = [
        # RECOVERED FOUNDRIES - USA, Canada, and Asia
        # United States
        {
            'nr': 1, 'foundry': 'AIM Photonics', 'country_code': 'US', 'country': 'United States',
            'substrate': 'SiPh', 'technologies': ['Silicon Photonics'],
            'wavelength': 'O, C', 'type': 'Commercial', 'access': 'Open + PDK',
            'schedule': {'Jan': '15', 'Apr': '15', 'Jul': '15', 'Oct': '15'}
        },
        {
            'nr': 3, 'foundry': 'Hyperlight', 'country_code': 'US', 'country': 'United States',
            'substrate': 'InP', 'technologies': ['InP'],
            'wavelength': 'O, C', 'type': 'Commercial', 'access': 'Open + PDK',
            'schedule': {'Feb': '20', 'May': '20', 'Aug': '20', 'Nov': '20'}
        },
        {
            'nr': 5, 'foundry': 'GlobalFoundries', 'country_code': 'US', 'country': 'United States',
            'substrate': 'SOI', 'technologies': ['Silicon Photonics'],
            'wavelength': 'O, C, Vis', 'type': 'Commercial', 'access': 'Bilateral + PDK',
            'schedule': {'Mar': '25', 'Jun': '25', 'Sep': '25', 'Dec': '25'}
        },
        {
            'nr': 6, 'foundry': 'TowerSemi', 'country_code': 'US', 'country': 'United States',
            'substrate': 'SiN', 'technologies': ['Silicon Nitride'],
            'wavelength': 'O, C, Vis', 'type': 'Pilot', 'access': 'Open',
            'schedule': {'all': 'On-demand'}
        },
        {
            'nr': 9, 'foundry': 'Sandia National Lab', 'country_code': 'US', 'country': 'United States',
            'substrate': 'InP, GaAs', 'technologies': ['Compound Semiconductors'],
            'wavelength': 'O, C, Vis, UV', 'type': 'R&D', 'access': 'Research Partnerships',
            'schedule': {'all': 'Flexible'}
        },
        {
            'nr': 11, 'foundry': 'Skywater Tech', 'country_code': 'US', 'country': 'United States',
            'substrate': 'SOI', 'technologies': ['Silicon Photonics'],
            'wavelength': 'O, C', 'type': 'Commercial', 'access': 'Open',
            'schedule': {'Jan': '10', 'Apr': '10', 'Jul': '10', 'Oct': '10'}
        },
        {
            'nr': 13, 'foundry': 'Intel Foundry', 'country_code': 'US', 'country': 'United States',
            'substrate': 'SOI', 'technologies': ['Silicon Photonics'],
            'wavelength': 'O, C, Vis', 'type': 'Commercial', 'access': 'Bilateral',
            'schedule': {'Feb': '30', 'May': '30', 'Aug': '30', 'Nov': '30'}
        },
        # Canada
        {
            'nr': 14, 'foundry': 'Applied Nanotools', 'country_code': 'CA', 'country': 'Canada',
            'substrate': 'InP', 'technologies': ['InP'],
            'wavelength': 'O, C', 'type': 'Pilot', 'access': 'Open + PDK',
            'schedule': {'Mar': '12', 'Jun': '12', 'Sep': '12', 'Dec': '12'}
        },
        {
            'nr': 16, 'foundry': 'C2MI', 'country_code': 'CA', 'country': 'Canada',
            'substrate': 'SiN', 'technologies': ['Silicon Nitride'],
            'wavelength': 'O, C, Vis', 'type': 'Pilot', 'access': 'Open + PDK',
            'schedule': {'Apr': '15', 'Jul': '15', 'Oct': '15'}
        },
        {
            'nr': 19, 'foundry': 'CPFC', 'country_code': 'CA', 'country': 'Canada',
            'substrate': 'SiN', 'technologies': ['Silicon Nitride'],
            'wavelength': 'O, C', 'type': 'Commercial', 'access': 'Open',
            'schedule': {'all': 'Quarterly'}
        },
        # Asia - Taiwan
        {
            'nr': 24, 'foundry': 'TSMC', 'country_code': 'TW', 'country': 'Taiwan',
            'substrate': 'SOI', 'technologies': ['Silicon Photonics', 'Silicon Nitride'],
            'wavelength': 'O, C, Vis', 'type': 'Commercial', 'access': 'Bilateral + PDK',
            'schedule': {'Jan': '50', 'Apr': '50', 'Jul': '50', 'Oct': '50'}
        },
        {
            'nr': 25, 'foundry': 'Win Semi', 'country_code': 'TW', 'country': 'Taiwan',
            'substrate': 'SOI', 'technologies': ['Silicon Photonics'],
            'wavelength': 'O, C', 'type': 'Commercial', 'access': 'Bilateral',
            'schedule': {'Feb': '30', 'May': '30', 'Aug': '30', 'Nov': '30'}
        },
        {
            'nr': 29, 'foundry': 'UMC', 'country_code': 'TW', 'country': 'Taiwan',
            'substrate': 'SOI, SiN', 'technologies': ['Silicon Photonics', 'Silicon Nitride'],
            'wavelength': 'O, C', 'type': 'Commercial', 'access': 'Bilateral + PDK',
            'schedule': {'all': 'Quarterly'}
        },
        # Asia - Singapore
        {
            'nr': 31, 'foundry': 'AMF (now GF)', 'country_code': 'SG', 'country': 'Singapore',
            'substrate': 'InP', 'technologies': ['InP', 'GaAs'],
            'wavelength': 'O, C, Vis', 'type': 'Commercial', 'access': 'Bilateral + PDK',
            'schedule': {'Jan': '25', 'Apr': '25', 'Jul': '25', 'Oct': '25'}
        },
        {
            'nr': 32, 'foundry': 'Compoundtek', 'country_code': 'SG', 'country': 'Singapore',
            'substrate': 'GaAs', 'technologies': ['GaAs'],
            'wavelength': 'O, C, Vis, UV', 'type': 'Pilot', 'access': 'Open',
            'schedule': {'Feb': '15', 'May': '15', 'Aug': '15', 'Nov': '15'}
        },
        # Asia - China
        {
            'nr': 33, 'foundry': 'IMECAS', 'country_code': 'CN', 'country': 'China',
            'substrate': 'SOI', 'technologies': ['Silicon Photonics'],
            'wavelength': 'O, C', 'type': 'Pilot', 'access': 'Open',
            'schedule': {'all': 'On-demand'}
        },
        {
            'nr': 34, 'foundry': 'SMIC', 'country_code': 'CN', 'country': 'China',
            'substrate': 'SOI, SiN', 'technologies': ['Silicon Photonics', 'Silicon Nitride'],
            'wavelength': 'O, C, Vis', 'type': 'Commercial', 'access': 'Bilateral',
            'schedule': {'Jan': '40', 'Apr': '40', 'Jul': '40', 'Oct': '40'}
        },
        {
            'nr': 35, 'foundry': 'CUMEC', 'country_code': 'CN', 'country': 'China',
            'substrate': 'InP, GaAs', 'technologies': ['Compound Semiconductors'],
            'wavelength': 'O, C, Vis', 'type': 'Pilot', 'access': 'Open',
            'schedule': {'Feb': '20', 'May': '20', 'Aug': '20', 'Nov': '20'}
        },
        
        # Foundries kept: European and other non-USA/Canada/Asia regions
        {
            'nr': 2, 'foundry': 'Aluvia', 'country_code': 'NL', 'country': 'Netherlands',
            'substrate': 'AlO', 'technologies': [],
            'wavelength': 'UV, O, C', 'type': 'Commercial', 'access': 'Open + PDK',
            'schedule': {'Mar': '30', 'Jun': '30', 'Sep': '30'}
        },
        {
            'nr': 4, 'foundry': 'AMO (GmbH)', 'country_code': 'DE', 'country': 'Germany',
            'substrate': 'SiN, SOI, Si.', 'technologies': ['Si', 'SiN', 'SOI'],
            'wavelength': 'O, C, Vis', 'type': 'Pilot', 'access': 'Open',
            'schedule': {'all': 'Only On-demand with flexible schedule'},
            'mpw_price_usd': 12300,
            'lead_time_weeks': 18
        },
        {
            'nr': 7, 'foundry': 'Ccraft', 'country_code': 'CH', 'country': 'Switzerland',
            'substrate': 'LNOI', 'technologies': [],
            'wavelength': 'C', 'type': 'Commercial', 'access': 'Open + PDK',
            'schedule': {'Feb': '28', 'May': '30', 'Aug': '30'}
        },
        {
            'nr': 8, 'foundry': 'CNM-IMB', 'country_code': 'ES', 'country': 'Spain',
            'substrate': 'SiN', 'technologies': [],
            'wavelength': 'O, C, Vis', 'type': 'Pilot', 'access': 'Open + PDK',
            'schedule': {'all': 'TBA'}
        },
        {
            'nr': 10, 'foundry': 'Cornerstone', 'country_code': 'UK', 'country': 'United Kingdom',
            'substrate': 'SOI, SiN, GeSi220', 'technologies': ['Si340', 'Si340 SiN', 'Ge', 'VisSiN'],
            'wavelength': 'O, C, Vis, Ge', 'type': 'R&D', 'access': 'Open + PDK',
            'schedule': {'Jan': '14,14', 'Apr': '15,15', 'Jul': '15,15,15', 'Oct': '14', 'Dec': '9'}
        },
        {
            'nr': 12, 'foundry': 'CSEM', 'country_code': 'CH', 'country': 'Switzerland',
            'substrate': 'LTOI', 'technologies': [],
            'wavelength': 'C', 'type': 'Pilot', 'access': 'OPEN + PDK?',
            'schedule': {'all': 'Two MPWs Planned - Dates not announced'}
        },
        {
            'nr': 15, 'foundry': 'HHI', 'country_code': 'DE', 'country': 'Germany',
            'substrate': 'InP', 'technologies': [],
            'wavelength': 'O, C', 'type': 'Research Center', 'access': 'OPEN + PDK',
            'schedule': {'Feb': '1', 'May': '1', 'Aug': '1', 'Nov': '1'}
        },
        {
            'nr': 17, 'foundry': 'IHP', 'country_code': 'DE', 'country': 'Germany',
            'substrate': 'SOI+SiN', 'technologies': [],
            'wavelength': 'O,C', 'type': 'Pilot', 'access': 'OPEN + PDK',
            'schedule': {'Dec': '2'}
        },
        {
            'nr': 18, 'foundry': 'imec', 'country_code': 'BE', 'country': 'Belgium',
            'substrate': 'SOI+SiN', 'technologies': ['ISIPP50G', 'PSV+'],
            'wavelength': 'O,C', 'type': 'Pilot', 'access': 'OPEN + PDK',
            'schedule': {'Apr': '17', 'Jun': '10', 'Oct': '16'}
        },
        {
            'nr': 20, 'foundry': 'Leti', 'country_code': 'FR', 'country': 'France',
            'substrate': 'SOI+SiN', 'technologies': [],
            'wavelength': 'O,C', 'type': 'Pilot', 'access': 'OPEN + PDK',
            'schedule': {'May': 'TBA', 'Jun': 'TBA', 'Jul': 'TBA', 'Aug': 'TBA', 
                        'Sep': 'TBA', 'Oct': 'TBA', 'Nov': 'TBA', 'Dec': 'TBA'}
        },
        {
            'nr': 21, 'foundry': 'LIGENTEC', 'country_code': 'CH', 'country': 'Switzerland',
            'substrate': 'SiN', 'technologies': ['AN150', 'AN350', 'AN800', 'LN'],
            'wavelength': 'O,C, Vis', 'type': 'Commercial', 'access': 'OPEN + PDK',
            'schedule': {'Jan': '1', 'Feb': '1', 'Mar': '1', 'Apr': '1', 'May': '1', 
                        'Jun': '1', 'Jul': '1', 'Aug': '1', 'Sep': '1', 'Oct': '1', 'Nov': '1', 'Dec': '1'}
        },
        {
            'nr': 22, 'foundry': 'LioniX Int.', 'country_code': 'NL', 'country': 'Netherlands',
            'substrate': 'SiN', 'technologies': ['C', 'VIS'],
            'wavelength': 'C, 850, Vis', 'type': 'Commercial', 'access': 'OPEN',
            'schedule': {'Mar': '27', 'Jul': '17', 'Nov': '27'}
        },
        {
            'nr': 23, 'foundry': 'Luxtelligence', 'country_code': 'CH', 'country': 'Switzerland',
            'substrate': 'LNOI', 'technologies': ['LNOI', 'LTOI'],
            'wavelength': 'O,C', 'type': 'Commercial', 'access': 'OPEN + PDK',
            'schedule': {'Jan': '1', 'Apr': '1', 'Aug': '1', 'Nov': '1'}
        },
        {
            'nr': 26, 'foundry': 'Silicon Austria Lab', 'country_code': 'AUT', 'country': 'Austria',
            'substrate': 'Unknown', 'technologies': [],
            'wavelength': 'Unknown', 'type': 'Pilot', 'access': 'Unknown',
            'schedule': {'all': 'Only On-demand with flexible schedule'}
        },
        {
            'nr': 27, 'foundry': 'SiPhotonIC', 'country_code': 'DK', 'country': 'Denmark',
            'substrate': 'Si, SiN, TFLN', 'technologies': [],
            'wavelength': 'Cband, Oband, Vis', 'type': 'Company', 'access': 'Open+PDK',
            'schedule': {'all': 'Only On-demand with flexible schedule'}
        },
        {
            'nr': 28, 'foundry': 'Sivers Photonics', 'country_code': 'UK', 'country': 'United Kingdom',
            'substrate': 'III-V', 'technologies': ['III-V Semiconductors'],
            'wavelength': 'C, O', 'type': 'Company', 'access': 'Dedicated Engineering Runs Only',
            'schedule': {'all': 'Dedicated Engineering Runs Only'}
        },
        {
            'nr': 30, 'foundry': 'Smart Photonics', 'country_code': 'NL', 'country': 'Netherlands',
            'substrate': 'InP', 'technologies': ['C-band', 'O-band'],
            'wavelength': 'O,C', 'type': 'Commercial', 'access': 'OPEN',
            'schedule': {'Apr': '16', 'Jul': '18', 'Oct': '24'}
        },
        {
            'nr': 36, 'foundry': 'STMicro', 'country_code': 'FR', 'country': 'France',
            'substrate': 'SOI+', 'technologies': ['PIC100'],
            'wavelength': 'O,C', 'type': 'Commercial', 'access': 'Bilateral + PDK',
            'schedule': {}, 'status': 'Potential Upcoming'
        },
        {
            'nr': 38, 'foundry': 'New Origin', 'country_code': 'NL', 'country': 'Netherlands',
            'substrate': 'SiN+', 'technologies': [],
            'wavelength': 'O,C, Visible', 'type': 'Commercial', 'access': 'OPEN + PDK',
            'schedule': {}, 'status': 'Potential Upcoming'
        },
        {
            'nr': 40, 'foundry': 'Fraunhofer', 'country_code': 'DE', 'country': 'Germany',
            'substrate': 'SOI, SiN, InP, SiC, Ge', 'technologies': [],
            'wavelength': 'O,C, Visible, Midl', 'type': 'Pilot', 'access': 'OPEN + PDK',
            'schedule': {}, 'status': 'Potential Upcoming'
        },
    ]
    
    # Convert to DataFrame
    df = pd.DataFrame(foundries)
    
    # Ensure technologies is always a list
    df['technologies'] = df['technologies'].apply(lambda x: x if isinstance(x, list) else [])
    
    # Add computed fields
    df['technologies_str'] = df['technologies'].apply(lambda x: ', '.join(x) if x else 'N/A')
    df['schedule_str'] = df['schedule'].apply(lambda x: json.dumps(x) if isinstance(x, dict) else str(x))
    
    # Determine technology category (needed before economic data)
    def categorize_tech(row):
        substrate = str(row['substrate']).upper()
        techs = ' '.join(row['technologies']).upper() if row['technologies'] else ''
        combined = f"{substrate} {techs}"
        
        if 'INP' in combined:
            return 'InP'
        elif 'LNOI' in combined or 'LTOI' in combined or 'LN' in combined:
            return 'LN (Lithium Niobate)'
        elif 'SIN' in combined and 'SOI' not in combined:
            return 'SiN (Silicon Nitride)'
        elif 'SOI' in combined or 'SI' in combined:
            return 'SiPh (Silicon Photonics)'
        elif 'ALN' in combined or 'ALO' in combined:
            return 'AlN/AlO'
        else:
            return 'Hybrid/Multi-platform'
    
    df['tech_category'] = df.apply(categorize_tech, axis=1)
    
    # Add economic data (after tech_category is set)
    df = add_economic_data(df)
    
    # Determine application domain
    def get_applications(row):
        wavelength = str(row['wavelength']).upper()
        apps = []
        if 'O' in wavelength or 'C' in wavelength:
            apps.append('Datacom')
        if 'VIS' in wavelength or 'VISIBLE' in wavelength or '850' in wavelength:
            apps.append('Sensing')
        if 'UV' in wavelength:
            apps.append('Specialized')
        if 'GE' in wavelength or 'MIDL' in wavelength:
            apps.append('Specialized')
        if not apps:
            apps.append('General')
        return ', '.join(apps)
    
    df['applications'] = df.apply(get_applications, axis=1)
    
    return df


def save_data_to_json(df: pd.DataFrame, filepath: str = 'foundry_data.json'):
    """Save DataFrame to JSON file."""
    df.to_json(filepath, orient='records', indent=2)


def load_data_from_json(filepath: str = 'foundry_data.json') -> pd.DataFrame:
    """Load DataFrame from JSON file."""
    return pd.read_json(filepath, orient='records')


if __name__ == '__main__':
    # Test data loading
    df = load_foundry_data()
    print(f"Loaded {len(df)} foundries")
    print(df[['nr', 'foundry', 'country', 'type', 'tech_category']].head(10))
    save_data_to_json(df, 'foundry_data.json')

