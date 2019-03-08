from datetime import date, datetime
import requests
import time
import re
import os
import tbapy

def get_keys():
    print("Loading API keys")
    tba_regex =       r"^TBA_AUTH_KEY:\s*\"(\S*)\"$"
    google_regex = r"^GOOGLE_AUTH_KEY:\s*\"(\S*)\"$"

    # Get text from file
    with open("keys.txt", 'r') as f:
        text = f.read()
    
    tba_match = re.search(tba_regex, text, re.MULTILINE)
    google_match = re.search(google_regex, text, re.MULTILINE)

    if tba_match:
        tba_key = tba_match.group(1)
    else:
        print("No TBA key found")
    
    if google_match:
        google_key = google_match.group(1)
    else:
        print("No Google key found")
    
    return (tba_key, google_key)


s = None
TBA_BASE = "https://www.thebluealliance.com/api/v3"

def init():
    # Get keys
    TBA_KEY, GOOGLE_KEY = get_keys()

    # Store google key
    os.environ["GOOGLE_API_KEY"] = GOOGLE_KEY

    tba = tbapy.TBA(TBA_KEY)

    # Generate request
    session = requests.Session()
    session.headers.update({'X-TBA-Auth-Key' : TBA_KEY})
    global s
    s = session

    has_tba = TBA_KEY != ""
    has_google = GOOGLE_KEY != ""

    return session, tba, has_tba, has_google

def get_data(year, preseason=False):
    """ Get match and event data for all regular-season events """
    event_types = list(range(0,7))
    if preseason:
        event_types += [100]
    r = s.get(TBA_BASE + '/events/{0}/simple'.format(year))
    events = r.json() # Get json version of match data
    matchlist = []
    eventDetails = {}
    for event in events:
        # Throw out off/preseasons
        if event['event_type'] not in event_types:
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
        if year == 0:
            r = s.get("{0}/teams/{p}{app}".format(TBA_BASE, p=page, app=append))
        else:
            r = s.get("{0}/teams/{yr}/{p}{app}".format(TBA_BASE, yr=year, p=page, app=append))

        # Stop loading when we get served an empty page
        if len(r.json()) == 0:
            break
        data += r.json()
        page += 1
    return data


def is_team_historic(team):
    """ Determine whether a SimpleTeam object represents a historic team """
    if team['nickname'] == "Team " + str(team['team_number']):
        return True
    if team['city'] == None and team['country'] == None and team['state_prov'] == None:
        return True
    return False

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

# The zero-day is used to determine the week number of an event
# Typically it's placed 8 days before the first week 1 event day
zero_days = {
    "2010": date(2010, 2, 24),
    "2011": date(2011, 2, 23),
    "2012": date(2012, 2, 21),
    "2013": date(2013, 2, 20),
    "2014": date(2014, 2, 19),
    "2015": date(2015, 2, 17),
    "2016": date(2016, 2, 23),
    "2017": date(2017, 2, 21),
    '2018': date(2018, 2, 20),
    '2019': date(2019, 2, 19)
}
def get_week(date):
    """ Get the FRC-conventional week number of the given date """
    if type(date) is str:
        date = datetime.strptime(date, "%Y-%m-%d").date()
    zero_day = zero_days[str(date.year)]
    delta = date - zero_day
    return int(delta.days / 7)

def get_from_timestamp(t: int):
    try:
        time = datetime.fromtimestamp(t)
        return time.isoformat(sep=' ')
    except TypeError:
        return "null"

def get_event_data(match, event_details):
    """ Return event data as a comma-sep string, as well as the match time and number """
    data = ""
    matchkey = match['key']
    # Event/match stuff
    # Match key example: "2018cmpmi_qm30"
    eventKey = matchkey.split('_')[0] # Get event portion
    data += eventKey[4:] + ','
    data += str(event_details[eventKey]['week']) + ','

    for field in ['city', 'state_prov', 'country']:
        data += event_details[eventKey][field] + ','
    try:
        matchTime = datetime.fromtimestamp(int(match['actual_time'])) 
        data += matchTime.isoformat(sep=' ') + ','
    except TypeError:
        #print("{0}: Missing timestamp".format(match['key']))
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
        #print("{0}: Missing timestamp".format(match['key']))
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

breakdown_2014 = []
breakdown_2015 = ["adjust_points","container_count_level1","container_count_level2","container_count_level3","container_count_level4","container_count_level5","container_count_level6","container_points","container_set","foul_count","foul_points","litter_count_container","litter_count_landfill","litter_count_unprocessed","litter_points","robot_set","teleop_points","total_points","tote_count_far","tote_count_near","tote_points","tote_set","tote_stack"]
breakdown_2016 = ["adjustPoints","autoBoulderPoints","autoBouldersHigh","autoBouldersLow","autoCrossingPoints","autoPoints","autoReachPoints","breachPoints","capturePoints","foulCount","foulPoints","position1crossings","position2","position2crossings","position3","position3crossings","position4","position4crossings","position5","position5crossings","auto","tba_rpEarned","techFoulCount","teleopBoulderPoints","teleopBouldersHigh","teleopBouldersLow","teleopChallengePoints","teleopCrossingPoints","teleopDefensesBreached","teleopPoints","teleopScalePoints","teleopTowerCaptured","totalPoints","towerEndStrength","towerFaceA","towerFaceB","towerFaceC"]
breakdown_2017 = ["adjustPoints","autoFuelHigh","autoFuelLow","autoFuelPoints","autoMobilityPoints","autoPoints","autoRotorPoints","foulCount","foulPoints","kPaBonusPoints","kPaRankingPointAchieved","autoMobility","rotor1Auto","rotor1Engaged","rotor2Auto","rotor2Engaged","rotor3Engaged","rotor4Engaged","rotorBonusPoints","rotorRankingPointAchieved","tba_rpEarned","techFoulCount","teleopFuelHigh","teleopFuelLow","teleopFuelPoints","teleopPoints","teleopRotorPoints","teleopTakeoffPoints","totalPoints","touchpadFar","touchpadMiddle","touchpadNear"]
breakdown_2018 = ["adjustPoints","autoOwnershipPoints","autoPoints","autoQuestRankingPoint","autoRun","autoRunPoints","autoScaleOwnershipSec","autoSwitchAtZero","autoSwitchOwnershipSec","endgamePoints","endgame","faceTheBossRankingPoint","foulCount","foulPoints","rp","tba_gameData","techFoulCount","teleopOwnershipPoints","teleopPoints","teleopScaleBoostSec","teleopScaleForceSec","teleopScaleOwnershipSec","teleopSwitchBoostSec","teleopSwitchForceSec","teleopSwitchOwnershipSec","totalPoints","vaultBoostPlayed","vaultBoostTotal","vaultForcePlayed","vaultForceTotal","vaultLevitatePlayed","vaultLevitateTotal","vaultPoints"]
breakdown_2019 = ['adjustPoints', 'autoPoints', 'bay1', 'bay2', 'bay3', 'bay4', 'bay5', 'bay6', 'bay7', 'bay8', 'cargoPoints', 'completeRocketRankingPoint', 'completedRocketFar', 'completedRocketNear', 'endgame', 'foulCount', 'foulPoints', 'habClimbPoints', 'habDockingRankingPoint', 'habLine', 'hatchPanelPoints', 'lowLeftRocketFar', 'lowLeftRocketNear', 'lowRightRocketFar', 'lowRightRocketNear', 'midLeftRocketFar', 'midLeftRocketNear', 'midRightRocketFar', 'midRightRocketNear', 'preMatchBay1', 'preMatchBay2', 'preMatchBay3', 'preMatchBay6', 'preMatchBay7', 'preMatchBay8', 'preMatchLevel', 'rp', 'sandStormBonusPoints', 'techFoulCount', 'teleopPoints', 'topLeftRocketFar', 'topLeftRocketNear', 'topRightRocketFar', 'topRightRocketNear', 'totalPoints']

headers = {
    "2014": standard_headers + breakdown_2014 + end_headers,
    "2015": standard_headers + breakdown_2015 + end_headers,
    "2016": standard_headers + breakdown_2016 + end_headers,
    "2017": standard_headers + breakdown_2017 + end_headers,
    "2018": standard_headers + breakdown_2018 + end_headers,
    "2019": standard_headers + breakdown_2019 + end_headers,
}

def calculate_score_2019(result):
    result = result.lower()
    score = 0
    if result == "unknown":
        return "NA"
    if "panel" in result:
        score += 2
    if "cargo" in result:
        score += 3
    return score


pattern = re.compile(r"tRocket|[bB]ay\d")
def is_a_bay_field(fieldname):
    return pattern.search(fieldname)


def process_endgame_2019(val):
    if val == "None":
        return 0
    elif val == "Unknown":
        return "NA"
    else:
        return int(val[-1])


def process_prematch_2019(val):
    if val == "None":
        return 0
    elif val == "Unknown":
        return "NA"
    else:
        return int(val[-1])
    

def trim_breakdown_2019(robot_number, score_breakdown):
    """ Trim the score breakdown to include only the scores of the robot_number provided """
    trimmed = {}
    # Iterate over fields in the score breakdown
    for field in score_breakdown:
        if "Robot" in field:
            fieldbotnumber = int(field[-1]) # Get the number for the robot indicated by this data field
            if robot_number == fieldbotnumber:
                val = score_breakdown[field]
                if "endgame" in field:
                    trimmed['endgame'] = process_endgame_2019(val)
                elif "habLine" in field:
                    trimmed['autoLine'] = str(val == "CrossedHabLineInSandstorm")
                elif "preMatchLevel" in field:
                    trimmed["preMatchLevel"] = process_prematch_2019(val)
        elif is_a_bay_field(field):
            trimmed[field] = calculate_score_2019(score_breakdown[field])
        else:
            trimmed[field] = score_breakdown[field]
    
    return trimmed



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

def trim_breakdown_2015(robot_number, score_breakdown):
    trimmed = {}
    # Iterate over fields in the score breakdown
    for field in score_breakdown:
        # For most fields in score breakdown, write them as-is
        trimmed[field] = score_breakdown[field]

    return trimmed

def trim_breakdown_2014(robot_number, score_breakdown):
    return {}

breakdown_trimmers = {
    '2014': trim_breakdown_2014,
    '2015': trim_breakdown_2015,
    '2016': trim_breakdown_2016,
    '2017': trim_breakdown_2017,
    '2018': trim_breakdown_2018,
    '2019': trim_breakdown_2019
}
