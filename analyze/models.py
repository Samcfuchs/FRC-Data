import trueskill as ts
import pandas as pd
import numpy as np
from typing import Tuple
import math
import tbapy
import os
import json

try:
    with open("../keys.json", 'r') as f:
        data = json.load(f)
        tba_key = data['TBA_API_KEY']

    tba = tbapy.TBA(tba_key)
except KeyError:
    print("No TBA key loaded")


def process_data(data):
    """
    Collate teams into 3-tuple alliances for each match and drop extra columns.
    """
    cols_ren = {
        'Competition Level':'comp_level',
        'Match Number': 'match',
        'Set Number': 'set',
    }
    team_cols = ['blue1','blue2','blue3','red1','red2','red3']
    df = data.copy()

    df.rename(columns=cols_ren, inplace=True)

    df.winner.fillna('tie', inplace=True)
    #df.dropna(inplace=True)
    df.red3 = pd.to_numeric(df.red3) # For 2006

    df['blue'] = list(zip(df.blue1, df.blue2, df.blue3))
    df['red'] = list(zip(df.red1, df.red2, df.red3))
    df.drop(team_cols, axis=1, inplace=True)

    df = df.loc[df['blue score'] + df['red score'] > -2,:]

    return df


def sort_data(df):
    """
    Sort matches into the approximate order they occurred
    """
    sort_order = ['Week','event_n','Event','comp_level_n','set','match']

    comp_level_f = { 'qm':0, 'qf':1, 'sf':2, 'f':3 }
    event_f = lambda k: 1 if k[:3] == 'cmp' else 0

    df['comp_level_n'] = df.comp_level.map(comp_level_f)
    df['event_n'] = df.Event.map(event_f)

    df.sort_values(sort_order, inplace=True)

    df.drop(['event_n','comp_level_n'], axis=1, inplace=True)

    return df


def get_teams(years):
    """
    Get a list of all teams that competed in the given range of years
    """
    teams = set()
    for year in years:
        teams.update([int(key[3:]) for key in tba.teams(year=year, keys=True)])
    
    return list(teams)


class EloModel:

    def __init__(self, teams=[], k=10, n=400, i=1000, logging=False):
        self.K = k
        self.N = n
        self.I = i
        self.logging = logging

        self.table = pd.DataFrame(columns=['Team','Rating','Rank'])
        self.log = {'Key':[], 'Prediction':[]}
        self.table.Team = teams
        self.table.Rating = [self.I] * len(self.table)
        self.table.set_index('Team', inplace=True)
    

    def load(self, filename):
        """ Load the model from a csv file """
        csv = pd.read_csv(filename)
        csv.set_index('Team', inplace=True)
        self.table = csv


    def rate(self, team):
        """ Get the rating for a team """
        return self.table.loc[team, 'Rating']
    
    
    def rate_alliance(self, alliance:Tuple):
        """ Get the total rating of an alliance """
        return sum(self.table.loc[alliance, 'Rating'])
    

    def P(self, r1, r2):
        """ Get the probability that r1 defeats r2 """
        return 1.0 / ( 1 + math.pow(10, (r2-r1)/self.N) )


    def predict(self, blue, red):
        """ Get the probability that the blue alliance wins """
        r_b = self.rate_alliance(blue)
        r_r = self.rate_alliance(red)

        p_b = self.P(r_b, r_r)

        return p_b
    
    
    def train(self, row):
        """ Train on a single match """
        b = row['blue']
        r = row['red']

        # find the win probability for blue
        p_b = self.predict(b, r)

        if self.logging:
            self.log['Key'].append(row.Key)
            self.log['Prediction'].append(p_b)
            
        # calculate the rating adjustment
        outcome = { 'blue': 1.0, 'red': 0.0, 'tie': 0.5 }[row.winner]
        delta = self.K * (outcome - p_b)

        # apply adjustment
        self.table.loc[row['blue'], 'Rating'] += delta
        self.table.loc[row['red'], 'Rating'] -= delta
    
    
    def test(self, winner) -> float:
        """ Get the Brier score of the model on the predictions it logged """
        winner.fillna('tie')
        f = { 'blue':1, 'red':0, 'tie':0.5 }

        return ((winner.map(f) - self.log['Prediction'])**2).mean()


    def rank(self):
        """ Rank and sort the table """
        self.table.Rank = self.table.Rating.rank(ascending=False)
        self.table.sort_values('Rating', ascending=False, inplace=True)
    

    def export(self, filename):
        """ Export the model to a csv file """
        columns = ['Rating', 'Rank']
        self.rank()
        self.table.to_csv(filename, columns=columns)


class TSModel:

    def __init__(self, teams=[], env=ts.setup(), logging=False):
        self.logging = logging
        self.env = env
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
        sigma = math.sqrt(sum((self.env.beta**2 + r.sigma**2) for r in ratings))

        return ts.Rating(mu, sigma)

    
    def train(self, row):
        """ Train the model on a single match record """
        r_blue = list(self.table.loc[row.blue, 'Rating'])
        r_red = list(self.table.loc[row.red, 'Rating'])

        if self.logging:
            self.log['Key'].append(row.Key)
            self.log['Prediction'].append(self.predict(row.blue, row.red))

        if row.winner == 'blue':
            result = [0,1]
        elif row.winner == 'red':
            result = [1,0]
        elif row.winner == 'tie':
            result = [0,0]
        
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


    @staticmethod
    def load(dataframe):
        """
        Import a file produced by MatchData_oneline and build a DataFrame that can
        be used to construct the sparse matrix and train the model.
        """
        DROPS = ['Year','Event','Week','comp_level','set','match','winner','City','State','Country','Time']
        COLS_REN = {
            'Key': 'key',
            'blue score':'score',  'blue':'teams',
            'red score':'score',   'red':'teams'
        }

        data = dataframe.copy()
        data = process_data(data)
        data = sort_data(data)
        data = data.drop(DROPS, axis=1)

        # Break into alliances
        blue = data[['blue score', 'blue']].copy()
        blue['Alliance'] = ['blue']*len(blue)
        blue.rename(columns=COLS_REN, inplace=True)

        red = data[['red score','red']].copy()
        red['Alliance'] = ['red']*len(red)
        red.rename(columns=COLS_REN, inplace=True)

        data = pd.concat([blue,red], axis=0).sort_index()
        data.set_index([data.index,"Alliance"], inplace=True)
        data = data[['teams','score']]

        teams = list(set([t for a in data.teams for t in a]))

        return teams, data


    def build_sparse_matrix(self, data, teams=None):
        """
        Build the sparse matrix from match-alliance pairs and event-match keys.
        If no list of teams is given, extract names of all teams from data
        """
        
        if teams is None:
            teams = list(set([ t for a in data.teams for t in a ]))
        self.teams = teams

        index = lambda r: '_'.join(map(str, r.name))

        row = {t:0 for t in self.teams}
        sparse = { index(r):dict(row) for i,r in data.iterrows() }

        def f(row):
            sparse[index(row)].update(dict(zip(row.teams, [1,1,1])))
        
        data.apply(f, axis=1)

        sparse_m = np.array([list(d.values()) for d in sparse.values()])
    
        self.sparse = sparse_m

        return self.sparse


    def train(self, data, y):
        """
        Construct the sparse matrix and fit OPRs for the scores in y. Returns
        a dataframe representation of the OPR table.

        Arguments:

        data -- a dataframe with a column `teams` which contains tuples of the
        members of each alliance for each alliance-match record.

        y    -- a 1-dimensional numpy array of the scores of each
        alliance-match. These must be in the same order as `data`, but they can
        represent any metric that the model should solve for.
        """
        self.build_sparse_matrix(data)

        coef = self.sparse.astype(np.bool)
        #scores = y.to_numpy()
        scores = np.array(y, dtype=np.uint8)

        print("coef shape:", coef.shape)
        print("y shape:", y.shape)
        oprs, self.resid,_,_ = np.linalg.lstsq(coef, scores, rcond=-1)

        self.opr_dict = { t:o for (t,o) in zip(self.teams, oprs) }

        self.table = pd.DataFrame(oprs, index=self.teams)
        self.table.index.name = 'team'
        #self.table.sort_values('opr', ascending=False, inplace=True)

        return self.table


    def predict(self, alliance):
        """ Predict the total score for an alliance """
        return self.table.loc[alliance, "opr"].sum()


    def rank(self):
        """ Rank and sort the table """
        self.table["Rank"] = self.table.opr.rank(ascending=False)
        self.table.sort_values('opr', ascending=False, inplace=True)


    def export(self, filename):
        """ Export the table to a csv file """
        columns = ["opr", "Rank"]
        self.rank()
        self.table.to_csv(filename, columns=columns)
    

