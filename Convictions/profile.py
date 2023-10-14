import os
from PIL import Image, ImageDraw, ImageFont, ImageOps
import discord
import requests
from io import BytesIO
import json

PROFILES_FOLDER = 'Profiles'
BACKGROUND_FOLDER = 'Assets/Backgrounds/'  # Folder containing background images

def create_profile_image(avatar_url, username, title, default_background_path=None):
    # Create a blank 1920x1080 background image
    profile_image = Image.new('RGBA', (1440, 920), (255, 255, 255, 255))  # 1920x1080 pixels, white background

    if default_background_path:
        # Open and load the default background image
        background = Image.open(default_background_path)

        # Resize the background image to 1920x1080 pixels using NEAREST resampling
        background = background.resize((1440, 920), Image.NEAREST)

        # Paste the default background image onto the blank image
        profile_image.paste(background, (0, 0))

    # Download the avatar image from the URL
    response = requests.get(avatar_url)
    if response.status_code == 200:
        avatar = Image.open(BytesIO(response.content))
        # Resize the avatar to a larger size with Lanczos resampling
        avatar = avatar.resize((400, 400), Image.LANCZOS)  # Adjust size as needed

        # Create a circular mask for the avatar
        mask = Image.new('L', avatar.size, 0)
        draw = ImageDraw.Draw(mask)
        draw.ellipse((0, 0, avatar.size[0], avatar.size[1]), fill=255)

        # Apply the circular mask to the avatar
        avatar = Image.composite(avatar, Image.new('RGBA', avatar.size), mask)

        # Paste the avatar onto the profile image at the top left corner
        profile_image.paste(avatar, (0, 0), avatar)  # Adjust position as needed

        # Calculate the size and position of the semi-transparent box
        box_width = avatar.width
        box_height = 120  # Adjust the box height as needed
        box_x = 0  # Place the box at the top left corner
        box_y = avatar.height  # Position the box below the avatar

        # Create a more transparent black box
        box = Image.new('RGBA', (box_width, box_height), (0, 0, 0, 128))  # Adjust alpha (4th value) for transparency
        profile_image.paste(box, (box_x, box_y), box)  # Paste the box onto the profile image

        # Use a default font if a custom font is not found
        try:
            font_path = os.path.join('Fonts', 'Poppins.ttf')
            font = ImageFont.truetype(font_path, 48)  # Larger font for username
            placeholder_font = ImageFont.truetype(font_path, 32)  # Smaller font for placeholder title
        except OSError:
            font = ImageFont.load_default()
            placeholder_font = ImageFont.load_default()

        # Create a drawing context for the profile image
        draw = ImageDraw.Draw(profile_image)

        # Text color and positioning
        text_color = (0, 255, 255)  # Neon cyan text color
        outline_color = (0, 0, 0)  # Black outline color
        username_x = box_x + 10  # Adjust the username position as needed
        username_y = box_y + 10
        title_x = box_x + 10  # Adjust the title position as needed
        title_y = box_y + box_height - 40  # Adjust the title position as needed

        # Draw username and title with black outline
        draw.text((username_x - 1, username_y), username, fill=outline_color, font=font)
        draw.text((username_x + 1, username_y), username, fill=outline_color, font=font)
        draw.text((username_x, username_y - 1), username, fill=outline_color, font=font)
        draw.text((username_x, username_y + 1), username, fill=outline_color, font=font)

        draw.text((title_x - 1, title_y), title, fill=outline_color, font=placeholder_font)
        draw.text((title_x + 1, title_y), title, fill=outline_color, font=placeholder_font)
        draw.text((title_x, title_y - 1), title, fill=outline_color, font=placeholder_font)
        draw.text((title_x, title_y + 1), title, fill=outline_color, font=placeholder_font)

        # Draw username and title in neon cyan over the black outline
        draw.text((username_x, username_y), username, fill=text_color, font=font)
        draw.text((title_x, title_y), title, fill=text_color, font=placeholder_font)

        # # Add copyright information at the top
        # copyright_text = "© 1128651413535346708 || 2023"
        # copyright_x = profile_image.width - 500  # Place at the top left corner
        # copyright_y = 4  # Adjust the vertical position as needed
        # draw.text((copyright_x, copyright_y), copyright_text, fill=outline_color, font=placeholder_font)

    return profile_image




async def generate_profile(ctx, user_profiles):
    user_id = str(ctx.author.id)

    if user_id in user_profiles:
        embed = discord.Embed(
            title="Profile Creation Failed",
            description="You already have a profile.",
            color=discord.Color.red()
        )
        await ctx.send(embed=embed)
    else:
        avatar_url = ctx.author.avatar.url if ctx.author.avatar else ctx.author.default_avatar.url
        username = ctx.author.name
        title = "Title Placeholder"
        rank = "Noob"  # Set the initial rank here

        # Set the default background image path here
        default_background_path = os.path.join(BACKGROUND_FOLDER, '11.png')

        # Set the default background URL here
        default_background_url = './Assets/Backgrounds/11.png'

        profile_image = create_profile_image(avatar_url, username, title, default_background_path)

        image_path = os.path.join(PROFILES_FOLDER, f'{user_id}.png')
        profile_image.save(image_path)

        user_profiles[user_id] = {
            'image_path': image_path,
            'title': title,
            'background_url': default_background_url,
            'rank': rank  # Include the rank field in the user's profile
        }

        # Save the entire user_profiles dictionary to the JSON file
        json_path = os.path.join(PROFILES_FOLDER, 'user_profiles.json')
        with open(json_path, 'w') as json_file:
            json.dump(user_profiles, json_file, indent=4)

        embed = discord.Embed(
            title="Profile Created",
            description="Your profile has been successfully created!",
            color=discord.Color.green()
        )
        await ctx.send(embed=embed)


async def view_profile(ctx, user_profiles, user_mention=None):
    if not user_mention:
        user_mention = ctx.author.mention

    user_id = str(ctx.author.id)

    if user_mention.startswith('<@') and user_mention.endswith('>'):
        user_id = user_mention.strip('<@!>')

    if user_id in user_profiles:
        profile_data = user_profiles.get(user_id)

        # Check if 'image_path' key is present in profile_data
        if profile_data and 'image_path' in profile_data:
            # Load the user's profile image with the updated title
            profile_image = Image.open(profile_data['image_path'])

            rank = profile_data.get('rank', 'No Rank')  # Get the user's rank or use 'No Rank' if not found

            # Create a drawing context for the profile image
            draw = ImageDraw.Draw(profile_image)

            # Use a default font if a custom font is not found
            try:
                font_path = os.path.join('Fonts', 'Poppins.ttf')
                font = ImageFont.truetype(font_path, 48)  # Larger font for username
            except OSError:
                font = ImageFont.load_default()

            # Text color and positioning
            text_color = (0, 255, 255)  # Neon cyan text color
            outline_color = (0, 0, 0)  # Black outline color

            # Calculate the size and position of the semi-transparent black box
            box_width = profile_image.width
            box_height = 100  # Adjust the box height as needed
            box_x = 0  # Place the box at the top left corner
            box_y = profile_image.height - box_height  # Position the box at the bottom

            # Create a more transparent black box
            box = Image.new('RGBA', (box_width, box_height), (0, 0, 0, 128))  # Adjust alpha (4th value) for transparency (0 is fully transparent)
            profile_image.paste(box, (box_x, box_y), box)  # Paste the box onto the profile image

            # Calculate the center position for the Rank text within the box
            rank_x = box_width // 2 - 75  # Center horizontally
            rank_y = box_y + (box_height - 48) // 2  # Center vertically (adjust text size as needed)

            # Draw rank with black outline
            draw.text((rank_x - 1, rank_y), rank, fill=outline_color, font=font)
            draw.text((rank_x + 1, rank_y), rank, fill=outline_color, font=font)
            draw.text((rank_x, rank_y - 1), rank, fill=outline_color, font=font)
            draw.text((rank_x, rank_y + 1), rank, fill=outline_color, font=font)

            # Draw rank in neon cyan over the black outline
            draw.text((rank_x, rank_y), rank, fill=text_color, font=font)

            # Add neon cyan lightning-style effects at the top and bottom edges
            lightning_color = (0, 255, 255)  # Neon cyan lightning color
            top_lightning_height = 10  # Height of the top lightning effect
            bottom_lightning_height = 10  # Height of the bottom lightning effect

            # Draw neon cyan lines at the top edge
            for y in range(top_lightning_height):
                for x in range(profile_image.width):
                    if x % 2 == 0:  # Draw lines at even x-coordinates for a segmented effect
                        profile_image.putpixel((x, y), lightning_color)

            # Draw neon cyan lines at the bottom edge
            for y in range(profile_image.height - bottom_lightning_height, profile_image.height):
                for x in range(profile_image.width):
                    if x % 2 == 1:  # Draw lines at odd x-coordinates for a segmented effect
                        profile_image.putpixel((x, y), lightning_color)

            # Send the profile image as a message attachment
            with BytesIO() as image_binary:
                profile_image.save(image_binary, format="PNG")
                image_binary.seek(0)
                file = discord.File(image_binary, filename="profile.png")

            await ctx.send(file=file)
        else:
            embed = discord.Embed(
                title="Profile Incomplete",
                description="Your profile data is incomplete. Please recreate your profile using `generateprofile`.",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
    else:
        embed = discord.Embed(
            title="Profile Not Found",
            description="The user's profile was not found.",
            color=discord.Color.red()
        )
        await ctx.send(embed=embed)



async def delete_profile(ctx, user_profiles):
    user_id = str(ctx.author.id)

    if user_id in user_profiles:
        os.remove(user_profiles[user_id]['image_path'])
        user_profiles.pop(user_id, None)  # Remove the user's profile

        # Save the updated user_profiles dictionary to the JSON file
        json_path = os.path.join(PROFILES_FOLDER, 'user_profiles.json')
        with open(json_path, 'w') as json_file:
            json.dump(user_profiles, json_file, indent=4)

        embed = discord.Embed(
            title="Profile Deleted",
            description="Your profile has been successfully deleted. You can create a new profile using `generateprofile`.",
            color=discord.Color.green()
        )
        await ctx.send(embed=embed)
    else:
        embed = discord.Embed(
            title="No Profile Found",
            description="You don't have a profile to delete. You can create a new profile using `generateprofile`.",
            color=discord.Color.red()
        )
        await ctx.send(embed=embed)