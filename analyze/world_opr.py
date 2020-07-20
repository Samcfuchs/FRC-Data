import pandas as pd
from models import OPRModel
import time

YEAR = 2016
model = OPRModel()

start = time.time()

data = pd.read_csv(f"data/{YEAR}_MatchData_ol.csv")
teams, train_data = OPRModel.load(data)
model.train(train_data, train_data.score)

print(f"Time: {int(time.time() - start)} s")
print(model.table.head(10))