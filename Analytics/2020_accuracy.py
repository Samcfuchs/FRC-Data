# %%
from models import OPRModel
import matplotlib.pyplot as plt
import seaborn as sns; sns.set()
import numpy as np
import pandas as pd

# %%
matchdata = pd.read_csv("../data/2020_MatchData.csv", index_col=[0,12])
matchdata_ol = pd.read_csv("../data/2020_MatchData_ol.csv", index_col=0)

teams, team_data = OPRModel.load(matchdata_ol.copy())
matchdata = matchdata.loc[matchdata["Robot Number"]==1,['teleopCellsInner','teleopCellsOuter']]

table = matchdata.merge(team_data['teams'], how='left', left_index=True, right_index=True)
table.head()

# %%
innermodel = OPRModel()
outermodel = OPRModel()

innermodel.train(table, table.teleopCellsInner)
outermodel.train(table, table.teleopCellsOuter)

combo = pd.DataFrame({'innerCellsContribution':innermodel.table.opr, 'outerCellsContribution':outermodel.table.opr})
combo.head()

# %%
combo['output'] = combo.apply(lambda r: 3 * r.innerCellsContribution + 2 * r.outerCellsContribution, axis=1)
combo.sort_values('output',ascending=False).head(10)

# %%
combo.to_csv('data/2020_cell_contribution.csv')
