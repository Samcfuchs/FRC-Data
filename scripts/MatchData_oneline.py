
import lib
from datetime import date, datetime
import argparse

parser = argparse.ArgumentParser(description="Get detailed match data.")
parser.add_argument('year', metavar='Y',type=str,
    help="Year to fetch data for")
parser.add_argument('-f','--file',type=str,
    help="A filename to write to")

args = parser.parse_args()
if args.file is None:
    args.file = f"data/{args.year}_MatchData_ol.csv"

YEAR = args.year
simple = True
FILENAME = args.file

s, tba,_,_ = lib.init()

print("Getting TBA data")
event_types = list(range(0,7))
events = tba.events(int(YEAR), simple=True)
events = [event for event in events if event.event_type in event_types]

# Get matches
matches = [tba.event_matches(event.key, simple=simple) for event in events]
matches = [match for event in matches for match in event]

# Make events indexable
events = {e.key: e for e in events}

# Filter matches without score breakdowns
if not simple:
    matches = [match for match in matches if match.score_breakdown is not None]

print(f"Imported {len(matches)} matches")

headers = ["Key","Year","Event","Week","City","State","Country","Time","Competition Level","Set Number","Match Number","blue1","blue2","blue3","red1","red2","red3","blue score","red score","winner"]
print("Building data")
data = [headers]

def get_context(match, event):
    try:
        matchtime = datetime.fromtimestamp(match.actual_time)
        time_str = matchtime.isoformat(sep=' ')
    except TypeError:
        time_str = "null"

    data = [
        match.key,
        event.key[:4],
        event.event_code,
        lib.get_week(event.start_date),
        event.city,
        event.state_prov,
        event.country,
        time_str,
        match.comp_level,
        match.set_number,
        match.match_number
    ]

    return data


for match in matches:
    row = []
    context = get_context(match, events[match.event_key])

    row += context
    for team in match.alliances['blue']['team_keys']:
        row.append(team[3:])
    for team in match.alliances['red']['team_keys']:
        row.append(team[3:])
    
    row.append(match.alliances['blue']['score'])
    row.append(match.alliances['red']['score'])

    row.append(match.winning_alliance) 

    data.append(row)
        
        

with open(FILENAME, 'w', encoding='utf-8') as f:
    for row in data:
        f.write(','.join(map(str,row)))
        f.write('\n')

print(f"Wrote data to {FILENAME}")
