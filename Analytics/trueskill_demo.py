#%% [markdown]
# # Historic Trueskill Modeling

#%%
# Set up environment
import models
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

#%% [markdown]
# ## Training the model
# We can now train the model on a range of years. I've already built the
# MatchData files for all the relevant years, so we can import them one by one
# and train the model on the full year of data. To train on the full range of
# data takes upwards of 20 minutes.

#%%
# Multi-year simulation
years = range(2005, 2020)
teams = models.get_teams(years)
model = TSModel(teams, logging=True)

print(f"Training on {','.join(map(str, years))}")
print('='*35)
start = time.time()

for year in years:
    filename = f"../data/{year}_MatchData_ol.csv"
    data = pd.read_csv(filename)
    data = models.process_data(data)
    data = models.sort_data(data)

    print(f"Year: {year}")
    print(f"Simulating {len(data)} matches")
    substart = time.time()

    data.apply(model.train, axis=1)

    print(f"Training time: {int(time.time() - substart)} s")
    print("=" * 35)

    model.export(f"data/{year}_end_ratings.csv")

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
# model's `train()` and `test()` methods, with logging enabled.

#%%
YEAR = 2019
trainedmodel = TSModel(logging=True)
trainedmodel.load(f"{YEAR-1}_end_ratings.csv")

data = pd.read_csv(f"../data/{YEAR}_MatchData_ol.csv")
data = models.process_data(data)
data = models.sort_data(data)

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
model.load("data/2019_end_ratings.csv")
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
# Prediction demo
def match_teams(match_key):
    match = tba.match(key=match_key, simple=True)

    blue = [int(t[3:]) for t in match.alliances['blue']['team_keys']]
    red = [int(t[3:]) for t in match.alliances['red']['team_keys']]

    return (blue,red)

match_key = "2019cmpmi_f1m1"
blue, red = match_teams(match_key)
print(f"Match: {match_key}")
print(f"Blue: {blue}")
print(f"Red: {red}")
print(f"Blue win probability: {model.predict(blue, red):.3%}")
print(f"Match quality: {model.quality(blue, red):.3%}")

#%% [markdown]
# We can also calculate the rating of an alliance by adding together the
# distributions for each team on the alliance. Naturally, we sum the variance as
# well to produce a skill rating for each alliance, which we can compare to rank
# the Einstein finalists.

#%%
# Rank finalist alliances
alliances = {
    'arc': (5406,930,1310,4004),
    'tes': (346,548,5401,2534),
    'cars': (5050,111,4607,2052),
    'dar': (3707,217,4481,1218),
    'cur': (195,3538,1073,230),
    'dal': (4003,133,862,2614)
}

ratings = pd.DataFrame(
    {
        'Alliance':list(alliances.keys()),
        'Rating':[model.rate_alliance(a) for a in list(alliances.values())]
    }
)

ratings['Score'] = ratings.Rating.apply(model.env.expose)
ratings.sort_values('Score', ascending=False)

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
data = models.process_data(data)
data = models.sort_data(data)
teams = models.get_teams([YEAR])

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