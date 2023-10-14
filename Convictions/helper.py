import discord

# Define a dictionary of command descriptions
command_descriptions = {
    'register': 'Allows users to register their accounts.',
    'startrankflow': 'Initializes the rank flow for a user.',
    'status': 'Displays the rank status (wins and losses) for a user.',
    'leaderboard [top]': 'Displays the leaderboard of top-ranked users (default is 10).',
    'log [opponent] [wins]': 'Logs a battle outcome with an opponent.',
    'useravatar [user]': 'Shows the avatar of a specified user.',
    'balance': 'Shows the balance of redants (currency) for the user.',
    'setbalance [amount] [target_user]': 'Sets the balance for a target user (requires authority).',
    'startcashflow': 'Initializes a redants account for a user.',
    'generateprofile': 'Generates a profile for the user.',
    'viewprofile': 'Views the user\'s profile.',
    'deleteprofile': 'Deletes the user\'s profile.',
    'render': 'Updates and renders the user\'s profile.',
    'bgshop': 'Displays the available background images in the shop.',
    'viewbg [background_id]': 'Views a specific background image.',
    'buybg [background_id]': 'Allows users to purchase background images.',
    'titleshop': 'Displays the available titles in the shop.',
    'buytitle [selected_title]': 'Allows users to purchase titles.',
    'restrict [user]': 'Restricts a user from using the bot (requires authority).',
    'unrestrict [user]': 'Unrestricts a user from using the bot (requires authority).',
    'viewrank': 'Views the user\'s rank.',
    'rankupdate': 'Updates user ranks based on wins.',
    'rankreset [target_user]': 'Resets wins and losses to 0 for a target user (requires authority).',
}



# Function to send a help message with command descriptions in an embedded format
async def send_help_message(ctx):
    embed = discord.Embed(title="Available Commands", description="Here are the available commands:")
    
    for command_name, description in command_descriptions.items():
        embed.add_field(name=f"-->{command_name}", value=description, inline=False)
    
    await ctx.send(embed=embed)
