import os
from PIL import Image, ImageDraw, ImageFont, ImageOps
import discord
import requests
from io import BytesIO
import json






PROFILES_FOLDER = 'Profiles'
BACKGROUND_FOLDER = 'Assets/Backgrounds/'

def create_profile_image(avatar_url, username, title, rank, default_background_path=None, default_card_image_path=None):
  profile_image = Image.new('RGBA', (1440, 920), (255, 255, 255, 255))

  if default_background_path:
      background = Image.open(default_background_path)
      separator_y = int(profile_image.height * 0.6)  # 60% from the top

      # Ensure the background covers the top half without resizing
      if background.size != (profile_image.width, separator_y):
          background = background.resize((profile_image.width, separator_y))

      profile_image.paste(background, (0, 0))

      bottom_half = Image.new('RGBA', (profile_image.width, profile_image.height - separator_y), (65, 65, 58, 255))

      profile_image.paste(bottom_half, (0, separator_y))

  response = requests.get(avatar_url)
  if response.status_code == 200:
      avatar = Image.open(BytesIO(response.content))
      avatar_size = (300, 300)
      avatar_x = 20
      avatar_y = separator_y - avatar_size[1] // 2
      mask = Image.new('L', avatar_size, 0)
      draw = ImageDraw.Draw(mask)
      draw.ellipse((0, 0, avatar_size[0], avatar_size[1]), fill=255)
      avatar = avatar.resize(avatar_size, Image.NEAREST)
      avatar.putalpha(mask)
      profile_image.paste(avatar, (avatar_x, avatar_y), avatar)

  # Load the card image if provided
  if default_card_image_path:
      card_image = Image.open(default_card_image_path)
      card_image = card_image.convert("RGBA")
      card_image = card_image.resize((360, 620), Image.NEAREST)
      card_image = card_image.rotate(15, expand=True)
      card_x = 900
      card_y = separator_y - int(card_image.height * 0.60)

      profile_image.paste(card_image, (card_x, card_y), card_image)

  font_path = os.path.join('Fonts', 'Poppins.ttf')

  username_font = ImageFont.truetype(font_path, 48)
  title_font = ImageFont.truetype(font_path, 42)
  rank_font = ImageFont.truetype(font_path, 36)

  draw = ImageDraw.Draw(profile_image)
  text_color = (255, 255, 255)
  outline_color = (0, 0, 0)

  username_y = separator_y + 140
  title_y = username_y + 50
  rank_y = title_y + 45

  draw.text((avatar_x, username_y), username, fill=text_color, font=username_font)
  draw.text((avatar_x, title_y), title, fill=text_color, font=title_font)
  draw.text((avatar_x, rank_y), rank, fill=text_color, font=rank_font)

  return profile_image



async def generate_profile(ctx, user_profiles, default_card_image_path=None, default_card_url=None):
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

      # Set the default titled rectangle image path or use the provided path
      if not default_card_image_path:
          default_card_image_path = './Assets/Cards/1.jpg'

      # Set the default card URL or use the provided URL
      if not default_card_url:
          default_card_url = default_card_image_path

      profile_image = create_profile_image(avatar_url, username, title, rank, default_background_path, default_card_image_path)

      image_path = os.path.join(PROFILES_FOLDER, f'{user_id}.png')
      profile_image.save(image_path)

      user_profiles[user_id] = {
          'image_path': image_path,
          'title': title,
          'background_url': default_background_url,
          'rank': rank,  # Include the rank field in the user's profile
          'card_url': default_card_url,  # Include card URL in the user's profile
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
          # Load the user's profile image
          profile_image = Image.open(profile_data['image_path'])

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