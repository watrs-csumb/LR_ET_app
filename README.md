# Land Repurposing App
This app is intended to make visualization of regional ET data simple and accessible, primarily for the purpose of identifying alternative land use options to fit water allocation limits.

## Setup
An environment file (.env) is required for a single value: PROJECT_ID.
The PROJECT_ID should be the project id of a Google Earth Engine project with the appropriate assets.

## Usage
- Run the following command in the terminal: shiny run --reload main.py
- Visit http://127.0.0.1:8000 in your browser of choice



# Land Repurposing App - Data Preparation
These tools are set up to prepare the data required to run the Land Repurposing app. This workflow needs to be followed to provide the necessary data before the app can be used.
Following the workflow in this order is recommended, even though some steps aren't necessarily order-dependent.


## ENV File
An environment file (.env) is required for a single value: PROJECT_ID.
The PROJECT_ID should be the project id of a Google Earth Engine project with the appropriate assets.


## Retrieving Spatial Data
The app uses four spatial datasets for non-field boundaries (hydrologic regions, subbasins, critically overdrafted subbasins, and groundwater sustainability agencies).
The Google Earth Engine project (the one who's ID is in the .env file) has assets for these.

Running the *get_geojsons.py* script will retrieve these assets as Feature Collections, convert them to GeoPandas GeoDataFrames, and save them as GeoJSONs in the **geodata** directory.


## Downloading OpenET Data


## Building the Bridge Table


## Generating Summaries