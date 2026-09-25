import pandas as pd
import geopandas as gpd
from pathlib import Path
import ee
import os
from dotenv import load_dotenv

load_dotenv()
project_id = os.getenv('PROJECT_ID')

ee.Authenticate()
ee.Initialize(project=project_id)

# Hydrologic Regions
hydrologic_path = Path(__file__).resolve().parent.parent / 'geodata' / 'hydrologic_regions.geojson'
hydrologic_gdf = gpd.read_file(hydrologic_path)

# Subbasins
subbasin_path = Path(__file__).resolve().parent.parent / 'geodata' / 'subbasins.geojson'
subbasin_gdf = gpd.read_file(subbasin_path)

# Overdrafted Subbasins
overdrafted_path = Path(__file__).resolve().parent.parent / 'geodata' / 'overdrafted_subbasins.geojson'
overdrafted_gdf = gpd.read_file(overdrafted_path)

# GSAs
gsa_path = Path(__file__).resolve().parent.parent / 'geodata' / 'groundwater_sustainability_agencies.geojson'
gsa_gdf = gpd.read_file(gsa_path)
gsa_gdf.drop(columns=['Basin_Name', 'Basin_Numb', 'Basin_Su_1'], inplace=True)

# LandIQ crop code to name conversion stuff
def set_default_mode(feature):
    mode_value = feature.get('mode')
    default_value = ee.Algorithms.If(mode_value, mode_value, 0)
    return feature.set('mode', default_value)

landiq_conversion_path = Path(__file__).resolve().parent.parent / 'landiq_conversion.csv'
if landiq_conversion_path.is_file():
    landiq_conversion = pd.read_csv(landiq_conversion_path).set_index('landiq_code')['crop_name'].to_dict()
else:
    landiq_cropland_path = Path(__file__).resolve().parent.parent / 'landiq_to_cropland.csv'
    landiq_conversion = pd.read_csv(landiq_cropland_path).set_index('code')['cropland'].to_dict()
    landiq_conversion[0] = 'default'

    cropland_name_path = Path(__file__).resolve().parent.parent / 'cropland_to_name.csv'
    cropland_to_name = pd.read_csv(cropland_name_path).set_index('code')['cadwr_crop'].to_dict()
    cropland_to_name['default'] = 'NA'

    for landiq_code, cropland in landiq_conversion.items():
        crop_name = ''
        crops: list[str] = cropland.split('-')

        for crop in crops:
            if '*' in crop:
                continue

            if crop_name != '':
                crop_name = crop_name + ', '

            crop_name = crop_name + cropland_to_name[crop]

        landiq_conversion[landiq_code] = crop_name

    df = pd.DataFrame(list(landiq_conversion.items()), columns=['landiq_code', 'cropland'])
    df = df.rename(columns={'cropland': 'crop_name'})
    
    df.to_csv(landiq_conversion_path, index=False)

# Fields
fields = ee.FeatureCollection(f'projects/{project_id}/assets/land_repurposing_app/openet_geodatabase_v2_clipped')

fields_path = Path(__file__).resolve().parent.parent / 'geodata' / 'fields.geojson'
if fields_path.is_file():
    print('Loading Field GDF')
    field_gdf = gpd.read_file(fields_path)
else:
    print('Computing Features to make Field GDF')
    field_gdf: gpd.GeoDataFrame = ee.data.computeFeatures({'expression': fields, 'fileFormat': 'GEOPANDAS_GEODATAFRAME'})
    field_gdf = field_gdf[['ACRES', 'HUC12', 'OPENET_ID', 'geometry']]
    print('Done')

    # Add LandIQ Annual Crop Types
    print('Adding LandIQ data')
    for year in range(2018, 2025):
        print(f'    Adding {year} data')

        landiq_path = Path(__file__).resolve().parent.parent / 'geodata' / f'landiq_results_{year}.geojson'
        if landiq_path.is_file():
            results_gdf = gpd.read_file(landiq_path)
        else:
            landiq_image = ee.Image(f'projects/{project_id}/assets/land_repurposing_app/{year}_cadwr_cropland_30m')
            print('        Reducing regions on image')
            results = landiq_image.reduceRegions(fields, ee.Reducer.mode().unweighted(), 30)
            results = results.map(set_default_mode)
            print('        Done')
            print('        Converting results to GeoDataFrame')
            results_gdf: gpd.GeoDataFrame = ee.data.computeFeatures({'expression': results, 'fileFormat': 'GEOPANDAS_GEODATAFRAME'})
            results_gdf.rename(columns={'mode': f'crop_{year}'}, inplace=True)
            results_gdf[f'crop_{year}'] = results_gdf[f'crop_{year}'].astype(int)
            results_gdf[f'crop_{year}'] = results_gdf[f'crop_{year}'].map(landiq_conversion)
            print('        Done')
            print('        Saving')
            results_gdf.to_file(landiq_path, index=False)
            print('        Done')
        print('        Joining fields and results')
        field_gdf = field_gdf.merge(results_gdf[[f'crop_{year}', 'geometry']], how='left', on='geometry')
        # field_gdf = gpd.merge(field_gdf, results_gdf[[f'crop_{year}', 'geometry']], how='left', predicate='intersects').drop(columns='index_right')
        print('        Done')
        print('    Done')
        print('Done')
    field_gdf.to_file(fields_path, index=False)
print('Done')


    
# Prepare fields
print('Preparing fields')
print('    Copying GDF')
field_points = field_gdf.copy()[['OPENET_ID', 'ACRES', 'crop_2018', 'crop_2019', 'crop_2020', 'crop_2021', 'crop_2022', 'crop_2023', 'crop_2024', 'geometry']]
print('    Done')
print('    Computing representative points')
field_points['geometry'] = field_points.geometry.representative_point()
print('    Done')
print('Done')

# Add Hydrologic Regions
print('Adding Hydrologic Regions')
field_points = gpd.sjoin(field_points, hydrologic_gdf[['HR_NAME', 'geometry']], how='left', predicate='intersects').drop(columns='index_right')
print('Done')

# Add Subbasins
print('Adding Subbasins')
field_points = gpd.sjoin(field_points, subbasin_gdf[['Basin_Subb', 'geometry']], how='left', predicate='intersects').drop(columns='index_right')
field_points['overdrafted_subbasin'] = field_points['Basin_Subb'].isin(overdrafted_gdf['Basin_Subb'].values)
print('Done')

# Add GSAs
print('Adding GSAs')
field_points = gpd.sjoin(field_points, gsa_gdf[['GSA_ID', 'geometry']], how='left', predicate='intersects').drop(columns='index_right')
print('Done')

# Saving
print('Saving')
path = Path(__file__).resolve().parent.parent / 'bridge_table.csv'
field_points[[
    'OPENET_ID', 'ACRES', 'GSA_ID', 'Basin_Subb', 'HR_NAME', 
    'crop_2018', 'crop_2019', 'crop_2020', 'crop_2021', 'crop_2022', 'crop_2023', 'crop_2024'
]].to_csv(path, index=False)
print('Done')

# Filter out fields less than 5 acres
# Filter out fields that have no crop ids
# By crop, default to top 5, have crops that have at least 2% of acerage of region
# LandIQ 2024 field boundaries
# filter out no 2024 crops, aggregate to compare to AJ's repo