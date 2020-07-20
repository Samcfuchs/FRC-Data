# %%
from models import OPRModel
import matplotlib.pyplot as plt
import seaborn as sns; sns.set()
import numpy as np
import pandas as pd

# %%
targets = ['teleopCellsInner','teleopCellsOuter','teleopCellsBottom', 'autoCellPoints', 'rp']

matchdata = pd.read_csv("../data/2020_MatchData.csv", index_col=[0,12])
matchdata_ol = pd.read_csv("../data/2020_MatchData_ol.csv", index_col=0)

teams, team_data = OPRModel.load(matchdata_ol.copy())
matchdata = matchdata.loc[matchdata["Robot Number"]==1,targets]

table = matchdata.merge(team_data['teams'], how='left', left_index=True, right_index=True)
table.head()

# %%
model = OPRModel()
y = table.drop('teams',axis=1).to_numpy()
y_names = table.drop('teams',axis=1).columns
y_names = {i:n for i,n in enumerate(y_names)}

model.train(table, y)
model.table.rename(columns=y_names,inplace=True)
results = model.table.copy()
results.head(10)

# %%
results['output'] = results.apply(lambda r: 3 * r.teleopCellsInner + 2 * r.teleopCellsOuter + r.teleopCellsBottom, axis=1)
results.sort_values('output',ascending=False).head(10)

# %%
#combo.to_csv('data/2020_cell_contribution.csv')
