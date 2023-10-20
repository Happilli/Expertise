import os
from PIL import Image, ImageDraw, ImageFont, ImageOps, ImageFilter
import discord
import requests
from io import BytesIO
import json
import datetime

PROFILES_FOLDER = 'Profiles'
BACKGROUND_FOLDER = 'Assets/Backgrounds/'

def create_profile_image(avatar_url, username, title, rank, default_background_path=None, default_card_image_path=None):
    profile_image = Image.new('RGBA', (1440, 920), (255, 255, 255, 255))

    if default_background_path:
        background = Image.open(default_background_path)
        separator_y = int(profile_image.height * 0.6)

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

        border_thickness = 12
        border_size = (avatar_size[0] + border_thickness * 2, avatar_size[1] + border_thickness * 2)
        border_mask = Image.new('L', border_size, 0)
        border_draw = ImageDraw.Draw(border_mask)
        border_draw.ellipse((0, 0, border_size[0], border_size[1]), fill=255)
        avatar_with_border = Image.new('RGBA', border_size, (0, 0, 0, 0))
        avatar_with_border.paste(avatar, (border_thickness, border_thickness), avatar)
        avatar_with_border.putalpha(border_mask)
        profile_image.paste(avatar_with_border, (avatar_x - border_thickness, avatar_y - border_thickness), avatar_with_border)

    dragon_shadow_path = 'Assets/dragon_shadow.png'
    dragon_shadow = Image.open(dragon_shadow_path)
    new_height = int(200 * 0.8)
    new_width = int(dragon_shadow.width * (new_height / dragon_shadow.height))
    dragon_shadow = dragon_shadow.resize((new_width, new_height))

    dragon_shadow_x = avatar_x + int(avatar_size[0] * 0.20)
    dragon_shadow_y = avatar_y + avatar_size[1] + 40
    profile_image.paste(dragon_shadow, (dragon_shadow_x, dragon_shadow_y), dragon_shadow)

    if default_card_image_path:
        card_image = Image.open(default_card_image_path)
        card_image = card_image.convert("RGBA")
        card_image = card_image.resize((390, 690), Image.NEAREST)

        frame_thickness = 10
        frame_size = (card_image.width + frame_thickness * 2, card_image.height + frame_thickness * 2)
        framed_card = Image.new("RGBA", frame_size, (0, 0, 0, 255))

        card_image = card_image.rotate(-10, expand=True)
        framed_card = framed_card.rotate(-10, expand=True)

        framed_card.paste(card_image, (frame_thickness, frame_thickness), card_image)
        card_x = 900
        card_y = separator_y - int(framed_card.height * 0.60)
        profile_image.paste(framed_card, (card_x, card_y), framed_card)

    font_path = os.path.join('Fonts', 'Poppins.ttf')
    username_font = ImageFont.truetype(font_path, 56)
    title_font = ImageFont.truetype(font_path, 42)
    rank_font = ImageFont.truetype(font_path, 36)
    datetime_font = ImageFont.truetype(font_path, 32)

    draw = ImageDraw.Draw(profile_image)
    text_color = (255, 255, 255)
    outline_color = (0, 0, 0)

    username_x = avatar_x + avatar_size[0] + 30
    username_y = avatar_y + 135
    title_x = username_x
    title_y = username_y + 60
    rank_x = username_x
    rank_y = title_y + 45

    username_font_color = (255, 255, 255)
    username_outline_color = (0, 0, 0)

    title_x = username_x
    title_y = username_y + 60
    title_font_color = (255, 255, 255)
    title_outline_color = (0, 0, 0)

    rank_x = username_x
    rank_y = title_y + 45
    rank_font_color = (255, 255, 255)
    rank_outline_color = (0, 0, 0)

    draw.text((username_x, username_y), username, fill=username_font_color, font=username_font, stroke_width=2, outline=username_outline_color)
    draw.text((title_x, title_y), title, fill=title_font_color, font=title_font, stroke_width=2, outline=title_outline_color)
    draw.text((rank_x, rank_y), rank, fill=rank_font_color, font=rank_font, stroke_width=2, outline=rank_outline_color)

    draw.text((username_x, username_y), username, fill=text_color, font=username_font)
    draw.text((title_x, title_y), title, fill=text_color, font=title_font)
    draw.text((rank_x, rank_y), rank, fill=text_color, font=rank_font)

    current_datetime = datetime.datetime.now().strftime('joined %Y/%m/%d')
    datetime_x = 1440 - 120 - len(current_datetime) * 12
    datetime_y = 920 - 60

    draw.text((datetime_x, datetime_y), current_datetime, fill=text_color, font=datetime_font)

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
        rank = "Noob"
        default_background_path = os.path.join(BACKGROUND_FOLDER, '11.png')
        default_background_url = './Assets/Backgrounds/11.png'

        if not default_card_image_path:
            default_card_image_path = './Assets/Cards/1.jpg'

        if not default_card_url:
            default_card_url = default_card_image_path

        profile_image = create_profile_image(avatar_url, username, title, rank, default_background_path, default_card_image_path)

        image_path = os.path.join(PROFILES_FOLDER, f'{user_id}.png')
        profile_image.save(image_path)

        user_profiles[user_id] = {
            'image_path': image_path,
            'title': title,
            'background_url': default_background_url,
            'rank': rank,
            'card_url': default_card_url
        }

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

        if profile_data and 'image_path' in profile_data:
            profile_image = Image.open(profile_data['image_path'])

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
        user_profiles.pop(user_id, None)

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
