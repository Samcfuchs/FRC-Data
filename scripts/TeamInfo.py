import requests
from datetime import date, datetime
import time
# Make sure you set your API key first
import geocoder
import lib

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

s = lib.init()

# Get list of teams from TBA
print("Getting data")
teams = lib.get_team_data(0, '/simple', True)

print("Retrieved {} teams".format(len(teams)))

problemTeams = []

def get_coords(team_key):
    r = s.get("{base}/team/{key}/simple".format(base=lib.TBA_BASE, key=team_key))
    team = r.json()
    print(team)

    loc = ",".join([team['city'], team['state_prov'], team['country']])
    geo = geocoder.google(loc, rate_limit=False)
    print(geo)
    if (geo.status == "ZERO_RESULTS"):
        print("No geocode for {} @ {}".format(team['key'], loc))
    elif (geo.status == "OVER_QUERY_LIMIT"):
        print("Over query limit on {} @ {}".format(team['key'], loc))
    elif (geo.status == "OK"):
        return geo

print("Writing file")
with open(FILENAME, 'w', encoding='utf-8') as f:
    f.write('Team,Nickname,City,State,Country,Latitude,Longitude\n')
    i = 0
    for team in teams[i:]:
        print("{}: {}".format(i, team['key']))
        i += 1

        if lib.is_team_historic(team):
            f.write("{n},{nick},null,null,null,null,null\n".format(n=team['team_number'], nick=team['nickname']))
            continue

        f.write(str(team['team_number']))
        f.write(',')

        try:
            f.write('"' + team['nickname'] + '"')
        except UnicodeEncodeError:
            print("Nickname: " + team['key'] + ": " + LINK_BASE + team['key'][3:])
            problemTeams.append(team['key'])
            f.write('null')
        f.write(',')

        try:
            f.write('"{}"'.format(team['city']))
        except UnicodeEncodeError:
            print("City: " + team['key'] + ": " + LINK_BASE + team['key'][3:])
            problemTeams.append(team['key'])
            f.write('null')
        f.write(',')

        f.write('"{}",'.format(team['state_prov']))

        f.write('"{}",'.format(team['country']))

        if lib.GOOGLE_KEY != "":
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
                f.write("null,null")

        f.write('\n')

print(problemTeams)
