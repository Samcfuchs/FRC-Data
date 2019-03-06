import sys
import lib

# Get year
try:
    YEAR = sys.argv[1]
except IndexError:
    #YEAR = 2018
    YEAR = input("Year (e.g. 2018): ")

YEAR = str(YEAR)
FILENAME = 'data/MatchData_basic.csv'

s = lib.init()

headers = lib.headers['2014']

print("Getting TBA data")
matches, eventDetails = lib.get_data(YEAR)

print("Imported {n} matches".format(n=len(matches)))

print("Writing file")
f = open(FILENAME, 'a', encoding='utf-8')

print("Writing header")
#f.write('Year,'+','.join(headers) + "\n")

print("Writing data")
for match in matches:
    for alliance in match['alliances']:
        robotnumber = 1
        for team in match['alliances'][alliance]['team_keys']:
            f.write(YEAR + ',')
            f.write(lib.get_event_data(match, eventDetails))

            # Team/alliance stuff
            f.write(team[3:] + ',')
            f.write(alliance + ',')
            f.write(str(robotnumber) + ',')

            # Record results for this team
            f.write(lib.get_full_result(match,alliance))

            f.write("\n")

            robotnumber += 1 # Increment robot number to move on to next team in alliance

f.close()
print("Wrote data to {fname}".format(fname=FILENAME))
