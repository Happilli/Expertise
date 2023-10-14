import discord
import json
import asyncio

class RankFlow:
    def __init__(self, bot):
        self.bot = bot
        self.data = self.load_data()

    def load_data(self):
        try:
            with open("Assets/storage/rank.json", "r") as file:
                data = json.load(file)
        except FileNotFoundError:
            data = {}
        return data

    def save_data(self):
        with open("Assets/storage/rank.json", "w") as file:
            json.dump(self.data, file, indent=4)

    def start_rank_flow(self, user_id):
        if user_id not in self.data:
            self.data[user_id] = {"wins": 0, "losses": 0}
            self.save_data()

    def update_stats(self, user_id, win=False):
        if user_id not in self.data:
            return "Please use 'startrankflow' command to initialize your data."

        if win:
            self.data[user_id]["wins"] += 1
        else:
            self.data[user_id]["losses"] += 1

        self.save_data()

    def get_stats(self, user_id):
        if user_id in self.data:
            stats = self.data[user_id]
            return f"Player {user_id}: Wins: {stats['wins']} Losses: {stats['losses']}"
        else:
            return "Player not found."

    def get_leaderboard(self, top=10):
        sorted_leaderboard = sorted(self.data.items(), key=lambda x: x[1]["wins"], reverse=True)

        embed = discord.Embed(
            title="🏆 Leaderboard 🏆",
            description="Top Players",
            color=discord.Color.gold()
        )

        leaderboard_text = ""

        for idx, (user_id, stats) in enumerate(sorted_leaderboard[:top], start=1):
            user = discord.utils.get(self.bot.get_all_members(), id=int(user_id)) or f"<@{user_id}>"
            wins, losses = stats["wins"], stats["losses"]

            leaderboard_text += f"{idx}. {user} - **W: {wins}** \\ **L: {losses}**\n"
            
            # Add a horizontal line after each player's entry
            leaderboard_text += "―――――――――――――――――――\n"

        embed.add_field(name="\u200B", value=leaderboard_text, inline=False)

        return embed

    async def battle_log(self, ctx, opponent: discord.User, wins: int):
        sender_id = str(ctx.author.id)
        opponent_id = str(opponent.id)

        if sender_id == opponent_id:
            return "You can't log a battle with yourself."

        if sender_id not in self.data or opponent_id not in self.data:
            return "Both players must initialize their rank data using `!startrankflow`."

        log_message = await ctx.send(f"{opponent.mention}, {ctx.author.mention} wants to log {wins} wins to you. React with ✅ to accept, ❌ to reject.")
        await log_message.add_reaction("✅")
        await log_message.add_reaction("❌")

        def check(reaction, user):
            return user == opponent and str(reaction.emoji) in ["✅", "❌"] and reaction.message == log_message

        try:
            reaction, user = await self.bot.wait_for("reaction_add", timeout=60.0, check=check)

            if str(reaction.emoji) == "✅":
                self.data[sender_id]["wins"] += wins
                self.data[opponent_id]["losses"] += wins
                self.save_data()
                return f"Battle log accepted! {ctx.author.mention} gained {wins} wins, and {opponent.mention} gained {wins} losses."
            elif str(reaction.emoji) == "❌":
                return f"Battle log rejected. No changes were made."

        except asyncio.TimeoutError:
            return "Battle log request timed out. No changes were made."
