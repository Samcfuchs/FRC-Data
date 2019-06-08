import trueskill as ts
import pandas as pd
import numpy as np
from typing import Tuple
import math
import tbapy
import os

class TSModel:
    tba = tbapy.TBA(os.environ['TBA_API_KEY'])

    def __init__(self, teams=[], tie_rate=0.02, logging=False):
        self.logging = logging
        self.env = ts.setup(draw_probability=tie_rate)
        self.table = pd.DataFrame(columns=['Team','Rating','Score','Rank'])
        self.log = {'Key':[], 'Prediction':[]}

        self.table.Team = teams
        self.table.Rating = [ts.Rating()] * len(self.table)
        self.table.set_index('Team', inplace=True)


    def load(self, filename):
        csv = pd.read_csv(filename)
        rating = list(map(ts.Rating, zip(csv.mu, csv.sigma)))
        csv['Rating'] = rating
        csv.set_index('Team', inplace=True)
        self.table = csv.drop(['mu','sigma'], axis=1)


    def rate(self, team):
        """ Get the ranking information for a team or list of teams """
        return self.table.loc[team,:]
    

    def rate_alliance(self, alliance:Tuple) -> ts.Rating:
        ratings = list(self.table.loc[alliance, 'Rating'])

        mu = sum(r.mu for r in ratings)
        sigma = sum((self.env.beta**2 + r.sigma**2) for r in ratings)

        return ts.Rating(mu, sigma)

    
    def train(self, row):
        """ Train the model on a single match record """
        r_blue = list(self.table.loc[row.blue, 'Rating'])
        r_red = list(self.table.loc[row.red, 'Rating'])

        if self.logging:
            self.log['Key'].append(row.Key)
            self.log['Prediction'].append(self.predict(row.blue, row.red))

        if row.winner == 'blue':
            result = [1,0]
        elif row.winner == 'red':
            result = [0,1]
        elif row.winner == 'tie':
            result = [1,1]
        
        try:
            new_blue, new_red = ts.rate([r_blue, r_red], result)
        except ValueError:
            print(f"Blue Ratings: {r_blue}")
            print(f"Red Ratings: {r_red}")
            print(result)

        self.table.loc[row.blue, 'Rating'] = new_blue
        self.table.loc[row.red, 'Rating'] = new_red

        return new_blue, new_red
    

    def scale_sigma(self, k=2.0):
        """ Scale the standard deviation of all scores by k """
        scale = lambda r: ts.Rating(r.mu, k * r.sigma)
        self.table.Rating = self.table.Rating.map(scale)
    

    def predict(self, blue, red) -> float:
        """ Predict the outcome of a match """
        r_blue = list(self.table.loc[blue, 'Rating'])
        r_red = list(self.table.loc[red, 'Rating'])

        blue_mu = sum(r.mu for r in r_blue)
        blue_sigma = sum((self.env.beta**2 + r.sigma**2) for r in r_blue)

        red_mu = sum(r.mu for r in r_red)
        red_sigma = sum((self.env.beta**2 + r.sigma**2) for r in r_red)

        x = (blue_mu - red_mu) / math.sqrt(blue_sigma+red_sigma)
        p_blue_win = self.env.cdf(x)
        return p_blue_win
    

    def test(self, winner) -> float:
        """ Get the Brier score of the model on the predictions it logged """
        winner.fillna('tie')
        f = { 'blue':1, 'red':0, 'tie':0.5 }

        return ((winner.map(f) - self.log['Prediction'])**2).mean()


    def quality(self, blue, red) -> float:
        """ Get the generalized quality of a match """
        r_blue = list(self.table.loc[blue, 'Rating'])
        r_red = list(self.table.loc[red, 'Rating'])

        return ts.quality((r_blue,r_red))
    

    def score(self):
        """ Calculate scores for all teams and add into table """
        self.table.Score = self.table.Rating.map(self.env.expose)
    

    def rank(self):
        """ Score all teams and rank them according to their score """
        self.score()
        self.table.Rank = self.table.Score.rank(ascending=False)
        self.table.sort_values('Score', ascending=False, inplace=True)
    

    def export(self, filename:str) -> pd.DataFrame:
        """ Export model to csv file """
        columns = ['mu','sigma','Score','Rank']

        self.rank()
        ratings = map(list, self.table.Rating)
        ratings_inv = list(zip(*ratings))

        output = self.table.drop('Rating', axis=1)
        output['mu'] = ratings_inv[0]
        output['sigma'] = ratings_inv[1]

        output.to_csv(filename, columns=columns)

        return output


class OPRModel:

    def __init__(self):
        pass


    def build_records(self, matchdata):
        DROPS = ['Year','Event','Week','comp_level','set','match','winner']
        COLS_REN = {
            'Key': 'key',
            'blue score':'score',  'blue':'teams',
            'red score':'score',   'red':'teams'
        }

        data = matchdata.drop(DROPS, axis=1)

        blue = data.loc[:,['Key','blue score','blue']]
        blue['alliance'] = ['blue']*len(blue)
        blue.rename(columns=COLS_REN, inplace=True)
        blue.index = blue.index * 2

        red = data.loc[:,['Key','red score','red']]
        red['alliance'] = ['red']*len(red)
        red.rename(columns=COLS_REN, inplace=True)
        red.index = red.index * 2 + 1

        data = pd.concat([blue,red], axis=0).sort_index()
        data = data[['key','alliance','teams','score']]

        return data


    def build_sparse_matrix(self, records):
        sparse = pd.DataFrame(0, index=np.arange(len(records)), columns=['key','alliance']+teams)
        sparse['key'] = data['key']
        sparse['alliance'] = data['alliance']

        def f(row):
            sparse.loc[(sparse.key==row.key) & (sparse.alliance==row.alliance),row.teams] = 1

        records.apply(f, axis=1)
        
        return sparse


    def train(self, data):
        records = self.build_records(data)
        sparse = self.build_sparse_matrix(records)

        coef = sparse.drop(['key','alliance'], axis=1).to_numpy()
        self.oprs,_,_,_ = np.linalg.lstsq(coef, data.score, rcond=None)
        self.oprs = pd.DataFrame({'team':teams, 'opr':oprs})
        self.oprs.sort_values('opr', ascending=False, inplace=True)
    
    
    def predict(self):
        pass
    

