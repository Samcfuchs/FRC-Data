import requests
from datetime import date, datetime
import time
# Make sure you set your API key first
import geocoder
import importlib

lib = importlib.import_module("Lib.py")
s = lib.s

"""
Use TBA APIv3 to retrieve a list of current FRC teams and their data:
    * Number
    * Name
    * City
    * State/Province
    * Country
Then use Google geocoding API to code the location into two more fields:
    * Latitude
    * Longitude
So we don't have to rely on Tableau's unreliable geocoding data.
Store this data in a csv file TeamInfo.csv
"""

LINK_BASE = "https://www.thebluealliance.com/team/"
FILENAME = 'data/TeamInfo.csv'

# Get list of teams from TBA
print("Getting data")
data = []
n = 0
while True:
    print("Page {0} loaded".format(n))
    r = s.get("{0}/teams/2018/{1}/simple".format(lib.TBA_BASE, n))
    # Stop loading once we get served an empty page
    if len(r.json()) == 0:
        break
    data += r.json()
    n += 1

print("Retrieved {} teams".format(len(data)))

teams = data
problemTeams = []

print("Writing file")
with open(FILENAME, 'w', encoding='utf-8') as f:
    f.write('Team,Nickname,City,State,Country,Latitude,Longitude\n')
    i = 0
    for team in teams[i:]:
        print("{}: {}".format(i, team['key']))
        i += 1
        f.write(team['key'][3:])
        f.write(',')

        try:
            f.write('"' + team['nickname'] + '"')
        except UnicodeEncodeError:
            print("Nickname: " + team['key'] + ": " + LINK_BASE + team['key'][3:])
            problemTeams.append(team['key'])
            f.write('null')
        f.write(',')

        try:
            f.write('"' + team['city'] + '"')
        except UnicodeEncodeError:
            print("City: " + team['key'] + ": " + LINK_BASE + team['key'][3:])
            problemTeams.append(team['key'])
            f.write('null')
        f.write(',')

        f.write('"{}",'.format(team['state_prov']))

        f.write('"{}",'.format(team['country']))

        loc = ",".join([team['city'], team['state_prov'], team['country']])
        geo = geocoder.google(loc, rate_limit=False)
        if (geo.status == "ZERO_RESULTS"):
            print("No geocode for {} @ {}".format(team['key'], loc))
        if (geo.status == "OK"):
            f.write(str(geo.latlng[0]))
            f.write(',')

            f.write(str(geo.latlng[1]))
        else:
            problemTeams.append(team['key'])
            print("Geocode error for {} @ {}".format(team['key'], loc))
            f.write("null")
            f.write(',')

            f.write("null")

        f.write('\n')

print(problemTeams)
