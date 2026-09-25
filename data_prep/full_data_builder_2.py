import ee
import os
from dotenv import load_dotenv

load_dotenv()
project_id = os.getenv('PROJECT_ID')

ee.Authenticate()
ee.Initialize(project=project_id)

# SHAPE_ASSET= f'projects/{old_project_id}/assets/land_repurposing_app/openet_geodatabase_v2_clipped'
SHAPE_ASSET= f'projects/{project_id}/assets/land_repurposing_app/openet_geodatabase_v2_new_basin' 
START_DATE='2017-10-01' # Start water year 2018 
END_DATE='2024-10-01' # End water year 2024
DRIVE_FOLDER='cal_i08_stats'
FILENAME='cal_i08_ensemble_pr_2018_2024'
ID_PROP='OPENET_ID' 
SHARD_COUNT=1 # Originally 20
FIELD_ID=None

OPENET_ASSET='projects/openet/assets/ensemble/conus/gridmet/monthly/v2_1'
OPENET_BAND='et_ensemble_mad'
GRIDMET_ASSET='IDAHO_EPSCOR/GRIDMET' 
GRIDMET_BAND='pr'

def month_seq(start,end):
    start_d=ee.Date(start).update(day=1)
    end_d=ee.Date(end).update(day=1)
    n=end_d.difference(start_d,'month').round().int()
    return ee.List.sequence(0,n.subtract(1)).map(lambda i:start_d.advance(i,'month'))

def make_row(openet_id,dataset,month,value):
    return ee.Feature(None,{'OPENET_ID':openet_id,'dataset':dataset,'month':month,'value':value})

def build_fc_base():
    fc=ee.FeatureCollection(SHAPE_ASSET)
    if FIELD_ID is None:
        return fc
    if isinstance(FIELD_ID,list):
        return fc.filter(ee.Filter.inList(ID_PROP,FIELD_ID))
    return fc.filter(ee.Filter.eq(ID_PROP,FIELD_ID))

def get_aoi(fc):
    return fc.geometry().bounds()

def openet_monthly_long(fc):
    months=month_seq(START_DATE,END_DATE)
    aoi=get_aoi(fc)

    def per_month(m0):
        d0=ee.Date(m0)
        d1=d0.advance(1,'month')
        month=d0.format('YYYY-MM')

        ic=(ee.ImageCollection(OPENET_ASSET)
            .filterDate(d0,d1)
            .filterBounds(aoi)
            .select(OPENET_BAND))

        im=ee.Image(ee.Algorithms.If(
            ic.size().gt(0),
            ic.mosaic().toFloat(),
            ee.Image.constant(-999).toFloat()
        )).rename('ensemble')

        stats=im.reduceRegions(
            collection=fc,
            reducer=ee.Reducer.mean(),
            scale=30
        )

        return stats.map(lambda f:make_row(
            ee.Feature(f).get(ID_PROP),
            'ensemble',
            month,
            ee.Feature(f).get('mean')
        ))

    return ee.FeatureCollection(months.map(per_month)).flatten()

def gridmet_pr_monthly_long(fc):
    months=month_seq(START_DATE,END_DATE)
    aoi=get_aoi(fc)

    ref=(ee.ImageCollection(GRIDMET_ASSET)
         .first()
         .select(GRIDMET_BAND))

    proj=ref.projection()
    scale=proj.nominalScale()

    def per_month(m0):
        d0=ee.Date(m0)
        d1=d0.advance(1,'month')
        month=d0.format('YYYY-MM')

        im=(ee.ImageCollection(GRIDMET_ASSET)
            .filterDate(d0,d1)
            .filterBounds(aoi)
            .select(GRIDMET_BAND)
            .sum()
            .rename('gridmet_pr')
            .toFloat())

        stats=im.reduceRegions(
            collection=fc,
            reducer=ee.Reducer.mean(),
            scale=scale,
            crs=proj
        )

        return stats.map(lambda f:make_row(
            ee.Feature(f).get(ID_PROP),
            'gridmet_pr',
            month,
            ee.Feature(f).get('mean')
        ))

    return ee.FeatureCollection(months.map(per_month)).flatten()

def tidy_long(fc):
    return fc.map(lambda f:ee.Feature(None,{
        'OPENET_ID':ee.Feature(f).get('OPENET_ID'),
        'dataset':ee.Feature(f).get('dataset'),
        'month':ee.Feature(f).get('month'),
        'value':ee.Feature(f).get('value')
    }))

def shard_fc_by_table_order(fc,shard_count,shard_index):
    size=ee.Number(fc.size())
    start=size.multiply(shard_index).divide(shard_count).floor()
    end=size.multiply(shard_index+1).divide(shard_count).floor()
    return ee.FeatureCollection(fc.toList(size).slice(start,end))

def export_long(fc,shard_index):
    tag=f'_{shard_index+1}_{SHARD_COUNT}'
    desc=f'{FILENAME}{tag}'
    task=ee.batch.Export.table.toDrive(
        collection=fc,
        description=desc,
        folder=DRIVE_FOLDER,
        fileNamePrefix=desc,
        fileFormat='CSV',
        selectors=['OPENET_ID','dataset','month','value']
    )
    task.start()
    print('Started export:',desc)

base_fc=build_fc_base()

for s in range(SHARD_COUNT):
    print(f'Building shard {s+1}/{SHARD_COUNT}')
    fc_shard=shard_fc_by_table_order(base_fc,SHARD_COUNT,s)
    et_long=openet_monthly_long(fc_shard)
    pr_long=gridmet_pr_monthly_long(fc_shard)
    tidy=tidy_long(ee.FeatureCollection([et_long,pr_long]).flatten())
    export_long(tidy,s)