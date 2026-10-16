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
# TODO
PERENNIAL_CROPS = []
ANNUAL_CROPS = []

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
        for water_year_class in ['Wet', 'Average', 'Dry']:
            class_data = summary[(summary['water_year_class'] == water_year_class) & (summary['dataset'] == dataset)]

            if class_data.shape[0] > 0:
                all_stats.append({
                    'label': water_year_class,
                    'med': class_data['MEDIAN'].iloc[0],
                    'q1': class_data['PCT25'].iloc[0],
                    'q3': class_data['PCT75'].iloc[0],
                    'whislo': class_data['LOWER_WHISKER'].iloc[0],
                    'whishi': class_data['UPPER_WHISKER'].iloc[0]
                })

        fig, ax = plt.subplots()
        ax.bxp(all_stats, showfliers=False)
        # ax.axhline(0, style='--')

        plt.xlabel('Water Year Classification')
        plt.ylabel(f'Total {value} (acre-ft)')
        plt.title(f'Annual {value} Distribution')
        plt.tight_layout()
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
        return summary[summary['dataset'] == dataset]['MEAN'].mean()


def select_crops(selection_type: str, region: str, value: str = 'ET', crop_display_setting: str = 'most_common') -> list[str]:
    '''
        Return list of 10 crops based on provided setting in a specified region across water years 2018 - 2024
        
        For "custom", returns a list of exactly one value: "custom"
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
            summary = hydrologic_crop_summary[(hydrologic_crop_summary['HR_NAME'] == region) & (hydrologic_crop_summary['dataset'] == dataset) & (hydrologic_crop_summary['water_year_class'] == 'all')]
        elif selection_type == 'i08':
            code = get_data(selection_type=input.selection_type.get(), region=selection(), data='id')
            selected_region = bridge[bridge['Basin_Subb'] == code]
            summary = subbasin_crop_summary[(subbasin_crop_summary['Basin_Subb'] == code) & (subbasin_crop_summary['dataset'] == dataset) & (subbasin_crop_summary['water_year_class'] == 'all')]
        elif selection_type == 'gsa':
            code = int(get_data(selection_type=input.selection_type.get(), region=selection(), data='id'))
            selected_region = bridge[bridge['GSA_ID'] == code]
            summary = gsa_crop_summary[(gsa_crop_summary['GSA_ID'] == code) & (gsa_crop_summary['dataset'] == dataset) & (gsa_crop_summary['water_year_class'] == 'all')]
        else:
            return []

        if crop_display_setting == 'most_common':
            return list(selected_region[['crop_2018', 'crop_2019', 'crop_2020', 'crop_2021', 'crop_2022', 'crop_2023', 'crop_2024']].stack().value_counts().head(10).index.values) 
        elif crop_display_setting == 'most_et':
            return list(summary.sort_values('weighted_mean', ascending=False).head(10)['crop'].values)
        elif crop_display_setting == 'least_et':
            return list(summary.sort_values('weighted_mean', ascending=True).head(10)['crop'].values)
        elif crop_display_setting == 'mix':
            return list(summary.sort_values('weighted_mean', ascending=False).head(5)['crop'].values) + list(summary.sort_values('weighted_mean', ascending=True).head(5)['crop'].values)
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

def get_crop_savings(selection_type: str, region: str, curr_crop: str, target_crops: list[str], acreage: float, value: str = 'ET', water_year_class: str = 'all'):
    if selection() != '':
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
            current_estimated = summary[summary['crop'] == curr_crop]['estimated_acre_ft'].mean()

            fig, ax = plt.subplots()
            target_summary = summary[summary['crop'] != curr_crop].groupby('crop')['estimated_acre_ft'].mean() - current_estimated
            sorted_summary = target_summary.sort_values(ascending=False)
            colors = ['C1' if val > 0 else 'C0' for val in sorted_summary.values]
            sorted_summary.plot.barh(color=colors, legend=False, ax=ax)
        elif value == 'PR':
            return empty_plot('"Precipitation Savings" not available.')
        elif value == 'Net ET':
            summary = summary[summary['dataset'] == 'net_et']
            current_estimated = summary[summary['crop'] == curr_crop]['estimated_acre_ft'].iloc[0]

            fig, ax = plt.subplots()
            sorted_summary = summary[summary['crop'] != curr_crop].sort_values('estimated_acre_ft', ascending=False)
            colors = ['C1' if val > current_estimated else 'C0' for val in sorted_summary['estimated_acre_ft']]
            sorted_summary.plot.barh(x='crop', y='estimated_acre_ft', color=colors, legend=False, ax=ax)

        # Wrap y-axis tick labels
        wrapped_labels = [textwrap.fill(label.get_text(), 15) for label in ax.get_yticklabels()]
        ax.set_yticklabels(wrapped_labels, ha='right', va='center')

        # Reference line at 0
        ax.axvline(x=0, linestyle='--', color='black', label=f'current: {current_estimated:.2f}')

        # Bar labels
        for container in ax.containers:
            ax.bar_label(container, padding=3, fmt='%+.2f')
        ax.margins(x=0.15)

        # plt.title(f'Annual {value} Savings by Switching from "{curr_crop}"')
        plt.xlabel(f'Estimated Annual {value} Relative to Current Crop (acre-ft)')
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

        return regions['ACRES'].sum()

        # if category == 'perennial':
        #     return 'PERENNIAL'
        # elif category == 'annual':
        #     return 'ANNUAL'
        # elif category == 'all':
        #     return 'ALL'
        # else:
        #     raise ValueError('If specifying a category for acreage calculation, must be either "perennial" or "annual".')

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

ui.page_opts(fillable=True)

with ui.sidebar(open='closed', width='260px', resizable=False):
    ui.input_radio_buttons(
        'selection_type',
        'Boundaries:',
        {
            'i03': 'Hydrologic Regions (i03)',
            'i08': 'Subbasins (i08)',
            'gsa': 'Groundwater Sustainability Agencies',
        },
        selected='i08'
    )

    ui.input_radio_buttons(
        'value_type',
        'Values:',
        {
            'ET': 'Evapotranspiration (ET)',
            'PR': 'Precipitation (PR)',
            'Net ET': 'Net ET (ET - PR)',
        },
    )

    ui.input_checkbox(
        'show_overdrafted',
        'Show Critically Overdrafted Subbasins',
        False,
    )


with ui.layout_columns(col_widths=[4, 8]):
    with ui.layout_columns(col_widths=[12, 6, 6]):
        #region Map Stuff
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
            @reactive.event(input.selection_type)
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

            @reactive.effect
            @reactive.event(input.show_overdrafted)
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
        #endregion    
        
        with ui.layout_columns(col_widths=[12, 12, 12]):
            # Region Name
            with ui.card(class_="d-flex align-items-center justify-content-center"):
                'Name:'
                @render.text
                def name_output():
                    # TODO: Formatting
                    return f'{selection()}'

            # Field Count
            with ui.card(class_="d-flex align-items-center justify-content-center"):
                'Number of fields:'
                
                @render.text
                def field_count_output():
                    if selection() == '':
                        return ''
                        
                    selection_type = input.selection_type.get()
                    count = get_field_count(selection_type, selection())
                    return f'{count} fields'

            # Mean Values
            with ui.card(class_="d-flex align-items-center justify-content-center"):
                @render.text
                def mean_header():
                    return f'Mean Field {input.value_type.get()}:'
                
                @render.text
                def mean_output():
                    if selection() == '':
                        return ''
                        
                    selection_type = input.selection_type.get()
                    value_type = input.value_type.get()
                    avg = get_avg(selection_type, selection(), value_type)
                    return f'{avg:.2f} acre-ft'

        # Acreage
        with ui.layout_columns(col_widths=[12, 12, 12]):
            with ui.card(class_="d-flex align-items-center justify-content-center"):
                'Total Field Acreage: '
                @render.text
                def total_acreage_output():
                    if selection() == '':
                        return ''
                    
                    selection_type = input.selection_type.get()
                    total_acreage = get_avg_acreage(selection_type, selection())
                    return f'{total_acreage:.2f} acres'

            with ui.card(class_="d-flex align-items-center justify-content-center"):
                'Perennial Field Acreage:'
                @render.text
                def perennial_acreage_output():
                    if selection() == '':
                        return ''
                    
                    selection_type = input.selection_type.get()
                    perennial_acreage = get_avg_acreage(selection_type, selection(), 'perennial')
                    return f'{perennial_acreage:.2f} acres'

            with ui.card(class_="d-flex align-items-center justify-content-center"):
                'Annual Field Acreage:'
                @render.text
                def annual_acreage_output():
                    if selection() == '':
                        return ''
                    
                    selection_type = input.selection_type.get()
                    annual_acreage = get_avg_acreage(selection_type, selection(), 'annual')
                    return f'{annual_acreage:.2f} acres'


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

                    with ui.panel_conditional('input.crop_display_setting === "custom"'):
                        ui.input_selectize(
                            'custom_crops',
                            'Customize Crop Selection',
                            [],
                            multiple=True
                        )

                    @reactive.effect
                    @reactive.event(input.crop_display_setting)
                    def custom_crop_selection():
                        if input.crop_display_setting.get() == 'custom':
                            new_choices = get_crops_for_selectize(input.selection_type.get(), selection())
                            ui.update_selectize('custom_crops', choices=new_choices, selected=input.custom_crops.get())
                
                with ui.card(height=798.5, full_screen=True):
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

                with ui.h3():
                    '     -->'

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
                    ui.update_selectize('target_crops', choices=new_choices, selected=old_targets)

            with ui.navset_card_tab(id='calc_year_classes'):
                with ui.nav_panel('All Years'):
                    @render.plot
                    def crop_savings_plot_all_years():
                        value_type = input.value_type.get()
                        selection_type = input.selection_type.get()

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
                            return get_crop_savings(selection_type, selection(), current_crop, target_crops, acres, value_type, 'all')

                
                with ui.nav_panel('Wet Years'):
                    @render.plot
                    def crop_savings_plot_wet_years():
                        value_type = input.value_type.get()
                        selection_type = input.selection_type.get()

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
                            return get_crop_savings(selection_type, selection(), current_crop, target_crops, acres, value_type, 'Wet')

                
                with ui.nav_panel('Average Years'):
                    @render.plot
                    def crop_savings_plot_normal_years():
                        value_type = input.value_type.get()
                        selection_type = input.selection_type.get()

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
                            return get_crop_savings(selection_type, selection(), current_crop, target_crops, acres, value_type, 'Average')
                
                with ui.nav_panel('Dry Years'):
                    @render.plot
                    def crop_savings_plot_dry_years():
                        value_type = input.value_type.get()
                        selection_type = input.selection_type.get()

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
                            return get_crop_savings(selection_type, selection(), current_crop, target_crops, acres, value_type, 'Dry')

        with ui.nav_panel('Regional Distribution'):
            @render.plot
            def annual_dist_plot():
                value_type = input.value_type.get()
                selection_type = input.selection_type.get()
                return get_annual_dist(selection_type, selection(), value_type)
