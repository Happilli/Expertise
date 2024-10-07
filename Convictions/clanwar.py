import json
import asyncio
import discord

WAR_DATA_JSON = 'clanWar/clanwar.json'

def start_war(team1_name, team2_name, goals):
    war_data = {
        'team1': {
            'name': team1_name,
            'users': [],
            'goals': goals,
            'current_status': 0
        },
        'team2': {
            'name': team2_name,
            'users': [],
            'goals': goals,
            'current_status': 0
        }
    }
    
    with open(WAR_DATA_JSON, 'w') as json_file:
        json.dump(war_data, json_file, indent=4)

def add_user_to_team(user_id, team_name):
    with open(WAR_DATA_JSON, 'r') as json_file:
        war_data = json.load(json_file)

    if team_name not in ['team1', 'team2']:
        return "Invalid team name."

    other_team_name = 'team2' if team_name == 'team1' else 'team1'
    if user_id in war_data[other_team_name]['users']:
        return "User is already in the other team."

    war_data[team_name]['users'].append(user_id)

    with open(WAR_DATA_JSON, 'w') as json_file:
        json.dump(war_data, json_file, indent=4)

    return f"User {user_id} has been added to {war_data[team_name]['name']}."

def get_war_data():
    with open(WAR_DATA_JSON, 'r') as json_file:
        war_data = json.load(json_file)
    
    return war_data

def increment_status(team_name):
    with open(WAR_DATA_JSON, 'r') as json_file:
        war_data = json.load(json_file)

    if team_name not in ['team1', 'team2']:
        return "Invalid team name."

    war_data[team_name]['current_status'] += 1

    with open(WAR_DATA_JSON, 'w') as json_file:
        json.dump(war_data, json_file, indent=4)

    return f"The {war_data[team_name]['name']} team's current status has been incremented to {war_data[team_name]['current_status']}."
def reset_war():
    war_data = {
        'team1': {
            'name': '',
            'users': [],
            'goals': 0,
            'current_status': 0
        },
        'team2': {
            'name': '',
            'users': [],
            'goals': 0,
            'current_status': 0
        }
    }

    with open(WAR_DATA_JSON, 'w') as json_file:
        json.dump(war_data, json_file, indent=4)

    return "The war data has been reset."

def get_team_status(team_name):
    with open(WAR_DATA_JSON, 'r') as json_file:
        war_data = json.load(json_file)

    if team_name not in ['team1', 'team2']:
        return "Invalid team name."

    return war_data[team_name]['current_status']

async def send_war_update(channel, war_data):
    team1 = war_data['team1']
    team2 = war_data['team2']

    message = f"**War Update**\n\n" \
              f"Team {team1['name']}: {team1['current_status']} / {team1['goals']} goals\n" \
              f"Team {team2['name']}: {team2['current_status']} / {team2['goals']} goals"

    await channel.send(message)

async def war_status_listener(channel):
    while True:
        war_data = get_war_data()
        await send_war_update(channel, war_data)
        await asyncio.sleep(60)
