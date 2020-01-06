#%% [markdown]
# Demo OPR Model

#%%
from models import OPRModel
import seaborn as sns; sns.set()
import time

#%%
# Train Model
model = OPRModel()

start = time.time()
model.train("../data/2012_MatchData_ol.csv")
print(f"Time: {int(time.time() - start)} s")

#%%
sns.kdeplot(model.opr_table.opr)

