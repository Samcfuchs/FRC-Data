import sys
import lib

# Get year
try:
    YEAR = sys.argv[1]
except IndexError:
    #YEAR = 2018
    YEAR = input("Year (e.g. 2018): ")

YEAR = str(YEAR)
FILENAME = 'data/{}_MatchData.csv'.format(YEAR)

s = lib.init()

# define trim_score_breakdown
if int(YEAR) <= 2014:
    trim_score_breakdown = lib.breakdown_trimmers['2014']
else:
    trim_score_breakdown = lib.breakdown_trimmers[YEAR]


print("Getting TBA data")
matches, eventDetails = lib.get_data(YEAR)

if int(YEAR) > 2014:
    print("Removing bad matches")
    matches = lib.remove_empty_matches(matches)

print("Imported {n} matches".format(n=len(matches)))

print("Writing file")
f = open(FILENAME, 'w', encoding='utf-8')

print("Writing header")
f.write(','.join(lib.headers[YEAR]) + "\n")

print("Writing data")
for match in matches:
    for alliance in match['alliances']:
        robotnumber = 1
        for team in match['alliances'][alliance]['team_keys']:
            f.write(lib.get_event_data(match, eventDetails))

            # Team/alliance stuff
            f.write(team[3:] + ',')
            f.write(alliance + ',')
            f.write(str(robotnumber) + ',')

            if int(YEAR) > 2014:
                bd = trim_score_breakdown(robotnumber, match['score_breakdown'][alliance])
                f.write(','.join(map(str, bd.values())) + ',')

            # Record results for this team
            f.write(lib.get_full_result(match,alliance))

            f.write("\n")

            robotnumber += 1 # Increment robot number to move on to next team in alliance

f.close()
print("Wrote data to {fname}".format(fname=FILENAME))
