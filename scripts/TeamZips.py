import lib
s, tba, has_tba, has_google = lib.init()

FILENAME = "data/TeamZips.csv"


print("Getting data")
teams = tba.teams(simple=False)

print(f"Retrieved {len(teams)} teams")

print("Writing file")

with open(FILENAME, 'w', encoding='utf-8') as f:
    f.write("Team,Nickname,City,State,Country,Zip\n")

    for team in teams:
        if lib.is_team_historic(team):
            f.write(f"{team.team_number},{team.nickname},null,null,null,null\n")
            continue

        row = [team.team_number, team.nickname, team.city, team.state_prov, team.country, team.postal_code]
        row = [f'"{item}"' for item in row]
        try:
            f.write(','.join(row) + '\n')
        except UnicodeEncodeError:
            print(row)

print("done")
    