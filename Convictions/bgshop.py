import discord
import os
import asyncio

# Define background prices for all 75 images (adjust as needed)
background_prices = {
    1: 1000,
    2: 2000,
    3: 1500,
    4: 2500,
    5: 2500,
    6: 4500,
    7: 8000,
    8: 9000,
    9: 2000,
    10: 1000,
    11: 9999,
    12: 3000,
    13: 3500,
    14: 6000,
    15: 5500,
    16: 4000,
    17: 7000,
    18: 5500,
    19: 3000,
    20: 4000,
    21: 3500,
    22: 4000,
    23: 1000,
    24: 9999,
    25: 3000,
    26: 3500,
    27: 6000,
    28: 5500,
    29: 4000,
    30: 7000,
    31: 5500,
    32: 3000,
    33: 4000,
    34: 3500,
    35: 4000,
    36: 7000,
    37: 5500,
    38: 3000,
    39: 4000,
    40: 3500,
    41: 4000,
    42: 5000,
    43: 8000,
    44: 4000,
    45: 6000,
    46: 5269,
    47: 4523,
    48: 6000,
    49: 5269,
    50: 4523,
    51: 6000,
    52: 4000,
    53: 1500,
    54: 2000,
    55: 4000,
    56: 8000,
    57: 9000,
    58: 4000,
    59: 7500,
    60: 4150,
    61: 8000,
    62: 4000,
    63: 9999,
    64: 15000,
    65: 12000,
    66: 8000,
    67: 12000,
    68: 12000,
    69: 5600,
    70: 7500,
    71: 8600,
    72: 4500,
    73: 9990,
    74: 10000,
    75: 20000
}

# Define background descriptions (adjust as needed)
background_descriptions = {
    1: "Gojo at Sky",
    2: "MUI Goku",
    3: "UI Goku",
    4: "Broly",
    5: "Asta",
    6: "Sasuke",
    7: "Akatsuki sasuke",
    8: "Giyu Tomioka",
    9: "Sasuke X Naruto",
    10: "GTR",
    11: "Haxx Disaster",
    12: "Todoro The neighbour ",
    13: "Red haired Shanks",
    14: "Yuji Itadori",
    15: "Vegeta",
    16: "miles spiderman",
    17: "Solo leveling",
    18: "Satoru Gojo final moments ",
    19: "goku black",
    20: "Itachi",
    21: "Ichigo",
    22: "genshin duo sexy",
    23: "seishiro Nagi",
    24: "Ray-Oxie",
    25: "sayans",
    26: "Gradient abstract material theme",
    27: "dragon Emperor",
    28: "Erza Scarlett",
    29: "COC",
    30: "Edward elrich ",
    31: "Yokai rise: nura",
    32: "denji: chainsaw man",
    33: "makima: control devil",
    34: "ryuk: death note ",
    35: "dio brando ",
    36: "dio x kujo",
    37: "rias babe  gremory",
    38: "starrk",
    39: "hunter",
    40: "kamadoe tanziro",
    41: "xiayou",
    42: "vasto lorde ichigo",
    43: "ANti-spiral",
    44: "Umiko Jabami",
    45: "Ryukendo",
    46: "Goku in nimbus",
    47: "Sasuke Naruto",
    48: "Albedo",
    49: "Honored one",
    50: "uchihas",
    51: "miku",
    52: "miku 2",
    53: "sexy waifu",
    54: "automata sexy",
    55: "Kanon",
    56: "Messi Lionel",
    57: "ronaldo 7",
    58: "AJ styles",
    59: "Muichiro demon slayer",
    60: "Pikachu",
    61: "Pikacamp",
    62: "Kokushibow",
    63: "Smexy anime waifu material",
    64: "Rias gremory",
    65: "marin kitagawa thigh",
    66: "egirl sexy version",
    67: "Killua",
    68: "L",
    69: "Boob Lordess 2",
    70: "Makima",
    71: "denji puccita chainsaw form",
    72: "power with silicon boobs",
    73: "og duo beyblade metal",
    74: "Otwo cute AF",
    75: "Nba"
}

async def show_background_shop(ctx, background_folder, user_balance,  filtered_backgrounds=None):
    background_files = os.listdir(background_folder)

 

    items_per_page = 5
    page_number = 1

    message = None  # Store the message object for editing

    while True:
        start_index = (page_number - 1) * items_per_page
        end_index = start_index + items_per_page

        backgrounds = []

        for index, file in enumerate(background_files[start_index:end_index]):
            background_id = start_index + index + 1  # Adjust the ID based on the start index
            price = background_prices.get(background_id, "N/A")
            price = int(price)  # Convert price to an integer
            description = background_descriptions.get(background_id, "No Description")

            # Check if the user has enough balance to buy the background
            if user_balance >= price:
                availability = "Available"
            else:
                availability = "Not Enough Redants"

            backgrounds.append({
                'name': f'Background {background_id}: {description}',
                'value': f'ID: {background_id}\nPrice: {price} redants\nAvailability: {availability}',
                'inline': True
            })

        embed = discord.Embed(
            title=f'Profile Background Shop (Page {page_number})',
            description='do **e!buybg [id]** to buy, Here are the available backgrounds:',
            color=0x00ff00  # Customize the color
        )

        for field in backgrounds:
            embed.add_field(name=field['name'], value=field['value'], inline=field['inline'])

        if message is None:
            message = await ctx.send(embed=embed)
        else:
            await message.edit(embed=embed)

        if page_number > 1:
            await message.add_reaction("⬅️")  # Left arrow reaction

        if end_index < len(background_files):
            await message.add_reaction("➡️")  # Right arrow reaction

        def check(reaction, user):
            return user == ctx.author and str(reaction.emoji) in ["⬅️", "➡️"]

        try:
            reaction, _ = await ctx.bot.wait_for("reaction_add", timeout=60, check=check)
            await message.clear_reactions()

            if reaction.emoji == "⬅️" and page_number > 1:
                page_number -= 1
            elif reaction.emoji == "➡️" and end_index < len(background_files):
                page_number += 1
        except asyncio.TimeoutError:
            break  # Stop pagination if no reaction is added within 60 seconds

