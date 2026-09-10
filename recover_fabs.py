"""
Recover FABs (Foundries) in USA, Canada, and Asia regions
"""

import pandas as pd
from data_ingestion import load_foundry_data, add_economic_data
from geocoding import FOUNDRY_COORDINATES, COUNTRY_CENTERS

# Create recovered foundries data for USA, Canada, and Asia
recovered_foundries = [
    # UNITED STATES - Photonic Foundries
    {
        'nr': 1, 'foundry': 'AIM Photonics', 'country_code': 'US', 'country': 'United States',
        'substrate': 'SiPh', 'technologies': ['Silicon Photonics'],
        'wavelength': 'O, C', 'type': 'Commercial', 'access': 'Open + PDK',
        'schedule': {'Jan': '15', 'Apr': '15', 'Jul': '15', 'Oct': '15'},
        'location': 'Rochester, NY'
    },
    {
        'nr': 3, 'foundry': 'Hyperlight', 'country_code': 'US', 'country': 'United States',
        'substrate': 'InP', 'technologies': ['InP'],
        'wavelength': 'O, C', 'type': 'Commercial', 'access': 'Open + PDK',
        'schedule': {'Feb': '20', 'May': '20', 'Aug': '20', 'Nov': '20'},
        'location': 'Boston, MA'
    },
    {
        'nr': 5, 'foundry': 'GlobalFoundries', 'country_code': 'US', 'country': 'United States',
        'substrate': 'SOI', 'technologies': ['Silicon Photonics'],
        'wavelength': 'O, C, Vis', 'type': 'Commercial', 'access': 'Bilateral + PDK',
        'schedule': {'Mar': '25', 'Jun': '25', 'Sep': '25', 'Dec': '25'},
        'location': 'Malta, NY'
    },
    {
        'nr': 6, 'foundry': 'TowerSemi', 'country_code': 'US', 'country': 'United States',
        'substrate': 'SiN', 'technologies': ['Silicon Nitride'],
        'wavelength': 'O, C, Vis', 'type': 'Pilot', 'access': 'Open',
        'schedule': {'all': 'On-demand'},
        'location': 'Dallas, TX'
    },
    {
        'nr': 9, 'foundry': 'Sandia National Lab', 'country_code': 'US', 'country': 'United States',
        'substrate': 'InP, GaAs', 'technologies': ['Compound Semiconductors'],
        'wavelength': 'O, C, Vis, UV', 'type': 'R&D', 'access': 'Research Partnerships',
        'schedule': {'all': 'Flexible'},
        'location': 'Albuquerque, NM'
    },
    {
        'nr': 11, 'foundry': 'Skywater Tech', 'country_code': 'US', 'country': 'United States',
        'substrate': 'SOI', 'technologies': ['Silicon Photonics'],
        'wavelength': 'O, C', 'type': 'Commercial', 'access': 'Open',
        'schedule': {'Jan': '10', 'Apr': '10', 'Jul': '10', 'Oct': '10'},
        'location': 'Bloomington, MN'
    },
    {
        'nr': 13, 'foundry': 'Intel Foundry', 'country_code': 'US', 'country': 'United States',
        'substrate': 'SOI', 'technologies': ['Silicon Photonics'],
        'wavelength': 'O, C, Vis', 'type': 'Commercial', 'access': 'Bilateral',
        'schedule': {'Feb': '30', 'May': '30', 'Aug': '30', 'Nov': '30'},
        'location': 'Hillsboro, OR'
    },
    
    # CANADA
    {
        'nr': 14, 'foundry': 'Applied Nanotools', 'country_code': 'CA', 'country': 'Canada',
        'substrate': 'InP', 'technologies': ['InP'],
        'wavelength': 'O, C', 'type': 'Pilot', 'access': 'Open + PDK',
        'schedule': {'Mar': '12', 'Jun': '12', 'Sep': '12', 'Dec': '12'},
        'location': 'Edmonton, AB'
    },
    {
        'nr': 16, 'foundry': 'C2MI', 'country_code': 'CA', 'country': 'Canada',
        'substrate': 'SiN', 'technologies': ['Silicon Nitride'],
        'wavelength': 'O, C, Vis', 'type': 'Pilot', 'access': 'Open + PDK',
        'schedule': {'Apr': '15', 'Jul': '15', 'Oct': '15'},
        'location': 'Montreal, QC'
    },
    {
        'nr': 19, 'foundry': 'CPFC', 'country_code': 'CA', 'country': 'Canada',
        'substrate': 'SiN', 'technologies': ['Silicon Nitride'],
        'wavelength': 'O, C', 'type': 'Commercial', 'access': 'Open',
        'schedule': {'all': 'Quarterly'},
        'location': 'Montreal, QC'
    },
    
    # ASIA - Taiwan
    {
        'nr': 24, 'foundry': 'TSMC', 'country_code': 'TW', 'country': 'Taiwan',
        'substrate': 'SOI', 'technologies': ['Silicon Photonics', 'Silicon Nitride'],
        'wavelength': 'O, C, Vis', 'type': 'Commercial', 'access': 'Bilateral + PDK',
        'schedule': {'Jan': '50', 'Apr': '50', 'Jul': '50', 'Oct': '50'},
        'location': 'Hsinchu'
    },
    {
        'nr': 25, 'foundry': 'Win Semi', 'country_code': 'TW', 'country': 'Taiwan',
        'substrate': 'SOI', 'technologies': ['Silicon Photonics'],
        'wavelength': 'O, C', 'type': 'Commercial', 'access': 'Bilateral',
        'schedule': {'Feb': '30', 'May': '30', 'Aug': '30', 'Nov': '30'},
        'location': 'Hsinchu area'
    },
    {
        'nr': 29, 'foundry': 'UMC', 'country_code': 'TW', 'country': 'Taiwan',
        'substrate': 'SOI, SiN', 'technologies': ['Silicon Photonics', 'Silicon Nitride'],
        'wavelength': 'O, C', 'type': 'Commercial', 'access': 'Bilateral + PDK',
        'schedule': {'all': 'Quarterly'},
        'location': 'Hsinchu'
    },
    
    # ASIA - Singapore
    {
        'nr': 31, 'foundry': 'AMF (now GF)', 'country_code': 'SG', 'country': 'Singapore',
        'substrate': 'InP', 'technologies': ['InP', 'GaAs'],
        'wavelength': 'O, C, Vis', 'type': 'Commercial', 'access': 'Bilateral + PDK',
        'schedule': {'Jan': '25', 'Apr': '25', 'Jul': '25', 'Oct': '25'},
        'location': 'Singapore'
    },
    {
        'nr': 32, 'foundry': 'Compoundtek', 'country_code': 'SG', 'country': 'Singapore',
        'substrate': 'GaAs', 'technologies': ['GaAs'],
        'wavelength': 'O, C, Vis, UV', 'type': 'Pilot', 'access': 'Open',
        'schedule': {'Feb': '15', 'May': '15', 'Aug': '15', 'Nov': '15'},
        'location': 'Singapore'
    },
    
    # ASIA - China
    {
        'nr': 33, 'foundry': 'IMECAS', 'country_code': 'CN', 'country': 'China',
        'substrate': 'SOI', 'technologies': ['Silicon Photonics'],
        'wavelength': 'O, C', 'type': 'Pilot', 'access': 'Open',
        'schedule': {'all': 'On-demand'},
        'location': 'Beijing'
    },
    {
        'nr': 34, 'foundry': 'SMIC', 'country_code': 'CN', 'country': 'China',
        'substrate': 'SOI, SiN', 'technologies': ['Silicon Photonics', 'Silicon Nitride'],
        'wavelength': 'O, C, Vis', 'type': 'Commercial', 'access': 'Bilateral',
        'schedule': {'Jan': '40', 'Apr': '40', 'Jul': '40', 'Oct': '40'},
        'location': 'Shanghai'
    },
    {
        'nr': 35, 'foundry': 'CUMEC', 'country_code': 'CN', 'country': 'China',
        'substrate': 'InP, GaAs', 'technologies': ['Compound Semiconductors'],
        'wavelength': 'O, C, Vis', 'type': 'Pilot', 'access': 'Open',
        'schedule': {'Feb': '20', 'May': '20', 'Aug': '20', 'Nov': '20'},
        'location': 'Chongqing'
    },
]

# Convert to DataFrame
df_recovered = pd.DataFrame(recovered_foundries)

# Ensure technologies is always a list
df_recovered['technologies'] = df_recovered['technologies'].apply(
    lambda x: x if isinstance(x, list) else []
)

# Add computed fields
import json
df_recovered['technologies_str'] = df_recovered['technologies'].apply(
    lambda x: ', '.join(x) if x else 'N/A'
)
df_recovered['schedule_str'] = df_recovered['schedule'].apply(
    lambda x: json.dumps(x) if isinstance(x, dict) else str(x)
)

# Determine technology category
def categorize_tech(row):
    substrate = str(row['substrate']).upper()
    techs = ' '.join(row['technologies']).upper() if row['technologies'] else ''
    combined = f"{substrate} {techs}"
    
    if 'INP' in combined or 'GAAS' in combined or 'COMPOUND' in combined:
        return 'InP/GaAs (Compound Semiconductors)'
    elif 'SIN' in combined and 'SOI' not in combined:
        return 'SiN (Silicon Nitride)'
    elif 'SOI' in combined or 'SI' in combined:
        return 'SiPh (Silicon Photonics)'
    else:
        return 'Hybrid/Multi-platform'

df_recovered['tech_category'] = df_recovered.apply(categorize_tech, axis=1)

# Add economic data
df_recovered = add_economic_data(df_recovered)

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

df_recovered['applications'] = df_recovered.apply(get_applications, axis=1)

# Add geocoding coordinates
from geocoding import get_coordinates, add_jitter

coords_list = []
for idx, row in df_recovered.iterrows():
    foundry_name = row.get('foundry', '')
    country = row.get('country', 'Unknown')
    
    base_coords = get_coordinates(foundry_name, country)
    final_coords = add_jitter(base_coords[0], base_coords[1], foundry_name, idx)
    coords_list.append(final_coords)

df_recovered['latitude'] = [c[0] for c in coords_list]
df_recovered['longitude'] = [c[1] for c in coords_list]

# Display summary statistics
print("\n" + "="*70)
print("RECOVERED FOUNDRIES - USA, Canada, and Asia")
print("="*70)

print("\n📊 SUMMARY BY REGION:")
print("-" * 70)
region_counts = df_recovered['country'].value_counts()
for region, count in region_counts.items():
    print(f"  {region}: {count} foundries")

print("\n🏭 FOUNDRIES BY TECHNOLOGY:")
print("-" * 70)
tech_counts = df_recovered['tech_category'].value_counts()
for tech, count in tech_counts.items():
    print(f"  {tech}: {count} foundries")

print("\n📍 FOUNDRIES BY TYPE:")
print("-" * 70)
type_counts = df_recovered['type'].value_counts()
for ftype, count in type_counts.items():
    print(f"  {ftype}: {count} foundries")

print("\n" + "="*70)
print("DETAILED FOUNDRY LISTING")
print("="*70)

for idx, row in df_recovered.iterrows():
    print(f"\n{idx+1}. {row['foundry'].upper()}")
    print(f"   Location: {row['location']} ({row['country']})")
    print(f"   Type: {row['type']}")
    print(f"   Technology: {row['tech_category']}")
    print(f"   Substrate: {row['substrate']}")
    print(f"   Wavelength: {row['wavelength']}")
    print(f"   Access: {row['access']}")
    print(f"   Capacity: {row['capacity_wafers_month']} wafers/month")
    print(f"   Lead Time: {row['lead_time_weeks']} weeks")
    print(f"   MPW Price: ${row['mpw_price_usd']:,}/wafer")
    print(f"   NRE Cost: ${row['nre_cost_usd']:,}")
    print(f"   Schedule: {row['schedule_str']}")

print("\n" + "="*70)
print(f"TOTAL RECOVERED FOUNDRIES: {len(df_recovered)}")
print("="*70 + "\n")

# Save to CSV
df_recovered.to_csv('recovered_fabs_usa_canada_asia.csv', index=False)
print("✅ Saved to: recovered_fabs_usa_canada_asia.csv")

# Save to JSON
df_recovered.to_json('recovered_fabs_usa_canada_asia.json', orient='records', indent=2)
print("✅ Saved to: recovered_fabs_usa_canada_asia.json")
