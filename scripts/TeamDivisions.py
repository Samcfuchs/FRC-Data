import requests
from datetime import date, datetime
import time
import sys
import lib

try:
    YEAR = int(sys.argv[1])
except IndexError:
    YEAR = input("Year (e.g. 2018): ")

if int(YEAR) < 2007:
    raise ValueError("Only valid for 2007 onward")
FILENAME = "data/{}_TeamDivisions.csv".format(YEAR)

divList = ['carv', 'gal', 'hop', 'new', 'roe', 'tur', 'arc', 'cars', 'cur', 'tes', 'dal', 'dar']
if YEAR <= 2016:
    cmps = [""]
elif int(YEAR) == 2017:
    cmps = ["mo", "tx"]
else:
    cmps = ["tx", "mi"]

s, tba, _, _ = lib.init()

print("Getting list of teams")
teamlist = tba.teams(year=YEAR, keys=True)

print("Getting division lists")
divTeams = {div: tba.event_teams(str(YEAR) + div, keys=True) for div in divList}

teamDivs = {t: div for div,teams in divTeams.items() for t in teams}

print("Getting einstein team list")
einsteinteams = []
for cmp in cmps:
    einsteinteams += tba.event_teams("{yr}cmp{st}".format(yr=YEAR, st=cmp), keys=True) 

print("Building data")
data = "Team,Division,Einstein\n"
for team in teamlist:
    try:
        div = teamDivs[team]
    except KeyError:
        div = "NA"

    data += f"{team[3:]},{div},{team in einsteinteams}\n"

print("Writing data")
with open(FILENAME, 'w', encoding='utf-8') as f:
    f.write(data)

print(f"Found {len(teamlist)} teams")
print(f"Wrote data to {FILENAME}")
