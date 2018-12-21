import importlib

lib = importlib.import_module("Lib")

FILENAME = 'data/2018_MatchData.csv'
YEAR = '2018'

s = lib.s

def write_header(f):
    print("Writing header")
    f.write('Event,Week,City,State,Country,Time,Match,Competition Level,Team,Alliance,Robot Number,')
    fullDataFields = matches[0]['score_breakdown']['blue'].keys() # Get list of field names from a random score breakdown
    dataFields = [] # Create empty list to store the final list of data field names
    # Auto crosses and end games are broken up by robot on each alliance
    # We need to make sure there's only one column because each row is just one team
    # We're looping through the list of fields and appending them onto the new list
    for field in fullDataFields:
        if field == 'autoRobot1':
            # We keep the first column but change the name
            dataFields.append('autoRun')
        elif field == 'endgameRobot1':
            # We keep the first column but change the name slightly
            dataFields.append('endgame')
        elif field[-1] in ['2','3']:
            # We throw out the other two columns
            # If the last character is 2 or 3 we move on to the next iteration of the loop
            continue
        else:
            # For everything else we just append the field name as-is
            dataFields.append(field)
            
    f.write(",".join(dataFields)) # Write the list of keys we just generated to the file, separated by commas
    f.write(',result,winMargin') # Add the last column
    f.write('\n') # Move to the next line

def trim_score_breakdown(robot_number, score_breakdown):
    """ Trim down the score breakdown to include only the scores of the robot_number provided """
    trimmed = {}
    # Iterate over fields in the score breakdown
    for field in score_breakdown:
        if field[-1] in ['1','2','3']:
            fieldbotnumber = int(field[-1]) # Get number for the robot indicated by this data field
            if robot_number == fieldbotnumber:
                # Only write the data if the data field number is the same as the robot number
                val = score_breakdown[field] 
                if "endgame" in field:
                    trimmed['endgame'] = val
                else:
                    trimmed["AutoRun"] = str(val == "AutoRun")
        else:
            # For most fields in score breakdown, write them as-is
            trimmed[field] = score_breakdown[field]

    return trimmed

print("Getting TBA data")
matches, eventDetails = lib.get_data(YEAR)

print("Removing bad matches")
matches = lib.remove_empty_matches(matches)

print("Imported {0} matches".format(len(matches)))

print("Writing file")
f = open(FILENAME, 'w') # Open file

print("Writing header")
write_header(f)

print("Writing data")
for match in matches:
    for alliance in match['alliances']:
        robotnumber = 1 # Track the alliance number of the robot we're logging
        for team in match['alliances'][alliance]['team_keys']:
            f.write(lib.get_event_data(match, eventDetails))

            # Team/alliance stuff
            f.write(team[3:] + ',') # Write team key but cut off "frc"
            f.write(alliance + ',')
            f.write(str(robotnumber) + ',')

            bd = trim_score_breakdown(robotnumber, match['score_breakdown'][alliance])
            f.write(','.join(map(str, bd.values())) + ',')

            # Record win/loss for each team
            f.write(lib.get_result(match, alliance) + ',')

            # Get score margin
            f.write(str(lib.get_win_margin(match, alliance)))

            f.write('\n') # Move to the next line

            robotnumber += 1 # Increment robot number - the teams are in order
                
f.close() # Close the file
print("Closed file")
