#%% [markdown]
# # Implementing TrueSkill for FRC
# The Elo system has been introduced to FRC by a number of people, most
# prominently Caleb Sykes, who built his own Elo model based on margins of
# victory, and whose scouting spreadsheets are widely known in the community.
# However, the Elo model has some significant weaknesses when applied to the FRC
# game
#
# ## Problems with the Elo Model
# 

#%%
import pandas as pd

YEAR = 2019
FILE = f"data/{YEAR}_MatchData_ol.csv"

data = pd.read_csv(FILE)
data.head()

#%%
# Rename columns
cols_ren = {
    'Key':'Key',
    'Event':'Event',
    'Week':'Week',
    'Competition Level':'comp_level',
    'Match Number': 'match',
    'Set Number': 'set',
}

data.rename(columns=cols_ren, inplace=True)
data.reset_index(drop=True, inplace=True)
data.drop(['City','State','Country','Time'], axis=1, inplace=True)

#%%
# Data processing
data['blue'] = list(zip(data.blue1, data.blue2, data.blue3))
data['red'] = list(zip(data.red1, data.red2, data.red3))
data.drop(['blue1','blue2','blue3','red1','red2','red3'], axis=1, inplace=True)
data.winner.fillna('tie', inplace=True)

#%% [markdown]
# In order for the TrueSkill algorithm to work correctly, we need to make sure
# that the matches are run through in order. If we simulate the Einstein finals
# first, we won't have any information about the teams competing, so they won't
# get the weight they should. It makes sense for the low-information,
# low-influence matches to occur at the beginning of the season. In any case,
# this is how the algorithm is meant to run. We order the matches like so:
# 
# 1. Week
# 2. Event
# 3. Competition level
# 4. Set number
# 5. Match number
# 
# It is possible, under this ordering, that matches between events could be out
# of order, but that's a non-issue, since each event in a given week has a
# different set of teams.

#%%
# Sort matches in order they occurred
comp_level_f = { 'qm':0, 'qf':1, 'sf':2, 'f':3 }
data['comp_level_n'] = data.comp_level.map(comp_level_f)
data.sort_values(['Week','Event','comp_level_n','set','match'], inplace=True)
data.reset_index(inplace=True, drop=True)
data.drop('comp_level_n', axis=1, inplace=True)
data.head(10)

#%%
# Set up rating
import trueskill as ts
from typing import Tuple

Alliance = Tuple[int, int, int]
TIE_RATE = len(data.loc[data.winner=='tie',:])/len(data)

env = ts.setup(draw_probability=TIE_RATE)

# Build ranking table
teams = data.blue + data.red
teams = [t for match in teams for t in match]
teams = list(set(teams))

r = [ts.Rating() for _ in teams]

ratings = pd.DataFrame(data={'Team':teams, 'Rating':r})

def match(blue: Alliance, red: Alliance, winner: str, inplace=False):
    r_blue = list(ratings.loc[ratings.Team.isin(blue), 'Rating'])
    r_red = list(ratings.loc[ratings.Team.isin(red), 'Rating'])

    result = { 'blue':1, 'red':1 }
    if winner != 'tie':
        result[winner] -= 1

    new_blue, new_red = ts.rate([r_blue, r_red], result.values())

    if inplace:
        ratings.loc[ratings.Team.isin(blue), 'Rating'] = new_blue
        ratings.loc[ratings.Team.isin(red), 'Rating'] = new_red

    return new_blue, new_red

def match_row(row):
    match(row.blue, row.red, row.winner, inplace=True)

#%%
# Run matches
import time
start = time.time()
data.apply(match_row, axis=1)
print(time.time() - start)

#%%
# Rank scores
scores = map(env.expose, ratings.Rating)
ratings['Score'] = list(scores)
leaderboard = ratings.sort_values('Score', ascending=False)
leaderboard.head(25)

#%%
