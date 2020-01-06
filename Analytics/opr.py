#%% [markdown]
# # Calculating OPRs

#%%
# Set up environment
import models
import tbapy
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns; sns.set(color_codes=True)
import time
import os

tba = tbapy.TBA(os.environ['TBA_API_KEY'])

#%%
# Build data struct
YEAR = 2012
DROPS = ['Year','Event','Week','comp_level','set','match','winner']
COLS_REN = {
    'Key': 'key',
    'blue score':'score',  'blue':'teams',
    'red score':'score',   'red':'teams'
}

data = pd.read_csv(f"../data/{YEAR}_MatchData_ol.csv")
data = models.process_data(data)
data = models.sort_data(data)
data = data.drop(DROPS, axis=1)

teams = models.get_teams([YEAR])

# Break up into alliances
blue = data.loc[:, ['Key','blue score','blue']]
blue['alliance'] = ['blue']*len(blue)
blue.rename(columns=COLS_REN, inplace=True)
blue.index = blue.index * 2

red = data.loc[:, ['Key','red score','red']]
red['alliance'] = ['red']*len(red)
red.rename(columns=COLS_REN, inplace=True)
red.index = red.index * 2 + 1

data = pd.concat([blue,red], axis=0).sort_index()
data = data[['key','alliance','teams','score']]

data.head(10)

#%%
# Build sparse matrix
sparse = pd.DataFrame(0, index=np.arange(len(data)), columns=['key','alliance','score']+teams)
sparse['key'] = data['key']
sparse['alliance'] = data['alliance']
sparse['score'] = data['score']

#%% [markdown]
# This is where we populate the matrix with 1's everywhere that a team
# participated in the match in question. This is the step that takes the
# longest--we should try to optimize this more if possible.

#%%
# Populate matrix
def f(row):
    sparse.loc[(sparse.key==row.key) & (sparse.alliance==row.alliance), row.teams] = 1

start = time.time()
data.apply(f, axis=1)
print(f"Time: {int(time.time() - start)} s")

#%%
# Solve for OPRs
coef = sparse.drop(['key','alliance','score'], axis=1).to_numpy()
oprs,resid,_,_ = np.linalg.lstsq(coef, data.score, rcond=None)

#%%
# Display OPRs
opr_dict = { t:o for (t,o) in zip(teams, oprs) }

opr_table = pd.DataFrame({'team':teams, 'opr':oprs})
opr_table.sort_values('opr', ascending=False, inplace=True)
opr_table.head()

#%%
# Visualize OPRs
sns.kdeplot(opr_table.opr, shade=True)

#%%
# Test OPR accuracy
def predict(alliance):
    return sum([opr_dict[t] for t in alliance])

def diff(row):
    return np.power(row.score - predict(row.teams),2)
    
sq_errors = data.apply(diff, axis=1)
#sns.kdeplot(sq_errors, shade=True)
plt.hist(sq_errors)

# %%
