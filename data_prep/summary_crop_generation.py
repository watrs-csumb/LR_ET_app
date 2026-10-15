import numpy as np
import pandas as pd
import geopandas as gpd
from pathlib import Path

hydrologic_path = Path(__file__).resolve().parent.parent / 'geodata' / 'hydrologic_regions.geojson'
hydrologic_regions = gpd.read_file(hydrologic_path)

subbasin_path = Path(__file__).resolve().parent.parent / 'geodata' / 'subbasins.geojson'
subbasins = gpd.read_file(subbasin_path)

gsa_path = Path(__file__).resolve().parent.parent / 'geodata' / 'groundwater_sustainability_agencies.geojson'
gsas = gpd.read_file(gsa_path)

print('loading csv')
data_path = Path(__file__).resolve().parent.parent / 'geodata' / 'data.csv'
data = pd.read_csv(data_path)
data = data.drop(columns=['value_acre_ft'])
print('done')

data_with_crops_path = Path('geodata/data_with_crops.csv')
if data_with_crops_path.is_file():
    print('Reading data with crops file')
    data = pd.read_csv(data_with_crops_path)
else:
    print('merging bridge data')
    bridge_path = Path(__file__).resolve().parent.parent / 'bridge_table.csv'
    bridge = pd.read_csv(bridge_path)
    # Actual summary based on 2024 LandIQ boundaries, so filter out fields without a crop in LandIQ 2024
    bridge = bridge[bridge['crop_2024'].notna()]
    # Also filter out fields that have no crops in any LandIQ 2018 - 2024
    bridge = bridge[bridge['crop_2018'].notna() | bridge['crop_2019'].notna() | bridge['crop_2020'].notna() | bridge['crop_2021'].notna() | bridge['crop_2022'].notna() | bridge['crop_2023'].notna() | bridge['crop_2024'].notna()]
    # Also also filter out fields that have are likely greenhouses
    bridge = bridge[
        (~bridge['crop_2018'].str.contains('Flowers, nursery and Christmas Tree Farms')) & (~bridge['crop_2018'].str.contains('Greenhouse')) & 
        (~bridge['crop_2019'].str.contains('Flowers, nursery and Christmas Tree Farms')) & (~bridge['crop_2019'].str.contains('Greenhouse')) & 
        (~bridge['crop_2020'].str.contains('Flowers, nursery and Christmas Tree Farms')) & (~bridge['crop_2020'].str.contains('Greenhouse')) & 
        (~bridge['crop_2021'].str.contains('Flowers, nursery and Christmas Tree Farms')) & (~bridge['crop_2021'].str.contains('Greenhouse')) & 
        (~bridge['crop_2022'].str.contains('Flowers, nursery and Christmas Tree Farms')) & (~bridge['crop_2022'].str.contains('Greenhouse')) & 
        (~bridge['crop_2023'].str.contains('Flowers, nursery and Christmas Tree Farms')) & (~bridge['crop_2023'].str.contains('Greenhouse')) & 
        (~bridge['crop_2024'].str.contains('Flowers, nursery and Christmas Tree Farms')) & (~bridge['crop_2024'].str.contains('Greenhouse'))
    ]

    bridge = bridge.melt(id_vars=['OPENET_ID', 'ACRES', 'HR_NAME', 'Basin_Subb', 'GSA_ID'], var_name='water_year', value_name='crop')
    bridge['water_year'] = bridge['water_year'].str.replace('crop_', '', regex=False)
    bridge['water_year'] = bridge['water_year'].astype(int)

    data = data.merge(bridge[['OPENET_ID', 'ACRES', 'HR_NAME', 'Basin_Subb', 'GSA_ID', 'water_year', 'crop']], on=['OPENET_ID', 'water_year'], how='left')
    data.to_csv(data_with_crops_path, index=False)
print('done')

water_year_classification = {
    2018: 'dry',
    2019: 'dry',
    2020: 'normal',
    2021: 'dry',
    2022: 'normal',
    2023: 'wet',
    2024: 'wet'
}

data['water_year_class'] = data['water_year'].map(water_year_classification)

print('hydrologic summary')
hydrologic_summary = data.assign(weighted_value=data['value_ft'] * data['ACRES']).groupby(['HR_NAME', 'dataset', 'water_year_class', 'crop'], as_index=False).aggregate(
    weighted_sum=('weighted_value', 'sum'),
    total_acres=('ACRES', 'sum')
)
hydrologic_summary['weighted_mean'] = hydrologic_summary['weighted_sum'] / hydrologic_summary['total_acres']

all_water_year_classes = data.assign(weighted_value=data['value_ft'] * data['ACRES']).groupby(['HR_NAME', 'dataset', 'crop'], as_index=False).aggregate(
    weighted_sum=('weighted_value', 'sum'),
    total_acres=('ACRES', 'sum')
)
all_water_year_classes['weighted_mean'] = all_water_year_classes['weighted_sum'] / all_water_year_classes['total_acres']
all_water_year_classes['water_year_class'] = 'all'

hydrologic_summary = pd.concat([hydrologic_summary, all_water_year_classes], ignore_index=True)
hydrologic_summary = hydrologic_summary.drop(columns=['weighted_sum', 'total_acres'])

hydrologic_summary_path = Path(__file__).resolve().parent.parent / 'data_summaries' / 'hydrologic_crop_summary.csv'
hydrologic_summary.to_csv(hydrologic_summary_path, index=False)
print('done')


print('subbasin summary')
subbasin_summary = data.assign(weighted_value=data['value_ft'] * data['ACRES']).groupby(['Basin_Subb', 'dataset', 'water_year_class', 'crop'], as_index=False).aggregate(
    weighted_sum=('weighted_value', 'sum'),
    total_acres=('ACRES', 'sum')
)
subbasin_summary['weighted_mean'] = subbasin_summary['weighted_sum'] / subbasin_summary['total_acres']

all_water_year_classes = data.assign(weighted_value=data['value_ft'] * data['ACRES']).groupby(['Basin_Subb', 'dataset', 'crop'], as_index=False).aggregate(
    weighted_sum=('weighted_value', 'sum'),
    total_acres=('ACRES', 'sum')
)
all_water_year_classes['weighted_mean'] = all_water_year_classes['weighted_sum'] / all_water_year_classes['total_acres']
all_water_year_classes['water_year_class'] = 'all'

subbasin_summary = pd.concat([subbasin_summary, all_water_year_classes], ignore_index=True)
subbasin_summary = subbasin_summary.drop(columns=['weighted_sum', 'total_acres'])

subbasin_summary_path = Path(__file__).resolve().parent.parent / 'data_summaries' / 'subbasin_crop_summary.csv'
subbasin_summary.to_csv(subbasin_summary_path, index=False)
print('done')


print('gsa summary')
gsa_summary = data.assign(weighted_value=data['value_ft'] * data['ACRES']).groupby(['GSA_ID', 'dataset', 'water_year_class', 'crop'], as_index=False).aggregate(
    weighted_sum=('weighted_value', 'sum'),
    total_acres=('ACRES', 'sum')
)
gsa_summary['weighted_mean'] = gsa_summary['weighted_sum'] / gsa_summary['total_acres']

all_water_year_classes = data.assign(weighted_value=data['value_ft'] * data['ACRES']).groupby(['GSA_ID', 'dataset', 'crop'], as_index=False).aggregate(
    weighted_sum=('weighted_value', 'sum'),
    total_acres=('ACRES', 'sum')
)
all_water_year_classes['weighted_mean'] = all_water_year_classes['weighted_sum'] / all_water_year_classes['total_acres']
all_water_year_classes['water_year_class'] = 'all'

gsa_summary = pd.concat([gsa_summary, all_water_year_classes], ignore_index=True)
gsa_summary = gsa_summary.drop(columns=['weighted_sum', 'total_acres'])

gsa_summary['GSA_ID'] = gsa_summary['GSA_ID'].astype(int)
gsa_summary_path = Path(__file__).resolve().parent.parent / 'data_summaries' / 'gsa_crop_summary.csv'
gsa_summary.to_csv(gsa_summary_path, index=False)
print('done')