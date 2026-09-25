import pandas as pd
from pathlib import Path

shards = []
for i in range(1, 202):
    shard = pd.read_csv(f'geodata/shards/cal_i08_ensemble_pr_2018_2024_{i}_200.csv')
    shards.append(shard)

data = pd.concat(shards)
data.fillna(0, inplace=True)
data['month'] = data['month'] + '-01'

eto = pd.read_csv('eto_CAproject.csv')
eto['month_date'] = pd.to_datetime(eto['month'])

data = pd.read_csv('geodata/data_unmodified.csv')
data['month_date'] = pd.to_datetime(data['month'])
data['water_year'] = data['month_date'].dt.year + (data['month_date'].dt.month >= 10)
data['year'] = data['month_date'].dt.year
data['month'] = data['month_date'].dt.month

data = data.merge(eto[['OPENET_ID', 'month_date', 'value']].rename(columns={'value': 'eto'}), on=['OPENET_ID', 'month_date'], how='left')
data = data.dropna(subset=['eto'])

print(data.shape)
print(data.info())
print(data.describe())

ensemble_data = data[data['dataset'] == 'ensemble'].copy()
data = data[data['dataset'] != 'ensemble']

ensemble_data['et_fraction'] = ensemble_data['value'] / ensemble_data['eto']
ensemble_data = ensemble_data.sort_values(['OPENET_ID', 'month_date'])

ensemble_data['previous_nonzero_et_fraction'] = ensemble_data['et_fraction'].where(ensemble_data['et_fraction'] != 0).groupby(ensemble_data['OPENET_ID']).ffill()
# ensemble_data['next_nonzero_et'] = ensemble_data['et_fraction'].where(ensemble_data['et_fraction'] != 0).groupby(ensemble_data['OPENET_ID']).bfill()

zero_mask = ensemble_data['value'] == 0
ensemble_data.loc[zero_mask, 'value'] = ensemble_data.loc[zero_mask, 'previous_nonzero_et_fraction'] * ensemble_data.loc[zero_mask, 'eto']

print(ensemble_data[ensemble_data['value'] == 0])

data = pd.concat([data, ensemble_data])
data.dropna(subset=['value'])

path = Path(__file__).resolve().parent.parent / 'geodata' / 'data.csv'
data.to_csv(path, index=False)
