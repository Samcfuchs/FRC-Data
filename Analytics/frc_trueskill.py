import trueskill as ts
import pandas as pd
import numpy as np
from typing import Tuple
import math
import tbapy
import os

class TSModel:
    table = pd.DataFrame(columns=['Team','Rating','Score','Rank'])
    tba = tbapy.TBA(os.environ['TBA_API_KEY'])

    def __init__(self, teams=[], tie_rate=0.02):
        self.env = ts.setup(draw_probability=tie_rate)

        self.table.Team = teams
        self.table.Rating = [ts.Rating()] * len(self.table)
        self.table.set_index('Team',inplace=True)


    def rate(self, team):
        """ Get the ranking information for a team or list of teams """
        return self.table.loc[team,:]
    

    def rate_alliance(self, alliance:Tuple):
        ratings = list(self.table.loc[alliance, 'Rating'])

        mu = sum(r.mu for r in ratings)
        sigma = sum((self.env.beta**2 + r.sigma**2) for r in ratings)

        return ts.Rating(mu, sigma)

    
    def rating(self, team):
        """ Get the specific rating for a team """
        return self.table.loc[team,:]
    

    def train(self, row):
        """ Train the model on a single match record """
        r_blue = list(self.table.loc[row.blue, 'Rating'])
        r_red = list(self.table.loc[row.red, 'Rating'])

        result = { 'blue':1, 'red':1 }
        if row.winner != 'tie':
            result[row.winner] -= 1
        
        new_blue, new_red = ts.rate([r_blue, r_red], result.values())

        self.table.loc[row.blue, 'Rating'] = new_blue
        self.table.loc[row.red, 'Rating'] = new_red

        return new_blue, new_red
    

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
