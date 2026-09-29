import json
from pathlib import Path
import matplotlib.pyplot as plt
import pandas as pd
import geopandas as gpd
from shapely.geometry import Point
import textwrap

from ipyleaflet import GeoJSON, Map
from shiny import reactive
from shiny.express import input, render, ui
from shinywidgets import render_widget

plt.style.use('bmh')

# region Map layer and GDF Loading
hydrologic_path = Path(__file__).resolve().parent / 'geodata' / 'hydrologic_regions.geojson'
with open(hydrologic_path, 'r') as f:
    hydrologic_regions = json.load(f)

hydrologic_layer = GeoJSON(
    data=hydrologic_regions,
    style={  
        'opacity': 1, 
        'fillOpacity': 0.1,
        'weight': 1,
        'color': 'black',
        'fillColor': 'black',
    },
    hover_style={'fillOpacity': 0.5},
)

hydrologic_gdf = gpd.read_file(hydrologic_path)
hydrologic_gdf.set_geometry('geometry', inplace=True)

subbasin_path = Path(__file__).resolve().parent / 'geodata' / 'subbasins.geojson'
with open(subbasin_path, 'r') as f:
    subbasins = json.load(f)

subbasin_layer = GeoJSON(
    data=subbasins,
    style={  
        'opacity': 1, 
        'fillOpacity': 0.1,
        'weight': 1,
        'color': 'black',
        'fillColor': 'black',
    },
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
        'fillOpacity': 0.4,
        'weight': 1,
        'fillColor': 'red',
    },
)

overdrafted_gdf = gpd.read_file(overdrafted_path)
overdrafted_gdf.set_geometry('geometry', inplace=True)

gsa_path = Path(__file__).resolve().parent / 'geodata' / 'groundwater_sustainability_agencies.geojson'
with open(gsa_path, 'r') as f:
    gsa_regions = json.load(f)

gsa_layer = GeoJSON(
    data=gsa_regions,
    style={  
        'opacity': 1, 
        'fillOpacity': 0.1,
        'weight': 1,
        'color': 'black',
        'fillColor': 'black',
    },
    point_style={
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


# hydrologic_summary = pd.read_csv('regions_ag_mask_open_data.csv')[['HR_NAME', 'area_acres', 'year_month', 'year', 'month', 'timestep', 'ENSEMBLE_ET_acre_ft']]
# subbasin_summary = pd.read_csv('gw_basin_ag_mask_open_data.csv')[['Basin_Subb', 'area_acres', 'year_month', 'year', 'month', 'timestep', 'ENSEMBLE_ET_acre_ft']]
hydrologic_summary_path = Path(__file__).resolve().parent / 'data_summaries' / 'hydrologic_summary.csv'
hydrologic_summary = pd.read_csv(hydrologic_summary_path)

subbasin_summary_path = Path(__file__).resolve().parent / 'data_summaries' / 'subbasin_summary.csv'
subbasin_summary = pd.read_csv(subbasin_summary_path)

gsa_summary_path = Path(__file__).resolve().parent / 'data_summaries' / 'gsa_summary.csv'
gsa_summary = pd.read_csv(gsa_summary_path)

hydrologic_crop_summary_path = Path(__file__).resolve().parent / 'data_summaries' / 'hydrologic_crop_summary.csv'
hydrologic_crop_summary = pd.read_csv(hydrologic_crop_summary_path)

subbasin_crop_summary_path = Path(__file__).resolve().parent / 'data_summaries' / 'subbasin_crop_summary.csv'
subbasin_crop_summary = pd.read_csv(subbasin_crop_summary_path)

gsa_crop_summary_path = Path(__file__).resolve().parent / 'data_summaries' / 'gsa_crop_summary.csv'
gsa_crop_summary = pd.read_csv(gsa_crop_summary_path)

bridge_path = Path(__file__).resolve().parent / 'bridge_table.csv'
bridge = pd.read_csv(bridge_path)


selection_coords = reactive.Value((-1, -1))
selection = reactive.Value('')

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

# TODO: Some input validation would probably be smart
def get_data(selection_type: str, region: str, data: str = 'id'):
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

def get_annual_total(selection_type: str, region: str, value: str = 'ET'):
    if selection() != '':
        if selection_type == 'i03':
            summary = hydrologic_summary[hydrologic_summary['HR_NAME'] == region]
        elif selection_type == 'i08':
            code = get_data(selection_type=input.selection_type.get(), region=selection(), data='id')
            summary = subbasin_summary[subbasin_summary['Basin_Subb'] == code]
        elif selection_type == 'gsa':
            code = int(get_data(selection_type=input.selection_type.get(), region=selection(), data='id'))
            summary = gsa_summary[gsa_summary['GSA_ID'] == code]
            summary['SUM'] = summary['SUM'] * 10  # GSAs are extra small, so make units a little smaller to match
        
        if value == 'ET':
            summary['SUM'] = summary['SUM'] / 10000  # by 10,000 acre-ft
            fig, ax = plt.subplots()
            summary[summary['dataset'] == 'ensemble'].plot.bar(x='water_year', y='SUM', ax=ax, legend=False, rot=0)
            ax.set_ylim(bottom = summary[summary['dataset'] == 'ensemble']['SUM'].min() * 0.95, top = summary[summary['dataset'] == 'ensemble']['SUM'].max() * 1.05)
            plt.ylabel(f'Total ET ({"thousands" if selection_type == "gsa" else "ten thousands"} of acre-ft)')
        elif value == 'PR':
            summary['SUM'] = summary['SUM'] / 1000  # by 1,000 acre-ft
            fig, ax = plt.subplots()
            summary[summary['dataset'] == 'gridmet_pr'].plot.bar(x='water_year', y='SUM', ax=ax, legend=False, rot=0)
            ax.set_ylim(bottom = summary[summary['dataset'] == 'gridmet_pr']['SUM'].min() * 0.95, top = summary[summary['dataset'] == 'gridmet_pr']['SUM'].max() * 1.05)
            plt.ylabel(f'Total PR ({"hundreds" if selection_type == "gsa" else "thousands"} of acre-ft)')
        elif value == 'Net ET':
            summary['SUM'] = summary['SUM'] / 10000  # by 10,000 acre-ft
            fig, ax = plt.subplots()
            summary[summary['dataset'] == 'net_et'].plot.bar(x='water_year', y='SUM', ax=ax, legend=False, rot=0)
            ax.set_ylim(bottom = summary[summary['dataset'] == 'net_et']['SUM'].min() * 0.95, top = summary[summary['dataset'] == 'net_et']['SUM'].max() * 1.05)
            plt.ylabel(f'Total Net ET ({"thousands" if selection_type == "gsa" else "ten thousands"} of acre-ft)')

        plt.title(f'Annual Total {value}')
        plt.xlabel('Water Year')
        # plt.tight_layout()
        return ax
    else:
        return empty_plot()

def get_annual_dist(selection_type: str, region: str, value: str = 'ET'):
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

        all_stats = []
        for water_year in range(2018, 2025):
            all_stats.append({
                'label': water_year,
                'med': summary[(summary['water_year'] == water_year) & (summary['dataset'] == dataset)]['MEDIAN'].iloc[0],
                'q1': summary[(summary['water_year'] == water_year) & (summary['dataset'] == dataset)]['PCT25'].iloc[0],
                'q3': summary[(summary['water_year'] == water_year) & (summary['dataset'] == dataset)]['PCT75'].iloc[0],
                'whislo': summary[(summary['water_year'] == water_year) & (summary['dataset'] == dataset)]['LOWER_WHISKER'].iloc[0],
                'whishi': summary[(summary['water_year'] == water_year) & (summary['dataset'] == dataset)]['UPPER_WHISKER'].iloc[0]
            })

        fig, ax = plt.subplots()
        ax.bxp(all_stats, showfliers=False)
        # ax.axhline(0, style='--')

        plt.xlabel('Water Year')
        plt.ylabel(f'Total {value} (acre-ft)')
        plt.title(f'Annual {value} Distribution')
        plt.tight_layout()
        return ax
    else:
        return empty_plot()

def get_total(selection_type: str, region: str, value: str = 'ET'):
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

        total = summary[summary['dataset'] == dataset]['SUM'].sum()
        mean = summary[summary['dataset'] == dataset]['MEAN'].sum()

        fig, ax = plt.subplots(figsize=(6, 4))
        ax.text(
            0.5, 0.8, 
            f'Across all years (2018 - 2024):', 
            fontsize=22, 
            color='black',
            ha='center',
            va='center'
        )
        ax.text(
            0.5, 0.5, 
            f'Total {value}: {total:,.2f} acre-ft', 
            fontsize=22, 
            color='black',
            ha='center',
            va='center'
        )
        ax.text(
            0.5, 0.2, 
            f'Mean {value}: {mean:,.2f} acre-ft', 
            fontsize=22, 
            color='black',
            ha='center',
            va='center'
        )
        ax.axis('off')
        return ax
    else:
        return empty_plot()

def select_crops(selection_type: str, region: str, crop_display_setting: str = 'most_common') -> list[str]:
    '''
        Return list of 10 crops based on provided setting in a specified region across water years 2018 - 2024
        
        For "custom", returns a list of exactly one value: "custom"
    '''
    if selection() != '':
        if crop_display_setting == 'custom':
            return ['custom']

        if selection_type == 'i03':
            selected_region = bridge[bridge['HR_NAME'] == region]
            summary = hydrologic_crop_summary[(hydrologic_crop_summary['HR_NAME'] == region) & (hydrologic_crop_summary['dataset'] == 'ensemble') & (hydrologic_crop_summary['water_year'] == 0)]
        elif selection_type == 'i08':
            code = get_data(selection_type=input.selection_type.get(), region=selection(), data='id')
            selected_region = bridge[bridge['Basin_Subb'] == code]
            summary = subbasin_crop_summary[(subbasin_crop_summary['Basin_Subb'] == code) & (subbasin_crop_summary['dataset'] == 'ensemble') & (subbasin_crop_summary['water_year'] == 0)]
        elif selection_type == 'gsa':
            code = int(get_data(selection_type=input.selection_type.get(), region=selection(), data='id'))
            selected_region = bridge[bridge['GSA_ID'] == code]
            summary = gsa_crop_summary[(gsa_crop_summary['GSA_ID'] == code) & (gsa_crop_summary['dataset'] == 'ensemble') & (gsa_crop_summary['water_year'] == 0)]
        else:
            return []

        if crop_display_setting == 'most_common':
            return list(selected_region[['crop_2018', 'crop_2019', 'crop_2020', 'crop_2021', 'crop_2022', 'crop_2023', 'crop_2024']].stack().value_counts().head(10).index.values) 
        elif crop_display_setting == 'most_et':
            return list(summary.sort_values('MEAN', ascending=False).head(10)['crop'].values)
        elif crop_display_setting == 'least_et':
            return list(summary.sort_values('MEAN', ascending=True).head(10)['crop'].values)
        elif crop_display_setting == 'mix':
            return list(summary.sort_values('MEAN', ascending=False).head(5)['crop'].values) + list(summary.sort_values('MEAN', ascending=True).head(5)['crop'].values)
        elif crop_display_setting == 'custom':
            return []
        else:
            return []
    else:
        return []

def get_crops_for_selectize(selection_type: str, region: str) -> dict[str, str]:
    if selection() != '':
        if selection_type == 'i03':
            crops = hydrologic_crop_summary[hydrologic_crop_summary['HR_NAME'] == region]['crop'].sort_values().unique()
        if selection_type == 'i08':
            code = get_data(selection_type=input.selection_type.get(), region=selection(), data='id')
            crops = subbasin_crop_summary[subbasin_crop_summary['Basin_Subb'] == code]['crop'].sort_values().unique()
        elif selection_type == 'gsa':
            code = int(get_data(selection_type=input.selection_type.get(), region=selection(), data='id'))
            crops = gsa_crop_summary[gsa_crop_summary['GSA_ID'] == code]['crop'].sort_values().unique()

        all_crops = {crop: crop for crop in crops}
        return all_crops
    else:
        return {}

def get_crop_comparison(selection_type: str, region: str, crops: list[str], value: str = 'ET'):
    if selection() != '':
        if selection_type == 'i03':
            summary = hydrologic_crop_summary[(hydrologic_crop_summary['HR_NAME'] == region) & (hydrologic_crop_summary['crop'].isin(crops)) & (hydrologic_crop_summary['water_year'] == 0)]
        if selection_type == 'i08':
            code = get_data(selection_type=input.selection_type.get(), region=selection(), data='id')
            summary = subbasin_crop_summary[(subbasin_crop_summary['Basin_Subb'] == code) & (subbasin_crop_summary['crop'].isin(crops)) & (subbasin_crop_summary['water_year'] == 0)]
        elif selection_type == 'gsa':
            code = int(get_data(selection_type=input.selection_type.get(), region=selection(), data='id'))
            summary = gsa_crop_summary[(gsa_crop_summary['GSA_ID'] == code) & (gsa_crop_summary['crop'].isin(crops)) & (gsa_crop_summary['water_year'] == 0)]
        
        if value == 'ET':
            fig, ax = plt.subplots()
            summary[summary['dataset'] == 'ensemble'].sort_values('MEAN', ascending=False).plot.barh(x='crop', y='MEAN', legend=False, ax=ax)
        elif value == 'PR':
            fig, ax = plt.subplots()
            summary[summary['dataset'] == 'gridmet_pr'].sort_values('MEAN', ascending=False).plot.barh(x='crop', y='MEAN', legend=False, ax=ax)
        elif value == 'Net ET':
            fig, ax = plt.subplots()
            summary[summary['dataset'] == 'net_et'].sort_values('MEAN', ascending=False).plot.barh(x='crop', y='MEAN', legend=False, ax=ax)

        # Wrap y-axis tick labels
        wrapped_labels = [textwrap.fill(label.get_text(), 15) for label in ax.get_yticklabels()]
        ax.set_yticklabels(wrapped_labels, ha='right', va='center')

        plt.title(f'Mean Annual {value} by Crop')
        plt.xlabel(f'Mean Annual {value} (acre-ft)')
        plt.ylabel('')
        plt.tight_layout()
        return ax
    else:
        return empty_plot()

def get_custom_crop_comparison():
    return empty_plot()

ui.tags.style('.bslib-value-box .value-box-value { font-size:20px !important; }')

ui.page_opts(fillable=True)

with ui.sidebar():
    'Filters:'

with ui.layout_columns(col_widths=[4, 8]):
    with ui.layout_columns(col_widths=[12, 12]):
        with ui.card(full_screen=True):
            m = Map(center=(37.5, -121.2), zoom=6)

            def map_click(**kwargs):
                if kwargs.get('type') == 'click':
                    print(kwargs)
                    coords = kwargs.get('coordinates')
                    point = Point(coords[1], coords[0])

                    selection_type = input.selection_type.get()

                    if selection_type == 'i03':
                        click_results = hydrologic_gdf[hydrologic_gdf.geometry.contains(point)]['HR_NAME']
                    elif selection_type == 'i08':
                        click_results = subbasin_gdf[subbasin_gdf.geometry.contains(point)]['Basin_Su_1']
                    elif selection_type == 'gsa':
                        click_results = gsa_gdf[gsa_gdf.geometry.contains(point)]['GSA_Name']

                    if len(click_results) > 0:
                        selection.set(click_results.iloc[0])
                    else:
                        selection.set('')

            m.on_interaction(map_click)

            @render_widget
            def map():
                m.add(subbasin_layer)
                return m     

            @reactive.effect
            @reactive.event(input.selection_type, input.show_overdrafted)
            def _():
                selection_type = input.selection_type.get()

                m.layers = m.layers[:1]
                if input.show_overdrafted.get():
                    m.add(overdrafted_layer)
                
                if selection_type == 'i03':
                    m.add(hydrologic_layer)
                elif selection_type == 'i08':
                    m.add(subbasin_layer)
                elif selection_type == 'gsa':
                    m.add(gsa_layer)       

                selection.set('')
            ui.input_checkbox(
                'show_overdrafted',
                'Show Critically Overdrafted Subbasins',
                False,
            )

            with ui.layout_columns(col_widths=[6, 6]):
                ui.input_radio_buttons(
                    'selection_type',
                    'Boundaries:',
                    {
                        'i03': ui.span('Hydrologic Regions (i03)'),
                        'i08': ui.span('Subbasins (i08)'),
                        'gsa': ui.span('Groundwater Sustainability Agencies'),
                    },
                    selected='i08'
                )

                ui.input_radio_buttons(
                    'value_type',
                    'Values:',
                    {
                        'ET': ui.span('Evapotranspiration (ET)'),
                        'PR': ui.span('Precipitation (PR)'),
                        'Net ET': ui.span('Net Evapotranspiration (ET - PR)'),
                    },
                )

        with ui.value_box(height='60px'):
            'Name'
            @render.text
            def name_output():
                return f'{selection()}'

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
                            'mix':         'Highest/Lowest Mean',
                            'custom':      'Custom Selected'
                        },
                        selected='most_common'
                    )

                    @render.ui
                    def custom_crop_selection():
                        if input.crop_display_setting.get() == 'custom':
                            return ui.input_selectize(
                                'custom_crops',
                                'Customize Crop Selection',
                                get_crops_for_selectize(input.selection_type.get(), selection()),
                                selected=None,
                                multiple=True,
                                # width=None,
                            )
                        else:
                            return None
                
                with ui.card(height=798, full_screen=True):
                    @render.plot
                    def crop_plot():
                        value_type = input.value_type.get()
                        selection_type = input.selection_type.get()
                        crop_display_setting = input.crop_display_setting.get()

                        if crop_display_setting == 'custom':
                            custom_crops = input.custom_crops.get()

                            if len(custom_crops) == 0:
                                return empty_plot('Please select crops to display (max 10)...')
                            elif len(custom_crops) > 10:
                                return empty_plot('More than 10 crops selected...')
                            else:
                                return get_crop_comparison(selection_type, selection(), custom_crops, value_type)
                        else:
                            crops = select_crops(selection_type, selection(), crop_display_setting)
                            return get_crop_comparison(selection_type, selection(), crops, value_type)

        with ui.nav_panel('Water Savings Calculator'):
            with ui.card():
                'Coming soon to a data visualization app near you!'


        with ui.nav_panel('Overall Regional Data'):
            with ui.layout_columns(col_widths=[12]):
                with ui.navset_card_tab(id='subtab'):
                    with ui.nav_panel('Annual Total Values'):
                        @render.plot
                        def annual_total_plot():
                            value_type = input.value_type.get()
                            selection_type = input.selection_type.get()
                            return get_annual_total(selection_type, selection(), value_type)

                    with ui.nav_panel('Annual Distributions'):
                        @render.plot
                        def annual_dist_plot():
                            value_type = input.value_type.get()
                            selection_type = input.selection_type.get()
                            return get_annual_dist(selection_type, selection(), value_type)

                    with ui.nav_panel('Overall Values'):
                        @render.plot
                        def total_plot():
                            value_type = input.value_type.get()
                            selection_type = input.selection_type.get()
                            return get_total(selection_type, selection(), value_type)


