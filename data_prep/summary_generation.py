import pandas as pd
import geopandas as gpd
from pathlib import Path

bridge = pd.read_csv('bridge_table.csv')
# Actual summary based on 2024 LandIQ boundaries, so filter out fields without a crop in LandIQ 2024
bridge = bridge[bridge['crop_2024'].notna()]
# Also filter out fields that have no crops in any LandIQ 2018 - 2024
bridge = bridge[bridge['crop_2018'].notna() | bridge['crop_2019'].notna() | bridge['crop_2020'].notna() | bridge['crop_2021'].notna() | bridge['crop_2022'].notna() | bridge['crop_2023'].notna() | bridge['crop_2024'].notna()]
# Also also filter out fields that have "nursery" in the crop name, as these are likely greenhouses
bridge = bridge[(~bridge['crop_2018'].str.contains('nursery')) & (~bridge['crop_2019'].str.contains('nursery')) & (~bridge['crop_2020'].str.contains('nursery')) & (~bridge['crop_2021'].str.contains('nursery')) & (~bridge['crop_2022'].str.contains('nursery')) & (~bridge['crop_2023'].str.contains('nursery')) & (~bridge['crop_2024'].str.contains('nursery'))]


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
net_data['value_acre_ft'] = net_data['value_acre_ft'] - data[data['dataset'] == 'gridmet_pr'].reset_index()['value_acre_ft']
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

print('merging bridge data')
data = data.merge(bridge[['OPENET_ID', 'HR_NAME', 'Basin_Subb', 'GSA_ID']], on='OPENET_ID', how='left')
print('done')

print('hydrologic summary')
hydrologic_summary = data.groupby(['HR_NAME', 'dataset', 'water_year'], as_index=False).aggregate(
    SUM = ('value_acre_ft', 'sum'),
    MEAN = ('value_acre_ft', 'mean'),
    MEDIAN = ('value_acre_ft', 'median'),
    PCT25 = ('value_acre_ft', pct25),
    PCT75 = ('value_acre_ft', pct75),
    LOWER_WHISKER = ('value_acre_ft', lower_whisker),
    UPPER_WHISKER = ('value_acre_ft', upper_whisker),
    STDDEV = ('value_acre_ft', 'std')
)
hydrologic_summary_path = Path(__file__).resolve().parent.parent / 'data_summaries' / 'hydrologic_summary.csv'
hydrologic_summary.to_csv(hydrologic_summary_path, index=False)
print('done')


print('subbasin summary')
subbasin_summary = data.groupby(['Basin_Subb', 'dataset', 'water_year'], as_index=False).aggregate(
    SUM = ('value_acre_ft', 'sum'),
    MEAN = ('value_acre_ft', 'mean'),
    MEDIAN = ('value_acre_ft', 'median'),
    PCT25 = ('value_acre_ft', pct25),
    PCT75 = ('value_acre_ft', pct75),
    LOWER_WHISKER = ('value_acre_ft', lower_whisker),
    UPPER_WHISKER = ('value_acre_ft', upper_whisker),
    STDDEV = ('value_acre_ft', 'std')
)
subbasin_summary_path = Path(__file__).resolve().parent.parent / 'data_summaries' / 'subbasin_summary.csv'
subbasin_summary.to_csv(subbasin_summary_path, index=False)
print('done')


print('gsa summary')
gsa_summary = data.groupby(['GSA_ID', 'dataset', 'water_year'], as_index=False).aggregate(
    SUM = ('value_acre_ft', 'sum'),
    MEAN = ('value_acre_ft', 'mean'),
    MEDIAN = ('value_acre_ft', 'median'),
    PCT25 = ('value_acre_ft', pct25),
    PCT75 = ('value_acre_ft', pct75),
    LOWER_WHISKER = ('value_acre_ft', lower_whisker),
    UPPER_WHISKER = ('value_acre_ft', upper_whisker),
    STDDEV = ('value_acre_ft', 'std')
)
gsa_summary['GSA_ID'] = gsa_summary['GSA_ID'].astype(int)
gsa_summary_path = Path(__file__).resolve().parent.parent / 'data_summaries' / 'gsa_summary.csv'
gsa_summary.to_csv(gsa_summary_path, index=False)
print('done')