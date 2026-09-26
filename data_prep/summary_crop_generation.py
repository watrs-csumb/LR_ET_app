import numpy as np
import pandas as pd
import geopandas as gpd
from datetime import datetime
from pathlib import Path

start_date = datetime(2017, 10, 1)
end_date = datetime(2024, 9, 30)

hydrologic_path = Path(__file__).resolve().parent.parent / 'geodata' / 'hydrologic_regions.geojson'
hydrologic_regions = gpd.read_file(hydrologic_path)

subbasin_path = Path(__file__).resolve().parent.parent / 'geodata' / 'subbasins.geojson'
subbasins = gpd.read_file(subbasin_path)

gsa_path = Path(__file__).resolve().parent.parent / 'geodata' / 'groundwater_sustainability_agencies.geojson'
gsas = gpd.read_file(gsa_path)

print('loading csv')
data_path = Path(__file__).resolve().parent.parent / 'geodata' / 'data.csv'
data = pd.read_csv(data_path)
print('done')

print('net et computation')
net_data = data[data['dataset'] == 'ensemble'].reset_index().copy()
net_data['value'] = net_data['value'] - data[data['dataset'] == 'gridmet_pr'].reset_index()['value']
net_data['dataset'] = 'net_et'
data = pd.concat([data, net_data])
print('done')

def pct25(series):
    return series.quantile(0.25)

def pct75(series):
    return series.quantile(0.75)

def lower_whisker(series):
    q1 = series.quantile(0.25)
    q3 = series.quantile(0.75)
    bound = q1 - (1.5 * (q3 - q1))
    return series[series >= bound].min()

def upper_whisker(series):
    q1 = series.quantile(0.25)
    q3 = series.quantile(0.75)
    bound = q3 + (1.5 * (q3 - q1))
    return series[series <= bound].max()

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
    # Also also filter out fields that have "nursery" in the crop name, as these are likely greenhouses
    bridge = bridge[(~bridge['crop_2018'].str.contains('nursery')) & (~bridge['crop_2019'].str.contains('nursery')) & (~bridge['crop_2020'].str.contains('nursery')) & (~bridge['crop_2021'].str.contains('nursery')) & (~bridge['crop_2022'].str.contains('nursery')) & (~bridge['crop_2023'].str.contains('nursery')) & (~bridge['crop_2024'].str.contains('nursery'))]

    bridge = bridge.melt(id_vars=['OPENET_ID', 'ACRES', 'HR_NAME', 'Basin_Subb', 'GSA_ID'], var_name='water_year', value_name='crop')
    bridge['water_year'] = bridge['water_year'].str.replace('crop_', '', regex=False)
    bridge['water_year'] = bridge['water_year'].astype(int)

    data = data.merge(bridge[['OPENET_ID', 'ACRES', 'HR_NAME', 'Basin_Subb', 'GSA_ID', 'water_year', 'crop']], on=['OPENET_ID', 'water_year'], how='left')
    data.to_csv(data_with_crops_path, index=False)
print('done')


print('hydrologic summary')
hydrologic_summary = data.groupby(['HR_NAME', 'dataset', 'water_year', 'crop'], as_index=False).aggregate(
    SUM = ('value', 'sum'),
    MEAN = ('value', 'mean'),
    MEDIAN = ('value', 'median'),
    PCT25 = ('value', pct25),
    PCT75 = ('value', pct75),
    LOWER_WHISKER = ('value', lower_whisker),
    UPPER_WHISKER = ('value', upper_whisker),
    STDDEV = ('value', 'std')
)

annual_mean = data.groupby(['HR_NAME', 'dataset', 'crop'], as_index=False).aggregate(
    SUM = ('value', 'sum'),
    MEAN = ('value', 'mean'),
    MEDIAN = ('value', 'median'),
    PCT25 = ('value', pct25),
    PCT75 = ('value', pct75),
    LOWER_WHISKER = ('value', lower_whisker),
    UPPER_WHISKER = ('value', upper_whisker),
    STDDEV = ('value', 'std')
)
annual_mean['water_year'] = 0
hydrologic_summary = pd.concat([hydrologic_summary, annual_mean], ignore_index=True)

hydrologic_summary_path = Path(__file__).resolve().parent.parent / 'data_summaries' / 'hydrologic_crop_summary.csv'
hydrologic_summary.to_csv(hydrologic_summary_path, index=False)
print('done')


print('subbasin summary')
subbasin_summary = data.groupby(['Basin_Subb', 'dataset', 'water_year', 'crop'], as_index=False).aggregate(
    SUM = ('value', 'sum'),
    MEAN = ('value', 'mean'),
    MEDIAN = ('value', 'median'),
    PCT25 = ('value', pct25),
    PCT75 = ('value', pct75),
    LOWER_WHISKER = ('value', lower_whisker),
    UPPER_WHISKER = ('value', upper_whisker),
    STDDEV = ('value', 'std')
)

annual_mean = data.groupby(['Basin_Subb', 'dataset', 'crop'], as_index=False).aggregate(
    SUM = ('value', 'sum'),
    MEAN = ('value', 'mean'),
    MEDIAN = ('value', 'median'),
    PCT25 = ('value', pct25),
    PCT75 = ('value', pct75),
    LOWER_WHISKER = ('value', lower_whisker),
    UPPER_WHISKER = ('value', upper_whisker),
    STDDEV = ('value', 'std')
)
annual_mean['water_year'] = 0
subbasin_summary = pd.concat([subbasin_summary, annual_mean], ignore_index=True)

subbasin_summary_path = Path(__file__).resolve().parent.parent / 'data_summaries' / 'subbasin_crop_summary.csv'
subbasin_summary.to_csv(subbasin_summary_path, index=False)
print('done')


print('gsa summary')
gsa_summary = data.groupby(['GSA_ID', 'dataset', 'water_year', 'crop'], as_index=False).aggregate(
    SUM = ('value', 'sum'),
    MEAN = ('value', 'mean'),
    MEDIAN = ('value', 'median'),
    PCT25 = ('value', pct25),
    PCT75 = ('value', pct75),
    LOWER_WHISKER = ('value', lower_whisker),
    UPPER_WHISKER = ('value', upper_whisker),
    STDDEV = ('value', 'std')
)

annual_mean = data.groupby(['GSA_ID', 'dataset', 'crop'], as_index=False).aggregate(
    SUM = ('value', 'sum'),
    MEAN = ('value', 'mean'),
    MEDIAN = ('value', 'median'),
    PCT25 = ('value', pct25),
    PCT75 = ('value', pct75),
    LOWER_WHISKER = ('value', lower_whisker),
    UPPER_WHISKER = ('value', upper_whisker),
    STDDEV = ('value', 'std')
)
annual_mean['water_year'] = 0
gsa_summary = pd.concat([gsa_summary, annual_mean], ignore_index=True)

gsa_summary['GSA_ID'] = gsa_summary['GSA_ID'].astype(int)
gsa_summary_path = Path(__file__).resolve().parent.parent / 'data_summaries' / 'gsa_crop_summary.csv'
gsa_summary.to_csv(gsa_summary_path, index=False)
print('done')