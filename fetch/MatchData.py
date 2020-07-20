
import lib
from datetime import date, datetime
import argparse

parser = argparse.ArgumentParser(description="Get detailed match data.")
parser.add_argument('year', metavar='Y',type=str,
    help="Year to fetch data for")
parser.add_argument('-s','--simple', action='store_true', 
    help="Write only basic match data (omit score breakdowns).")
parser.add_argument('-f','--file',type=str,
    help="A filename to write to")

args = parser.parse_args()
if args.file is None:
    args.file = f"data/{args.year}_MatchData{'_basic' if args.simple else ''}.csv"

YEAR = args.year
simple = args.simple or (int(args.year) <= 2014)
FILENAME = args.file

s, tba,_,_ = lib.init()

# define trim_score_breakdown
if int(YEAR) <= 2014:
    trim_score_breakdown = lib.breakdown_trimmers['2014']
    headers = lib.standard_headers
else:
    trim_score_breakdown = lib.breakdown_trimmers[YEAR]
    headers = lib.standard_headers
    if not simple:
        headers = lib.standard_headers + lib.headers[YEAR]

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

print("Building data")
data = ','.join(headers) + '\n'

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
    context = ','.join(map(str,get_context(match, events[match.event_key])))
    for alliance in match.alliances:
        for robotnumber,team in enumerate(match['alliances'][alliance]['team_keys']):
            # Event & Match context
            data += context + ','

            # Team context
            data += f"{team[3:]},"
            data += f"{alliance},"
            data += f"{1+robotnumber},"

            data += f"{lib.get_result(match,alliance)},"
            data += f"{lib.get_win_margin(match,alliance)},"

            if not simple:
                bd = trim_score_breakdown(1+robotnumber, match.score_breakdown[alliance])
                data += ','.join(map(str, bd.values()))
            
            data += '\n'


with open(FILENAME, 'w', encoding='utf-8') as f:
    f.write(data)

print(f"Wrote data to {FILENAME}")
