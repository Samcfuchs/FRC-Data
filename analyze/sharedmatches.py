import pandas as pd
import numpy as np

teams = [254, 118]
#teams = [236,1124]

year = 2019
for year in range(2001, 2020):
    file = f"C:/Users/Sam/Documents/236/Statistics/data/{year}_MatchData_basic.csv"
    data = pd.read_csv(file, index_col=False)

    indices = [np.array(data.loc[data.Team==team, 'Key']) for team in teams]

    a = np.array(indices)

    if a.shape[0] == 2:
        print(f"{year}: {np.intersect1d(a[0],a[1], assume_unique=True)}")
    else:
        print(f"{year}: {np.intersect1d(np.intersect1d(a[0],a[1]), a[2])}")

print("Done")
    
