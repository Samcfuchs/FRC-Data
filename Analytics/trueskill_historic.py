#%%
# # Historic Trueskill Modeling

#%%
# Set up environment
from frc_trueskill import TSModel
import tbapy
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns; sns.set(color_codes=True)
import time
import pickle
import os

tba = tbapy.TBA(os.environ['TBA_API_KEY'])

#%%
# Create our data processing pipeline
def process_data(df):
    cols_ren = {
        'Competition Level':'comp_level',
        'Match Number': 'match',
        'Set Number': 'set',
    }
    team_cols = ['blue1','blue2','blue3','red1','red2','red3']

    df.rename(columns=cols_ren, inplace=True)

    df.drop(['City','State','Country','Time'], axis=1, inplace=True)
    df.winner.fillna('tie', inplace=True)
    df.dropna(inplace=True)
    df.red3 = pd.to_numeric(df.red3) # For 2006

    df['blue'] = list(zip(df.blue1, df.blue2, df.blue3))
    df['red'] = list(zip(df.red1, df.red2, df.red3))
    df.drop(team_cols, axis=1, inplace=True)

    df = df.loc[df['blue score'] + df['red score'] > -2,:]

    df.reset_index(drop=True, inplace=True)

    return df

def sort_data(df):
    sort_order = ['Week','event_n','Event','comp_level_n','set','match']

    comp_level_f = { 'qm':0, 'qf':1, 'sf':2, 'f':3 }
    event_f = lambda k: 1 if k[:3] == 'cmp' else 0

    df['comp_level_n'] = df.comp_level.map(comp_level_f)
    df['event_n'] = df.Event.map(event_f)

    df.sort_values(sort_order, inplace=True)
    df.reset_index(inplace=True, drop=True)

    df.drop(['event_n','comp_level_n'], axis=1, inplace=True)

    return df

def get_teams(years):
    teams = set()
    for year in years:
        teams.update([int(key[3:]) for key in tba.teams(year=year, keys=True)])
    
    return list(teams)

#%%
# Multi-year simulation
years = range(2005, 2020)
teams = get_teams(years)
model = TSModel(teams, logging=True)

print(f"Training on {','.join(map(str, years))}")
print('='*35)
start = time.time()

for year in years:
    filename = f"../data/{year}_MatchData_ol.csv"
    data = pd.read_csv(filename)
    data = process_data(data)
    data = sort_data(data)

    print(f"Year: {year}")
    print(f"Simulating {len(data)} matches")
    substart = time.time()

    data.apply(model.train, axis=1)

    print(f"Training time: {int(time.time() - substart)} s")
    print("=" * 35)

    model.export(f"{year}_end_ratings.csv")

print(f"Training time: {int(time.time() - start)} s")
