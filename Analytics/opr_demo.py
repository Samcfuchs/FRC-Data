#%% [markdown]
# # Demo OPR Model

#%%
from models import OPRModel
import seaborn as sns; sns.set()
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import time

#%%
# Train Model
YEAR = 2008
model = OPRModel()

start = time.time()
data = pd.read_csv(f"../data/{YEAR}_MatchData_ol.csv")
teams, train_data = OPRModel.load(data)
model.train(train_data, train_data.score)

print(f"Time: {int(time.time() - start)} s")
model.opr_table.head(10)

# %%
sns.kdeplot(model.opr_table.opr, shade=True)
plt.xlabel("OPR")
plt.ylabel("Density")
plt.show()

# %% [markdown]
# We know generally that OPRs are most valuable in the scope of a single event,
# where information is less sparse and there are fewer variables. Let's try to
# train the model on event data.

# %%
YEAR = 2019
EVENT = "cmpmi"
FILENAME = f"../data/{YEAR}_MatchData_ol.csv"

event_model = OPRModel()

year_data = pd.read_csv(FILENAME)
event_data = year_data.loc[year_data.Event==EVENT, :]
teams, train_data = OPRModel.load(event_data)
event_model.train(train_data, train_data.score).head()

# %%
sns.kdeplot(event_model.opr_table.opr, shade=True)
plt.xlabel("OPR")
plt.ylabel("Density")
plt.show()
