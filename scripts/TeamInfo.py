import requests
from datetime import date, datetime
import time
# Make sure you set your API key first
import lib
s, tba, has_tba, has_google = lib.init()
import geocoder

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
teams = tba.teams(simple=True)

print(f"Retrieved {len(teams)} teams")

problemTeams = []

def get_coords(team):
    loc = f"{team.city},{team.state_prov},{team.country}"
    geo = geocoder.google(loc, rate_limit=False)
    if (geo.status == "ZERO_RESULTS"):
        print("No geocode for {team.key} @ {loc}")
        return "null,null", True
    elif (geo.status == "OVER_QUERY_LIMIT"):
        print("Over query limit on {team.key} @ {loc}")
        return "null,null", True
    elif geo.status == "REQUEST_DENIED":
        print("Google key not loaded")
        return "null,null", True
    elif (geo.status == "OK"):
        return ','.join(map(str,geo.latlng)), False

print("Writing file")
with open(FILENAME, 'w', encoding='utf-8') as f:
    f.write('Team,Nickname,City,State,Country,Latitude,Longitude\n')
    i = 0
    for team in teams[i:]:
        print(f"{i}: {team.key}")
        i += 1

        if lib.is_team_historic(team):
            f.write(f"{team.team_number},{team.nickname},null,null,null,null,null\n")
            continue

        f.write(f'{team.team_number},')

        try:
            f.write(f'"{team.nickname}",')
        except UnicodeEncodeError:
            print(f"Nickname: {team['key']}: {LINK_BASE}{team.key[3:]}")
            problemTeams.append(team.team_number)
            f.write('null,')

        try:
            f.write(f'"{team.city}",')
        except UnicodeEncodeError:
            print(f"City: {team.key}: {LINK_BASE}{team.key[3:]}")
            problemTeams.append(team.team_number)
            f.write('null,')

        f.write(f'"{team.state_prov}",')

        f.write(f'"{team.country}",')

        if has_google:
            s,r = get_coords(team)
            f.write(s)
            if r:
                problemTeams.append(team.team_number)
        else:
            f.write("null,null")

        f.write('\n')

print(problemTeams)
