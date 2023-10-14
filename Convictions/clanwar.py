# convictions/clanwar.py

import json
import asyncio
import discord
import json

# Define the path to the JSON file that will store the war data
WAR_DATA_JSON = 'clanWar/clanwar.json'

# Function to start a war with specified goals
def start_war(team1_name, team2_name, goals):
    # Create a dictionary to store war data
    war_data = {
        'team1': {
            'name': team1_name,
            'users': [],
            'goals': goals,
            'current_status': 0  # Initialize current_status to 0 for team1
        },
        'team2': {
            'name': team2_name,
            'users': [],
            'goals': goals,
            'current_status': 0  # Initialize current_status to 0 for team2
        }
    }
    
    # Write the war data to the JSON file
    with open(WAR_DATA_JSON, 'w') as json_file:
        json.dump(war_data, json_file, indent=4)

# Function to add a user to a team
def add_user_to_team(user_id, team_name):
    # Load the current war data from the JSON file
    with open(WAR_DATA_JSON, 'r') as json_file:
        war_data = json.load(json_file)

    # Check if the team_name is valid (team1 or team2)
    if team_name not in ['team1', 'team2']:
        return "Invalid team name."

    # Check if the user is already in the other team
    other_team_name = 'team2' if team_name == 'team1' else 'team1'
    if user_id in war_data[other_team_name]['users']:
        return "User is already in the other team."

    # Add the user to the specified team
    war_data[team_name]['users'].append(user_id)

    # Update the JSON file with the modified data
    with open(WAR_DATA_JSON, 'w') as json_file:
        json.dump(war_data, json_file, indent=4)

    return f"User {user_id} has been added to {war_data[team_name]['name']}."

# Function to get the current war data
def get_war_data():
    # Load the current war data from the JSON file
    with open(WAR_DATA_JSON, 'r') as json_file:
        war_data = json.load(json_file)
    
    return war_data



# Function to increment the current_status of a team
def increment_status(team_name):
    # Load the current war data from the JSON file
    with open(WAR_DATA_JSON, 'r') as json_file:
        war_data = json.load(json_file)

    # Check if the team_name is valid (team1 or team2)
    if team_name not in ['team1', 'team2']:
        return "Invalid team name."

    # Increment the current_status of the specified team
    war_data[team_name]['current_status'] += 1

    # Update the JSON file with the modified data
    with open(WAR_DATA_JSON, 'w') as json_file:
        json.dump(war_data, json_file, indent=4)

    return f"The {war_data[team_name]['name']} team's current status has been incremented to {war_data[team_name]['current_status']}."



