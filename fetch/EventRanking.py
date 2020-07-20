import lib
import argparse

"""
Generates the current ranking table for the given event
Uses TBA's definitions of field titles, so this should work generically for
any year.
"""

parser = argparse.ArgumentParser(description="Get the ranking table for an event.")
parser.add_argument('event', metavar='E', type=str, help="Event key (example: 2019cthar)")
parser.add_argument('-f','--file', type=str, help="Filename (default: Ranking_eventkey.csv)")

args = parser.parse_args()
if args.file is None:
    args.file = "data/Ranking_" + args.event + ".csv"

EVENT_KEY = args.event
YEAR = args.event[:4]
FILENAME = args.file

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

print(f"Wrote data to {FILENAME}")
