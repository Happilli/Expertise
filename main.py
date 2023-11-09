import os
import discord
from discord.ext import commands, tasks, menus
import logging
import json
import asyncio
import re
from PIL import Image, ImageDraw, ImageFont, ImageOps
from Convictions import registration, avatar, currency, profile, helper
from Convictions.rank import RankFlow
from Convictions.bgshop import show_background_shop, background_descriptions, background_prices
from Convictions import clanwar
import replit 
import requests
from webserver import keep_alive
from discord.ext.commands import check
import imageio
from discord.ui import View
import io

# Define the path to the folder containing your background images
BACKGROUND_FOLDER = './Assets/Backgrounds/'

# Define the channel where the bot will send welcome and farewell messages
welcome_channel_id = 1144137252977524736  # Replace with your welcome channel ID
farewell_channel_id = 1144162687337631764  # Replace with your farewell channel ID

# Constants
TOKEN = os.environ.get('RUNNER')
PREFIX = 'e!'
PROFILES_FOLDER = 'Profiles'

# Define your custom prefixes
custom_prefixes = ["e.", "E.", "E!", "e!"]

# Function to check the custom prefix
def custom_prefix(bot, message):
    content = message.content.strip()  # Remove leading and trailing spaces
    for prefix in custom_prefixes:
        if content.startswith(prefix):
            return prefix
    return commands.when_mentioned_or(*custom_prefixes)(bot, message)

# Intents
intents = discord.Intents.default()
intents.typing = False
intents.presences = False
intents.message_content = True
user_profiles = {}

# Create a bot instance with custom prefix, intents, and case-insensitivity
bot = commands.Bot(command_prefix=custom_prefix, intents=intents, case_insensitive=True, help_command=None)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('discord')
logger.setLevel(logging.INFO)

# Define a simple "hello" command
@bot.command()
async def hello(ctx):
    await ctx.send("Hello, I am your flexible bot!")


# Load registered user IDs from the accounts.txt file
registered_users = set()
with open('Assets/accounts.txt', 'r') as file:
    registered_users = {int(line.strip()) for line in file if line.strip()}

# Create a currency manager instance
currency_manager = currency.CurrencyManager("Currency")

# Define the path to the user profiles JSON file
USER_PROFILES_JSON_PATH = os.path.join(PROFILES_FOLDER, 'user_profiles.json')

# Function to save user profiles to the JSON file
def save_user_profiles():
    with open(USER_PROFILES_JSON_PATH, 'w') as json_file:
        json.dump(user_profiles, json_file, indent=4)

# Load user profiles
def load_user_profiles():
    try:
        with open(os.path.join(PROFILES_FOLDER, 'user_profiles.json'), 'r') as json_file:
            return json.load(json_file)
    except FileNotFoundError:
        return {}

# Initialize the RankFlow class here
global rank_flow
rank_flow = RankFlow(bot)  # Pass the bot instance as an argument

# Define the on_ready event handler
@bot.event
async def on_ready():
    logger.info(f'Logged in as {bot.user.name}')
    global user_profiles
    user_profiles = load_user_profiles()
    logger.info('User profiles loaded.')

@bot.command()
async def help(ctx, page: int = 1):
  await helper.send_help_message(ctx, page)

@bot.event
async def on_message(message):
    if message.author == bot.user:
        return  # Ignore messages sent by the bot itself

    victory_keywords = ["won the battle!", "has fled the battle!"]

    for keyword in victory_keywords:
        if keyword in message.content:
            mentions = message.mentions
            if mentions:
                winner = mentions[0]
                duel_type = "battle" if "won" in keyword else "duel"
                duel_link = message.jump_url
                if duel_type == "duel":
                    outcome = f"Emerging from the nowhere notorious, {winner.mention} stands short!"
                else:
                    outcome = f"Emerging from the {duel_type} victorious, {winner.mention} stands tall!"

                logging_channel_id = 1144143641678458981  # Replace with the actual logging channel ID
                logging_channel = bot.get_channel(logging_channel_id)

                if logging_channel:
                    embed = discord.Embed(title="Duel Outcome",
                                          description=outcome,
                                          color=discord.Color.green())
                    embed.add_field(
                        name="Jump to Message",
                        value="**[Click here to go to the message]({})**".format(
                            duel_link),
                        inline=False)
                    await logging_channel.send(embed=embed)
            break

    await bot.process_commands(message)

# Command: Register
@bot.command()
async def register(ctx):
    await registration.register_user(ctx, registered_users)

# Update the is_registered check to send a registration message
def is_registered():
    async def predicate(ctx):
        user_id = ctx.author.id
        if user_id in registered_users:
            return True
        else:
            await send_registration_message(ctx)
            raise NotRegisteredError()
    return commands.check(predicate)

# Define a function to send the registration message
async def send_registration_message(ctx):
    await ctx.send("You need to register first. Use `!register` to register your account.")

# Custom exception for not registered users
class NotRegisteredError(commands.CheckFailure):
    pass

@bot.command()
@is_registered()
async def startrankflow(ctx):
    user_id = str(ctx.author.id)

    # Check if the user's rank already exists
    if user_id in rank_flow.data:
        await ctx.send("Your rank already exists. You can't start the rank flow again.")
        return

    # Initialize the user's wins and losses to 0 using rank_flow
    rank_flow.start_rank_flow(user_id)

    await ctx.send("Rank flow initialized for your account. Wins and losses set to 0.")

@bot.command(name="stats")
@is_registered()
async def status(ctx):
    # Check if rank_flow is initialized
    if 'rank_flow' in globals():
        # Check the rank_flow data for the user
        user_id = str(ctx.author.id)
        if user_id in rank_flow.data:
            user_stats = rank_flow.data[user_id]
            wins = user_stats.get("wins", 0)
            losses = user_stats.get("losses", 0)

            # Get the user object (User, not Member)
            user = ctx.author
            avatar_url = user.avatar.url if user.avatar else user.default_avatar.url

            # Create an embedded message
            embed = discord.Embed(
                title=f'{ctx.author.name}\'s Rank Status',
                description=f'Wins: {wins}\nLosses: {losses}',
                color=discord.Color.green()  # Customize the color
            )
            embed.set_thumbnail(
                url=avatar_url)  # Set the user's avatar as the thumbnail
            await ctx.send(embed=embed)
        else:
            await ctx.send("You have not initialized your rank data yet. Use `!startrankflow` to begin.")
    else:
        await ctx.send("The rank system is not initialized. Use `!startrankflow` to initialize it.")




class MyView(discord.ui.View):
    @discord.ui.button(label="Top Player", style=discord.ButtonStyle.primary, emoji="😎")
    async def button_callback(self, interaction, button):
        # await interaction.message.edit(content="You clicked the button!")

        # Assuming "show_top" is a function that shows the top player.
        top_player_embed = await show_top(interaction.channel)

        if top_player_embed:
            # Delete the leaderboard message
            await interaction.message.delete()

            # Send the top player embed
            await interaction.channel.send(embed=top_player_embed)

# @bot.command()
# async def button(ctx):
#     await ctx.send("This is a button!", view=MyView())

@bot.command(name="lb")
@is_registered()
async def leaderboard(ctx, top: int = 10):
    if top <= 0:
        await ctx.send("Please provide a positive number for the leaderboard size.")
        return

    loading_msg = await ctx.send("Generating the leaderboard...")

    try:
        leaderboard_image = await rank_flow.get_leaderboard(top)

        # Delete the loading message
        await loading_msg.delete()

        leaderboard_msg = await ctx.send(file=discord.File(leaderboard_image, "leaderboard.png"))

        # Set up the view with the leaderboard message ID
        view = MyView()
        view.message_id = leaderboard_msg.id

        # Send the leaderboard message with the view
        await ctx.send(view=view)
    except Exception as e:
        await loading_msg.edit(content=f"An error occurred while generating the leaderboard: {e}")


async def show_top(ctx):
    # This command should be used to show the top player (you need to implement this)
    top_player = await rank_flow.get_top_player()
    if top_player:
        embed = discord.Embed(title="Top Player", description=top_player, color=discord.Color.blue())
        return embed  # Return the embed to be sent in the button_callback

    return None  # Return None if there's no top player to show

# You can remove or comment out the previous top command if you're using this approach.



@bot.command()
@is_registered()
async def log(ctx, opponent: discord.User, wins: int = 1):
  if wins != 1:
    await ctx.send("You can only log 1 point at a time!")
    return

  result_message = await rank_flow.battle_log(ctx, opponent, wins=1)
  await ctx.send(result_message)


# Command: User Avatar
@bot.command()
@is_registered()
async def useravatar(ctx, user: discord.User = None):
  await avatar.show_avatar(ctx, user)


@bot.command()
@is_registered()
async def trade(ctx, user2: discord.User, amount: int):
  # Check if user1 exists in the currency data (the user invoking the command)
  user1 = ctx.author
  user1_id_str = str(user1.id)

  # Load the currency data from the JSON file
  with open('Currency/currency.json', 'r') as currency_file:
    currency_data = json.load(currency_file)

  if user1_id_str not in currency_data:
    await ctx.send(
        f"{user1.mention}, you don't have an account yet. Use `!startcashflow` to create one."
    )
    return

  # Check if user2 exists in the currency data
  user2_id_str = str(user2.id)
  if user2_id_str not in currency_data:
    await ctx.send(
        f"{user2.mention} doesn't have an account yet. They need to use `!startcashflow` to create one."
    )
    return

  # Check if the users are different
  if user1.id == user2.id:
    await ctx.send("Cannot trade with yourself.")
    return

  # Send a trade confirmation message
  trade_message = await ctx.send(
      f"{user1.mention} wants to trade {amount} with {user2.mention}. React with ✅ to accept or ❌ to decline."
  )

  # Add reactions
  await trade_message.add_reaction('✅')  # Checkmark
  await trade_message.add_reaction('❌')  # Cross

  def check(reaction, user):
    return user == user2 and str(reaction.emoji) in ['✅', '❌']

  try:
    reaction, _ = await bot.wait_for('reaction_add', timeout=8.0, check=check)

    if str(reaction.emoji) == '✅':
      # Check if user1 has enough balance
      if currency_data[user1_id_str] >= amount:
        # Deduct the amount from user1 and add it to user2
        currency_data[user1_id_str] -= amount
        currency_data[user2_id_str] += amount

        # Update the JSON file with the new balances with proper formatting
        with open('Currency/currency.json', 'w') as currency_file:
          json.dump(currency_data, currency_file,
                    indent=4)  # Indent for better readability

        await ctx.send(
            f"Trade successful! {user1.mention} gave {amount} to {user2.mention}"
        )
      else:
        await ctx.send(
            f"Trade failed! {user1.mention} does not have enough balance.")
    else:
      await ctx.send(f"{user2.mention} declined the trade.")
  except asyncio.TimeoutError:
    await ctx.send("Trade request timed out.")


@bot.command(name="bal")
@is_registered()
async def balance(ctx):
  user_id = str(ctx.author.id)

  # Load the currency data from the JSON file
  with open('Currency/currency.json', 'r') as currency_file:
    currency_data = json.load(currency_file)

  if user_id in currency_data:
    balance = currency_data[user_id]

    # Format the balance with commas
    formatted_balance = "{:,}".format(balance)

    # Get the user's avatar URL
    user_avatar_url = ctx.author.avatar.url if ctx.author.avatar else ctx.author.default_avatar.url

    embed = discord.Embed(
        title=f"{ctx.author.name}'s balance",
        color=discord.Color.purple()  # Customize the color
    )
    embed.add_field(name="REDANTS", value=f"{formatted_balance}", inline=False)
    embed.set_thumbnail(
        url=user_avatar_url)  # Set the user's avatar as the thumbnail

    await ctx.send(embed=embed)
  else:
    embed = discord.Embed(
        title="No Redants Account",
        description=
        "You don't have a Redants account. Please use `!startcashflow` to create one.",
        color=discord.Color.red())
    await ctx.send(embed=embed)


# Add this constant to store the ID of the specific user with authority
SPECIFIC_USER_ID = 1128651413535346708  # Replace with the actual user ID


# Modify the set_balance command
@bot.command(name="sb")
@is_registered()
async def setbalance(ctx, amount: int, target_user: discord.User = None):
  user_id = ctx.author.id

  # Check if the user invoking the command is the specific user with authority
  if user_id == SPECIFIC_USER_ID:
    if target_user is None:
      await ctx.send("Please specify a target user to set the balance.")
    else:
      target_user_id = str(target_user.id)
      currency_manager.set_balance(target_user_id, amount)
      await ctx.send(
          f'The balance for {target_user.mention} has been set to {amount} redants.'
      )
  else:
    await ctx.send(
        "You do not have the authority to set balances for other users.")


# Assuming 'currency' is a folder containing 'currency.json'
currency_file_path = os.path.join('Currency', 'currency.json')


@bot.command()
@is_registered()
async def startcashflow(ctx):
  user_id = ctx.author.id

  # Check if the user already has an account in the currency.json file
  if os.path.exists(currency_file_path):
    with open(currency_file_path, 'r') as file:
      currency_data = json.load(file)
      if str(user_id) in currency_data:
        await ctx.send('You already have a redants account.')
      else:
        currency_data[str(user_id)] = 0
        with open(currency_file_path, 'w') as file:
          json.dump(currency_data, file, indent=4)
        await ctx.send(
            'Welcome! Your redants account has been created with a balance of 0 redants.'
        )
  else:
    # If the file doesn't exist, create it and add the user's account
    currency_data = {str(user_id): 0}
    with open(currency_file_path, 'w') as file:
      json.dump(currency_data, file, indent=4)
    await ctx.send(
        'Welcome! Your redants account has been created with a balance of 0 redants.'
    )


# Command: Generate Profile
@bot.command()
@is_registered()
async def generateprofile(ctx):
  await profile.generate_profile(ctx, user_profiles)


# Text-based loading animation
loading_animation = [
    "Fetching profile, please wait...", "Fetching profile, please wait.",
    "Fetching profile, please wait..", "Fetching profile, please wait..."
]

@bot.command(name="profile")
@is_registered()
async def viewprofile(ctx, user_mention: discord.Member = None):
    loading_msg = await ctx.send(loading_animation[0])

    try:
        # Check if a user mention is provided, and if not, use the user who issued the command
        target_user = user_mention if user_mention else ctx.author

        # Convert the user_mention to lowercase for non-case sensitive comparison
        target_user_mention_lower = target_user.mention.lower()

        # Fetch and display the user's profile
        await profile.view_profile(ctx, user_profiles, target_user_mention_lower)

        await loading_msg.edit(content="Completed")
        await asyncio.sleep(2)
        await loading_msg.delete()

    except Exception as e:
        await ctx.send(f"An error occurred: {str(e)}")


@bot.command()
@is_registered()
async def deleteprofile(ctx):
    # Ask for confirmation
    confirmation_message = await ctx.send("Are you sure you want to delete your profile? React with ✅ to confirm or ❌ to cancel.")

    # Add reaction emojis to the message
    await confirmation_message.add_reaction("✅")  # Check mark
    await confirmation_message.add_reaction("❌")  # Cross mark

    def check(reaction, user):
        return user == ctx.author and str(reaction.emoji) in ["✅", "❌"]

    try:
        reaction, _ = await bot.wait_for('reaction_add', check=check, timeout=30)
    except asyncio.TimeoutError:
        await ctx.send("You didn't confirm in time. Deletion canceled.")
        return

    if str(reaction.emoji) == "✅":
        # Perform the profile deletion here
        await profile.delete_profile(ctx, user_profiles)
    else:
        await ctx.send("Deletion canceled.")

    # Delete the confirmation message
    await confirmation_message.delete()



@bot.command()
@is_registered()
async def render(ctx):
    user_id = str(ctx.author.id)

    if user_id in user_profiles:
        loading_msg = await ctx.send("Rendering profile... [.]")

        profile_data = user_profiles[user_id]

        new_title = profile_data.get('title', 'Title Placeholder')
        new_background_url = profile_data.get('background_url', 'Assets/Backgrounds/7.png')
        new_rank = profile_data.get('rank', 'Noob')
        new_card_url = profile_data.get('card_url', None)

        profile_data['title'] = new_title
        profile_data['background_url'] = new_background_url
        profile_data['rank'] = new_rank
        profile_data['card_url'] = new_card_url

        json_path = os.path.join(PROFILES_FOLDER, 'user_profiles.json')
        with open(json_path, 'w') as json_file:
            json.dump(user_profiles, json_file, indent=4)

        avatar_url = ctx.author.avatar.url if ctx.author.avatar else ctx.author.default_avatar.url
        username = ctx.author.name

        profile_image = profile.create_profile_image(avatar_url, username, new_title, new_rank, new_background_url, new_card_url)

        image_path = profile_data['image_path']
        profile_image.save(image_path)

        await loading_msg.edit(content="Rendering profile... [✓]")
        await loading_msg.delete()

        profile_embed = discord.Embed(
            title="Your Profile",
            description="Here is your updated profile:",
            color=discord.Color.green()
        )
        profile_embed.set_thumbnail(url=ctx.author.avatar.url)
        profile_embed.add_field(name="Title", value=new_title, inline=False)
        profile_embed.add_field(name="Rank", value=new_rank, inline=False)
        profile_embed.set_image(url=f"attachment://{image_path.split('/')[-1]}")

        await ctx.send(embed=profile_embed, file=discord.File(image_path))

    else:
        embed = discord.Embed(
            title="Profile Not Found",
            description="Your profile does not exist. Please create a profile using `generateprofile`.",
            color=discord.Color.red()
        )
        await ctx.send(embed=embed)


async def send_embed(ctx, title, description, color):
  embed = discord.Embed(
      title=title,
      description=description,
      color=color
  )
  await ctx.send(embed=embed)

# Event: Command Error
@bot.event
async def on_command_error(ctx, error):
  if isinstance(error, commands.CommandNotFound):
    if ctx.author.id in registered_users:
      await send_embed(
          ctx, "Command Not Found",
          "Sorry, that command does not exist. Use `help` to see available commands.",
          discord.Color.red())
    else:
      await send_embed(
          ctx, "What's this?",
          "You need to register by using the **register** command.",
          discord.Color.red())
  else:
    logger.error(f'Error: {str(error)}', exc_info=True)

# Define the path to the folder containing background images
background_folder = './Assets/Backgrounds/'


@bot.command(name='bgshop')
@is_registered()
async def background_shop(ctx, *, args: str = None):
    user_id = ctx.author.id

    # Load the currency data from the JSON file
    with open('Currency/currency.json', 'r') as currency_file:
        currency_data = json.load(currency_file)

    user_balance = currency_data.get(str(user_id), 0)

    # Define the path to your background folder
    background_folder = './Assets/Backgrounds/'  # Update with your actual path

    # Parse the command arguments
    filter_letter = None

    if args:
        args = args.split()
        # Check for the --n flag
        if len(args) == 2 and args[0] == '--n':
            filter_letter = args[1].lower()  # Convert the filter letter to lowercase

    # Define a function to check if a background is available
    def is_background_available(bg_id):
        return (
            bg_id in background_descriptions
            and bg_id in background_prices
            and (background_prices[bg_id] <= user_balance or user_balance < 0)  # Treat negative balance as not enough funds
        )

    if filter_letter == "":
        # Treat empty filter_letter as no filtering
        filter_letter = None

    if filter_letter:
        filtered_backgrounds = {
            bg_id: bg_description
            for bg_id, bg_description in background_descriptions.items()
            if bg_description.lower().startswith(filter_letter)
        }
    else:
        # Show all backgrounds, even if user can't afford them
        filtered_backgrounds = background_descriptions.copy()

    # Create an embed to display the filtered backgrounds
    embed = discord.Embed(
        title="H4X Mart - Background Shop",
        description="Welcome to H4X Mart's Background Shop! Browse and purchase backgrounds to customize your profile.",
        color=0x00FF00,  # Green color
    )

    for bg_id, bg_description in filtered_backgrounds.items():
        price = background_prices.get(bg_id, 0)
        if user_balance >= 0 and price > user_balance:
            availability = "NOT available"  # User can't afford
        else:
            availability = "available"
        embed.add_field(name=f"ID: {bg_id}", value=f"Description: {bg_description}\nPrice: {price} credits\nAvailability: {availability}", inline=False)

    # Tutorial section
    embed.add_field(
        name="How to Buy Backgrounds",
        value="To buy a background, use the command `e!buybg [ID]`, where `[ID]` is the ID of the background you want to purchase. For example, to buy Background 1, use `e!buybg bg1`.",
        inline=False
    )

    # Send the embed as a message with pagination
    shop_menu = BackgroundShopMenu(ctx, background_folder, user_balance, filtered_backgrounds)
    await shop_menu.start(ctx)

# Create a custom menu for pagination
class BackgroundShopMenu(menus.Menu):
    def __init__(self, ctx, background_folder, user_balance, filtered_backgrounds):
        super().__init__(timeout=60.0)
        self.ctx = ctx
        self.background_folder = background_folder
        self.user_balance = user_balance
        self.filtered_backgrounds = filtered_backgrounds
        self.page = 0
        self.per_page = 5  # Number of items to display per page

    async def send_initial_message(self, ctx, channel):
        return await ctx.send(embed=self.get_page_embed())

    def get_page_embed(self):
        start_index = self.page * self.per_page
        end_index = (self.page + 1) * self.per_page
        current_page = list(self.filtered_backgrounds.items())[start_index:end_index]

        embed = discord.Embed(
            title="H4X Mart - Background Shop",
            description="To buy a background, use the command `e!buybg [ID]`, where `[ID]` is the ID of the background you want to purchase",
            color=0x00FF00,  # Green color
        )

        for bg_id, bg_description in current_page:
            price = background_prices.get(bg_id, 0)
            if self.user_balance >= 0 and price > self.user_balance:
                availability = "NOT available"  # User can't afford
            else:
                availability = "available"
            embed.add_field(name=f"ID: {bg_id}", value=f"Description: {bg_description}\nPrice: {price} credits\nAvailability: {availability}", inline=False)

        embed.set_footer(text=f"Page {self.page + 1}/{len(self.filtered_backgrounds) // self.per_page + 1}")
        return embed

    @menus.button('\N{BLACK LEFT-POINTING TRIANGLE}')
    async def on_back_button(self, payload):
        if self.page > 0:
            self.page -= 1
            await self.message.edit(embed=self.get_page_embed())

    @menus.button('\N{BLACK RIGHT-POINTING TRIANGLE}')
    async def on_next_button(self, payload):
        if (self.page + 1) * self.per_page < len(self.filtered_backgrounds):
            self.page += 1
            await self.message.edit(embed=self.get_page_embed())


@bot.command(name='viewbg')
@is_registered()  # Assuming you have an is_registered decorator for user registration
async def view_background(ctx, background_id: int):
    background_folder = 'Assets/Backgrounds/'  # Define your background folder

    # Check if the requested background ID exists
    if background_id in background_descriptions:
        # Determine the file extension based on the existence of JPG, PNG, and GIF files
        jpg_background = os.path.join(background_folder, f'{background_id}.jpg')
        png_background = os.path.join(background_folder, f'{background_id}.png')
        gif_background = os.path.join(background_folder, f'{background_id}.gif')

        if os.path.exists(jpg_background):
            selected_background = f'{background_id}.jpg'
        elif os.path.exists(png_background):
            selected_background = f'{background_id}.png'
        elif os.path.exists(gif_background):
            selected_background = f'{background_id}.gif'
        else:
            await ctx.send('Background image not found.')
            return

        background_path = os.path.join(background_folder, selected_background)

        # Get the description for the selected background from the imported background_descriptions dictionary
        description = background_descriptions.get(background_id, "No Description")

        # Create an embedded message
        embed = discord.Embed(
            title=f'Viewing Background {background_id}',
            description=description,  # Set the description of the image
            color=discord.Color.blue()  # You can change the color as needed
        )

        # Add the selected background image as a field in the embedded message
        if selected_background.endswith('.gif'):
            embed.set_image(url=f"attachment://{selected_background}")
        else:
            embed.set_image(url=f"attachment://{selected_background}")

        # Get the price for the selected background from the imported background_prices dictionary
        price = background_prices.get(background_id, "N/A")  # Get the price or "N/A" if not found

        # Add the price to the embedded message
        embed.add_field(name="Price", value=f"{price} redants", inline=False)

        # Send the embedded message with the selected background image as an attachment
        with open(background_path, 'rb') as background_file:
            file = discord.File(background_file, filename=selected_background)
            await ctx.send(embed=embed, file=file)
    else:
        await ctx.send('Invalid background ID.')


# Define the path to the folder containing background images
MY_FOLDER = './Assets/Backgrounds/'


@bot.command()
@is_registered()
async def buybg(ctx, background_id: int):
    user_id = str(ctx.author.id)

    # Load the currency data from the JSON file
    with open('Currency/currency.json', 'r') as currency_file:
        currency_data = json.load(currency_file)

    # Check if the provided background_id is valid
    if 1 <= background_id <= len(background_prices):
        price = background_prices[background_id]

        # Check if the user has enough redants to make the purchase
        if currency_data.get(user_id, 0) >= price:
            # Deduct the cost of the background from the user's balance
            currency_data[user_id] = currency_data.get(user_id, 0) - price

            # Determine the extension type based on the background_id
            if background_id in [11, 69, 81, 93, 94, 95, 96, 98, 99, 100, 101, 104, 107 ]:  # Background 11 is in PNG format
                extension = 'png'
            # elif background_id in [67, 68]:  # Backgrounds 67 and 68 are in GIF format
            #     extension = 'gif'
            else:
                extension = 'jpg'  # All other backgrounds are in JPG format

            # Generate the background URL based on the background_id and extension
            background_url = os.path.join(MY_FOLDER, f'{background_id}.{extension}')

            # Get the description for the purchased background from the imported background_descriptions dictionary
            description = background_descriptions.get(background_id, "No Description")

            # Update the user's profile with the purchased background URL and description
            user_profiles[user_id]['background_url'] = background_url
            user_profiles[user_id]['background_description'] = description
            save_user_profiles()  # You need to implement this function to save user profiles

            # Update the currency data in the JSON file
            with open('Currency/currency.json', 'w') as currency_file:
                json.dump(currency_data, currency_file, indent=4)  # Indent for better readability

            # Send a confirmation message to the user with the description
            await ctx.send(
                f'You have successfully purchased Background ``{background_id}`` named  ``{description}``. Your new background has been applied to your render.\n'
            )

        else:
            await ctx.send("You don't have enough redants to purchase this background.")
    else:
        await ctx.send("Invalid background ID.")


# Define the path to the folder containing card images
card_folder = './Assets/Cards/'  # Update with your actual path

# Define card information with descriptions and prices
card_info = {
  "1.jpg": {"name": "Sasuke", "description": "Akatsuki version", "price": 5100},
  "2.jpg": {"name": "Goku", "description": "version Ultra instinct !", "price": 15000},
  "3.jpg": {"name": "Gojo", "description": "Gojo the free version", "price": 20000},
  "4.jpg": {"name": "senku", "description": "dr. stone scienctist prehstoric ", "price": 5000},
  "5.jpg": {"name": "nagi", "description": "blue lock : lazy genius", "price": 5900},
  "6.jpg": {"name": "bachira", "description": "Blue lock: monster inside me ", "price": 10000},
  "7.jpg": {"name": "kaguya", "description": "shinomiya kaguya the sexy ", "price": 9000},
  "8.jpg": {"name": "Esdeath", "description": "the fallen angel: ice princess ", "price": 14000},
  "9.jpg": {"name": "byakyuya", "description": "senbon zakura kageyoshi", "price": 12000},
  "10.jpg": {"name": "killua", "description": "fast AF", "price": 4000},
  "11.jpg": {"name": "Sukuna", "description": "greatest curse spirit", "price": 18000},
  "12.jpg": {"name": "Saitama", "description": "Can solo your fav anime-verse", "price": 25000},
  "13.jpg": {"name": "nami", "description": "weather babe", "price": 11000},
  "14.jpg": {"name": "ace", "description": "fire fist asce", "price": 4900},
  "15.jpg": {"name": "zoro", "description": "king of the hell", "price": 17000},
  "16.jpg": {"name": "luffy", "description": "future king of the pirates !", "price": 21000},
  "17.jpg": {"name": "sakamoto", "description": "have u heard of me?", "price": 15000},
  "18.jpg": {"name": "killua2", "description": "fast AF boiee", "price": 14000},
  "19.jpg": {"name": "usopp", "description": "greastest god of al time, d god, shogei king", "price": 18000},
  "20.jpg": {"name": "kurapika", "description": "literally , takne a coffin for the enemy ", "price": 25000},
  "21.jpg": {"name": "giyu", "description": "shinobu's babe fr.", "price": 12000},
  "22.jpg": {"name": "l", "description": "hmm, the best genus ever has high iq AF", "price": 13000},
  "23.jpg": {"name": "shanks", "description": "has the best emperor haki ever !", "price": 18000},
  "24.jpg": {"name": "gon", "description": "his daddy left him, xd", "price": 21000},
  "25.jpg": {"name": "light", "description": "kira aka kami sama xD", "price": 12000},
  "26.jpg": {"name": "rin", "description": "da' wablu guy ", "price": 24000},
  "27.jpg": {"name": "sanji", "description": "ladies rikkybell aka chef ", "price": 19000},
  "28.jpg": {"name": "franky", "description": "robotic pirate ", "price": 9000},
  "29.jpg": {"name": "chopper", "description": "big mom babe", "price": 7500},
  "30.jpg": {"name": "brook", "description": "panty lorde ", "price": 7000},
  "31.jpg": {"name": "robin", "description": "babe material  ", "price": 6500},
  "32.jpg": {"name": "law", "description": "water law trafalgar d. shambles ", "price": 18000},
  "33.jpg": {"name": "mori", "description": "bulies DBZ ? ", "price": 17000},
  "34.jpg": {"name": "mikey", "description": "KIck lee  ", "price": 2500},
  "35.jpg": {"name": "ichigo", "description": "shinigami, quincy, fullbringer maybe future soul king  ", "price": 17500},
  "36.jpg": {"name": "itachi", "description": "ur already in my genjutsu...  ", "price": 17500},
  "37.jpg": {"name": "samrick", "description": "DEv photo.. ", "price": 175000},
  "38.jpg": {"name": "ryuma", "description": "king of swords : wano hero ", "price": 11500},
  "39.jpg": {"name": "raiden", "description": "raiden babe shogun : genshin  ", "price": 12500},
  "40.jpg": {"name": "rias", "description": "boob ?  ", "price": 50000},
  "41.jpg": {"name": "aot", "description": "attk on titan wall scene ", "price": 20000},
  "42.png": {"name": "guts", "description": "fade to black ", "price": 12000},
  "43.png": {"name": "power", "description": "blood devil sexyy ", "price": 12000},
  "44.png": {"name": "garou", "description": "monster form ", "price": 12000},
  "45.jpg": {"name": "crown", "description": "multi liner", "price": 12000},

}


# Constants
CARDS_PER_PAGE = 4

@bot.command(name='cardshop')
@is_registered()
async def card_shop(ctx):
    user_id = str(ctx.author.id)

    # Load the currency data from the JSON file
    with open('Currency/currency.json', 'r') as currency_file:
        currency_data = json.load(currency_file)

    # List of available cards
    available_cards = []

    for card_name, card_data in card_info.items():
        name = card_data.get("name", "Unnamed Card")
        description = card_data.get("description", "No description available")
        price = card_data.get("price", 0)

        if currency_data.get(user_id, 0) >= price:
            availability = "Available"
        else:
            availability = "Not Enough Redants"

        available_cards.append((name, description, price, availability))

    # Calculate the total number of pages
    total_pages = (len(available_cards) + CARDS_PER_PAGE - 1) // CARDS_PER_PAGE

    # Initialize page index
    page_index = 0

    message = None

    # Add reaction controls
    async def add_reactions():
        await message.add_reaction("⬅️")
        await message.add_reaction("➡️")

    # Function to update the message with the current page
    async def update_page():
        nonlocal page_index, message  # Declare message as nonlocal
        embed = discord.Embed(
            title=f'Card Shop - Page {page_index + 1}/{total_pages}',
            description='To buy a card, use **e!buycard [name]**. Here are the available cards:',
            color=discord.Color.blue()
        )

        start_idx = page_index * CARDS_PER_PAGE
        end_idx = (page_index + 1) * CARDS_PER_PAGE

        for card_data in available_cards[start_idx:end_idx]:
            name, description, price, availability = card_data
            embed.add_field(
                name=name,
                value=f'Description: {description}\nPrice: {price} redants\nAvailability: {availability}',
                inline=True
            )

        # Send the embedded message
        if message:
            await message.edit(embed=embed)
        else:
            message = await ctx.send(embed=embed)
            await add_reactions()

    # Initial page display
    await update_page()

    def check(reaction, user):
        return user == ctx.author and reaction.message == message

    while True:
        try:
            reaction, user = await bot.wait_for('reaction_add', check=check, timeout=60.0)
        except asyncio.TimeoutError:
            break

        if str(reaction.emoji) == '⬅️':
            # Move to the previous page
            page_index = (page_index - 1) % total_pages
            await update_page()
        elif str(reaction.emoji) == '➡️':
            # Move to the next page
            page_index = (page_index + 1) % total_pages
            await update_page()

        # Remove the user's reaction
        await message.remove_reaction(reaction, user)

    # Remove reactions when done
    await message.clear_reactions()



@bot.command(name='cardview')
@is_registered()
async def view_card(ctx, *, card_name: str):
    user_id = str(ctx.author.id)

    # Normalize the input card name to lowercase for case-insensitive comparison
    card_name_lower = card_name.lower()

    # Check if the card with the provided name exists
    matching_card = None
    for card, card_data in card_info.items():
        if card_data.get("name").lower() == card_name_lower:
            matching_card = card
            break

    if matching_card:
        card_data = card_info[matching_card]
        name = card_data.get("name", "Unnamed Card")
        description = card_data.get("description", "No description available")
        price = card_data.get("price", 0)

        # Load the currency data from the JSON file
        with open('Currency/currency.json', 'r') as currency_file:
            currency_data = json.load(currency_file)

        # Check if the user has enough currency to afford the card
        if currency_data.get(user_id, 0) >= price:
            availability = "Available"
        else:
            availability = "Not Enough Redants"

        # Display the card details
        embed = discord.Embed(
            title=f'Viewing Card: {name}',
            description=f'Description: {description}\nPrice: {price} redants\nAvailability: {availability}\n\n',

            color=discord.Color.blue()  # Customize the color
        )

        # Include an image of the card
        card_path = os.path.join(card_folder, matching_card)
        with open(card_path, 'rb') as card_file:
            embed.set_image(url=f"attachment://{matching_card}")

        # Mention the currency file
        embed.set_footer(text="Developer : @samrick")

        await ctx.send(embed=embed, file=discord.File(card_path, filename=matching_card))
    else:
        await ctx.send("Card not found. Please check the card name and ensure it's spelled correctly.")

# Define the constant folder path for cards
CARD_FOLDER = './Assets/Cards/'

@bot.command(name='buycard')
@is_registered()
async def buy_card(ctx, *, card_name: str):
    user_id = str(ctx.author.id)

    # Normalize the input card name to lowercase for case-insensitive comparison
    card_name_lower = card_name.lower()

    # Check if the card with the provided name exists
    matching_card = None
    for card, card_data in card_info.items():
        if card_data.get("name").lower() == card_name_lower:
            matching_card = card
            break

    if matching_card:
        card_data = card_info[matching_card]
        name = card_data.get("name", "Unnamed Card")
        price = card_data.get("price", 0)
        card_url = CARD_FOLDER + matching_card  # Construct the card URL based on the card name

        # Load the currency data from the JSON file
        with open('Currency/currency.json', 'r') as currency_file:
            currency_data = json.load(currency_file)

        # Check if the user has enough currency to afford the card
        if currency_data.get(user_id, 0) >= price:
            # Deduct the cost of the card from the user's balance
            currency_data[user_id] = currency_data.get(user_id, 0) - price

            # Update the JSON file with the new balances with proper formatting
            with open('Currency/currency.json', 'w') as currency_file:
                json.dump(currency_data, currency_file, indent=4)  # Indent for better readability

            # Update the user's profile with the purchased card's URL
            if user_id in user_profiles:
                user_profiles[user_id]['card_url'] = card_url
                save_user_profiles()

                await ctx.send(
                    f'You have successfully purchased the card: "{name}". It has been added to your profile.'
                )
            else:
                await ctx.send("Your profile does not exist. Please register first.")
        else:
            await ctx.send("You don't have enough redants to purchase this card.")
    else:
        await ctx.send("Card not found. Please check the card name and ensure it's spelled correctly.")

# Define the titles and their prices
title_prices = {
    "Malice": 100,
    "Godly": 200,
    "Boob Lover": 150,
    "Legendary": 250,
    "Mighty": 250,
    "Thigh Lover": 450,
    "Menece": 800,
    "Immortal": 900,
    "Mythical": 2000,
    "Divine": 1000,
    "Supreme": 1500,
    "Ass Lover": 2000,
    "Conqueror": 3000,
    "Slayer": 500,
    "Warrior": 400,
    "Ninja": 350,
    "Wizard": 350,
    "Dragon": 750,
    "Star": 600,
    "Royal": 900,
    "Dark": 850,
    "Radioactive": 850,
    "King": 1200,
    "Horny": 1200,
}


@bot.command(name='titleshop')
@is_registered()
async def title_shop(ctx):
    user_id = str(ctx.author.id)

    # Load the currency data from the JSON file
    with open('Currency/currency.json', 'r') as currency_file:
        currency_data = json.load(currency_file)

    # Create an embedded message to display the title shop
    embed = discord.Embed(
        title='Title Shop',
        description='do **e!buytitle [name]** to buy, Here are the available titles:',
        color=discord.Color.blue()  # Customize the color
    )

    # Determine the number of pages based on the number of titles
    num_titles = len(title_prices)
    num_pages = (num_titles + 4) // 5  # Ceiling division to calculate pages

    # Initialize page and start index
    current_page = 1
    start_index = 0

    for title, price in list(title_prices.items())[start_index:start_index + 5]:
        # Check if the user can afford the title
        if currency_data.get(user_id, 0) >= price:
            availability = "Available"
        else:
            availability = "Not Enough Redants"

        embed.add_field(
            name=title,
            value=f'Price: {price} redants\nAvailability: {availability}',
            inline=True
        )

    # Send the initial embed message
    message = await ctx.send(embed=embed)

    # Define reactions for pagination
    reactions = ['⬅️', '➡️']

    # Add reactions to the message
    for reaction in reactions:
        await message.add_reaction(reaction)

    def check(reaction, user):
        return (
            user == ctx.author and
            reaction.message == message and
            str(reaction.emoji) in reactions
        )

    while True:
        try:
            reaction, user = await bot.wait_for('reaction_add', check=check, timeout=60.0)

            if str(reaction.emoji) == '⬅️':
                # Go to the previous page
                current_page -= 1
            elif str(reaction.emoji) == '➡️':
                # Go to the next page
                current_page += 1

            # Ensure the page number is within bounds
            current_page = max(1, min(current_page, num_pages))

            # Update the start index based on the current page
            start_index = (current_page - 1) * 5

            # Clear the existing fields in the embed
            embed.clear_fields()

            for title, price in list(title_prices.items())[start_index:start_index + 5]:
                # Check if the user can afford the title
                if currency_data.get(user_id, 0) >= price:
                    availability = "Available"
                else:
                    availability = "Not Enough Redants"

                embed.add_field(
                    name=title,
                    value=f'Price: {price} redants\nAvailability: {availability}',
                    inline=True
                )

            # Update the message with the new embed
            await message.edit(embed=embed)

        except asyncio.TimeoutError:
            break

    # Remove reactions after pagination
    await message.clear_reactions()

@bot.command(name='buytitle')
@is_registered()
async def buy_title(ctx, *, selected_title: str):
    user_id = str(ctx.author.id)

    # Load the currency data from the JSON file
    with open('Currency/currency.json', 'r') as currency_file:
        currency_data = json.load(currency_file)

    # Convert the user's input to lowercase for case-insensitive comparison
    selected_title_lower = selected_title.lower()

    # Check if the selected title exists in the title shop (case-insensitive)
    matching_titles = [title for title in title_prices if title.lower() == selected_title_lower]

    if matching_titles:
        # Assuming there are no duplicate titles with the same lowercase representation
        selected_title = matching_titles[0]
        price = title_prices[selected_title]

        # Check if the user has enough redants to make the purchase
        if currency_data.get(user_id, 0) >= price:
            # Deduct the cost of the title from the user's balance
            currency_data[user_id] = currency_data.get(user_id, 0) - price

            # Update the JSON file with the new balances with proper formatting
            with open('Currency/currency.json', 'w') as currency_file:
                json.dump(currency_data, currency_file, indent=4)  # Indent for better readability

            # Update user_profiles or do whatever is needed to apply the purchased title
            user_profiles[user_id]['title'] = selected_title
            save_user_profiles()

            await ctx.send(
                f'You have successfully purchased the "{selected_title}" title. It has been added to your profile.'
            )
        else:
            await ctx.send("You don't have enough redants to purchase this title.")
    else:
        await ctx.send(
            "Invalid title. Please check the available titles using `!titleshop`.")


# Load restricted user IDs from the text file
def load_restricted_users():
  try:
    with open('Assets/ban.txt', 'r') as file:
      return set(int(line.strip()) for line in file)
  except FileNotFoundError:
    return set()


# Save restricted user IDs to the text file
def save_restricted_users(restricted_users):
  with open('Assets/ban.txt', 'w') as file:
    for user_id in restricted_users:
      file.write(str(user_id) + '\n')


# Initialize restricted user IDs from the text file
restricted_users = load_restricted_users()


# Restrict command to add a user to the restricted list
@bot.command()
async def restrict(ctx, user: discord.User):
  if ctx.author.id == 1128651413535346708:  # Replace with your own user ID
    restricted_users.add(user.id)
    save_restricted_users(restricted_users)
    await ctx.send(f"{user.mention} has been restricted from using the bot.")
  else:
    await ctx.send("You do not have permission to use this command.")


# Unrestrict command to remove a user from the restricted list
@bot.command()
async def unrestrict(ctx, user: discord.User):
  if ctx.author.id == 1128651413535346708:  # Replace with your own user ID
    if user.id in restricted_users:
      restricted_users.remove(user.id)
      save_restricted_users(restricted_users)
      await ctx.send(
          f"{user.mention} has been unrestricted and can now use the bot.")
    else:
      await ctx.send(f"{user.mention} is not currently restricted.")
  else:
    await ctx.send("You do not have permission to use this command.")


# Check if a user is restricted before processing commands
@bot.check
def is_user_restricted(ctx):
  return ctx.author.id not in restricted_users


# Load data from rank.json
def load_rank_data():
  try:
    with open("Assets/storage/rank.json", "r") as file:
      return json.load(file)
  except FileNotFoundError:
    return {}


# Load rank data from rank.json
rank_data = load_rank_data()

rank_thresholds = {
    "Novice": 0,
    "Rookie": 10,
    "Stone": 20,
    "Bronze": 30,
    "Silver": 50,
    "Golden": 80,
    "Titan": 130,
    "Supreme": 210,
    "Heroic": 340,
    "Legend": 550,
    "Saiyan": 850
}


@bot.command()
@is_registered()
async def tierlist(ctx):
  # Define the rank thresholds
  rank_thresholds = {
      "Novice": 0,
      "Rookie": 10,
      "Stone": 20,
      "Bronze": 30,
      "Silver": 50,
      "Golden": 80,
      "Titan": 130,
      "Supreme": 210,
      "Heroic": 340,
      "Legend": 550,
      "Saiyan": 850
  }

  # Create an embedded message to display the tier list
  embed = discord.Embed(
      title='Tier List',
      description=
      'Here are the available ranks and the required number of wins to achieve them:',
      color=discord.Color.gold()  # Customize the color
  )

  for rank, wins_required in rank_thresholds.items():
    embed.add_field(name=rank,
                    value=f'Wins Required: {wins_required}',
                    inline=True)

  await ctx.send(embed=embed)


@bot.command()
@is_registered()
async def viewrank(ctx):
    user_id = str(ctx.author.id)
    profile = user_profiles.get(user_id)

    if profile and "rank" in profile:
        rank = profile["rank"]
        user = ctx.author
        user_avatar = user.avatar.url if user.avatar else user.default_avatar.url

        # Define a dictionary mapping ranks to text-based emojis
        rank_icons = {
            "Novice": "😊",
            "Rookie": ":full_moon_with_face:",
            "Stone": ":rock:",
            "Bronze": "🥉",
            "Silver": "🥈",
            "Golden": "🥇",
            "Titan": "🏋️‍♂️",
            "Supreme": "👑",
            "Heroic": "⚡",
            "Legend": "🏆",
            "Saiyan": "🐉"
        }

        embed = discord.Embed(
            title=f"{user.display_name}'s Rank",
            color=discord.Color.gold()
        )

        # Display the user's username and their rank at the top
        embed.description = f"{rank} \n {rank_icons.get(rank, 'Rank icon not found')}"

        # Set the user's avatar as the thumbnail
        embed.set_thumbnail(url=user_avatar)

        await ctx.send(embed=embed)
    else:
        await ctx.send("Rank not found.")


@bot.command(name='rankupdate')
@is_registered()
async def update_rank_command(ctx):
  # Load the latest rank data from the JSON file
  rank_data = load_rank_data()

  for user_id, profile_data in user_profiles.items():
    wins = rank_data.get(user_id, {}).get("wins", 0)
    assigned_rank = None  # Initialize to None
    for rank, threshold in rank_thresholds.items():
      if wins >= threshold:
        assigned_rank = rank  # Assign the rank
      else:
        break
    profile_data["rank"] = assigned_rank  # Assign the last achieved rank

  await ctx.send("User ranks have been updated.")


# Update ranks using the loaded rank data
update_rank_command(user_profiles, rank_data)


# Command to reset wins and losses to 0
@bot.command()
@is_registered()
async def rankreset(ctx, target_user: discord.User):
  # Check if the user invoking the command is the specific user with authority
  if ctx.author.id == SPECIFIC_USER_ID:
    target_user_id = str(target_user.id)

    # Check if the user exists in rank_data and update wins and losses to 0
    if target_user_id in rank_data:
      rank_data[target_user_id]["wins"] = 0
      rank_data[target_user_id]["losses"] = 0

      # Save the updated rank data
      rank_data_path = "Assets/storage/rank.json"
      with open(rank_data_path, "w") as rank_file:
        json.dump(rank_data, rank_file, indent=4)

      await ctx.send(
          f"{target_user.mention}'s wins and losses have been reset to 0 in the rank data."
      )
    else:
      await ctx.send(f"{target_user.mention} does not have existing rank data."
                     )
  else:
    await ctx.send(
        "You do not have the authority to reset wins and losses for other users."
    )


@bot.command()
@is_registered()
async def botinfo(ctx):
  # Define the bot's profile picture URL
  bot_pfp_url = "https://cdn.discordapp.com/avatars/1149406804174970921/f40dd64dc05d7d8c3ef05a31ac2f47fd.png?size=1024"

  # Create an embedded message to display bot information
  embed = discord.Embed(
      title="Expertise Bot Information",
      description=
      "Expertise Bot: Because even robots need a little bit of chaos in their circuits! 🤖✨",
      color=discord.Color.blue())

  # Set the bot's profile picture
  embed.set_thumbnail(url=bot_pfp_url)

  # Add bot details and emojis
  embed.add_field(name="Bot Name", value="Expertise Bot :robot:")
  embed.add_field(name="Bot Version", value="1.0 :rocket:")
  embed.add_field(name="Developer", value="Samrick && Safal :technologist:")

  # Mention that it's made for Haxx Disaster and personal server
  embed.add_field(name="Purpose",
                  value="To Serve Haxx Disaster :earth_africa:")
  # # Mention that it's made for Haxx Disaster and personal server
  # embed.add_field(name="Website",
  #                 value="https://RyuZinOh.github.io")

  # Add a footer with text
  embed.set_footer(text="Thank you for using Expertise!")

  # Send the embedded message
  await ctx.send(embed=embed)


# Define the user ID of the allowed user
ALLOWED_USER_ID = 1128651413535346708  # Replace with the actual user ID


# Custom check function to restrict command usage to the allowed user
def is_allowed_user(ctx):
  return ctx.author.id == ALLOWED_USER_ID


@bot.command()
@commands.check(is_allowed_user)  # Apply the custom check
async def startwar(ctx, team1_name, team2_name, goals):
  # Call the start_war function to initiate a war
  clanwar.start_war(team1_name, team2_name, goals)
  await ctx.send(
      f"War between {team1_name} and {team2_name} started with goals: {goals}")


@bot.command(name="waradd")
@is_registered()
async def addusertoteam(ctx, user_id, team_name):
  # Check if the command invoker is allowed to use this command (specific user)
  if ctx.author.id == 1128651413535346708:
    result = clanwar.add_user_to_team(user_id, team_name)
    await ctx.send(result)
  else:
    await ctx.send("You do not have permission to use this command.")


@bot.command(name="warstats")
# @is_registered()
async def getwardata(ctx):
    # Check if the war data JSON file exists and load it
    try:
        with open('clanWar/clanwar.json', 'r') as war_file:
            war_data = json.load(war_file)
    except FileNotFoundError:
        war_data = {}

    # Create an embedded message to display the current war data
    embed = discord.Embed(
        title='Current War Data',
        color=discord.Color.green()  # Customize the color
    )

    # Check if there are teams in the war data
    if 'team1' in war_data and 'team2' in war_data:
        # Add team information to the embed message
        for team_name, team_data in war_data.items():
            team_users = ', '.join(team_data['users'])
            team_goals = team_data['goals']
            team_status = team_data['current_status']

            embed.add_field(
                name=f'Team {team_data["name"]}',
                value=f'Users: {team_users}\nGoals: {team_goals}\nCurrent Status: {team_status}',
                inline=False
            )

        # Save the image path
        image_path = 'clanWar/battle.jpg'

        # Set the image for the embedded message
        embed.set_image(url='attachment://modified_image.jpg')

        # Open the image
        image = Image.open(image_path)
        draw = ImageDraw.Draw(image)

        # Set the font size (you can adjust the size)
        font_size = 42  # You can change this value to adjust the font size
        font = ImageFont.truetype(
            "Fonts/Poppins.ttf",
            font_size)  # Replace with the path to your font file

        # Add team names at the top
        team1_name = war_data['team1']['name']
        team2_name = war_data['team2']['name']

        # Set fixed X and Y positions for team names at the top
        x_position1 = 20
        x_position2 = image.width - len(team2_name) * (font_size // 2) - 69
        y_position = 20

        # Add team names to the image at the top
        draw.text((x_position1, y_position), team1_name, fill="white", font=font)
        draw.text((x_position2, y_position), team2_name, fill="white", font=font)

        # Save the modified image
        image.save('clanWar/modified_image.jpg')

        # Send the embedded message with the modified image as an attachment
        await ctx.send(embed=embed,
                       file=discord.File('clanWar/modified_image.jpg'))
    else:
        await ctx.send('No war data available.')


@bot.command()
# @is_registered()
async def warlog(ctx, opponent: discord.User):
  with open('clanWar/clanwar.json', 'r') as json_file:
    clanwar_data = json.load(json_file)

  author_mention = ctx.author.mention
  opponent_mention = opponent.mention

  # Check if the opponent is a member of any team
  opponent_in_team = False
  for team, data in clanwar_data.items():
    if opponent_mention in data["users"]:
      opponent_in_team = True
      break

  if not opponent_in_team:
    await ctx.send(
        f"{opponent_mention} is not a member of any team in the clan war.")
    return

  for team, data in clanwar_data.items():
    if author_mention in data["users"]:
      if opponent_mention in data["users"]:
        await ctx.send("You can't log a match with your own teammate.")
        return

      message = await ctx.send(
          f"{author_mention} wants to log a match with {opponent_mention} for Team {data['name']}. React with ✅ to accept or ❌ to cancel."
      )

      await message.add_reaction('✅')
      await message.add_reaction('❌')

      def check(reaction, user):
        return user == opponent and str(reaction.emoji) in ['✅', '❌']

      try:
        reaction, _ = await bot.wait_for('reaction_add',
                                         timeout=60.0,
                                         check=check)

        if str(reaction.emoji) == '✅':
          data["current_status"] += 1
          with open('clanWar/clanwar.json', 'w') as json_file:
            json.dump(clanwar_data, json_file, indent=4)

          # Calculate current status in the specified format
          current_status = f"Team {clanwar_data['team1']['name']} [{clanwar_data['team1']['current_status']}/{clanwar_data['team1']['goals']}] and Team {clanwar_data['team2']['name']} [{clanwar_data['team2']['current_status']}/{clanwar_data['team2']['goals']}]"

          await ctx.send(
              f"{opponent_mention} has accepted the match log! Current status: {current_status}"
          )

          # Send an embed in a specific channel
          channel_id = 1144817850436042762  # Replace with your channel ID
          channel = bot.get_channel(channel_id)

          embed = discord.Embed(
              title=current_status,
              description=
              f"{author_mention} won over {opponent_mention} in this match!\n[Message Link]({message.jump_url})",
              color=discord.Color.green())
          await channel.send(embed=embed)
        else:
          await ctx.send(f"{opponent_mention} has canceled the match log.")
      except asyncio.TimeoutError:
        await ctx.send(
            f"{opponent_mention} didn't respond in time. Match log request has expired."
        )
      return  # Exit the function if the author's team is found

  await ctx.send(f"You are not a member of any team in the clan war.")


# Check if the user is the authorized user
def is_authorized(ctx):
  return ctx.message.author.id == 1128651413535346708


@bot.command()
@is_registered()
@commands.check(lambda ctx: ctx.message.author.id == 1128651413535346708)
async def warupdate(ctx):
  # Load the JSON data from your file
  with open('clanWar/clanwar.json', 'r') as json_file:
    data = json.load(json_file)

  # Variables to store the image paths for Team1 and Team2
  team1_image_path = 'clanWar/team1.png'  # Replace with the actual path to Team1's image
  team2_image_path = 'clanWar/team2.png'  # Replace with the actual path to Team2's image

  # Access team1 and team2 data from the loaded JSON
  team1 = data['team1']
  team2 = data['team2']

  # Extract relevant information from the teams
  team1_name = team1['name']
  team1_goals = int(team1['goals'])
  team1_status = int(team1['current_status'])

  team2_name = team2['name']
  team2_goals = int(team2['goals'])
  team2_status = int(team2['current_status'])

  # Calculate the point gain format for each team
  team1_point_gain = f"[{team1_status} / {team1_goals}]"
  team2_point_gain = f"[{team2_status} / {team2_goals}]"

  # Determine the winning and losing teams
  if team1_status == team2_status:
    result_message = "It's a tie!"
    winner_name = None
    loser_name = None
  elif team1_status > team2_status:
    result_message = f"Congratulations to **{team1_name}** for winning the war! Let's give them a round of applause. 👏"
    winner_name = team1_name
    loser_name = team2_name
    winning_team_image_path = team1_image_path
  else:
    result_message = f"Congratulations to **{team2_name}** for winning the war! Let's give them a round of applause. 👏"
    winner_name = team2_name
    loser_name = team1_name
    winning_team_image_path = team2_image_path

  # Get the specific Discord channel where you want to send the message
  channel_id = 1144817850436042762  # Replace with your channel ID
  channel = bot.get_channel(channel_id)

  # Load the images for Team1 and Team2 and resize them to the desired size (e.g., 64x64 pixels)
  team1_image = Image.open(team1_image_path).resize((64, 64))
  team2_image = Image.open(team2_image_path).resize((64, 64))

  # Create an embed message with detailed information
  embed = discord.Embed(title="War Update",
                        description=result_message,
                        color=discord.Color.green())

  # Mention both the winning and losing teams
  if winner_name:
    embed.add_field(
        name=f"Winner: **{winner_name}**",
        value=
        f"Point Gain: {team1_point_gain if winner_name == team1_name else team2_point_gain}",
        inline=False)
  if loser_name:
    embed.add_field(
        name=f"Loser: {loser_name}",
        value=
        f"Point Gain: {team1_point_gain if loser_name == team1_name else team2_point_gain}",
        inline=False)

  # Mention the users of each team
  team1_users = [user_mention.strip('<@!>') for user_mention in team1['users']]
  team2_users = [user_mention.strip('<@!>') for user_mention in team2['users']]

  if team1_users:
    users_mention = [f"<@{user_id}>" for user_id in team1_users]
    embed.add_field(name=f"{team1_name} Team",
                    value=", ".join(users_mention),
                    inline=False)
  if team2_users:
    users_mention = [f"<@{user_id}>" for user_id in team2_users]
    embed.add_field(name=f"{team2_name} Team",
                    value=", ".join(users_mention),
                    inline=False)

  # Add the resized image of the winning team to the embed on the opposite side
  if winner_name:
    embed.set_thumbnail(url="attachment://winning_team.png")

  # Send the embed message with the winning team's image to the specified Discord channel
  await channel.send(embed=embed,
                     files=[
                         discord.File(winning_team_image_path,
                                      filename="winning_team.png")
                     ])


# Define the path to the JSON file
json_file_path = 'clanWar/clanwar.json'


@bot.command()
@is_registered()
@commands.check(is_authorized)
async def clearwar(ctx):
  # Create an empty dictionary
  empty_data = {}

  # Write the empty dictionary to the JSON file
  with open(json_file_path, 'w') as json_file:
    json.dump(empty_data, json_file, indent=4)

  # Send a confirmation message
  await ctx.send("The war data has been cleared.")


@bot.command(name="warhelp")
async def warhelp(ctx):
  # Create an embedded message to provide user-friendly explanations of commands
  embed = discord.Embed(
      title="Internal Clan war system",
      description="Here are the commands for Clan War system",
      color=discord.Color.blue())

  embed.add_field(
      name="`e!startwar <team1_name> <team2_name> <goals>`",
      value="Start a war between two teams with specified names and goals.",
      inline=False)

  embed.add_field(
      name="`e!waradd <user_id> <team_name>`",
      value=
      "Add a user to a team in the ongoing war. (Restricted to authorized user)",
      inline=False)

  embed.add_field(
      name="`e!warstats`",
      value=
      "View the current war statistics, including team data and an image of the current status.",
      inline=False)

  embed.add_field(
      name="`e!warlog <opponent>`",
      value=
      "Log a match with an opponent from the opposing team. Opponent must accept the log request. (Restricted to team members)",
      inline=False)

  embed.add_field(
      name="`e!warupdate`",
      value=
      "Update the war status, announce the winning team, and display team members and their point gains. (Restricted to authorized user)",
      inline=False)

  embed.add_field(name="`e!clearwar`",
                  value="Clear all war data. (Restricted to authorized user)",
                  inline=False)

  embed.add_field(
      name="**Note:**",
      value=
      "Replace `<team1_name>`, `<team2_name>`, `<goals>`, `<user_id>`, and `<team_name>` with appropriate values when using the commands.",
      inline=False)

  embed.set_footer(text="Prefix: e!")

  # Send the embedded help message to the user
  await ctx.send(embed=embed)

# Your user ID
kms = 1128651413535346708

@bot.command(name='hakai')
@is_registered()
async def hakai(ctx, user_id: int):
    # Check if the user invoking the command is the authorized user
    if ctx.author.id == kms:
        # Check if the provided user ID is valid and exists in user_profiles.json
        user_profiles_file = 'Profiles/user_profiles.json'
        currency_file = 'Currency/currency.json'
        rank_file = 'Assets/storage/rank.json'
        ban_file = 'Assets/ban.txt'
        accounts_file = 'Assets/accounts.txt'  # Add the path to accounts.txt

        # Construct the path to the user's profile image file
        user_image_file = f'Profiles/{user_id}.png'

        try:
            # Load user_profiles.json, currency.json, and rank.json
            with open(user_profiles_file, 'r') as user_profiles_data:
                user_profiles = json.load(user_profiles_data)

            with open(currency_file, 'r') as currency_data:
                currency = json.load(currency_data)

            with open(rank_file, 'r') as rank_data:
                rank = json.load(rank_data)
        except FileNotFoundError:
            await ctx.send("One or more required files not found.")
            return

        # Check if the user exists in user_profiles.json
        if str(user_id) in user_profiles:
            # Remove the user's data
            del user_profiles[str(user_id)]
            if str(user_id) in currency:
                del currency[str(user_id)]
            if str(user_id) in rank:
                del rank[str(user_id)]

            # Append the user's ID to ban.txt if it's not already there
            with open(ban_file, 'r') as ban_data:
                banned_users = ban_data.read().splitlines()

            if str(user_id) not in banned_users:
                with open(ban_file, 'a') as ban_data:
                    ban_data.write(str(user_id) + '\n')

            # Remove the user's ID from accounts.txt
            with open(accounts_file, 'r') as accounts_data:
                accounts = accounts_data.read().splitlines()

            if str(user_id) in accounts:
                accounts.remove(str(user_id))

            with open(accounts_file, 'w') as accounts_data:
                accounts_data.write('\n'.join(accounts))

            # Delete the user's profile image file if it exists
            if os.path.exists(user_image_file):
                os.remove(user_image_file)

            # Save the modified data back to the files
            with open(user_profiles_file, 'w') as user_profiles_data:
                json.dump(user_profiles, user_profiles_data, indent=4)

            with open(currency_file, 'w') as currency_data:
                json.dump(currency, currency_data, indent=4)

            with open(rank_file, 'w') as rank_data:
                json.dump(rank, rank_data, indent=4)

            await ctx.send(f"User with ID {user_id} has been 'hakai'd.")
        else:
            await ctx.send("User not found in user profiles.")
    else:
        await ctx.send("You are not authorized to use this command.")

@bot.command(name='hibernate')
@is_registered()
async def refresh(ctx):
    if ctx.author.id == kms:
        await ctx.send("** Bot went for quick relization **")

        # Gracefully exit the bot process to trigger Replit's automatic restart
        os._exit(0)

    else:
        await ctx.send("You are not authorized to use this command.")

# Command to add a user ID to a file
@bot.command(name="deluxeadd")
@is_registered()
async def adduserid(ctx, user_id_to_add: int):
    # Check if the user invoking the command has the specified user ID
    if ctx.author.id == 1128651413535346708:
        # Add the provided user ID to the 'Deluxe_Profile/deluxe.txt' file
        with open('Deluxe_Profile/deluxe.txt', 'a') as file:
            file.write(str(user_id_to_add) + '\n')
        await ctx.send(f"User ID {user_id_to_add} has been added to the allowed user IDs.")
    else:
        await ctx.send("You are not authorized to use this command.")


# Constants
FINAL_GIF_SIZE = (690, 300)
AVATAR_SIZE = (120, 120)
AVATAR_BORDER_WIDTH = 2
AVATAR_BORDER_COLOR = (0, 255, 255)
BORDER_WIDTH = 2
BORDER_COLOR = (0, 255, 255)
FONT_PATH = 'Fonts/Poppins.ttf'
USERNAME_FONT_SIZE = 26
TITLE_FONT_SIZE = 18
RANK_FONT_SIZE = 22

def create_profile_gif(ctx, user_avatar_url, json_content, output_folder, bg_path=None):
    try:
        gif_path = bg_path or 'Luxuries/killua.gif'
        gif = imageio.get_reader(gif_path)
        username_font = ImageFont.truetype(FONT_PATH, size=USERNAME_FONT_SIZE)
        title_font = ImageFont.truetype(FONT_PATH, size=TITLE_FONT_SIZE)
        rank_font = ImageFont.truetype(FONT_PATH, size=RANK_FONT_SIZE)

        modified_frames = []

        for frame in gif:
            frame_image = Image.fromarray(frame)
            frame_image = frame_image.resize(FINAL_GIF_SIZE)

            draw = ImageDraw.Draw(frame_image)

            user_avatar = Image.open(requests.get(user_avatar_url, stream=True).raw)
            avatar_with_border = ImageOps.expand(user_avatar.resize(AVATAR_SIZE), border=AVATAR_BORDER_WIDTH, fill=AVATAR_BORDER_COLOR)
            frame_image.paste(avatar_with_border, (7, 7))

            x_info, y_info = 10, 130
            user_id = str(ctx.author.id)

            if user_id in json_content:
                content = json_content[user_id]
                username, title, rank = ctx.author.display_name, content["title"], content["rank"]
                draw.text((x_info, y_info), username, fill=BORDER_COLOR, font=username_font)
                draw.text((x_info, y_info + 30), title, fill=BORDER_COLOR, font=title_font)

                rank_x, rank_y = frame_image.width - 100, 10
                draw.text((rank_x, rank_y), rank, fill=BORDER_COLOR, font=rank_font)

            frame_image.paste(BORDER_COLOR, (0, 0, frame_image.width, BORDER_WIDTH))
            frame_image.paste(BORDER_COLOR, (0, frame_image.height - BORDER_WIDTH, frame_image.width, frame_image.height))

            modified_frames.append(frame_image)

        gif_filename = os.path.join(output_folder, f'{ctx.author.id}_profile.gif')
        modified_frames[0].save(gif_filename, save_all=True, append_images=modified_frames[1:], duration=gif.get_meta_data()['duration'], loop=0)

        return gif_filename

    except Exception as e:
        print(f"An error occurred: {e}")

def read_json_content():
    try:
        with open('Profiles/user_profiles.json', 'r') as file:
            return json.load(file)
    except FileNotFoundError:
        print("user_profiles.json file not found.")
        return {}

@bot.command()
@is_registered()
async def generatedeluxeprofile(ctx):
    json_content = read_json_content()

    with open('Deluxe_Profile/deluxe.txt', 'r') as file:
        allowed_user_ids = [line.strip() for line in file]

    user_id = str(ctx.author.id)

    if user_id not in allowed_user_ids:
        await ctx.send("You are not allowed to use this command.")
        return

    output_folder = 'Deluxe_Profile/profiles'
    gif_filename = os.path.join(output_folder, f"{user_id}_profile.gif")

    if os.path.exists(gif_filename):
        await ctx.send("You already have a deluxe profile!")
        return

    loading_msg = await ctx.send("Generating the deluxe profile...")
    user_avatar_url = ctx.author.avatar.url if ctx.author.avatar else ctx.author.default_avatar.url

    gif_filename = create_profile_gif(ctx, user_avatar_url, json_content, output_folder)

    await loading_msg.edit(content="Deluxe profile generated!")
    await asyncio.sleep(1)
    await loading_msg.delete()

    with open(gif_filename, 'rb') as file:
        await ctx.send(file=discord.File(file))

@bot.command()
@is_registered()
async def deluxeprofile(ctx):
    loading_msg = await ctx.send("Loading your deluxe profile...")

    try:
        with open('Deluxe_Profile/deluxe.txt', 'r') as file:
            allowed_user_ids = [line.strip() for line in file]

        user_id = str(ctx.author.id)

        if user_id not in allowed_user_ids:
            await ctx.send("You are not allowed to use this command.")
            return

        gif_filename = os.path.join('Deluxe_Profile/profiles', f'{user_id}_profile.gif')

        if os.path.exists(gif_filename):
            await ctx.send(file=discord.File(gif_filename))  # Send the GIF
            await loading_msg.edit(content="Deluxe profile loaded!")
            await asyncio.sleep(1)  # Sleep for 1 second
        else:
            await ctx.send("Oops! Your deluxe profile couldn't be found.")

    except Exception as e:
        print(f"An error occurred: {e}")

    finally:
        await loading_msg.delete()  # Delete the loading message after everything is done

@bot.command()
@is_registered()
async def luxuryshop(ctx):
    with open('Deluxe_Profile/deluxe.txt', 'r') as file:
        allowed_user_ids = [line.strip() for line in file]

    user_id = str(ctx.author.id)

    if user_id not in allowed_user_ids:
        await ctx.send("You are not allowed to use this command.")
        return

    luxury_folder = 'Luxuries'
    gif_files = [f for f in os.listdir(luxury_folder) if f.endswith('.gif')]

    if gif_files:
        embed = discord.Embed(title="Luxury GIF Shop", color=0x00FFFF)

        gif_list = "\n".join([f"{i}: **{os.path.splitext(gif_file)[0]}**" for i, gif_file in enumerate(gif_files, start=1)])
        embed.description = f"Available Luxury GIFs:\n{gif_list}"

        await ctx.send(embed=embed)
    else:
        await ctx.send("No luxury GIFs available in the shop at the moment.")

@bot.command()
@is_registered()
async def viewluxury(ctx, gif_id: int):
    with open('Deluxe_Profile/deluxe.txt', 'r') as file:
        allowed_user_ids = [line.strip() for line in file]

    user_id = str(ctx.author.id)

    if user_id not in allowed_user_ids:
        await ctx.send("You are not allowed to use this command.")
        return

    luxury_folder = 'Luxuries'
    gif_files = [f for f in os.listdir(luxury_folder) if f.endswith('.gif')]

    if 1 <= gif_id <= len(gif_files):
        gif_file = gif_files[gif_id - 1]
        gif_name = os.path.splitext(gif_file)[0]

        gif_path = os.path.join(luxury_folder, gif_file)

        embed = discord.Embed(title=f"Viewing Luxury GIF #{gif_id}: {gif_name}", color=0x00FFFF)
        embed.set_image(url=f"attachment://{gif_file}")

        await ctx.send(embed=embed, file=discord.File(gif_path))
    else:
        await ctx.send("Invalid GIF ID. Please provide a valid GIF ID to view a luxury GIF.")

@bot.command()
@is_registered()
async def applybg(ctx, bg_name: str):
    with open('Deluxe_Profile/deluxe.txt', 'r') as file:
        allowed_user_ids = [line.strip() for line in file]

    user_id = str(ctx.author.id)

    if user_id not in allowed_user_ids:
        await ctx.send("You are not allowed to use this command.")
        return

    json_content = read_json_content()
    luxury_folder = 'Luxuries'
    gif_files = [f for f in os.listdir(luxury_folder) if f.endswith('.gif')]
    bg_name_lower = bg_name.lower()

    if any(bg_name_lower == gif_file.lower()[:-4] for gif_file in gif_files):
        bg_file = next(gif_file for gif_file in gif_files if bg_name_lower == gif_file.lower()[:-4])
        bg_path = os.path.join(luxury_folder, bg_file)
        user_avatar_url = ctx.author.avatar.url if ctx.author.avatar else ctx.author.default_avatar.url
        profile_gif_path = os.path.join('Deluxe_Profile/profiles', f'{user_id}_profile.gif')

        if not os.path.exists(profile_gif_path):
            await ctx.send("You don't have an existing profile GIF. Please generate one first using `!generatedeluxeprofile`.")
            return

        loading_msg = await ctx.send(f"Applying {bg_name} to your Luxury profile ..")

        try:
            gif_filename = create_profile_gif(ctx, user_avatar_url, json_content, 'Deluxe_Profile/profiles', bg_path)

            await loading_msg.edit(content=f"Completed!")

            # Send the newly generated profile GIF
            await ctx.send(file=discord.File(gif_filename))

        except Exception as e:
            await loading_msg.edit(content=f"An error occurred while applying the background: {e}")

    else:
        await ctx.send("Invalid background name. Please provide a valid background GIF name.")

# # Command to render and update the user_profile.json
# @bot.command()
# @is_registered()
# async def renderdeluxe(ctx, target_user_id: int, new_title: str, new_rank: str):
#     json_content = read_json_content()

#     # Check if the target_user_id is in the JSON content
#     target_user_id_str = str(target_user_id)
#     if target_user_id_str in json_content:
#         # Update the rank and title for the specified user
#         json_content[target_user_id_str]["title"] = new_title
#         json_content[target_user_id_str]["rank"] = new_rank

#         # Save the updated JSON content back to the file
#         with open('Profiles/user_profiles.json', 'w') as file:
#             json.dump(json_content, file, indent=4)

#         await ctx.send(f"Updated rank and title for user ID {target_user_id}.")
#     else:
#         await ctx.send(f"User ID {target_user_id} not found in user_profiles.json.")


# Command to remove a user ID from the file
@bot.command(name="deluxeremove")
@is_registered()
async def removeuserid(ctx, user_id_to_remove: int):
    # Check if the user invoking the command has the specified user ID
    if ctx.author.id == 1128651413535346708:
        # Read the current user IDs from the file
        with open('Deluxe_Profile/deluxe.txt', 'r') as file:
            user_ids = [line.strip() for line in file]

        if str(user_id_to_remove) in user_ids:
            # Remove the provided user ID from the list
            user_ids.remove(str(user_id_to_remove))

            # Write the updated list back to the file
            with open('Deluxe_Profile/deluxe.txt', 'w') as file:
                for user_id in user_ids:
                    file.write(user_id + '\n')

            await ctx.send(f"User ID {user_id_to_remove} has been removed from the allowed user IDs.")
        else:
            await ctx.send(f"User ID {user_id_to_remove} was not found in the allowed user IDs list.")
    else:
        await ctx.send("You are not authorized to use this command.")


# Start the web server
keep_alive()

# Run the bot
bot.run(TOKEN)