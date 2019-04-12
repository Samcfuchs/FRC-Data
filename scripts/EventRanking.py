import requests
from datetime import date, datetime
import time
import sys
import lib
import tbapy

"""
Generates the current ranking table for the given event
Uses TBA's definitions of field titles, so this should work generically for
any year.
"""

try:
    EVENT_KEY = sys.argv[1]
except IndexError:
    EVENT_KEY = input("Event key (e.g. 2018cthar): ")

YEAR = EVENT_KEY[:4]
if int(YEAR) < 2007:
    raise ValueError("Only valid for 2007 onward")
FILENAME = "data/Ranking_" + EVENT_KEY + ".csv"

s, tba, _, _ = lib.init()


def get_header(rank):
    data = "Rank,Team,"
    data += ','.join(map(lambda p : p['name'], rank['sort_order_info']))

    if int(YEAR) >= 2018:
        data += ",Null"

    data += ",W,L,T,OPR,DPR,CCWM\n"
    return data


print("Retrieving data")
rank = tba.event_rankings(EVENT_KEY)
oprs = tba.event_oprs(EVENT_KEY)

print("Building data")
data = get_header(rank)

for i,team in enumerate(rank.rankings):
    team_key = team['team_key']

    row = [
        team['rank'],
        team_key[3:],

    ] + team['sort_orders'] + [

        team['record']['wins'],
        team['record']['losses'],
        team['record']['ties'],

        oprs['oprs'][team_key],
        oprs['dprs'][team_key],
        oprs['ccwms'][team_key]
    ]

    data += ','.join(map(str,row))
    data += "\n"

print("Writing file")
with open(FILENAME, 'w') as f:
    f.write(data)

print("Wrote data to {0}".format(FILENAME))
