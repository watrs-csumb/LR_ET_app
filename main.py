import json
from pathlib import Path
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import geopandas as gpd
from shapely.geometry import Point
import textwrap
from adjustText import adjust_text
from faicons import icon_svg

from ipyleaflet import GeoJSON, Map
from shiny import reactive
from shiny.express import input, render, ui
from shinywidgets import render_widget

MIN_AVG_CROP_COVERAGE_PERC = 1  # The minimum average percentage of a region's total acreage over all years a crop needs to cover to be included in the application.

plt.style.use('bmh')

selection = reactive.Value('')  # Stores name of last clicked map region (HR_NAME, Basin_Subb, or GSA_Name)

#region Map layer and GDF Loading
def get_style(feature_id):
    '''Set selected region to a dark purple.'''
    with reactive.isolate():
        selected_id = selection.get()
    
    if feature_id == selected_id:
        return {
            'opacity': 1, 
            'fillOpacity': 0.7,
            'weight': 1,
            'color': 'black',
            'fillColor': 'purple',
        }
    else:
        return {
            'opacity': 1, 
            'fillOpacity': 0.1,
            'weight': 1,
            'color': 'black',
            'fillColor': 'black',
        }

def get_hydrologic_region_style(feature):
    '''Calls get_style with the HR_NAME to match the reactive selection value.'''
    return get_style(feature['properties'].get('HR_NAME'))

hydrologic_path = Path(__file__).resolve().parent / 'geodata' / 'hydrologic_regions.geojson'
with open(hydrologic_path, 'r') as f:
    hydrologic_regions = json.load(f)

hydrologic_layer = GeoJSON(
    data=hydrologic_regions,
    style_callback=get_hydrologic_region_style,
    hover_style={'fillOpacity': 0.5},
)

hydrologic_gdf = gpd.read_file(hydrologic_path)
hydrologic_gdf.set_geometry('geometry', inplace=True)


def get_subbasin_style(feature):
    '''Calls get_style with the Basin_Su_1 (Subbasin Name) to match the reactive selection value.'''
    return get_style(feature['properties'].get('Basin_Su_1'))

subbasin_path = Path(__file__).resolve().parent / 'geodata' / 'subbasins.geojson'
with open(subbasin_path, 'r') as f:
    subbasins = json.load(f)

subbasin_layer = GeoJSON(
    data=subbasins,
    style_callback=get_subbasin_style,
    hover_style={'fillOpacity': 0.5},
)

subbasin_gdf = gpd.read_file(subbasin_path)
subbasin_gdf.set_geometry('geometry', inplace=True)


overdrafted_path = Path(__file__).resolve().parent / 'geodata' / 'overdrafted_subbasins.geojson'
with open(overdrafted_path, 'r') as f:
    overdrafted_basins = json.load(f)

overdrafted_layer = GeoJSON(
    data=overdrafted_basins,
    style={  
        'opacity': 0, 
        'fillOpacity': 0.5,
        'weight': 1,
        'fillColor': 'red',
    },
)

overdrafted_gdf = gpd.read_file(overdrafted_path)
overdrafted_gdf.set_geometry('geometry', inplace=True)


def get_gsa_style(feature):
    '''Calls get_style with the GSA_Name to match the reactive selection value.'''
    return get_style(feature['properties'].get('GSA_Name'))

gsa_path = Path(__file__).resolve().parent / 'geodata' / 'groundwater_sustainability_agencies.geojson'
with open(gsa_path, 'r') as f:
    gsa_regions = json.load(f)

gsa_layer = GeoJSON(
    data=gsa_regions,
    style_callback=get_gsa_style,
    point_style={  # erases random point geometry in the gsa dataset
        'radius': 0,
        'fillOpacity': 0,
        'opacity': 0,
        'interactive': False
    },
    hover_style={'fillOpacity': 0.5},
)

gsa_gdf = gpd.read_file(gsa_path)
gsa_gdf.set_geometry('geometry', inplace=True)
# endregion


#region Summary Loading
# Summaries contain general aggregated ET, precip, and net ET data (no consideration of crop types)
hydrologic_summary_path = Path(__file__).resolve().parent / 'data_summaries' / 'hydrologic_summary.csv'
hydrologic_summary = pd.read_csv(hydrologic_summary_path)

subbasin_summary_path = Path(__file__).resolve().parent / 'data_summaries' / 'subbasin_summary.csv'
subbasin_summary = pd.read_csv(subbasin_summary_path)

gsa_summary_path = Path(__file__).resolve().parent / 'data_summaries' / 'gsa_summary.csv'
gsa_summary = pd.read_csv(gsa_summary_path)

# Boxplot summaries contain regionally-aggregated field information ready to manually build boxplots
hydrologic_boxplot_path = Path(__file__).resolve().parent / 'data_summaries' / 'hydrologic_boxplot.csv'
hydrologic_boxplot = pd.read_csv(hydrologic_boxplot_path)

subbasin_boxplot_path = Path(__file__).resolve().parent / 'data_summaries' / 'subbasin_boxplot.csv'
subbasin_boxplot = pd.read_csv(subbasin_boxplot_path)

gsa_boxplot_path = Path(__file__).resolve().parent / 'data_summaries' / 'gsa_boxplot.csv'
gsa_boxplot = pd.read_csv(gsa_boxplot_path)

# Crop summaries contain aggregated ET, precip, and net ET data by crop type
# Crop coverage contains information on how much acreage each crop takes, and is used for filtering out rare crop combinations
hydrologic_crop_summary_path = Path(__file__).resolve().parent / 'data_summaries' / 'hydrologic_crop_summary.csv'
hydrologic_crop_summary = pd.read_csv(hydrologic_crop_summary_path)
hydrologic_crop_coverage_path = Path(__file__).resolve().parent / 'data_summaries' / 'hydrologic_crop_coverage.csv'
hydrologic_crop_coverage = pd.read_csv(hydrologic_crop_coverage_path)

subbasin_crop_summary_path = Path(__file__).resolve().parent / 'data_summaries' / 'subbasin_crop_summary.csv'
subbasin_crop_summary = pd.read_csv(subbasin_crop_summary_path)
subbasin_crop_coverage_path = Path(__file__).resolve().parent / 'data_summaries' / 'subbasin_crop_coverage.csv'
subbasin_crop_coverage = pd.read_csv(subbasin_crop_coverage_path)

gsa_crop_summary_path = Path(__file__).resolve().parent / 'data_summaries' / 'gsa_crop_summary.csv'
gsa_crop_summary = pd.read_csv(gsa_crop_summary_path)
gsa_crop_coverage_path = Path(__file__).resolve().parent / 'data_summaries' / 'gsa_crop_coverage.csv'
gsa_crop_coverage = pd.read_csv(gsa_crop_coverage_path)
# endregion


# The bridge table contains crosswalk information, including the acreage, hydrologic region, subbasin, gsa, and annual crop types for each field
bridge_path = Path(__file__).resolve().parent / 'bridge_table.csv'
bridge = pd.read_csv(bridge_path)

def empty_plot(message: str = 'Please select a region...'):
    '''Displays a message in place of an actual plot.'''
    fig, ax = plt.subplots(figsize=(6, 4))
    
    ax.text(
        0.5, 0.5, 
        message, 
        fontsize=22, 
        color='black',
        ha='center',
        va='center'
    )
    ax.axis('off')
    return ax

def get_data(selection_type: str, region: str, data: str = 'id'):
    '''
        Get a value from a geodataframe. This is mainly used to get IDs from names, but can be used to retrieve any valid value.

        Args:
            selection_type: The boundary scale. Primarily takes from the selection_type ui.input
            region: The region name.
            data: The value to retrieve from the geodataframe. Defaults to "id", which is a keyword for getting any region's ID column.

        Returns:
            The data value for that region.
    '''

    if selection_type == 'i03':
        search_gdf = hydrologic_gdf
        name_column = 'HR_NAME'
        id_column = 'OBJECTID'
    elif selection_type == 'i08':
        search_gdf = subbasin_gdf
        name_column = 'Basin_Su_1'
        id_column = 'Basin_Subb'
    elif selection_type == 'gsa':
        search_gdf = gsa_gdf
        name_column = 'GSA_Name'
        id_column = 'GSA_ID'
    else:
        return '0.0'

    if data == 'id':
        gdf = search_gdf[search_gdf[name_column] == region][id_column]

        if len(gdf) > 0:
            return str(gdf.iloc[0])
    elif data in search_gdf.columns:
        gdf = search_gdf[search_gdf[name_column] == region][data]

        if len(gdf) > 0:
            return gdf.iloc[0]
    
    return '0.0'

def outlier_design(total_count):
    return {
        'marker': 'o', 
        'markerfacecolor': 'blue', 
        'markeredgecolor': 'none', 
        'alpha': max(0.03, 1 / (1 + np.log10(total_count)))
    }

def get_annual_dist(selection_type: str, region: str, value: str = 'ET'):
    if selection() != '':
        if value == 'ET':
            dataset = 'ensemble'
        elif value == 'PR':
            dataset = 'gridmet_pr'
        elif value == 'Net ET':
            dataset = 'net_et'

        if selection_type == 'i03':
            boxplots = hydrologic_boxplot[(hydrologic_boxplot['HR_NAME'] == region) & (hydrologic_boxplot['dataset'] == dataset)]
        elif selection_type == 'i08':
            code = get_data(selection_type=input.selection_type.get(), region=selection(), data='id')
            boxplots = subbasin_boxplot[(subbasin_boxplot['Basin_Subb'] == code) & (subbasin_boxplot['dataset'] == dataset)]
        elif selection_type == 'gsa':
            code = int(get_data(selection_type=input.selection_type.get(), region=selection(), data='id'))
            boxplots = gsa_boxplot[(gsa_boxplot['GSA_ID'] == code) & (gsa_boxplot['dataset'] == dataset)]

        stats = []
        lowest = 100
        for water_year_class in ['Wet', 'Average', 'Dry']:
            box = boxplots[boxplots['water_year_class'] == water_year_class]

            if box.shape[0] == 0:
                continue
            box = box.iloc[0]

            stats.append({
                'med': box['MEDIAN'],
                'q1': box['PCT25'],
                'q3': box['PCT75'],
                'whislo': box['LOWER_WHISKER'],
                'whishi': box['UPPER_WHISKER'],
                'label': water_year_class,
            })

            if box['LOWER_WHISKER'] < lowest:
                lowest = box['LOWER_WHISKER']

        fig, ax = plt.subplots()
        ax.bxp(stats, showfliers=False)

        # if summary['value_ft'].min() < 0:
        #     plt.axhline(y=0, linestyle='--', color='black')

        plt.ylim(top=6, bottom=min(-0.01, lowest - 0.01))  # TODO: Un-hardcode this
        plt.xlabel('Water Year Classification')
        plt.ylabel(f'Annual Field {value} (acre-ft / acre)')
        plt.title(f'Annual Field {value} Distribution')
        plt.suptitle('')
        plt.tight_layout()
        return ax
    else:
        return empty_plot()

def get_annual_totals(selection_type: str, region: str, value: str = 'ET'):
    if selection() != '':
        if selection_type == 'i03':
            summary = hydrologic_summary[hydrologic_summary['HR_NAME'] == region]
            summary['total'] = summary['SUM'] / 1000000
            unit = 'millions of'
        elif selection_type == 'i08':
            code = get_data(selection_type=input.selection_type.get(), region=selection(), data='id')
            summary = subbasin_summary[subbasin_summary['Basin_Subb'] == code]
            summary['total'] = summary['SUM'] / 1000000
            unit = 'millions of'
        elif selection_type == 'gsa':
            code = int(get_data(selection_type=input.selection_type.get(), region=selection(), data='id'))
            summary = gsa_summary[gsa_summary['GSA_ID'] == code]
            summary['total'] = summary['SUM'] / 1000
            unit = 'thousands of'

        if value == 'ET':
            dataset = 'ensemble'
        elif value == 'PR':
            dataset = 'gridmet_pr'
        elif value == 'Net ET':
            dataset = 'net_et'

        summary = summary[summary['dataset'] == dataset]
        summary['zeroes'] = 0

        fig, ax = plt.subplots()
        for water_year_class in [('Wet', 'blue'), ('Average', 'green'), ('Dry', 'red')]:
            summary[summary['water_year_class'] == water_year_class[0]].plot.scatter(
                x='total', y='zeroes', 
                c=water_year_class[1], 
                s=100,
                alpha=0.7,
                ax=ax, label=water_year_class[0]
            )

        plt.gca().get_yaxis().set_visible(False)

        plt.xlabel(f'Total {value}\n({unit} acre-ft)')
        plt.title(f'Annual Region {value} Totals')
        plt.legend(bbox_to_anchor=(1,1))
        plt.tight_layout()

        labels = [ax.text(point.total, point.zeroes, point.water_year) for point in summary.itertuples()]
        adjust_text(
            labels, arrowprops=dict(arrowstyle='-', color='gray', lw=0.5), 
            only_move={'points': 'xy+', 'text': 'xy+', 'objects': 'xy+'}, 
            expand=(1.2, 1.5), force_static=(0.1, 1), force_explode=(0.1, 0.8)
        )
        return ax
    else:
        return empty_plot()

def get_avg(selection_type: str, region: str, value: str = 'ET'):
    if selection() != '':
        if selection_type == 'i03':
            summary = hydrologic_summary[hydrologic_summary['HR_NAME'] == region]
        elif selection_type == 'i08':
            code = get_data(selection_type=input.selection_type.get(), region=selection(), data='id')
            summary = subbasin_summary[subbasin_summary['Basin_Subb'] == code]
        elif selection_type == 'gsa':
            code = int(get_data(selection_type=input.selection_type.get(), region=selection(), data='id'))
            summary = gsa_summary[gsa_summary['GSA_ID'] == code]

        if value == 'ET':
            dataset = 'ensemble'
        elif value == 'PR':
            dataset = 'gridmet_pr'
        elif value == 'Net ET':
            dataset = 'net_et'

        # Average across years
        return summary[summary['dataset'] == dataset]['weighted_mean'].mean()

def select_crops(selection_type: str, region: str, value: str = 'ET', crop_display_setting: str = 'most_common') -> list[str]:
    '''
        Return list of 10 crops based on provided setting in a specified region across water years 2018 - 2024
    '''
    if selection() != '':
        if crop_display_setting == 'custom':
            return ['custom']

        if value == 'ET':
            dataset = 'ensemble'
        elif value == 'PR':
            dataset = 'gridmet_pr'
        elif value == 'Net ET':
            dataset = 'net_et'

        if selection_type == 'i03':
            selected_region = bridge[bridge['HR_NAME'] == region]
            valid_crops = hydrologic_crop_coverage[
                (hydrologic_crop_coverage['HR_NAME'] == region) & 
                (hydrologic_crop_coverage['avg_perc'] >= MIN_AVG_CROP_COVERAGE_PERC)
            ]['crop'].unique()
            summary = hydrologic_crop_summary[
                (hydrologic_crop_summary['HR_NAME'] == region) & (hydrologic_crop_summary['dataset'] == dataset) & 
                (hydrologic_crop_summary['water_year_class'] == 'all') & (hydrologic_crop_summary['crop'].isin(valid_crops))
            ]
        elif selection_type == 'i08':
            code = get_data(selection_type=input.selection_type.get(), region=selection(), data='id')
            selected_region = bridge[bridge['Basin_Subb'] == code]
            valid_crops = subbasin_crop_coverage[
                (subbasin_crop_coverage['Basin_Subb'] == code) & 
                (subbasin_crop_coverage['avg_perc'] >= MIN_AVG_CROP_COVERAGE_PERC)
            ]['crop'].unique()
            summary = subbasin_crop_summary[
                (subbasin_crop_summary['Basin_Subb'] == code) & (subbasin_crop_summary['dataset'] == dataset) & 
                (subbasin_crop_summary['water_year_class'] == 'all') & (subbasin_crop_summary['crop'].isin(valid_crops))
            ]
        elif selection_type == 'gsa':
            code = int(get_data(selection_type=input.selection_type.get(), region=selection(), data='id'))
            selected_region = bridge[bridge['GSA_ID'] == code]
            valid_crops = gsa_crop_coverage[
                (gsa_crop_coverage['GSA_ID'] == code) & 
                (gsa_crop_coverage['avg_perc'] >= MIN_AVG_CROP_COVERAGE_PERC)
            ]['crop'].unique()
            summary = gsa_crop_summary[
                (gsa_crop_summary['GSA_ID'] == code) & (gsa_crop_summary['dataset'] == dataset) & 
                (gsa_crop_summary['water_year_class'] == 'all') & (gsa_crop_summary['crop'].isin(valid_crops))
            ]
        else:
            return []

        if crop_display_setting == 'most_common':
            stacked = selected_region[['crop_2018', 'crop_2019', 'crop_2020', 'crop_2021', 'crop_2022', 'crop_2023', 'crop_2024']].stack()
            return list(stacked[stacked.isin(valid_crops)].value_counts().head(10).index.values) 
        elif crop_display_setting == 'most_et':
            return list(summary.sort_values('weighted_mean', ascending=False).head(10)['crop'].values)
        elif crop_display_setting == 'least_et':
            return list(summary.sort_values('weighted_mean', ascending=True).head(10)['crop'].values)
        elif crop_display_setting == 'mix':
            return list(summary.sort_values('weighted_mean', ascending=False).head(5)['crop'].values) + list(summary.sort_values('weighted_mean', ascending=True).head(5)['crop'].values)
        else:
            return []
    else:
        return []

def get_crops_for_selectize(selection_type: str, region: str) -> dict[str, str]:
    if selection() != '':
        if selection_type == 'i03':   #TODO: Working on getting the selectize to only use valid crops (ones with enough coverage)
            crops = hydrologic_crop_coverage[
                (hydrologic_crop_coverage['HR_NAME'] == region) & 
                (hydrologic_crop_coverage['avg_perc'] >= MIN_AVG_CROP_COVERAGE_PERC)
            ]['crop'].sort_values().unique()
            # crops = hydrologic_crop_summary[hydrologic_crop_summary['HR_NAME'] == region]['crop'].sort_values().unique()
        if selection_type == 'i08':
            code = get_data(selection_type=input.selection_type.get(), region=selection(), data='id')
            crops = subbasin_crop_coverage[
                (subbasin_crop_coverage['Basin_Subb'] == code) & 
                (subbasin_crop_coverage['avg_perc'] >= MIN_AVG_CROP_COVERAGE_PERC)
            ]['crop'].sort_values().unique()
            # crops = subbasin_crop_summary[subbasin_crop_summary['Basin_Subb'] == code]['crop'].sort_values().unique()
        elif selection_type == 'gsa':
            code = int(get_data(selection_type=input.selection_type.get(), region=selection(), data='id'))
            crops = gsa_crop_coverage[
                (gsa_crop_coverage['GSA_ID'] == code) & 
                (gsa_crop_coverage['avg_perc'] >= MIN_AVG_CROP_COVERAGE_PERC)
            ]['crop'].sort_values().unique()
            # crops = gsa_crop_summary[gsa_crop_summary['GSA_ID'] == code]['crop'].sort_values().unique()

        all_crops = {crop: crop for crop in crops}
        return all_crops
    else:
        return {}

def get_crop_comparison(selection_type: str, region: str, crops: list[str], value: str = 'ET'):
    if selection() != '':
        if selection_type == 'i03':
            summary = hydrologic_crop_summary[(hydrologic_crop_summary['HR_NAME'] == region) & (hydrologic_crop_summary['crop'].isin(crops)) & (hydrologic_crop_summary['water_year_class'] == 'all')]
        if selection_type == 'i08':
            code = get_data(selection_type=input.selection_type.get(), region=selection(), data='id')
            summary = subbasin_crop_summary[(subbasin_crop_summary['Basin_Subb'] == code) & (subbasin_crop_summary['crop'].isin(crops)) & (subbasin_crop_summary['water_year_class'] == 'all')]
        elif selection_type == 'gsa':
            code = int(get_data(selection_type=input.selection_type.get(), region=selection(), data='id'))
            summary = gsa_crop_summary[(gsa_crop_summary['GSA_ID'] == code) & (gsa_crop_summary['crop'].isin(crops)) & (gsa_crop_summary['water_year_class'] == 'all')]
        
        if value == 'ET':
            fig, ax = plt.subplots()
            summary[summary['dataset'] == 'ensemble'].sort_values('weighted_mean', ascending=False).plot.barh(x='crop', y='weighted_mean', legend=False, ax=ax)
        elif value == 'PR':
            fig, ax = plt.subplots()
            summary[summary['dataset'] == 'gridmet_pr'].sort_values('weighted_mean', ascending=False).plot.barh(x='crop', y='weighted_mean', legend=False, ax=ax)
        elif value == 'Net ET':
            fig, ax = plt.subplots()
            summary[summary['dataset'] == 'net_et'].sort_values('weighted_mean', ascending=False).plot.barh(x='crop', y='weighted_mean', legend=False, ax=ax)

        # Wrap y-axis tick labels
        wrapped_labels = [textwrap.fill(label.get_text(), 15) for label in ax.get_yticklabels()]
        ax.set_yticklabels(wrapped_labels, ha='right', va='center')

        plt.title(f'Mean Annual {value} by Crop')
        plt.xlabel(f'Mean Annual {value} (acre-ft / acre)')
        plt.ylabel('')
        plt.tight_layout()
        return ax
    else:
        return empty_plot()

def get_crop_calculator_comparison(selection_type: str, region: str, curr_crop: str, target_crops: list[str], acreage: float, display_relative: str, value: str = 'ET', water_year_class: str = 'all'):
    if selection() != '':
        if value == 'PR':
            return empty_plot('Calculator not available for precipitation data.')

        all_crops = target_crops + [curr_crop]

        if selection_type == 'i03':
            summary = hydrologic_crop_summary[(hydrologic_crop_summary['HR_NAME'] == region) & (hydrologic_crop_summary['crop'].isin(all_crops)) & (hydrologic_crop_summary['water_year_class'] == water_year_class)]
        if selection_type == 'i08':
            code = get_data(selection_type=input.selection_type.get(), region=selection(), data='id')
            summary = subbasin_crop_summary[(subbasin_crop_summary['Basin_Subb'] == code) & (subbasin_crop_summary['crop'].isin(all_crops)) & (subbasin_crop_summary['water_year_class'] == water_year_class)]
        elif selection_type == 'gsa':
            code = int(get_data(selection_type=input.selection_type.get(), region=selection(), data='id'))
            summary = gsa_crop_summary[(gsa_crop_summary['GSA_ID'] == code) & (gsa_crop_summary['crop'].isin(all_crops)) & (gsa_crop_summary['water_year_class'] == water_year_class)]

        # Multiply by acreage to get depth
        summary['estimated_acre_ft'] = summary['weighted_mean'] * acreage

        if(summary[summary['crop'] == curr_crop].shape[0] <= 0):
            return empty_plot(f'Current Crop ({curr_crop})\nis invalid for this region / year type combination.')
        
        if value == 'ET':
            summary = summary[summary['dataset'] == 'ensemble']
        elif value == 'Net ET':
            summary = summary[summary['dataset'] == 'net_et']

        current_estimated = summary[summary['crop'] == curr_crop]['estimated_acre_ft'].mean()
        fig, ax = plt.subplots()

        if display_relative:
            fmt = '%+.2f'

            target_summary = summary[summary['crop'] != curr_crop].groupby('crop')['estimated_acre_ft'].mean() - current_estimated
            sorted_summary = target_summary.sort_values(ascending=False)

            colors = ['C1' if val > 0 else 'C0' for val in sorted_summary.values]
            sorted_summary.plot.barh(color=colors, legend=False, ax=ax)
            
            ax.axvline(x=0, linestyle='--', color='black', label=f'current: {current_estimated:.2f}')
            plt.title(f'Annual {value} Relative to Current Crop')
            plt.xlabel(f'Estimated Annual {value} Relative to Current Crop (acre-ft)')
        else:
            fmt = '%.2f'

            sorted_summary = summary.groupby('crop')['estimated_acre_ft'].mean().sort_values(ascending=False)

            colors = [
                'C1' if val > current_estimated else
                'black' if val == current_estimated else 
                'C0' for val in sorted_summary.values
            ]
            sorted_summary.plot.barh(color=colors, legend=False, ax=ax)
            
            plt.title(f'Mean Annual {value} by Crop')
            plt.xlabel(f'Estimated Annual {value} (acre-ft)')

        # Wrap y-axis tick labels
        wrapped_labels = [textwrap.fill(label.get_text(), 15) for label in ax.get_yticklabels()]
        ax.set_yticklabels(wrapped_labels, ha='right', va='center')

        # Reference line at 0
        ax.axvline(x=0, linestyle='--', color='black', label=f'current: {current_estimated:.2f}')

        # Bar labels
        for container in ax.containers:
            ax.bar_label(container, padding=3, fmt=fmt)
        ax.margins(x=0.15)

        plt.ylabel('')
        plt.tight_layout()
        return ax
    else:
        return empty_plot()

def get_avg_acreage(selection_type: str, region: str, category: str = 'all'):
    if selection() != '':
        if selection_type == 'i03':
            regions = bridge[bridge['HR_NAME'] == region]
        if selection_type == 'i08':
            code = get_data(selection_type=input.selection_type.get(), region=selection(), data='id')
            regions = bridge[bridge['Basin_Subb'] == code]
        elif selection_type == 'gsa':
            code = int(get_data(selection_type=input.selection_type.get(), region=selection(), data='id'))
            regions = bridge[bridge['GSA_ID'] == code]

        total_acres = regions['ACRES'].sum()

        if category == 'perennial':
            return (regions[regions['category_2024'] == 'Perennial']['ACRES'].sum() / total_acres) * 100
        elif category == 'annual':
            return (regions[regions['category_2024'] == 'Annual']['ACRES'].sum() / total_acres) * 100
        elif category == 'fallow':
            return (1 - (regions[regions['category_2024'] == 'Perennial']['ACRES'].sum() / total_acres) - (regions[regions['category_2024'] == 'Annual']['ACRES'].sum() / total_acres)) * 100
        elif category == 'all':
            return total_acres
        else:
            raise ValueError('If specifying a category for acreage calculation, must be either "perennial" or "annual".')

def get_field_count(selection_type: str, region: str):
    if selection() != '':
        if selection_type == 'i03':
            return bridge[bridge['HR_NAME'] == region].shape[0]
        if selection_type == 'i08':
            code = get_data(selection_type=input.selection_type.get(), region=selection(), data='id')
            return bridge[bridge['Basin_Subb'] == code].shape[0]
        elif selection_type == 'gsa':
            code = int(get_data(selection_type=input.selection_type.get(), region=selection(), data='id'))
            return bridge[bridge['GSA_ID'] == code].shape[0]

ui.tags.style('.bslib-value-box .value-box-value { font-size:20px !important; }')
ui.page_opts(window_title='CASC Tool', fillable=True)  # Consumptive wAter uSe Comparison (CASC) Tool

# Icon for the information pop-up in the region info section
info_icon = ui.span(
    icon_svg('circle-info', width='24px', height='24px', position='absolute', margin_right='7px'),
    style='''
        color: #007bff; 
        border-radius: 50%; 
        display: flex; 
        align-items: center; 
        justify-content: center; 
        width: 24px; 
        height: 24px; 
        cursor: pointer;
        position:absolute; 
        top: 5px; 
        right: 7px;
    '''
)


with ui.panel_absolute(top='20px', right='25px'):
    ui.input_action_button(
        'about',
        'ABOUT'
    )

@reactive.effect
@reactive.event(input.about)
def update_about_button():
    if input.about.get() % 2 == 0:
        ui.update_action_button('about', label='ABOUT')
    else:
        ui.update_action_button('about', label='BACK')

# Main Application
with ui.panel_conditional('input.about % 2 === 0'):
    with ui.layout_columns(col_widths=[4, 8]):
        with ui.layout_columns(col_widths=[12, 12]):
            # region Map Control Stuff
            with ui.card():
                with ui.layout_columns(col_widths=[6, 6, 12]):
                    # User input for region boundary type to use
                    ui.input_select(
                        'selection_type',
                        'Boundaries:',
                        {
                            'i03': 'Hydrologic Regions (i03)',
                            'i08': 'Subbasins (i08)',
                            'gsa': 'Groundwater Sustainability Agencies',
                        },
                        selected='i08'  # Default to subbasins
                    )

                    # User input for type of data to use
                    ui.input_select(
                        'value_type',
                        'Values:',
                        {
                            'ET': 'Evapotranspiration (ET)',
                            'PR': 'Precipitation (PR)',
                            'Net ET': 'Net ET (ET - PR)',
                        },
                        selected='ET'  # Default to ET
                    )

                    # Toggle for highlighting critically overdrafted subbasins
                    ui.input_checkbox(
                        'show_overdrafted',
                        'Show Critically Overdrafted Subbasins',
                        False
                    )
            # endregion


            #region Map Stuff
            with ui.card(full_screen=True, fill=True):
                # Create a map centered on California
                m = Map(center=(37.5, -121.2), zoom=6)

                def map_click(**kwargs):
                    '''Handle a map click by storing the'''
                    if kwargs.get('type') == 'click':
                        print(kwargs)
                        # Get click coordinates for determining the region clicked in
                        coords = kwargs.get('coordinates')
                        point = Point(coords[1], coords[0])

                        selection_type = input.selection_type.get()

                        # Determine which region the click coordinates landed in
                        if selection_type == 'i03':
                            click_results = hydrologic_gdf[hydrologic_gdf.geometry.contains(point)]['HR_NAME']
                        elif selection_type == 'i08':
                            click_results = subbasin_gdf[subbasin_gdf.geometry.contains(point)]['Basin_Su_1']
                        elif selection_type == 'gsa':
                            click_results = gsa_gdf[gsa_gdf.geometry.contains(point)]['GSA_Name']

                        # Set the reactive selection value to the clicked region
                        if len(click_results) > 0:
                            selection.set(click_results.iloc[0])
                        else:
                            selection.set('')
                        
                        # Refresh styles to visually update which region is selected
                        # if selection_type == 'i03':
                        hydrologic_layer._update_data(None)
                        # elif selection_type == 'i08':
                        subbasin_layer._update_data(None)
                        # elif selection_type == 'gsa':
                        gsa_layer._update_data(None)

                # Assign the click handler to the map's interaction response
                m.on_interaction(map_click)

                @render_widget
                def map():
                    # m.add(subbasin_layer)  # Starting with subbasin layer as default
                    return m     

                # Update which boundaries are shown when the input value changes. Also, reset selection since the selected region will no longer be shown
                @reactive.effect
                @reactive.event(input.selection_type)
                def _():
                    selection_type = input.selection_type.get()

                    # Reset map to just the base map layer
                    m.layers = m.layers[:1]  

                    # If active, always put the overdrafted subbasins layer below whatever the currently selected boundaries are
                    if input.show_overdrafted.get():
                        m.add(overdrafted_layer)

                    # Add selected boundaries on the top layer
                    if selection_type == 'i03':
                        m.add(hydrologic_layer)
                    elif selection_type == 'i08':
                        m.add(subbasin_layer)
                    elif selection_type == 'gsa':
                        m.add(gsa_layer)       

                    # Reset selection since the previously selected region is gone
                    selection.set('')

                # Update overdrafted subbasin layer when the option to show it is changed. Doesn't reset selection since boundaries aren't changing
                @reactive.effect
                @reactive.event(input.show_overdrafted)
                def _():
                    selection_type = input.selection_type.get()

                    # Reset map to just the base map layer
                    m.layers = m.layers[:1]

                    # If active, always put the overdrafted subbasins layer below whatever the currently selected boundaries are
                    if input.show_overdrafted.get():
                        m.add(overdrafted_layer)

                    # Add selected boundaries on the top layer
                    if selection_type == 'i03':
                        m.add(hydrologic_layer)
                    elif selection_type == 'i08':
                        m.add(subbasin_layer)
                    elif selection_type == 'gsa':
                        m.add(gsa_layer)  


                with ui.card(style='white-space: pre-wrap;', fill=True):
                    # Information pop-up
                    with ui.popover(title='Region Data', placement='right'):
                        info_icon 
                        'The information in this box is based on 2024 field boundaries and crop types (except for the mean field value, which is an average over 2018 - 2024).'

                    with ui.card_body():
                        @render.text
                        def name_output():
                            # TODO: Formatting
                            return f'Region: {selection()}'
                        
                        @render.text
                        def field_count_total_acreage_output():
                            if selection() == '':
                                return f'Total Acreage:                     Field Count:     '
                                
                            selection_type = input.selection_type.get()
                            count = get_field_count(selection_type, selection())
                            total_acreage = get_avg_acreage(selection_type, selection())
                            return f'Total Acreage: {total_acreage:.2f} acres       Field Count: {count}'

                        @render.text
                        def perennial_annual_acreage_output():
                            if selection() == '':
                                return f'Perennial:  XX %                   Annual  XX %                   Fallow  XX %'
                            
                            selection_type = input.selection_type.get()
                            perennial_acreage = get_avg_acreage(selection_type, selection(), 'perennial')
                            annual_acreage = get_avg_acreage(selection_type, selection(), 'annual')
                            fallow_acreage = get_avg_acreage(selection_type, selection(), 'fallow')
                            return f'Perennial: {perennial_acreage:.2f}%                  Annual {annual_acreage:.2f}%                  Fallow {fallow_acreage:.2f}%'

                        @render.text
                        def mean_output():
                            if selection() == '':
                                return f'Weighted Mean Field {input.value_type.get()}:'
                                
                            selection_type = input.selection_type.get()
                            value_type = input.value_type.get()
                            avg = get_avg(selection_type, selection(), value_type)
                            return f'Weighted Mean Field {input.value_type.get()}: {avg:.2f} acre-ft'
            #endregion

        with ui.navset_pill(id='tab'):
            with ui.nav_panel('Regional Crop Data'):
                with ui.layout_columns(col_widths=[3, 9]):
                    with ui.card():
                        ui.input_radio_buttons(
                            'crop_display_setting',
                            'Crop Types to Display:',
                            {
                                'most_common': 'Most Common',
                                'most_et':     'Highest Mean',
                                'least_et':    'Lowest Mean',
                                'mix':         'Highest/Lowest Mean'
                            },
                            selected='most_common'
                        )
                    
                    with ui.card(height=798.5, full_screen=True):
                        @render.plot
                        def crop_plot():
                            value_type = input.value_type.get()
                            selection_type = input.selection_type.get()
                            crop_display_setting = input.crop_display_setting.get()

                            crops = select_crops(selection_type, selection(), value_type, crop_display_setting)
                            return get_crop_comparison(selection_type, selection(), crops, value_type)


            with ui.nav_panel('Water Savings Calculator'):
                with ui.card():
                    with ui.layout_columns(col_widths=[6, 6]):
                        with ui.h6():
                            'Region (selected from map):'
                            @render.text
                            def calc_region_display():
                                return f'{selection()}'

                        ui.input_numeric(
                            'calc_acreage',
                            'Field Acreage:',
                            25,
                            min=0.1,
                            step=0.1
                        )

                with ui.layout_columns(col_widths=[5, 2, 5]):
                    ui.input_selectize(
                        'current_crop',
                        'Current Crop',
                        []
                    )

                    with ui.h3(style='display: flex; justify-content: center; align-items: center; font-size: 60px;'):
                        ''
                        '\u2192'

                    ui.input_selectize(
                        'target_crops',
                        'Target Crops',
                        [],
                        multiple=True
                    )

                    @reactive.effect
                    @reactive.event(input.selection_type, selection)
                    def current_and_target_crop_selection():
                        new_choices = get_crops_for_selectize(input.selection_type.get(), selection())

                        old_current = input.current_crop.get()
                        if old_current not in new_choices:
                            old_current = ''
                        ui.update_selectize('current_crop', choices=new_choices, selected=old_current)

                        old_targets = list(input.target_crops.get())
                        for target in old_targets:
                            if target not in new_choices:
                                old_targets.remove(target)
                        if old_current != '':
                            new_choices.pop(old_current)
                        ui.update_selectize('target_crops', choices=new_choices, selected=old_targets)

                    @reactive.effect
                    @reactive.event(input.current_crop)
                    def remove_current_crop_from_target_options():
                        current_choices = get_crops_for_selectize(input.selection_type.get(), selection())

                        current_crop = input.current_crop.get()
                        if(current_crop != ''):
                            current_choices.pop(current_crop)

                        old_targets = list(input.target_crops.get())
                        for target in old_targets:
                            if target not in current_choices:
                                old_targets.remove(target)
                        ui.update_selectize('target_crops', choices=current_choices, selected=old_targets)

                with ui.layout_columns(col_widths=[1, 2]):
                    ui.input_switch(
                        'calculator_display_relative',
                        'Display: ',
                        True
                    )

                    @render.text
                    def calculator_display_setting_type():
                        display_relative = input.calculator_display_relative.get()
                        value_type = input.value_type.get()

                        if display_relative:
                            return f'Relative {value_type}'
                        else:
                            return f'Total {value_type}'

                with ui.navset_card_tab(id='calc_year_classes'):
                    with ui.nav_panel('All Years'):
                        @render.plot
                        def crop_savings_plot_all_years():
                            value_type = input.value_type.get()
                            selection_type = input.selection_type.get()
                            display_relative = input.calculator_display_relative.get()

                            current_crop = input.current_crop.get()
                            target_crops = list(input.target_crops.get())
                            acres = input.calc_acreage.get()

                            if selection() == '':
                                return empty_plot()
                            elif len(target_crops) == 0:
                                return empty_plot('Please select crops to compare (max 9)...')
                            elif len(target_crops) > 9:
                                return empty_plot('More than 9 comparison crops selected...')
                            else:
                                return get_crop_calculator_comparison(selection_type, selection(), current_crop, target_crops, acres, display_relative, value_type, 'all')

                    
                    with ui.nav_panel('Wet Years'):
                        @render.plot
                        def crop_savings_plot_wet_years():
                            value_type = input.value_type.get()
                            selection_type = input.selection_type.get()
                            display_relative = input.calculator_display_relative.get()

                            current_crop = input.current_crop.get()
                            target_crops = list(input.target_crops.get())
                            acres = input.calc_acreage.get()

                            if selection() == '':
                                return empty_plot()
                            elif len(target_crops) == 0:
                                return empty_plot('Please select crops to compare (max 9)...')
                            elif len(target_crops) > 9:
                                return empty_plot('More than 9 comparison crops selected...')
                            else:
                                return get_crop_calculator_comparison(selection_type, selection(), current_crop, target_crops, acres, display_relative, value_type, 'Wet')

                    
                    with ui.nav_panel('Average Years'):
                        @render.plot
                        def crop_relative_plot_normal_years():
                            value_type = input.value_type.get()
                            selection_type = input.selection_type.get()
                            display_relative = input.calculator_display_relative.get()

                            current_crop = input.current_crop.get()
                            target_crops = list(input.target_crops.get())
                            acres = input.calc_acreage.get()

                            if selection() == '':
                                return empty_plot()
                            elif len(target_crops) == 0:
                                return empty_plot('Please select crops to compare (max 9)...')
                            elif len(target_crops) > 9:
                                return empty_plot('More than 9 comparison crops selected...')
                            else:
                                return get_crop_calculator_comparison(selection_type, selection(), current_crop, target_crops, acres, display_relative, value_type, 'Average')
                    
                    with ui.nav_panel('Dry Years'):
                        @render.plot
                        def crop_savings_plot_dry_years():
                            value_type = input.value_type.get()
                            selection_type = input.selection_type.get()
                            display_relative = input.calculator_display_relative.get()

                            current_crop = input.current_crop.get()
                            target_crops = list(input.target_crops.get())
                            acres = input.calc_acreage.get()

                            if selection() == '':
                                return empty_plot()
                            elif len(target_crops) == 0:
                                return empty_plot('Please select crops to compare (max 9)...')
                            elif len(target_crops) > 9:
                                return empty_plot('More than 9 comparison crops selected...')
                            else:
                                return get_crop_calculator_comparison(selection_type, selection(), current_crop, target_crops, acres, display_relative, value_type, 'Dry')

            with ui.nav_panel('Regional Distribution'):
                @render.plot
                def annual_dist_plot():
                    value_type = input.value_type.get()
                    selection_type = input.selection_type.get()
                    return get_annual_dist(selection_type, selection(), value_type)
                
                @render.plot
                def annual_total_plot():
                    value_type = input.value_type.get()
                    selection_type = input.selection_type.get()
                    return get_annual_totals(selection_type, selection(), value_type)

# About Page
with ui.panel_conditional('input.about % 2 != 0'):
    pass