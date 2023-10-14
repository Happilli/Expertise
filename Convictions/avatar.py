import discord

async def show_avatar(ctx, user: discord.User = None):
    try:
        user = user or ctx.author
        avatar_url = user.avatar.url if user.avatar else user.default_avatar.url

        embed = discord.Embed(title=f"{user.name}'s Avatar", color=discord.Color.blue())
        embed.set_image(url=avatar_url)
        embed.add_field(name="Avatar URL", value=f"[Click Here]({avatar_url})")
        
        await ctx.send(embed=embed)
    except Exception as e:
        await ctx.send(f"An error occurred: {str(e)}")
