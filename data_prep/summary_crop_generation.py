import numpy as np
import pandas as pd
import geopandas as gpd
from pathlib import Path

YEAR_COUNT = 7

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

print('Loading bridge table')
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
print('Done')

hydrologic_region_acreage_path = Path(__file__).resolve().parent.parent / 'geodata' / 'hydrologic_region_acreage.csv'
if hydrologic_region_acreage_path.is_file():
    print('Loading Hydrologic Region acreage data')
    hydrologic_region_acreage = pd.read_csv(hydrologic_region_acreage_path).set_index('HR_NAME')['ACRES'].to_dict()
else:
    print('Building Hydrologic Region acreage data')
    hydrologic_region_acreage_df = bridge.groupby('HR_NAME')['ACRES'].sum()
    hydrologic_region_acreage_df.to_csv(hydrologic_region_acreage_path)
    
    hydrologic_region_acreage = hydrologic_region_acreage_df.to_dict()
print('Done')

subbasin_acreage_path = Path(__file__).resolve().parent.parent / 'geodata' / 'subbasin_acreage.csv'
if subbasin_acreage_path.is_file():
    print('Loading Subbasin acreage data')
    subbasin_acreage = pd.read_csv(subbasin_acreage_path).set_index('Basin_Subb')['ACRES'].to_dict()
else:
    print('Building Subbasin acreage data')
    subbasin_acreage_df = bridge.groupby('Basin_Subb')['ACRES'].sum()
    subbasin_acreage_df.to_csv(subbasin_acreage_path)
    
    subbasin_acreage = subbasin_acreage_df.to_dict()
print('Done')

gsa_acreage_path = Path(__file__).resolve().parent.parent / 'geodata' / 'gsa_acreage.csv'
if gsa_acreage_path.is_file():
    print('Loading GSA acreage data')
    gsa_acreage = pd.read_csv(gsa_acreage_path).set_index('GSA_ID')['ACRES'].to_dict()
else:
    print('Building GSA acreage data')
    gsa_acreage_df = bridge.groupby('GSA_ID')['ACRES'].sum()
    gsa_acreage_df.to_csv(gsa_acreage_path)
    
    gsa_acreage = gsa_acreage_df.to_dict()
print('Done')


data_with_crops_path = Path('geodata/data_with_crops.csv')
if data_with_crops_path.is_file():
    print('Reading data with crops file')
    data = pd.read_csv(data_with_crops_path)
else:
    print('merging bridge data')
    bridge_melt = bridge.melt(id_vars=['OPENET_ID', 'ACRES', 'HR_NAME', 'Basin_Subb', 'GSA_ID', 'category_2024'], var_name='water_year', value_name='crop')
    bridge_melt['water_year'] = bridge_melt['water_year'].str.replace('crop_', '', regex=False)
    bridge_melt['water_year'] = bridge_melt['water_year'].astype(int)

    data = data.merge(bridge_melt[['OPENET_ID', 'ACRES', 'HR_NAME', 'Basin_Subb', 'GSA_ID', 'water_year', 'crop']], on=['OPENET_ID', 'water_year'], how='left')
    data.to_csv(data_with_crops_path, index=False)
print('done')

print('merging water year classifications')
water_year_class_path = Path(__file__).resolve().parent.parent / 'geodata' / 'hr_regions_wateryear_type.csv'
water_year_class = pd.read_csv(water_year_class_path)
data = data.merge(water_year_class[['HR_NAME', 'water_year', 'wb_class']], how='left', on=['HR_NAME', 'water_year'])
data = data.rename(columns={'wb_class': 'water_year_class'})
print('done')


#region Hydrologic Regions
print('hydrologic summary')
hydrologic_summary = data.assign(weighted_value=data['value_ft'] * data['ACRES']).groupby(['HR_NAME', 'dataset', 'water_year', 'water_year_class', 'crop'], as_index=False).aggregate(
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


print('Getting valid crops for hydrologic')
hydrologic_crop_coverage = bridge[bridge['HR_NAME'].notna()].groupby(['HR_NAME', 'crop_2018'], as_index=False).aggregate(crop_total_acres_2018=('ACRES', 'sum'))
hydrologic_crop_coverage = hydrologic_crop_coverage.rename(columns={'crop_2018': 'crop'})
hydrologic_crop_coverage['perc_2018'] = (hydrologic_crop_coverage['crop_total_acres_2018'] / hydrologic_crop_coverage['HR_NAME'].map(hydrologic_region_acreage)) * 100

for year in range(2019, 2025):
    hydrologic_next_year_coverage = bridge[bridge['HR_NAME'].notna()].groupby(['HR_NAME', f'crop_{year}'], as_index=False).aggregate(crop_total_acres=('ACRES', 'sum'))
    hydrologic_next_year_coverage = hydrologic_next_year_coverage.rename(columns={'crop_total_acres': f'crop_total_acres_{year}', f'crop_{year}': 'crop'})
    hydrologic_next_year_coverage[f'perc_{year}'] = (hydrologic_next_year_coverage[f'crop_total_acres_{year}'] / hydrologic_next_year_coverage['HR_NAME'].map(hydrologic_region_acreage)) * 100

    hydrologic_crop_coverage = pd.merge(hydrologic_crop_coverage, hydrologic_next_year_coverage, how='outer', on=['HR_NAME', 'crop'])

hydrologic_crop_coverage = hydrologic_crop_coverage.fillna(0)
hydrologic_crop_coverage['avg_perc'] = (hydrologic_crop_coverage['perc_2018']
                                        + hydrologic_crop_coverage['perc_2019'] 
                                        + hydrologic_crop_coverage['perc_2020'] 
                                        + hydrologic_crop_coverage['perc_2021'] 
                                        + hydrologic_crop_coverage['perc_2022'] 
                                        + hydrologic_crop_coverage['perc_2023'] 
                                        + hydrologic_crop_coverage['perc_2024']) / 7

hydrologic_crop_coverage_path = Path(__file__).resolve().parent.parent / 'data_summaries' / 'hydrologic_crop_coverage.csv'
hydrologic_crop_coverage[['HR_NAME', 'crop', 'avg_perc']].to_csv(hydrologic_crop_coverage_path, index=False)
print('done')
#endregion




#region Subbasins
print('subbasin summary')
subbasin_summary = data.assign(weighted_value=data['value_ft'] * data['ACRES']).groupby(['Basin_Subb', 'dataset', 'water_year', 'water_year_class', 'crop'], as_index=False).aggregate(
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


print('Getting valid crops for subbasins')
subbasin_crop_coverage = bridge[bridge['Basin_Subb'].notna()].groupby(['Basin_Subb', 'crop_2018'], as_index=False).aggregate(crop_total_acres_2018=('ACRES', 'sum'))
subbasin_crop_coverage = subbasin_crop_coverage.rename(columns={'crop_2018': 'crop'})
subbasin_crop_coverage['perc_2018'] = (subbasin_crop_coverage['crop_total_acres_2018'] / subbasin_crop_coverage['Basin_Subb'].map(subbasin_acreage)) * 100

for year in range(2019, 2025):
    subbasin_next_year_coverage = bridge[bridge['Basin_Subb'].notna()].groupby(['Basin_Subb', f'crop_{year}'], as_index=False).aggregate(crop_total_acres=('ACRES', 'sum'))
    subbasin_next_year_coverage = subbasin_next_year_coverage.rename(columns={'crop_total_acres': f'crop_total_acres_{year}', f'crop_{year}': 'crop'})
    subbasin_next_year_coverage[f'perc_{year}'] = (subbasin_next_year_coverage[f'crop_total_acres_{year}'] / subbasin_next_year_coverage['Basin_Subb'].map(subbasin_acreage)) * 100

    subbasin_crop_coverage = pd.merge(subbasin_crop_coverage, subbasin_next_year_coverage, how='outer', on=['Basin_Subb', 'crop'])

subbasin_crop_coverage = subbasin_crop_coverage.fillna(0)
subbasin_crop_coverage['avg_perc'] = (subbasin_crop_coverage['perc_2018'] 
                                      + subbasin_crop_coverage['perc_2019'] 
                                      + subbasin_crop_coverage['perc_2020'] 
                                      + subbasin_crop_coverage['perc_2021'] 
                                      + subbasin_crop_coverage['perc_2022'] 
                                      + subbasin_crop_coverage['perc_2023'] 
                                      + subbasin_crop_coverage['perc_2024']) / 7

subbasin_crop_coverage_path = Path(__file__).resolve().parent.parent / 'data_summaries' / 'subbasin_crop_coverage.csv'
subbasin_crop_coverage[['Basin_Subb', 'crop', 'avg_perc']].to_csv(subbasin_crop_coverage_path, index=False)
print('done')
#endregion




#region GSAs
print('gsa summary')
gsa_summary = data.assign(weighted_value=data['value_ft'] * data['ACRES']).groupby(['GSA_ID', 'dataset', 'water_year', 'water_year_class', 'crop'], as_index=False).aggregate(
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

print('Getting valid crops for gsas')
gsa_crop_coverage = bridge[bridge['GSA_ID'].notna()].groupby(['GSA_ID', 'crop_2018'], as_index=False).aggregate(crop_total_acres_2018=('ACRES', 'sum'))
gsa_crop_coverage = gsa_crop_coverage.rename(columns={'crop_2018': 'crop'})
gsa_crop_coverage['perc_2018'] = (gsa_crop_coverage['crop_total_acres_2018'] / gsa_crop_coverage['GSA_ID'].map(gsa_acreage)) * 100

for year in range(2019, 2025):
    gsa_next_year_coverage = bridge[bridge['GSA_ID'].notna()].groupby(['GSA_ID', f'crop_{year}'], as_index=False).aggregate(crop_total_acres=('ACRES', 'sum'))
    gsa_next_year_coverage = gsa_next_year_coverage.rename(columns={'crop_total_acres': f'crop_total_acres_{year}', f'crop_{year}': 'crop'})
    gsa_next_year_coverage[f'perc_{year}'] = (gsa_next_year_coverage[f'crop_total_acres_{year}'] / gsa_next_year_coverage['GSA_ID'].map(gsa_acreage)) * 100

    gsa_crop_coverage = pd.merge(gsa_crop_coverage, gsa_next_year_coverage, how='outer', on=['GSA_ID', 'crop'])

gsa_crop_coverage = gsa_crop_coverage.fillna(0)
gsa_crop_coverage['avg_perc'] = (gsa_crop_coverage['perc_2018'] 
                                      + gsa_crop_coverage['perc_2019'] 
                                      + gsa_crop_coverage['perc_2020'] 
                                      + gsa_crop_coverage['perc_2021'] 
                                      + gsa_crop_coverage['perc_2022'] 
                                      + gsa_crop_coverage['perc_2023'] 
                                      + gsa_crop_coverage['perc_2024']) / 7

gsa_crop_coverage_path = Path(__file__).resolve().parent.parent / 'data_summaries' / 'gsa_crop_coverage.csv'
gsa_crop_coverage[['GSA_ID', 'crop', 'avg_perc']].to_csv(gsa_crop_coverage_path, index=False)
print('done')
#endregion

