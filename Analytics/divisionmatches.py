import pandas as pd
import numpy as np

teams = [254, 118, 148]
#teams = [236,1124]

year = 2019
for year in range(2007, 2019):
    file = f"C:/Users/Sam/Documents/236/Statistics/data/{year}_TeamDivisions.csv"
    data = pd.read_csv(file, index_col=False)

    divisions = [data.loc[data.Team==team, 'Division'].values[0] for team in teams]

    print(f"{year}: {set(divisions)}")

print("Done")
    
