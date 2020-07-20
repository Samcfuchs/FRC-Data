from datetime import date, datetime
import requests
import time
import re
import os
import tbapy
import json

def get_keys():
    """ Retrieve API keys from keys.json in the project root """
    print("Loading API keys")
    
    with open("keys.json", 'r') as f:
        keys = json.load(f)
    
    tba_key = ""
    google_key = ""
    
    try:
        tba_key = keys['TBA_API_KEY']
    except KeyError:
        print("No TBA key found")
    
    try:
        google_key = keys['GOOGLE_API_KEY']
    except KeyError:
        print("No Google key found")
    
    return (tba_key, google_key)


def get_keys_env():
    print("Loading API keys")

    tba_key = ""
    google_key = ""

    try:
        tba_key = os.environ["TBA_API_KEY"]
    except KeyError:
        print("Missing TBA key")

    try:
        google_key = os.environ["GOOGLE_API_KEY"]
    except KeyError:
        print("Missing Google key")

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


def is_team_historic(team):
    """ Determine whether a SimpleTeam object represents a historic team """
    if team['nickname'] == "Team " + str(team['team_number']):
        return True
    if team['city'] == None and team['country'] == None and team['state_prov'] == None:
        return True
    return False


# The zero-day is used to determine the week number of an event
# Typically it's placed 8 days before the first week 1 event day
zero_days = {
    "2001": date(2001, 2, 21),
    "2002": date(2002, 2, 27),
    "2003": date(2003, 2, 26),
    "2004": date(2004, 2, 25),
    "2005": date(2005, 2, 23),
    "2006": date(2006, 2, 22),
    "2007": date(2007, 2, 21),
    "2008": date(2008, 2, 20),
    "2009": date(2009, 2, 18),
    "2010": date(2010, 2, 24),
    "2011": date(2011, 2, 23),
    "2012": date(2012, 2, 21),
    "2013": date(2013, 2, 20),
    "2014": date(2014, 2, 19),
    "2015": date(2015, 2, 17),
    "2016": date(2016, 2, 23),
    "2017": date(2017, 2, 21),
    '2018': date(2018, 2, 20),
    '2019': date(2019, 2, 19),
    '2020': date(2020, 2, 15)
}
def get_week(date):
    """ Get the FRC-conventional week number of the given date """
    if type(date) is str:
        date = datetime.strptime(date, "%Y-%m-%d").date()
    zero_day = zero_days[str(date.year)]
    delta = date - zero_day
    return int(delta.days / 7)


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


#### MATCHDATA YEARLY FUNCTIONS ####
standard_headers = ["Key","Year","Event","Week","City","State","Country","Time","Competition Level","Set Number","Match Number","Team","Alliance","Robot Number","result","winMargin"]

breakdown_2014 = []
breakdown_2015 = ["adjust_points","container_count_level1","container_count_level2","container_count_level3","container_count_level4","container_count_level5","container_count_level6","container_points","container_set","foul_count","foul_points","litter_count_container","litter_count_landfill","litter_count_unprocessed","litter_points","robot_set","teleop_points","total_points","tote_count_far","tote_count_near","tote_points","tote_set","tote_stack"]
breakdown_2016 = ["adjustPoints","autoBoulderPoints","autoBouldersHigh","autoBouldersLow","autoCrossingPoints","autoPoints","autoReachPoints","breachPoints","capturePoints","foulCount","foulPoints","position1crossings","position2","position2crossings","position3","position3crossings","position4","position4crossings","position5","position5crossings","auto","tba_rpEarned","techFoulCount","teleopBoulderPoints","teleopBouldersHigh","teleopBouldersLow","teleopChallengePoints","teleopCrossingPoints","teleopDefensesBreached","teleopPoints","teleopScalePoints","teleopTowerCaptured","totalPoints","towerEndStrength","towerFaceA","towerFaceB","towerFaceC"]
breakdown_2017 = ["adjustPoints","autoFuelHigh","autoFuelLow","autoFuelPoints","autoMobilityPoints","autoPoints","autoRotorPoints","foulCount","foulPoints","kPaBonusPoints","kPaRankingPointAchieved","autoMobility","rotor1Auto","rotor1Engaged","rotor2Auto","rotor2Engaged","rotor3Engaged","rotor4Engaged","rotorBonusPoints","rotorRankingPointAchieved","tba_rpEarned","techFoulCount","teleopFuelHigh","teleopFuelLow","teleopFuelPoints","teleopPoints","teleopRotorPoints","teleopTakeoffPoints","totalPoints","touchpadFar","touchpadMiddle","touchpadNear"]
breakdown_2018 = ["adjustPoints","autoOwnershipPoints","autoPoints","autoQuestRankingPoint","autoRun","autoRunPoints","autoScaleOwnershipSec","autoSwitchAtZero","autoSwitchOwnershipSec","endgamePoints","endgame","faceTheBossRankingPoint","foulCount","foulPoints","rp","tba_gameData","techFoulCount","teleopOwnershipPoints","teleopPoints","teleopScaleBoostSec","teleopScaleForceSec","teleopScaleOwnershipSec","teleopSwitchBoostSec","teleopSwitchForceSec","teleopSwitchOwnershipSec","totalPoints","vaultBoostPlayed","vaultBoostTotal","vaultForcePlayed","vaultForceTotal","vaultLevitatePlayed","vaultLevitateTotal","vaultPoints"]
breakdown_2019 = ['adjustPoints', 'autoPoints', 'bay1', 'bay2', 'bay3', 'bay4', 'bay5', 'bay6', 'bay7', 'bay8', 'cargoPoints', 'completeRocketRankingPoint', 'completedRocketFar', 'completedRocketNear', 'endgame', 'foulCount', 'foulPoints', 'habClimbPoints', 'habDockingRankingPoint', 'habLine', 'hatchPanelPoints', 'lowLeftRocketFar', 'lowLeftRocketNear', 'lowRightRocketFar', 'lowRightRocketNear', 'midLeftRocketFar', 'midLeftRocketNear', 'midRightRocketFar', 'midRightRocketNear', 'preMatchBay1', 'preMatchBay2', 'preMatchBay3', 'preMatchBay6', 'preMatchBay7', 'preMatchBay8', 'preMatchLevel', 'rp', 'sandStormBonusPoints', 'techFoulCount', 'teleopPoints', 'topLeftRocketFar', 'topLeftRocketNear', 'topRightRocketFar', 'topRightRocketNear', 'totalPoints']
breakdown_2020 = ["adjustPoints", "autoCellPoints", "autoCellsBottom", "autoCellsInner", "autoCellsOuter", "autoInitLinePoints", "autoPoints", "controlPanelPoints", "endgamePoints", "endgame", "endgameRungIsLevel", "foulCount", "foulPoints", "initLine", "rp", "shieldEnergizedRankingPoint", "shieldOperationalRankingPoint", "stage1Activated", "stage2Activated", "stage3Activated", "stage3TargetColor", "tba_numRobotsHanging", "tba_shieldEnergizedRankingPointFromFoul", "techFoulCount", "teleopCellPoints", "teleopCellsBottom", "teleopCellsInner", "teleopCellsOuter", "teleopPoints", "totalPoints"]

headers = {
    "2014": breakdown_2014,
    "2015": breakdown_2015,
    "2016": breakdown_2016,
    "2017": breakdown_2017,
    "2018": breakdown_2018,
    "2019": breakdown_2019,
    "2020": breakdown_2020
}

# Identifies fields that contain robot-specific data
robot_pattern = re.compile(r"Robot\d$")

def trim_breakdown_2020(robot_number, score_breakdown):
    """ Trim the score breakdown to include only the scores of the robot_number provided """
    trimmed = {}
    # Iterate over fields in the score breakdown
    for field in score_breakdown:
        if robot_pattern.search(field):
            fieldbotnumber = int(field[-1]) # Get the number for the robot indicated by this data field
            if robot_number == fieldbotnumber:
                val = score_breakdown[field]
                if "endgame" in field:
                    trimmed['endgame'] = val
                elif "initLine" in field:
                    trimmed['autoLine'] = str(val == "Exited")
        elif field == "endgameRungIsLevel":
            trimmed[field] = str(score_breakdown[field]=="IsLevel")
        else:
            trimmed[field] = score_breakdown[field]
    
    return trimmed

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
    '2019': trim_breakdown_2019,
    '2020': trim_breakdown_2020
}
