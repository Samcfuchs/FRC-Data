import requests
from datetime import date, datetime
import time
import sys
import importlib
lib = importlib.import_module("Lib")
s=lib.s

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

# Get list of teams from TBA


def get_data():
    print("  Getting rankings")
    rank = s.get('{base}/event/{eventkey}/rankings'.format(base=lib.TBA_BASE, eventkey=EVENT_KEY))
    print("  Getting oprs")
    oprs = s.get('{base}/event/{eventkey}/oprs'.format(base=lib.TBA_BASE, eventkey=EVENT_KEY))
    # Error if data is no good
    if rank.status_code == 404 or rank.json()['rankings'] == None:
        raise ValueError("Event data does not exist")

    sort_orders = [x['name'] for x in rank.json()['sort_order_info']]
    # 2018 data has an unlabeled empty field that is always 0s
    # It's not in the sort order info so we add a label for that field
    if YEAR == '2018':
        sort_orders.append("Null")

    return rank, oprs, sort_orders


def get_header(sort_orders):
    data = ""
    data += 'Rank,Team,'
    data += ','.join(sort_orders)
    data += ',W,L,T,OPR,DPR,CCWM\n'
    return data


def get_team_data(team, oprs):
    data = ""
    data += str(team['rank']) + ','
    data += team['team_key'][3:] + ','

    for value in team['sort_orders']:
        data += str(value) + ','

    data += str(team['record']['wins']) + ','
    data += str(team['record']['losses']) + ','
    data += str(team['record']['ties']) + ','

    data += str(oprs.json()['oprs'][team['team_key']]) + ','
    data += str(oprs.json()['dprs'][team['team_key']]) + ','
    data += str(oprs.json()['ccwms'][team['team_key']]) + ','

    return data + "\n"


print("Retrieving data")
rank, oprs, SORT_ORDERS = get_data()

print("Writing file")
with open(FILENAME, 'w') as f:
    f.write(get_header(SORT_ORDERS))

    data = ""
    for team in rank.json()['rankings']:
        data += get_team_data(team, oprs)
    f.write(data)

print("Wrote data to {0}".format(FILENAME))
