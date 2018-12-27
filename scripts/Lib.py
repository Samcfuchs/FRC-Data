from datetime import date, datetime
import requests
import time

TBA_KEY = "***REMOVED***"
TBA_BASE = "https://www.thebluealliance.com/api/v3"

def init():
    # Generate request
    s = requests.Session()
    s.headers.update({'X-TBA-Auth-Key' : TBA_KEY})
    return s

def get_data(year):
    """ Get match and event data for all regular-season events """
    r = s.get(TBA_BASE + '/events/{0}/simple'.format(year))
    events = r.json() # Get json version of match data
    matchlist = []
    eventDetails = {}
    for event in events:
        # Throw out off/preseasons
        if event['event_type'] not in range(0,7):
            continue
        r = s.get(TBA_BASE + '/event/' + event['key'] + '/matches')
        eventdata = r.json()
        matchlist.append(eventdata)
        # Log event details to register
        eventDetails[event['key']] = get_event_details(event['key'])
    
    print("Flattening list")
    matches = flatten_array(matchlist)
    return matches, eventDetails

def get_team_data(year, append='', doprint=True):
    """ Get data for every team that competed in the given year """
    data = []
    page = 0
    while True:
        if doprint:
            print("Page {0} loaded".format(page))
        r = s.get("{0}/teams/{1}/{2}{3}".format(TBA_BASE, year, page, append))

        # Stop loading when we get served an empty page
        if len(r.json()) == 0:
            break
        data += r.json()
        page += 1
    return data

# Generate a dictionary of the details of the event
def get_event_details(key):
    """ Generate a dictionary of relevant event information """
    details = {}
    r = s.get(TBA_BASE + '/event/' + key + '/simple')
    json = r.json()
    details['city'] = "\"" + json['city'] + "\""
    details['state_prov'] = "\"" + json['state_prov'] + "\""
    details['country'] = "\"" + json['country'] + "\""
    details['location'] = "\"" + json['city'] + ', ' + json['state_prov'] + ', ' + json['country'] + "\""
    matchDate = datetime.strptime(json['start_date'], "%Y-%m-%d").date()
    details['week'] = get_week(matchDate)
    return details

zero_days = {
    "2016": date(2016, 2, 23),
    "2017": date(2017, 2, 21),
    '2018': date(2018, 2, 20)
}
def get_week(eventDate):
    """ Get the FRC-conventional week number of the given date """
    zero_day = zero_days[str(eventDate.year)]
    delta = eventDate - zero_day
    return int(delta.days / 7)

def get_event_data(match, event_details):
    """ Return event data as a comma-sep string, as well as the match time and number """
    data = ""
    matchkey = match['key']
    # Event/match stuff
    # Match key example: "2018cmpmi_qm30"
    eventKey = matchkey.split('_')[0] # Get event portion
    # f.write(eventKey[4:] + ',') # cut off the year
    # f.write(str(event_details[eventKey]['week']) + ',') # Week
    data += eventKey[4:] + ','
    data += str(event_details[eventKey]['week']) + ','

    for field in ['city', 'state_prov', 'country']:
        data += event_details[eventKey][field] + ','
    try:
        matchTime = datetime.fromtimestamp(int(match['actual_time'])) 
        data += matchTime.isoformat(sep=' ') + ','
    except TypeError:
        print("{0}: Missing timestamp".format(match['key']))
        data += "null,"
    data += match['key'].split('_')[1] + ','
    data += match['comp_level'] + ','
    return data

def remove_empty_matches(matches, doprint=True):
    """ Return the list of matches but without any that lack a score breakdown """
    good=[]
    for match in matches:
        if match['score_breakdown'] != None:
            good.append(match)
        else:
            if doprint:
                print("  Removed {}".format(match['key']))
    return good

def flatten_array(arr):
    """ Flatten a 2-dimensional array to one dimension """
    return [element for sublist in arr for element in sublist]

def write_event_data(f, match, event_details):
    """ Write event data to the provided file, as well as the match time and number """
    matchkey = match['key']
    # Event/match stuff
    # Match key example: "2018cmpmi_qm30"
    eventKey = matchkey.split('_')[0] # Get event portion
    f.write(eventKey[4:] + ',') # cut off the year
    f.write(str(event_details[eventKey]['week']) + ',') # Week

    for field in ['city', 'state_prov', 'country']:
        f.write(event_details[eventKey][field] + ',')
    try:
        matchTime = datetime.fromtimestamp(int(match['actual_time'])) 
        f.write(matchTime.isoformat(sep=' ') + ',')
    except TypeError:
        print("{0}: Missing timestamp".format(match['key']))
        f.write("null,")
    f.write(match['key'].split('_')[1] + ',') # Match number
    f.write(match['comp_level'] + ',')

def get_result(match, alliance):
    """ Determine whether this alliance won the match """
    if match['winning_alliance'] == alliance:
        return 'W'
    if match['winning_alliance'] == '':
        return 'T'
    return 'L'

def get_win_margin(match, alliance):
    if alliance == 'blue':
        oppAlliance = 'red'
    elif alliance == 'red':
        oppAlliance = 'blue'

    ourScore = match['alliances'][alliance]['score']
    oppScore = match['alliances'][oppAlliance]['score']

    return ourScore - oppScore

def get_full_result(match, alliance):
    """ Returns full results, both result and margin: "W,132" """
    return get_result(match, alliance) + "," + str(get_win_margin(match, alliance))

#### MATCHDATA YEARLY FUNCTIONS ####
standard_headers = ["Event","Week","City","State","Country","Time","Match","Competition Level","Team","Alliance","Robot Number"]
end_headers = ["result", "winMargin"]

breakdown_2016 = ["adjustPoints","autoBoulderPoints","autoBouldersHigh","autoBouldersLow","autoCrossingPoints","autoPoints","autoReachPoints","breachPoints","capturePoints","foulCount","foulPoints","position1crossings","position2","position2crossings","position3","position3crossings","position4","position4crossings","position5","position5crossings","auto","tba_rpEarned","techFoulCount","teleopBoulderPoints","teleopBouldersHigh","teleopBouldersLow","teleopChallengePoints","teleopCrossingPoints","teleopDefensesBreached","teleopPoints","teleopScalePoints","teleopTowerCaptured","totalPoints","towerEndStrength","towerFaceA","towerFaceB","towerFaceC"]
breakdown_2017 = ["adjustPoints","autoFuelHigh","autoFuelLow","autoFuelPoints","autoMobilityPoints","autoPoints","autoRotorPoints","foulCount","foulPoints","kPaBonusPoints","kPaRankingPointAchieved","autoMobility","rotor1Auto","rotor1Engaged","rotor2Auto","rotor2Engaged","rotor3Engaged","rotor4Engaged","rotorBonusPoints","rotorRankingPointAchieved","tba_rpEarned","techFoulCount","teleopFuelHigh","teleopFuelLow","teleopFuelPoints","teleopPoints","teleopRotorPoints","teleopTakeoffPoints","totalPoints","touchpadFar","touchpadMiddle","touchpadNear"]
breakdown_2018 = ["adjustPoints","autoOwnershipPoints","autoPoints","autoQuestRankingPoint","autoRun","autoRunPoints","autoScaleOwnershipSec","autoSwitchAtZero","autoSwitchOwnershipSec","endgamePoints","endgame","faceTheBossRankingPoint","foulCount","foulPoints","rp","tba_gameData","techFoulCount","teleopOwnershipPoints","teleopPoints","teleopScaleBoostSec","teleopScaleForceSec","teleopScaleOwnershipSec","teleopSwitchBoostSec","teleopSwitchForceSec","teleopSwitchOwnershipSec","totalPoints","vaultBoostPlayed","vaultBoostTotal","vaultForcePlayed","vaultForceTotal","vaultLevitatePlayed","vaultLevitateTotal","vaultPoints"]

headers = {
    "2016": standard_headers + breakdown_2016 + end_headers,
    "2017": standard_headers + breakdown_2017 + end_headers,
    "2018": standard_headers + breakdown_2018 + end_headers,
}


def trim_breakdown_2018(robot_number, score_breakdown):
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

def trim_breakdown_2017(robot_number, score_breakdown):
    trimmed = {}
    # Iterate over fields in the score breakdown
    for field in score_breakdown:
        if "robot" in field:
            fieldbotnumber = int(field[5]) # Get number for the robot indicated by this data field
            if robot_number == fieldbotnumber:
                # Only write the data if the data field number is the same as the robot number
                trimmed['auto']  = score_breakdown[field] == "Mobility"
        else:
            # For most fields in score breakdown, write them as-is
            trimmed[field] = score_breakdown[field]
    
    return trimmed

def trim_breakdown_2016(robot_number, score_breakdown):
    trimmed = {}
    # Iterate over fields in the score breakdown
    for field in score_breakdown:
        # Unreachable code
        if "robot" in field:
            fieldbotnumber = int(field[5]) # Get number for the robot indicated by this data field
            if robot_number == fieldbotnumber:
                # Only write the data if the data field number is the same as the robot number
                val = score_breakdown[field]
                trimmed['auto'] = val
        else:
            # For most fields in score breakdown, write them as-is
            trimmed[field] = score_breakdown[field]

    return trimmed

breakdown_trimmers = {
    '2016': trim_breakdown_2016,
    '2017': trim_breakdown_2017,
    '2018': trim_breakdown_2018
}

s = init()
