from pathlib import Path
import ee
import geemap
import os
from dotenv import load_dotenv

load_dotenv()
project_id = os.getenv('PROJECT_ID')

ee.Authenticate()
ee.Initialize(project=project_id)

hydrologic_path = Path(__file__).resolve().parent.parent / 'geodata' / 'hydrologic_regions.geojson'
if hydrologic_path.is_file():
    print('Hydrologic Regions GeoJSON already exists. Skipping...')
else:
    print('Retrieving Hydrologic Regions GeoJSON...')
    hydrologic_regions = ee.FeatureCollection(f'projects/{project_id}/assets/land_repurposing_app/i03_hydrologic_regions_clipped')
    geemap.ee_to_geojson(hydrologic_regions, filename=str(hydrologic_path))
    print('Done')

subbasin_path = Path(__file__).resolve().parent.parent / 'geodata' / 'subbasins.geojson'
if subbasin_path.is_file():
    print('Subbasins GeoJSON already exists. Skipping...')
else:
    print('Retrieving Subbasins GeoJSON...')
    subbasins = ee.FeatureCollection(f'projects/{project_id}/assets/land_repurposing_app/i08_subbasins_clipped')
    geemap.ee_to_geojson(subbasins, filename=str(subbasin_path))
    print('Done')

overdrafted_path = Path(__file__).resolve().parent.parent / 'geodata' / 'overdrafted_subbasins.geojson'
if overdrafted_path.is_file():
    print('Overdrafted Subbasins GeoJSON already exists. Skipping...')
else:
    print('Retrieving Overdrafted Subbasins GeoJSON...')
    overdrafted = ee.FeatureCollection(f'projects/{project_id}/assets/land_repurposing_app/overdrafted_subbasins_clipped')
    geemap.ee_to_geojson(overdrafted, filename=str(overdrafted_path))
    print('Done')

gsa_path = Path(__file__).resolve().parent.parent / 'geodata' / 'groundwater_sustainability_agencies.geojson'
if gsa_path.is_file():
    print('Groundwater Sustainability Agencies GeoJSON already exists. Skipping...')
else:
    print('Retrieving Groundwater Sustainability Agencies GeoJSON...')
    gsas = ee.FeatureCollection(f'projects/{project_id}/assets/land_repurposing_app/groundwater_sustainability_agencies_clipped')
    geemap.ee_to_geojson(gsas, filename=str(gsa_path))
    print('Done')