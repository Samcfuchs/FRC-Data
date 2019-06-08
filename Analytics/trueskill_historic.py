#%%
# # Historic Trueskill Modeling

#%%
# Set up environment
from models import TSModel
import tbapy
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns; sns.set(style='whitegrid', color_codes=True)
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

#%% [markdown]
# ## Training the model
# We can now train the model on a range of years. I've already built the
# MatchData files for all the relevant years, so we can import them one by one
# and train the model on the full year of data. To train on the full range of
# data takes upwards of 20 minutes.

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
print(f"Brier score: {model.test(data.winner)}")

#%% [markdown]
# ## Testing
# It's important to ensure that our tests are meaningful - particularly, they
# should mirror the actual use case of our model. In this case, we want to use
# our fully trained model to predict a match outcome before it happens. To this
# effect, we test by importing the 2018 model and training it on the 2019 season
# once again and recording our predictions. Then we find the Brier score of
# those predictions against the actual results. All of this is handled by the
# model's `train()` and `test()` methods.

#%%
YEAR = 2019
trainedmodel = TSModel(logging=True)
trainedmodel.load(f"{YEAR-1}_end_ratings.csv")

data = pd.read_csv(f"../data/{YEAR}_MatchData_ol.csv")
data = process_data(data)
data = sort_data(data)

print(f"Year: {YEAR}")
print(f"Simulating {len(data)} matches")
substart = time.time()

data.apply(trainedmodel.train, axis=1)

print(f"Training time: {int(time.time() - substart)} s")
print("=" * 35)

print(f"Brier score: {trainedmodel.test(data.winner)}")

#%% [markdown]
# We can also assess our model by looking at the distribution of skill across
# all FRC teams. Here we show the distribution of score for all teams which
# played matches in 2019.

#%%
model = TSModel(logging=True)
model.load("2019_end_ratings.csv")
sns.kdeplot(model.table.loc[model.table.Score != 0,'Score'])
plt.show()

#%% [markdown]
# We can also visualize ratings by graphing the mean ($\mu$) against the
# standard deviation ($\sigma$) of each team. Interestingly, we see in the lower
# left that the teams trail off toward the higher $\mu$ values, with low
# $\sigma$. Upon closer examination, we can see that these teams are all the
# well-recognized powerhouse teams - in this chart, we actually have a visual
# representation of the best teams in FRC.

#%%
# Plot with matplot
filtered = model.table.loc[model.table.Score != 0]
pairs = list(map(tuple, filtered.Rating))
x,y = zip(*pairs)
z = filtered.Score
t = list(filtered.index)

plt.rcParams['image.cmap'] = 'viridis_r'
plt.rcParams['font.family'] = 'Segoe UI'

fig,(ax1,ax2) = plt.subplots(1,2, figsize=(12,8))
fig.suptitle("Team Ratings")

ax1.scatter(x,y,c=z, alpha=0.3, s=6)

ax1.set_title("All Teams")
ax1.set_xlabel(r'$\mu$')
ax1.set_ylabel(r'$\sigma$')

ax1.spines['right'].set_visible(False)
ax1.spines['top'].set_visible(False)
ax1.spines['left'].set_visible(False)
ax1.spines['bottom'].set_visible(False)

ax2.scatter(x,y,c=z, alpha=1.0, s=50)

ax2.set_title("Powerhouse Tail")
ax2.set_xlabel(r'$\mu$')
ax2.set_ylabel(r'$\sigma$')

for i,txt in list(enumerate(t))[:10]:
    offy=-4
    if txt == 1678:
        offy=1
    elif txt == 118:
        offy=-9
    ax2.annotate(txt, (x[i],y[i]),(10,offy), textcoords='offset pixels')

ax2.spines['right'].set_visible(False)
ax2.spines['top'].set_visible(False)
ax2.spines['left'].set_visible(False)
ax2.spines['bottom'].set_visible(False)

ax2.set_xlim(35,45)
ax2.set_ylim(1,1.5)

fig.show()

#%%
# Build dataframe for OPRS
YEAR = 2019
DROPS = ['Year','Event','Week','comp_level','set','match','winner']
COLS_REN = {
    'Key': 'key',
    'blue score':'score',  'blue':'teams',
    'red score':'score',   'red':'teams'
}

data = pd.read_csv(f"../data/{YEAR}_MatchData_ol.csv")
data = process_data(data)
data = sort_data(data)
teams = get_teams([YEAR])

data.drop(DROPS, axis=1, inplace=True)

blue = data.loc[:,['Key','blue score','blue']]
blue['alliance'] = ['blue']*len(blue)
blue.rename(columns=COLS_REN, inplace=True)
blue.index = blue.index * 2

red = data.loc[:,['Key','red score','red']]
red['alliance'] = ['red']*len(red)
red.rename(columns=COLS_REN, inplace=True)
red.index = red.index * 2 + 1

data = pd.concat([blue,red], axis=0).sort_index()
data = data[['key','alliance','teams','score']]
data.head(10)

#%%
# Build matrix
sparse = pd.DataFrame(0, index=np.arange(len(data)), columns=['key','alliance']+teams)
sparse['key'] = data['key']
sparse['alliance'] = data['alliance']

def f(row):
    sparse.loc[(sparse.key==row.key) & (sparse.alliance==row.alliance),row.teams] = 1

start = time.time()
data.apply(f, axis=1)
print(f"Time: {int(time.time() - start)} s")

#%%
# Solve for OPRS
coef = sparse.drop(['key','alliance'], axis=1).to_numpy()
oprs,resid,_,_ = np.linalg.lstsq(coef, data.score, rcond=None)
oprs = pd.DataFrame({'team':teams,'opr':oprs})
oprs.sort_values('opr', ascending=False, inplace=True)
oprs.head(25)

#%%
fig,ax = plt.subplots()

x = model.table.sort_values('Team').loc[model.table.index.isin(oprs.team),'Score']
y = oprs.sort_values('team').opr

ax.scatter(x, y, alpha=0.1)
ax.set_title('Metrics')
ax.set_xlabel('Score')
ax.set_ylabel('OPR')

fig.show()
