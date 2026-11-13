import pandas as pd
import geopandas as gpd
from pathlib import Path

bridge = pd.read_csv('bridge_table.csv')
# Actual summary based on 2024 LandIQ boundaries, so filter out fields without a crop in LandIQ 2024
bridge = bridge[bridge['crop_2024'].notna()]
# Also filter out fields that have no crops in any LandIQ 2018 - 2024
bridge = bridge[bridge['crop_2018'].notna() | bridge['crop_2019'].notna() | bridge['crop_2020'].notna() | bridge['crop_2021'].notna() | bridge['crop_2022'].notna() | bridge['crop_2023'].notna() | bridge['crop_2024'].notna()]
# Also also filter out fields that have are likely greenhouses
bad_crops = ['Flowers, nursery and Christmas Tree Farms', 'Greenhouse']
bridge = bridge[(~bridge['crop_2018'].isin(bad_crops)) & (~bridge['crop_2019'].isin(bad_crops)) & (~bridge['crop_2020'].isin(bad_crops)) & (~bridge['crop_2021'].isin(bad_crops)) & (~bridge['crop_2022'].isin(bad_crops)) & (~bridge['crop_2023'].isin(bad_crops)) & (~bridge['crop_2024'].isin(bad_crops))]


hydrologic_path = Path(__file__).resolve().parent.parent / 'geodata' / 'hydrologic_regions.geojson'
hydrologic_regions = gpd.read_file(hydrologic_path)

subbasin_path = Path(__file__).resolve().parent.parent / 'geodata' / 'subbasins.geojson'
subbasins = gpd.read_file(subbasin_path)

gsa_path = Path(__file__).resolve().parent.parent / 'geodata' / 'groundwater_sustainability_agencies.geojson'
gsas = gpd.read_file(gsa_path)

print('loading csv')
data_path = Path(__file__).resolve().parent.parent / 'geodata' / 'data.csv'
data = pd.read_csv(data_path)
# data.drop(columns=['value_ft'])
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
data = data.merge(bridge[['OPENET_ID', 'HR_NAME', 'Basin_Subb', 'GSA_ID', 'ACRES']], on='OPENET_ID', how='left')
print('done')

print('merging water year classifications')
water_year_class_path = Path(__file__).resolve().parent.parent / 'geodata' / 'hr_regions_wateryear_type.csv'
water_year_class = pd.read_csv(water_year_class_path)
data = data.merge(water_year_class[['HR_NAME', 'water_year', 'wb_class']], how='left', on=['HR_NAME', 'water_year'])
data = data.rename(columns={'wb_class': 'water_year_class'})
print('done')


print('hydrologic summary')
# Field-wise summary
hydrologic_fields = data[['HR_NAME', 'dataset', 'water_year_class', 'value_ft']].dropna(subset=['HR_NAME'])
hydrologic_fields_path = Path(__file__).resolve().parent.parent / 'data_summaries' / 'hydrologic_fields.csv'
hydrologic_fields.to_csv(hydrologic_fields_path, index=False)

# Overall summary
hydrologic_summary = data.groupby(['HR_NAME', 'dataset', 'water_year', 'water_year_class'], as_index=False).aggregate(SUM = ('value_acre_ft', 'sum'))

hydrologic_weighted_summary = data.assign(weighted_value=data['value_ft'] * data['ACRES']).groupby(['HR_NAME', 'dataset', 'water_year', 'water_year_class'], as_index=False).aggregate(
    weighted_sum=('weighted_value', 'sum'),
    total_acres=('ACRES', 'sum')
)
hydrologic_weighted_summary['weighted_mean'] = hydrologic_weighted_summary['weighted_sum'] / hydrologic_weighted_summary['total_acres']

hydrologic_summary = hydrologic_summary.merge(
    hydrologic_weighted_summary[['HR_NAME', 'dataset', 'water_year', 'water_year_class', 'weighted_mean']], 
    how='left', 
    on=['HR_NAME', 'dataset', 'water_year', 'water_year_class']
)
hydrologic_summary_path = Path(__file__).resolve().parent.parent / 'data_summaries' / 'hydrologic_summary.csv'
hydrologic_summary.to_csv(hydrologic_summary_path, index=False)
print('done')


print('subbasin summary')
# Field-wise summary
subbasin_fields = data[['Basin_Subb', 'dataset', 'water_year_class', 'value_ft']].dropna(subset=['Basin_Subb'])
subbasin_fields_path = Path(__file__).resolve().parent.parent / 'data_summaries' / 'subbasin_fields.csv'
subbasin_fields.to_csv(subbasin_fields_path, index=False)

# Overall summary
subbasin_summary = data.groupby(['Basin_Subb', 'dataset', 'water_year', 'water_year_class'], as_index=False).aggregate(SUM = ('value_acre_ft', 'sum'))

subbasin_weighted_summary = data.assign(weighted_value=data['value_ft'] * data['ACRES']).groupby(['Basin_Subb', 'dataset', 'water_year', 'water_year_class'], as_index=False).aggregate(
    weighted_sum=('weighted_value', 'sum'),
    total_acres=('ACRES', 'sum')
)
subbasin_weighted_summary['weighted_mean'] = subbasin_weighted_summary['weighted_sum'] / subbasin_weighted_summary['total_acres']

subbasin_summary = subbasin_summary.merge(
    subbasin_weighted_summary[['Basin_Subb', 'dataset', 'water_year', 'water_year_class', 'weighted_mean']], 
    how='left', 
    on=['Basin_Subb', 'dataset', 'water_year', 'water_year_class']
)
subbasin_summary_path = Path(__file__).resolve().parent.parent / 'data_summaries' / 'subbasin_summary.csv'
subbasin_summary.to_csv(subbasin_summary_path, index=False)
print('done')


print('gsa summary')
# Field-wise summary
gsa_fields = data[['GSA_ID', 'dataset', 'water_year_class', 'value_ft']].dropna(subset=['GSA_ID'])
gsa_fields['GSA_ID'] = gsa_fields['GSA_ID'].astype(int)
gsa_fields_path = Path(__file__).resolve().parent.parent / 'data_summaries' / 'gsa_fields.csv'
gsa_fields.to_csv(gsa_fields_path, index=False)

# Overall summary
gsa_summary = data.groupby(['GSA_ID', 'dataset', 'water_year', 'water_year_class'], as_index=False).aggregate(SUM = ('value_acre_ft', 'sum'))

gsa_weighted_summary = data.assign(weighted_value=data['value_ft'] * data['ACRES']).groupby(['GSA_ID', 'dataset', 'water_year', 'water_year_class'], as_index=False).aggregate(
    weighted_sum=('weighted_value', 'sum'),
    total_acres=('ACRES', 'sum')
)
gsa_weighted_summary['weighted_mean'] = gsa_weighted_summary['weighted_sum'] / gsa_weighted_summary['total_acres']

gsa_summary = gsa_summary.merge(
    gsa_weighted_summary[['GSA_ID', 'dataset', 'water_year', 'water_year_class', 'weighted_mean']], 
    how='left', 
    on=['GSA_ID', 'dataset', 'water_year', 'water_year_class']
)
gsa_summary['GSA_ID'] = gsa_summary['GSA_ID'].astype(int)
gsa_summary_path = Path(__file__).resolve().parent.parent / 'data_summaries' / 'gsa_summary.csv'
gsa_summary.to_csv(gsa_summary_path, index=False)
print('done')