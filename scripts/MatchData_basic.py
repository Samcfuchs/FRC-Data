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
            data += YEAR + ','
            data += match.event_key[4:] + ','
            data += match.comp_level + ','
            data += str(match.set_number) + ','
            data += str(match.match_number) + ','
            data += str(lib.get_week(event.start_date)) + ','
            data += str(event.city) + ','
            data += str(event.state_prov) + ','
            data += str(event.country) + ','
            data += lib.get_from_timestamp(match.time) + ','
            data += team[3:] + ','
            data += alliance + ','
            data += str(robotnumber) + ','
            data += str(match.alliances[alliance]['score']) + ','
            data += lib.get_full_result(match, alliance)
            data += '\n'

            robotnumber += 1 # Increment robot number to move on to next team in alliance

f.write(data)
f.close()
print("Wrote data to {fname}".format(fname=FILENAME))
