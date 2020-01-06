#%%
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
sns.set()

FNAME_RATINGS = "Analytics/data/2019_end_ratings.csv"
FNAME_METRIC = "data/ACS_17_5YR_S1903.csv"
FNAME_DETAILS = "data/TeamZips.csv"

ratings = pd.read_csv(FNAME_RATINGS).drop(["mu","sigma"], axis=1)
details = pd.read_csv(FNAME_DETAILS).drop(['City', 'State', 'Country'], axis=1)

income = pd.read_csv(FNAME_METRIC).loc[:,['GEO.id2','HC03_EST_VC02']].astype({"GEO.id2": "object"})
income.rename(columns={"GEO.id2": "ZIP", "HC03_EST_VC02": "income"}, inplace=True)
income.ZIP = income.ZIP.map(lambda s: (5-len(str(s))) * "0" + str(s))

print(income.head())

combined = ratings.merge(details, how="left", on="Team")

combined = combined.merge(income, left_on="Zip", right_on="ZIP")

plot = plt.scatter(combined.income, combined.Score)
plt.savefig("Analytics/compiled/figure.png")


# %%
