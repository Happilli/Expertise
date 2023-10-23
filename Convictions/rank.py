import discord
import json
import asyncio
from PIL import Image, ImageDraw, ImageFont, ImageOps
import io

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

    async def get_leaderboard(self, top=10):
        sorted_leaderboard = sorted(self.data.items(), key=lambda x: x[1]["wins"], reverse=True)
        headers = ["Rank", "Username", "Wins", "Losses", "Win Rate"]
        column_percentages = [15, 35, 15, 15, 20]

        background_image = Image.open("Assets/lb.jpg")
        draw = ImageDraw.Draw(background_image)
        font = ImageFont.truetype("Fonts/Poppins.ttf", size=40)
        text_color = (255, 255, 255)
        column_positions = [int(1920 * sum(column_percentages[:i]) / 100) for i in range(len(column_percentages))]
        y = 40

        for i, header in enumerate(headers):
            x = column_positions[i]
            header_width = len(header) * 15
            x -= header_width // 2

            if header == "Rank":
                header_width = 15 * 2
                x += 38

            if header == "Username":
                header_width = 35 * 2
                x -= 75

            draw.text((x, y), header, fill=text_color, font=font)
            if i > 0:
                draw.line([(x, 0), (x, 1080)], fill=text_color, width=2)

        y += 60
        draw.line([(0, y), (1920, y)], fill=text_color, width=2)
        y += 20

        for idx, (user_id, stats) in enumerate(sorted_leaderboard[:top], start=1):
            user = await self.bot.fetch_user(int(user_id))
            username = user.name if user else f"{user_id}"
            wins, losses = stats["wins"], stats["losses"]
            win_rate = wins / (wins + losses) * 100 if wins + losses > 0 else 0

            for i, cell in enumerate([str(idx), username, str(wins), str(losses), f"{win_rate:.2f}%"]):
                x = column_positions[i]
                cell_width = len(cell) * 15
                x -= cell_width // 2

                if headers[i] == "Rank":
                    cell_width = 15 * 2
                    x += 30

                if headers[i] == "Username":
                    cell_width = 35 * 2
                    x += 15

                draw.text((x, y), cell, fill=text_color, font=font)

            y += 60

        img_byte_array = io.BytesIO()
        background_image = ImageOps.expand(background_image, border=20, fill=(0, 0, 0))
        background_image.save(img_byte_array, format="PNG")
        img_byte_array.seek(0)

        return img_byte_array

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

    async def get_top_player(self):
        sorted_leaderboard = sorted(self.data.items(), key=lambda x: x[1]["wins"], reverse=True)
        if sorted_leaderboard:
            top_player_id, top_player_stats = sorted_leaderboard[0]
            user = await self.bot.fetch_user(int(top_player_id))
            if user:
                top_player_name = user.name
                top_player_wins = top_player_stats["wins"]
                top_player_losses = top_player_stats["losses"]
                top_player_win_rate = (top_player_wins / (top_player_wins + top_player_losses)) * 100
                return f"Player: {top_player_name}, Wins: {top_player_wins}, Losses: {top_player_losses}, Win Rate: {top_player_win_rate:.2f}%"
        return "No top player found"
