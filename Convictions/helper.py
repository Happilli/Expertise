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



# Function to send a paginated help message
async def send_help_message(ctx, page=1, commands_per_page=5):
    commands = list(command_descriptions.items())
    start_index = (page - 1) * commands_per_page
    end_index = start_index + commands_per_page
    page_commands = commands[start_index:end_index]

    embed = discord.Embed(title="Available Commands", description="Here are the available commands:", color=0x00ffff)  # Set the color to neon cyan

    for i, (command_name, description) in enumerate(page_commands, start=start_index + 1):
        embed.add_field(name=f"Command {i}", value=f"{command_name}: {description}", inline=False)

    embed.set_footer(text=f"Page {page}/{(len(commands) + commands_per_page - 1) // commands_per_page}")

    if hasattr(ctx, 'help_message'):
        await ctx.help_message.edit(embed=embed)
    else:
        ctx.help_message = await ctx.send(embed=embed)

    # Add reaction controls for pagination
    if page > 1:
        await ctx.help_message.add_reaction('⬅️')  # Previous page
    if end_index < len(commands):
        await ctx.help_message.add_reaction('➡️')  # Next page

    # Define a check function for the reaction filter
    def check(reaction, user):
        return user == ctx.author and reaction.message.id == ctx.help_message.id

    while True:
        try:
            reaction, user = await ctx.bot.wait_for('reaction_add', timeout=60, check=check)
        except asyncio.TimeoutError:
            break  # Stop listening for reactions after 60 seconds

        if str(reaction) == '⬅️' and page > 1:
            page -= 1
        elif str(reaction) == '➡️' and end_index < len(commands):
            page += 1
        else:
            continue

        await ctx.help_message.remove_reaction(reaction, ctx.author)

        # Update the message with the new page
        start_index = (page - 1) * commands_per_page
        end_index = start_index + commands_per_page
        page_commands = commands[start_index:end_index]

        embed.clear_fields()
        for i, (command_name, description) in enumerate(page_commands, start=start_index + 1):
            embed.add_field(name=f"Command {i}", value=f"{command_name}: {description}", inline=False)
        embed.set_footer(text=f"Page {page}/{(len(commands) + commands_per_page - 1) // commands_per_page}")

        await ctx.help_message.edit(embed=embed)
