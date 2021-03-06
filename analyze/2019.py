#%%
# Import and process data
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
sns.set(color_codes=True)
import os

# Const
cargo_color = "#F9651D"
panel_color = "#FFC613"

# Set up data
data = pd.read_csv("C:/Users/Sam/Documents/236/Statistics/data/2019_MatchData.csv")

# Generate columns
data["cargoScored"] = data["cargoPoints"] / 3
data["panelsScored"] = data["hatchPanelPoints"] / 2
data['Team'] = list(map(str,data.Team))

data.head(6)
print(len(data))
list(data)
#teams = pd.read_csv("../data/TeamInfo.csv")

#%%
# Stratify data by teams
data_team = {}
for i, row in data.iterrows():
    team = row.Team

    try:
        data_team[team].append(row)
    except KeyError:
        data_team[team] = []
        data_team[team].append(row)
#%%
# Convert team records to dataframes
#for t in data_team:
#    data_team[t] = pd.DataFrame(data_team[t])

data_team = {t: pd.DataFrame(data_team[t]) for t in data_team}

#%%
team = '236'
week = 6

fig, (ax1,ax2) = plt.subplots(2,1, figsize=(10,10))
shade = False
lim = 20
w_ovr = 0.58

team_dist = data.loc[(data.Team == team) & (data.Week == week), :]
ovr_dist = data.loc[(data["Robot Number"] == 1) & (data.Week == week), :]

sns.kdeplot(team_dist["cargoScored"], shade=shade, color=cargo_color, ax=ax1)
sns.kdeplot(team_dist["panelsScored"], shade=shade, color=panel_color, ax=ax1)

sns.kdeplot(ovr_dist['cargoScored'], shade=shade, color=cargo_color, ax=ax2, bw=w_ovr)
sns.kdeplot(ovr_dist['panelsScored'], shade=shade, color=panel_color, ax=ax2, bw=w_ovr)

ax1.axvline(team_dist["cargoScored"].mean(), color=cargo_color, linestyle='dashed')
ax1.axvline(team_dist["panelsScored"].mean(), color=panel_color, linestyle='dashed')

ax2.axvline(ovr_dist['cargoScored'].mean(), color=cargo_color, linestyle='dashed')
ax2.axvline(ovr_dist['panelsScored'].mean(), color=panel_color, linestyle='dashed')

ax1.set_title(team + " Week {} Scoring Distribution".format(week))
ax2.set_title("Overall Week {} Scoring Distribution".format(week))

ax1.set_xlim(right=lim)
ax2.set_xlim(right=lim)

ax1.legend(["Cargo Scored", "Panels Scored",
    "Mean Panels: {}".format(round(team_dist["cargoScored"].mean(),2)),
    "Mean Cargo: {}".format(round(team_dist["panelsScored"].mean(),2))]
)
ax2.legend(["Cargo Scored", "Panels Scored",
    "Mean Panels: {}".format(round(ovr_dist["cargoScored"].mean(),2)),
    "Mean Cargo: {}".format(round(ovr_dist["panelsScored"].mean(),2))]
)
fig.savefig("distribution2.png")
fig.show()

#%%
team = "236"
def getTeamData(team, filt=lambda df: df):
    df = filt(data_team[team])
    return {
        "Team": team, 
        "avgCargo": df.cargoScored.mean(), 
        "avgPanels": df.panelsScored.mean()
    }

f = lambda df: df.loc[df.Week > 3,:]

teamdata_l = [getTeamData(t,f) for t in data_team]

teamdata = pd.DataFrame(teamdata_l)

df = data_team[team]
t_cargo = df.loc[df.Week==6,"cargoScored"].mean()
t_panels = df.loc[df.Week==6,"panelsScored"].mean()

fig, ax = plt.subplots(1,1, figsize=(8,5))
sns.kdeplot(teamdata.avgCargo, ax=ax, color=cargo_color)
sns.kdeplot(teamdata.avgPanels, ax=ax, color=panel_color)

fig.suptitle("Average Team-wise Scoring Week > 3")

ax.axvline(t_cargo, color=cargo_color, linestyle='dashed')
ax.axvline(t_panels, color=panel_color, linestyle='dashed')
ax.set_xlim(right=14)

fig.savefig("Teamwise_6.png")
fig.show()

#%%
# Get tails for density plot
better_panels = teamdata.loc[teamdata.avgPanels >= t_panels, :]
better_cargo = teamdata.loc[teamdata.avgCargo >= t_cargo, :]
print("Tail for cargo: {}".format(len(better_cargo)))
print("Tail for panels: {}".format(len(better_panels)))

#%%
print(len(data_team))
