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
# Setup
from frc_trueskill import TSModel
import tbapy
import os
import pandas as pd
import trueskill as ts
import time
import pickle
import seaborn as sns; sns.set(color_codes=True)
import matplotlib.pyplot as plt

YEAR = 2019
FILE = f"data/{YEAR}_MatchData_ol.csv"
tba = tbapy.TBA(os.environ['TBA_API_KEY'])

#%% [markdown]
# Let's import and set up our data here. Chiefly, we group the alliances into
# tuples and store them directly in the dataframe, which makes our algorithms
# much easier to write.

#%%
# Get match data
data = pd.read_csv(FILE)
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

# Data processing
data['blue'] = list(zip(data.blue1, data.blue2, data.blue3))
data['red'] = list(zip(data.red1, data.red2, data.red3))
data.drop(['blue1','blue2','blue3','red1','red2','red3'], axis=1, inplace=True)
data.winner.fillna('tie', inplace=True)
data.head()

#%% [markdown]
# We also need to sort the matches out so they go in order. This means that when
# we assess a given match with a given team, that team's score is updated with
# all the matches they've already played and none of the ones that they haven't.

#%%
# Sort matches in order they occurred
comp_level_f = { 'qm':0, 'qf':1, 'sf':2, 'f':3 }
data['comp_level_n'] = data.comp_level.map(comp_level_f)
data.sort_values(['Week','Event','comp_level_n','set','match'], inplace=True)
data.reset_index(inplace=True, drop=True)
data.drop('comp_level_n', axis=1, inplace=True)
data.head(10)

#%%
# Get list of teams
teams = data.blue + data.red
teams = [t for match in teams for t in match]
teams = list(set(teams))

#%% [markdown]
# Now we can actually train the model with a full year of match data. This
# usually takes around 4-5 minutes.

#%%
# Train model
model = TSModel(teams)

start = time.time()
data.apply(model.train, axis=1)
print(f"Training time: {int(time.time() - start)} s")

#%% [markdown] 
#
# We can now score and rank the teams based on their skill levels as assessed by
# the model. Note that we use `model.rank()` to apply scores to all the teams. A
# team's TrueSkill Rating consists of two values, $\mu$ and $\sigma$, which
# define a gaussian distribution of the player's probable skill. In order to
# rank teams, however, we need to reduce these values to a single number
# expressing score. The score of a player, then, is defined as the lower tail of
# their skill distribution - the skill they would hypothetically demonstrate in
# their worst game out of 1000. In our case,
#
# $$score_i = \mu_i - 3\sigma_i$$

#%%
# Evaluate results
model.rank()
model.table.sort_values('Score', ascending=False, inplace=True)
model.table.head()

#%% [markdown]
# We can use these scores to represent the general distribution of skill in FRC.
# A density plot of scores will work well enough, although ideally we could
# build a density plot out of the actual skill distributions.

#%%
# Visual
sns.kdeplot(model.table.Score, shade=True)

#%%
# One of the most powerful abilities this model brings to the table is
# predicting the outcomes of matches based on the competitors, as demonstrated
# below. Note that this works best with a well-trained model, so it's not very
# useful early on in competition.

#%%
# Predict match
def match_teams(match_key):
    match = tba.match(key=match_key,simple=True)

    blue = list(map(lambda t: int(t[3:]), match.alliances['blue']['team_keys']))
    red = list(map(lambda t: int(t[3:]), match.alliances['red']['team_keys']))

    return (blue,red)

match_key = "2019cmpmi_f1m1"
m_teams = match_teams(match_key)
print(f"Match: {match_key}")
print(f"Blue: {m_teams[0]}")
print(f"Red: {m_teams[1]}")
print(f"Blue win probability: {model.predict(m_teams[0],m_teams[1]):.3%}")
print(f"Match quality: {model.quality(m_teams[0],m_teams[1]):.3}")

#%%
# In the same way that we can rate a team's skill, we can use the team's skill
# to calculate the skill of an alliance. Note that the rating for an alliance is
# usually negative. This is because while we average the mean skills of the
# members, we add together their variances.

#%%
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
