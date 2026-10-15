import pandas as pd
import geopandas as gpd
from pathlib import Path

MM_TO_INCHES = 25.4
INCHES_TO_FEET = 12


shards = []
for i in range(1, 202):
    shard = pd.read_csv(f'geodata/shards/cal_i08_ensemble_pr_2018_2024_{i}_200.csv')
    shards.append(shard)

data = pd.concat(shards)
data = data.rename(columns={'value': 'value_mm'})
data.fillna(0, inplace=True)
data['month'] = data['month'] + '-01'

eto = pd.read_csv('eto_CAproject.csv')
eto['month_date'] = pd.to_datetime(eto['month'])

data['month_date'] = pd.to_datetime(data['month'])
data['water_year'] = data['month_date'].dt.year + (data['month_date'].dt.month >= 10)
data['year'] = data['month_date'].dt.year
data['month'] = data['month_date'].dt.month

data = data.merge(eto[['OPENET_ID', 'month_date', 'value']].rename(columns={'value': 'eto'}), on=['OPENET_ID', 'month_date'], how='left')
data = data.dropna(subset=['eto'])

ensemble_data = data[data['dataset'] == 'ensemble'].copy()
data = data[data['dataset'] != 'ensemble']

ensemble_data['et_fraction'] = ensemble_data['value_mm'] / ensemble_data['eto']
ensemble_data = ensemble_data.sort_values(['OPENET_ID', 'month_date'])

ensemble_data['previous_nonzero_et_fraction'] = ensemble_data['et_fraction'].where(ensemble_data['et_fraction'] != 0).groupby(ensemble_data['OPENET_ID']).ffill()

zero_mask = ensemble_data['value_mm'] == 0
ensemble_data.loc[zero_mask, 'value_mm'] = ensemble_data.loc[zero_mask, 'previous_nonzero_et_fraction'] * ensemble_data.loc[zero_mask, 'eto']

data = pd.concat([data, ensemble_data])
data.dropna(subset=['value_mm'])

# Convert mm to ft
data['value_in'] = data['value_mm'] / MM_TO_INCHES
data['value_ft'] = data['value_in'] / INCHES_TO_FEET

# Convert to acre-feet
fields_path = Path(__file__).resolve().parent.parent / 'geodata' / 'fields.geojson'
fields = gpd.read_file(fields_path)
data = pd.merge(data, fields[['OPENET_ID', 'ACRES']], on='OPENET_ID', how='left')
data['value_acre_ft'] = data['value_ft'] * data['ACRES']

# Simplify to water yearly values
data = data.groupby(['OPENET_ID', 'dataset', 'water_year'], as_index=False).aggregate(
    value_ft=('value_ft', 'sum'),
    value_acre_ft=('value_acre_ft', 'sum')
)

# Add "net_et" dataset
net_data = data[data['dataset'] == 'ensemble'].reset_index().copy()
net_data['value_ft'] = net_data['value_ft'] - data[data['dataset'] == 'gridmet_pr'].reset_index()['value_ft']
net_data['value_acre_ft'] = net_data['value_acre_ft'] - data[data['dataset'] == 'gridmet_pr'].reset_index()['value_acre_ft']
net_data['dataset'] = 'net_et'
data = pd.concat([data, net_data])

path = Path(__file__).resolve().parent.parent / 'geodata' / 'data.csv'
data[['OPENET_ID', 'dataset', 'water_year', 'value_ft', 'value_acre_ft']].to_csv(path, index=False)

# TODO: Pivot table to make more sense
# TODO: More unit-specific column names