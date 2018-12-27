import requests
from datetime import date, datetime
import time
import sys
import importlib
lib = importlib.import_module("Lib")

try:
    YEAR = sys.argv[1]
except IndexError:
    YEAR = input("Year (e.g. 2018): ")

if int(YEAR) < 2007:
    raise ValueError("Only valid for 2007 onward")
FILENAME = "data/{}_TeamDivisions.csv".format(YEAR)
divList = ['carv', 'gal', 'hop', 'new', 'roe', 'tur', 'arc', 'cars', 'cur', 'tes', 'dal', 'dar']
cmps = {
    '2016': [''],
    '2017': ['mo', 'tx'],
    '2018': ['mi', 'tx']
}

s = lib.init()

# Get list of teams from championships
print("Getting list of CMP teams")
cmpteams = {}
for div in divList:
    r = s.get('{base}/event/{yr}{div}/teams/keys'.format(base=lib.TBA_BASE, yr=YEAR, div=div))
    for team in r.json():
        cmpteams[team] = div

print("Getting list of Einstein teams")
einsteinteams = []
if int(YEAR) <= 2016:
    cmpyr = "2016"
elif int(YEAR) == 2017:
    cmpyr = "2017"
else:
    cmpyr = "2018"
for cmp in cmps[cmpyr]:
    r = s.get('{base}/event/{yr}cmp{cmp}/teams/keys'.format(base=lib.TBA_BASE, yr=YEAR, cmp=cmp))
    einsteinteams += r.json()

def getDivision(team):
    if type(team) is int:
        team = "frc" + str(team)

    if team not in cmpteams:
        return "NA"
    else:
        return cmpteams[team]

print("Getting team list")
teamdata = lib.get_team_data(YEAR,"/keys")

print("Associating team divisions")
divteams = {}
for team in teamdata:
    divteams[team] = getDivision(team)

print("Building filestring")
data = ""
data += "Team,Division,Einstein\n"
for team in divteams:
    data += team[3:] + ","
    data += divteams[team] + ','
    if team in einsteinteams:
        data += "TRUE"
    else:
        data += "FALSE"
    data += "\n"

print("Writing file")
with open(FILENAME, 'w', encoding='utf-8') as f:
    f.write(data)

print("Found {0} teams".format(len(divteams)))
print("Wrote data to {0}".format(FILENAME))
