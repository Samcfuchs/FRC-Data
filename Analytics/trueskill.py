#%% [markdown]
# # Implementing TrueSkill for FRC
# The Elo system has been introduced to FRC by a number of people, most
# prominently Caleb Sykes, who built his own Elo model based on margins of
# victory, and whose scouting spreadsheets are widely known in the community.
# However, the Elo model has some significant weaknesses when applied to the FRC
# game
#
# ## Problems with the Elo Model
# The chief issue with the elo model is that it's not designed for the task
# we're putting it to.
#
# ### The multiplayer problem
# Elo designed his ranking system for chess, a 1 vs 1 game. When we extend this
# model to 3 vs 3 FRC matches, we made a couple assumptions. First, we assumed
# that the skill of an alliance was equal to the sum of the skills of its
# members. This is roughly accurate, and works well enough when applied
# symmetrically, but we know that some teams work together better than others -
# an alliance of 1114 and 2056 will certainly outperform an alliance of 1114 and
# 254, even if 254 has a higher rating than both. isn't a good basis for more
# complex assumptions.
#
# The complement of this assumption lies in the training of the elo model - when
# a team wins or loses a match, the penalty is applied equally to each team.
# It's hard to say exactly how we should allocate points to the members of the
# alliance, it's not intuitive that they should be equal.
#
# ### The Crisis of Confidence
# When any model starts out, it has to assume that all the competing teams are
# of equal skill. However, the Elo model makes no acknowledgement of this
# assumption. We can artificially inflate the $K$-value of early matches to
# allow teams to separate themselves, but this could equally lead to an unlucky
# team early on accumulating a deficit that is difficult to overcome. In
# addition, because some teams only compete in ten matches throughout the
# season, it's a bit unfair to have their final score be a result of ten very
# volatile matches. A good model should in some way acknowledge when it makes
# those assumptions and give a confidence level for each team's score.
#
# ### Tuning Things is Hard and Subjective
# Another challenge in building a good metric is trying to eliminate the role of
# human intervention. Naturally, people (including me) are biased and will build
# models that naturally support their biases. Therefore, if we can build a model
# that eliminates that human component to the best of our abilities, we then
# maximize its predictive power. To this end, the Elo model has two different
# constants that need to be chosen subjectively to best sort the players. When I
# built my model, I arbitrarily used the ones used by the World Chess
# Federation, without putting too much effort into trying to optimize it. This
# process could probably be improved but I don't want to.

#%%
import pandas as pd
import time
import trueskill as ts
from typing import Tuple
import math
import os
import tbapy

tba = tbapy.TBA(os.environ['TBA_API_KEY'])

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

#%% [markdown] 
# Let's build some convenience functions for efficiency. For the sake of speed, 
# we want to be able to `.apply` a function across the dataframe, so we build 
# some wrapper functions around `TrueSkill.rate`.

#%%
# Set up rating
Alliance = Tuple[int, int, int]
TIE_RATE = len(data.loc[data.winner=='tie',:])/len(data)

env = ts.setup(draw_probability=TIE_RATE)

# Build ranking table
teams = data.blue + data.red
teams = [t for match in teams for t in match]
teams = list(set(teams))

r = [ts.Rating() for _ in teams]

ratings = pd.DataFrame(data={'Team':teams, 'Rating':[ts.Rating()]*len(teams)})

def match(table, blue: Alliance, red: Alliance, winner: str, inplace=False):
    r_blue = list(table.loc[table.Team.isin(blue), 'Rating'])
    r_red = list(table.loc[table.Team.isin(red), 'Rating'])

    result = { 'blue':1, 'red':1 }
    if winner != 'tie':
        result[winner] -= 1

    new_blue, new_red = ts.rate([r_blue, r_red], result.values())

    if inplace:
        table.loc[table.Team.isin(blue), 'Rating'] = new_blue
        table.loc[table.Team.isin(red), 'Rating'] = new_red

    return new_blue, new_red

def match_row(row):
    match(ratings, row.blue, row.red, row.winner, inplace=True)

#%%
# Run matches
start = time.time()
data.apply(match_row, axis=1)
print(time.time() - start)

#%%
# Rank scores
scores = map(env.expose, ratings.Rating)
ratings['Score'] = list(scores)
leaderboard = ratings.sort_values('Score', ascending=False)
leaderboard.reset_index(drop=True,inplace=True)
leaderboard.head(25)

#%% [markdown]
# Let's see a distribution of these scores - we hope that they're approximately
# normally distributed, since that indicates the metric is accurate and can be
# used to make valid predictions.

#%%
import seaborn as sns; sns.set(color_codes=True)
sns.kdeplot(leaderboard.Score)

#%%
def quality(blue:Alliance, red:Alliance):
    r_blue = list(ratings.loc[ratings.Team.isin(blue), 'Rating'])
    r_red = list(ratings.loc[ratings.Team.isin(red), 'Rating'])

    return ts.quality((r_blue, r_red))

def win_prob(blue:Alliance, red:Alliance):
    r_blue = list(ratings.loc[ratings.Team.isin(blue), 'Rating'])
    r_red = list(ratings.loc[ratings.Team.isin(red), 'Rating'])

    blue_mu = sum(r.mu for r in r_blue)
    blue_sigma = sum((env.beta**2 + r.sigma**2) for r in r_blue)

    red_mu = sum(r.mu for r in r_red)
    red_sigma = sum((env.beta**2 + r.sigma**2) for r in r_red)

    x = (blue_mu - red_mu) / math.sqrt(blue_sigma+red_sigma)
    p_blue_win = env.cdf(x)
    return p_blue_win

def match_teams(match_key):
    match = tba.match(key=match_key,simple=True)
    blue = match.alliances['blue']['team_keys']
    red = match.alliances['red']['team_keys']

    blue = list(map(lambda t: int(t[3:]), blue))
    red = list(map(lambda t: int(t[3:]), red))

    return (blue,red)

#%%
# Predict match
match_key = "2019dar_qm82"
m_teams = match_teams(match_key)
print(f"Match: {match_key}")
print(f"Blue: {m_teams[0]}")
print(f"Red: {m_teams[1]}")
print(f"Blue win probability: {win_prob(m_teams[0],m_teams[1]):.3%}")
print(f"Match quality: {quality(m_teams[0],m_teams[1]):.3}")

#%%
# Rank event
event = "2019dar"

event_teams = tba.event_teams(event, keys=True)
event_teams = map(lambda t: int(t[3:]), event_teams)

event_ranking = leaderboard.loc[leaderboard.Team.isin(event_teams),:]
event_ranking.sort_index()
event_ranking['Rank'] = event_ranking.Score.rank(ascending=False)
event_ranking.head(10)

#%% [markdown]
# ## Testing
# We'll run a formal test for our data, training it on the first qualifying
# weeks of competition, then we'll see how well it is able to predict
# championship matches. This is a pretty ideal test case - all of the
# championship teams have played a significant number of matches already, and
# will be playing to the best of their ability at the championship.

#%%
# Train on qualifying data
training = data.loc[data.Week <= 7,:]

trained = pd.DataFrame(data={'Team':teams, 'Rating': [ts.Rating()]*len(teams)})
training.apply(lambda row:match(trained, row.blue, row.red, row.winner, inplace=True), axis=1)
trained.head(10)

#%%
# Test
test = data.loc[data.Week > 7,:]
test['blue_win'] = test.winner.map({'blue':1, 'red':0, 'tie':0.5})
pred = test.apply(lambda row:win_prob(row.blue, row.red), axis=1)
test.loc[:,'prediction'] = pred
test.loc[:,'rounded_prediction'] = list(map(round, pred))
test.loc[:,'error'] = test.prediction - test.blue_win
print(f"Mean Squared Error: {(test.error**2).mean():.3}")
print(f"Raw predictions correct: {(test.blue_win == test.rounded_prediction).mean():.3%}") 

#%% [markdown]
# Let's make some bold predictions. From just the alliance picks, we'll predict
# who will win the 2019 championships.
