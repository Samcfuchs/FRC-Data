import sys
import lib

# Get year
try:
    YEAR = sys.argv[1]
except IndexError:
    #YEAR = 2018
    YEAR = input("Year (e.g. 2018): ")

YEAR = str(YEAR)
FILENAME = 'data/{}_MatchData_basic.csv'.format(YEAR)
HEADERS = ["Year","Event","Competition Level","Set","Match","Week","City","State","Country","Time","Team","Alliance","Robot Number","Score","Result","Win Margin"]
FILE_MODE = 'w'

append_mode = True
if append_mode:
    FILENAME = 'data/MatchData_basic.csv'
    FILE_MODE = 'a'

s, tba, _, _ = lib.init()

headers = lib.headers['2014']

print("Getting TBA data")
print("Getting events")
eventlist = tba.events(YEAR, simple=True)

print("Trimming non-official events")
eventlist = [e for e in eventlist if e.event_type in list(range(0,7))]

print("Getting matches")
matchlist = []
for event in eventlist:
    matchlist += tba.event_matches(event['key'], simple=True)

print("Imported {n} matches".format(n=len(matchlist)))

print("Writing file")
f = open(FILENAME, FILE_MODE, encoding='utf-8')

if not append_mode:
    print("Writing header")
    f.write(','.join(HEADERS) + "\n")

print("Writing data")
data = ""
for match in matchlist:
    event = next(e for e in eventlist if e.key == match.event_key)
    for alliance in match['alliances']:
        robotnumber = 1
        for team in match['alliances'][alliance]['team_keys']:
            row = [
                YEAR,
                match.event_key[4:],
                match.comp_level,
                match.set_number,
                match.match_number,
                lib.get_week(event.start_date),
                event.city,
                event.state_prov,
                event.country,
                lib.get_from_timestamp(match.time),
                team[3:],
                alliance,
                robotnumber,
                match.alliances[alliance]['score'],
                lib.get_full_result(match, alliance)
            ]

            data += ','.join(map(str,row))
            data += '\n'

            robotnumber += 1 # Increment robot number to move on to next team in alliance

f.write(data)
f.close()
print("Wrote data to {fname}".format(fname=FILENAME))
