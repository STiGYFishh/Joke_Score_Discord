import discord
from discord.ext import commands
from discord.utils import get
from datetime import datetime
import traceback
import random
import time
import json
import os


class JokeScore:
    def __init__(self, bot):
        self.bot = bot
        self.votes = {}  # trip nested dictionary boiiiiii
        self.expiry_time = 120  # Time in seconds until a vote expires
        self.json_file = "data/jokescore/jokes.json"
        self.today = datetime.now().strftime('%d-%m-%Y')

        self.leaderboard_titles = [
            "Most Boisterous Bois",
            "Biggest Dickheads",
            "Best Banter Board",
            "Silliest Sods",
            "Funniest Men"
        ]

        self.do_setup()

    def do_setup(self):
        try:
            if not os.path.isdir(os.path.dirname(self.json_file)):
                os.mkdir(os.path.dirname(self.json_file))
            if not os.path.isfile(self.json_file):
                with open(self.json_file, "w") as votes:
                    json.dump({}, votes)
            else:
                with open(self.json_file, "r") as votes:
                    self.votes = json.load(votes)
        except OSError:
            traceback.print_exc()

    async def save_votes(self):
        self.today = datetime.now().strftime('%d-%m-%Y')
        filename = os.path.basename(self.json_file)
        dir_path = os.path.dirname(self.json_file)
        daily_file = f"{dir_path}/{self.today}_{filename}"

        try:
            with open(self.json_file, "w") as votes:
                json.dump(self.votes, votes)
            if not os.path.isfile(daily_file):
                with open(daily_file, "w") as votes:
                    json.dump(self.votes, votes)
        except OSError as e:
            await self.bot.say(f"There Was an Error Whilst Writing the Vote Tally. A {type(e).__name__} was raised:")
            traceback.print_exc()

    @commands.command(name="jokescore",
                      aliases=["js", "joke"], pass_context=True)
    async def joke_score(self, ctx, mention: str, *, comment):
        """ Score everyone's jokes. """
        strongo = get(self.bot.get_all_emojis(), name='strongo')
        russles = get(self.bot.get_all_emojis(), name='russles')
        reactions = {
            russles:                     -3,
            "\N{ANGRY FACE}":            -2,
            "\N{UNAMUSED FACE}":         -1,
            "\N{SMIRKING FACE}":          1,
            "\N{FACE WITH TEARS OF JOY}": 2,
            strongo:                      3,
        }
        comment = "".join(comment)
        if len(comment) >= 500:
            await self.bot.way("Comment length too long: max 500 chars.")
            return False
        if len(ctx.message.mentions) == 0:
            await self.bot.say(
                "You forgot to mention anyone "
                f"{ctx.message.author.mention}, you knob")
            return False

        if len(ctx.message.mentions) > 1:
            await self.bot.say("One at a time mate...")
            return False

        user = ctx.message.mentions[0]
        poll = await self.bot.say("Vote with reactions: -3/-2/-1/+1/+2/+3.\n"
            f"Vote will expire in {self.expiry_time / 60} minutes!")

        if user.id not in self.votes:
            self.votes[user.id] = {"total": 0, "incidents": {}}

        self.votes[user.id]["incidents"][poll.id] = {
            "timestamp": int(time.time()),
            "comment": comment,
            "voters": {}
        }

        for reaction in reactions:
            await self.bot.add_reaction(poll, reaction)

        def check(reaction, check_user):
            return check_user.id != user.id and not check_user.bot

        while self.votes[user.id]["incidents"][poll.id]["timestamp"] + self.expiry_time > int(time.time()):
            react_event = await self.bot.wait_for_reaction(
                message=poll,
                check=check,
                emoji=reactions,
                timeout=5)

            if react_event:
                emoji = react_event.reaction.emoji
                if emoji in reactions:
                    self.votes[user.id]["incidents"][poll.id]["voters"][str(react_event.user)] = reactions[emoji]

        voters_fmt = ""
        total_score = 0
        for voter, score in self.votes[user.id]["incidents"][poll.id]["voters"].items():
            voters_fmt += f"*{voter}*: **{score:+d}**\n"
            total_score += score
        await self.bot.say(f'Joke Finished: "{comment}"\n\n{voters_fmt}\n'
            f'{"-"*32}\n*total*: **{total_score:+d}**')
        await self.bot.delete_message(poll)

        self.votes[user.id]["total"] += sum(self.votes[user.id]["incidents"][poll.id]["voters"].values())

        await self.save_votes()

    @commands.command(name="jscomment", aliases=["jsc"], pass_context=True)
    async def joke_score_comment(self, ctx, message_id: str, mention: str, *, comment):
        """ Edit a comment on a past joke, example: /jscomment 1234 @user 'new comment' """
        comment = "".join(comment)
        if len(comment) >= 500:
            await self.bot.say("Comment length too long: max 500 chars.")
            return False

        if len(ctx.message.mentions) == 0:
            await self.bot.say(
                "You forgot to mention anyone "
                f"{ctx.message.author.mention}, you knob")
            return False

        if len(ctx.message.mentions) > 1:
            await self.bot.say("One at a time mate...")
            return False

        user = ctx.message.mentions[0]
        try:
            old = self.votes[user.id]["incidents"][message_id]["comment"]
            self.votes[user.id]["incidents"][message_id]["comment"] = comment
            await self.save_votes()

            await self.bot.say(
                "Comment successfully updated!\n"
                f"```old comment: {old}```\n"
                f"```new comment: {comment}```")

        except KeyError:
            await self.bot.say(
                f"Comment not found for user: {user.display_name}"
                f"with message id: {message_id}")

    @commands.command(name="jsdelpoll", aliases=["jsdl"], pass_context=True)
    async def joke_score_delete_poll(self, ctx, mention: str, message_id: str):
        """ Delete a Previous Poll from a Users History """
        if len(ctx.message.mentions) == 0:
            await self.bot.say(
                "You forgot to mention anyone "
                f"{ctx.message.author.mention}, you knob")
            return False

        if len(ctx.message.mentions) > 1:
            await self.bot.say("One at a time mate...")
            return False

        user = ctx.message.mentions[0]
        try:
            poll_votes = sum(self.votes[user.id]["incidents"][message_id]["voters"].values())
            self.votes[user.id]["incidents"].pop(message_id)
            self.votes[user.id]["total"] -= poll_votes

            await self.save_votes()
            await self.bot.say("Poll successfully removed!")

        except KeyError:
            await self.bot.say(
                f"Poll not found for user: {user.display_name} "
                f"with message id: {message_id}")

    @commands.command(name="jsdeluser", aliases=["jsdu"], pass_context=True)
    async def joke_score_delete_user(self, ctx, mention: str):
        """ Delete a User and all of their Polls """
        if len(ctx.message.mentions) == 0:
            await self.bot.say(
                "You forgot to mention anyone "
                f"{ctx.message.author.mention}, you knob")
            return False

        if len(ctx.message.mentions) > 1:
            await self.bot.say("One at a time mate...")
            return False

        user = ctx.message.mentions[0]
        try:
            self.votes.pop(user.id)
            await self.save_votes()
            await self.bot.say("User successfully removed!")
        except KeyError:
            await self.bot.say(f"User not on file: {user.display_name}")

    @commands.command(name="jokeleaderboard", aliases=["jstable", "jslb", "jlb"], pass_context=False)
    async def joke_score_leaderboard(self):
        """ Show the Joke Score Leaderboard """
        embed = discord.Embed(
            colour=discord.Colour(0xc27c0e),
            url="https://github.com/STiGYFishh/Joke_Score_Discord/")

        embed.set_thumbnail(
            url="https://cdn.discordapp.com/emojis/296358609661591552.png?v=1")
        embed.set_footer(text="Joke Score Leaderboard")

        leaderboard_text = ""

        sorted_score = sorted(
            self.votes.keys(),
            key=lambda x: self.votes[x]['total'],
            reverse=True)

        for user_id in sorted_score:
            user = await self.bot.get_user_info(user_id)
            leaderboard_text += f"{user.display_name}: {self.votes[user_id]['total']}\n"

        embed.add_field(
            name=random.choice(self.leaderboard_titles),
            value=leaderboard_text,
            inline=False)

        await self.bot.say(embed=embed)

    @commands.command(name="jokescorereport", aliases=["jsr", "incident_report"], pass_context=True)
    async def joke_score_report(self, ctx, mention: str, sort="new"):
        """ Show a User's Joke History, example: /jokescorereport @user top """
        if len(ctx.message.mentions) == 0:
            await self.bot.say(
                "You forgot to mention anyone "
                f"{ctx.message.author.mention}, you knob")
            return False

        if len(ctx.message.mentions) > 1:
            await self.bot.say("One at a time mate...")
            return False

        user = ctx.message.mentions[0]

        try:
            if sort.lower() in ["new", "old", "top"]:
                if sort == "new":
                    sorted_incidents = sorted(
                        self.votes[user.id]["incidents"].keys(),
                        key=lambda x: self.votes[user.id]["incidents"][x]['timestamp'],
                        reverse=True)
                if sort == "old":
                    sorted_incidents = sorted(
                        self.votes[user.id]["incidents"].keys(),
                        key=lambda x: self.votes[user.id]["incidents"][x]['timestamp'])
                if sort == "top":
                    sorted_incidents = sorted(
                        self.votes[user.id]["incidents"].keys(),
                        key=lambda x: self.votes[user.id]["incidents"][x]['votes'],
                        reverse=True)

        except (KeyError, TypeError):
            await self.bot.say("This user has no incidents to report")
            return False

        def create_report_embed(user):
            embed = discord.Embed(
                colour=discord.Colour(0xc27c0e),
                url="https://github.com/STiGYFishh/Joke_Score_Discord/")

            embed.set_thumbnail(url=user.avatar_url)
            embed.set_footer(
                text=f"Joke Score Incident Report for {user.display_name}")

            return embed

        embed = create_report_embed(user)

        fields = 0
        report_embeds = [embed]
        for incident_id in sorted_incidents:
            if fields >= 25:
                embed = create_report_embed(user)
                report_embeds.append(embed)
                fields = 0

            date = datetime.fromtimestamp(
                int(self.votes[user.id]["incidents"][incident_id]["timestamp"])
            ).strftime("%c")

            votes = sum(self.votes[user.id]["incidents"][incident_id]["voters"].values())

            voters_fmt = ""
            for voter, score in self.votes[user.id]["incidents"][incident_id]["voters"].items():
                voters_fmt += f"*{voter}*: **{score:+d}**\n"

            comment = self.votes[user.id]["incidents"][incident_id]["comment"]

            report_text = (f"**Date**: {date}\n**Voters**:\n{voters_fmt}\n"
                f"**Votes Total**: *{votes}*\n**incident_id**: {incident_id}\n{'-'*32}")

            embed.add_field(name=comment, value=report_text, inline=False)
            fields += 1

        for embed in report_embeds:
            await self.bot.say(embed=embed)

    @commands.command(name="jokescorelocalbackup", aliases=["jsbak"], pass_context=True)
    async def jokescore_local_backup(self, ctx):
        """ Create a backup of the database and send the file as an attachment. """
        await self.save_votes()

        try:
            #  to be implemented when discord.py updated to the rewrite
            #  await ctx.message.channel.send('Copy of JokeScore JSON File', file=discord.File(self.json_file, 'jokescore_backup.json'))
            await self.bot.send_file(ctx.message.channel,
                self.json_file,
                filename="jokescore_backup.json",
                content="Copy of Jokescore JSON file.")
        except (OSError, discord.HTTPException):
            await self.bot.say(f"An Error Ocurred Whilst Sending the Backup File. A {type(e).__name__} was raised:")
            traceback.print_exc()


def setup(bot):
    bot.add_cog(JokeScore(bot))
