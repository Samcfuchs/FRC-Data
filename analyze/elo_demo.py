#%% [markdown]
# # Elo Algorithm Demo

#%%
# Import libraries
import models
from models import EloModel
import pandas as pd
import time
import matplotlib.pyplot as plt
import seaborn as sns

#%%
# Train all-time Elo scores
years = range(2005, 2020)
teams = models.get_teams(years)

model = EloModel(teams, k=30, n=400, i=1000, logging=True)

print(f"Training on {','.join(map(str,years))}")
print('='*35)
start = time.time()
winners = []

for year in years:
    filename = f"../data/{year}_MatchData_ol.csv"
    data = pd.read_csv(filename)
    data = models.process_data(data)
    data = models.sort_data(data)
    winners.append(data.winner)

    print(f"Year: {year}")
    print(f"Simulating {len(data)} matches")
    substart = time.time()

    data.apply(model.train, axis=1)

    print(f"Training time: {int(time.time() - substart)} s")
    print("="*35)

    model.export(f"data/{year}_end_elos_k30.csv")

print(f"Training Time: {int(time.time() - start)} s")
print(f"Brier score: {model.test(pd.concat(winners))}")


#%%
sns.kdeplot(model.table.Rating, shade=True)
plt.show()

#%%
model.table.head(25)

#%%
# Test
YEAR = 2019

trained = EloModel(k=20, logging=True)
trained.load(f"data/{YEAR-1}_end_elos_k20.csv")

filename = f"../data/{YEAR}_MatchData_ol.csv"
data = pd.read_csv(filename)
data = models.process_data(data)
data = models.sort_data(data)

print(f"Year: {year}")
print(f"Simulating {len(data)} matches")
substart = time.time()

data.apply(trained.train, axis=1)

print(f"Training time: {int(time.time() - substart)} s")
print("="*35)

print(f"Brier: {trained.test(data.winner)}")


#%%
