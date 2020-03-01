#%% [markdown]
# # Demo OPR Model
# This notebook briefly demonstrates some basic analytics using the OPR model
# built in models.py for this project.

#%%
from models import OPRModel
import seaborn as sns; sns.set()
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import time

# %% [markdown]
# Because this model is generalized, it's trivial to calculate world OPRs for
# all teams. This operation has been optimized significantly, but still takes up
# to 5 minutes.

#%%
# Train Model
YEAR = 2019
model = OPRModel()

start = time.time()
data = pd.read_csv(f"../data/{YEAR}_MatchData_ol.csv")
teams, train_data = OPRModel.load(data)
model.train(train_data, train_data.score)

print(f"Time: {int(time.time() - start)} s")
model.opr_table.head(10)

# %% [markdown]
# We can use this OPR table to visualize the rough distribution of skill in the
# given year.

# %%
sns.kdeplot(model.opr_table.opr, shade=True)
plt.title(f"{YEAR} OPR Distribution")
plt.xlabel("OPR")
plt.ylabel("Density")
plt.show()

# %% [markdown]
# We know generally that OPRs are most valuable in the scope of a single event,
# where information is less sparse and there are fewer variables. Let's try to
# train the model on event data.

# %%
YEAR = 2019
EVENT = "necmp"
FILENAME = f"../data/{YEAR}_MatchData_ol.csv"

event_model = OPRModel()

year_data = pd.read_csv(FILENAME)
event_data = year_data.loc[year_data.Event==EVENT, :]
teams, train_data = OPRModel.load(event_data)
event_model.train(train_data, train_data.score).head()

# %%
sns.kdeplot(event_model.opr_table.opr, shade=True)
plt.title(f"{YEAR}{EVENT} OPR Distribution")
plt.xlabel("OPR")
plt.ylabel("Density")
plt.show()

# %% [markdown]
# A more conventional analytics technique might be to average together all of a
# team's scoring performances. However, because this metric doesn't account for
# the abilities of their alliance members, we find that it's significantly less
# accurate than the OPR metric.

# %%
event_data_6 = pd.read_csv(f"../data/{YEAR}_MatchData.csv")
event_data_6 = event_data_6.loc[event_data_6.Event==EVENT,:]
event_data_6.head(12)

# %%
team = 195
event_data_6.loc[event_data_6.Team==team, "totalPoints"].mean() / 3

# %% [markdown]
# In this event, team 195 (the CyberKnights) have an OPR of 38, but a standard
# mean scoring statistic is only 29--a significant difference in a game that
# generally scored fewer than 100 points.
