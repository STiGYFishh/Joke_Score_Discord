import discord
from discord.ext import commands
from datetime import datetime
import asyncio
import traceback
import random
import time
import json
import os

class JokeScore:
    def __init__(self, bot):
        self.bot = bot
        self.votes = {} # trip nested dictionary boiiiiii
        self.vote_messages = {} # nested dict boiiii
        self.reactions = ['\U0001F53C','\U0001F53D']
        self.expiry_time = 120 # Time in seconds until a vote expires

        self.leaderboard_titles = [\
                "Most Boisterous Bois",\
                "Biggest Dickheads",\
                "Best Banter Board",\
                "Silliest Sods",\
                "Funniest Men"
                ]

        self.do_setup()

    def do_setup(self):
        try:
            if not os.path.isfile("joke_score.json"):
                with open("joke_score.json", "w") as file:
                    json.dump({}, file)
            else:
                with open("joke_score.json", "r") as file:
                    votes = json.load(file)
                    self.votes = votes
        except OSError:
            traceback.print_exc()

    async def save_votes(self): 
        try:
            with open("joke_score.json", "w") as file:
                json.dump(self.votes, file)
        except OSError:
            await self.bot.say("An Error occured whilst writing the vote tally.")
            traceback.print_exc()

    @commands.command(name="jokescore", aliases=["js","joke"], pass_context=True)
    async def joke_score(self , ctx, mention: str, bonus = 0, comment = "", *args):
        """ Score everyone's jokes. """
        if len(ctx.message.mentions) == 0:
            await self.bot.say("You forgot to mention anyone "
                                f"{ctx.message.author.mention}, you knob")
            return False

        if len(ctx.message.mentions) > 1:
            await self.bot.say("One at a time mate...")
            return False

        if bonus > 10 or bonus < -10:
            await self.bot.say("Valid Bonus Values are between -10 and 10")
            return False
			
		comment = " ".join(comment, *args)

        user = ctx.message.mentions[0]
        react_message = ctx.message

        if not user.id in self.votes.keys():
            self.votes[user.id] = {"total":bonus, "incidents":{}}
        else:
            self.votes[user.id]["total"] += bonus

        self.vote_messages[react_message.id] = {\
                "user_id":user.id,\
                "timestamp":int(time.time()),\
                "comment": comment,\
                "votes": bonus,\
                "bonus": bonus\
                }

        self.votes[user.id]["incidents"][react_message.id] =\
                self.vote_messages[react_message.id]

        for reaction in self.reactions:
            await self.bot.add_reaction(react_message, reaction)

        expire_message = await self.bot.say("Vote will expire in "
            f"{self.expiry_time / 60} minutes!")

        await asyncio.sleep(self.expiry_time)
        await self.bot.edit_message(expire_message,\
                f"This Joke Poll has Expired the Message ID was: {react_message.id}")

        self.vote_messages[react_message.id].pop("user_id")
        self.votes[user.id]["incidents"][react_message.id] =\
                self.vote_messages[react_message.id]

        self.vote_messages.pop(react_message.id)

        await self.bot.delete_message(react_message)
        await self.save_votes()
            

    async def on_reaction_add(self, reaction, user): 
        if reaction.message.id in self.vote_messages.keys(): 
        #Check the message is a vote poll created by the bot.
            if not user.bot and user.id != self.bot.user.id: 
                #Make sure bots can't vote and the initial bot reactions aren't counted
                user_id = self.vote_messages[reaction.message.id]["user_id"]

                if reaction.emoji == "\U0001F53C":
                    self.votes[user_id]["total"] += 1
                    self.votes[user_id]["incidents"][reaction.message.id]["votes"] += 1
                elif reaction.emoji == "\U0001F53D":
                    self.votes[user_id]["total"] -= 1
                    self.votes[user_id]["incidents"][reaction.message.id]["votes"] -= 1
                else:
                    await self.bot.remove_reaction(reaction.message,\
                            reaction.emoji, user)

    async def on_reaction_remove(self, reaction, user):
        if reaction.message.id in self.vote_messages.keys(): 
        #Check the message is a vote poll created by the bot.
            if not user.bot and user.id != self.bot.user.id: 
            #Make sure bots can't vote and the initial bot reactions aren't counted
                user_id = self.vote_messages[reaction.message.id]["user_id"]

                if reaction.emoji == "\U0001F53C":
                    self.votes[user_id]["total"] -= 1
                    self.votes[user_id]["incidents"][reaction.message.id]["votes"] -= 1
                elif reaction.emoji == "\U0001F53D":
                    self.votes[user_id]["total"] += 1
                    self.votes[user_id]["incidents"][reaction.message.id]["votes"] += 1

    @commands.command(name="jscomment", aliases=["jsc"], pass_context=True)
    async def joke_score_comment(self, ctx, message_id: int, mention: str, comment: str):
        """ Edit a comment on a past joke, example: /jscomment 1234 @user 'new comment' """
        if len(ctx.message.mentions) == 0:
            await self.bot.say("You forgot to mention anyone "
                                f"{ctx.message.author.mention}, you knob")
            return False

        if len(ctx.message.mentions) > 1:
            await self.bot.say("One at a time mate...")
            return False

        user = ctx.message.mentions[0]
        try:
            old = self.votes[user.id]["incidents"][str(message_id)]["comment"]
            self.votes[user.id]["incidents"][str(message_id)]["comment"] = comment
            await self.save_votes()

            await self.bot.say("Comment successfully updated!\n"
                    f"```old comment: {old}```\n"
                    f"```new comment: {comment}```")

        except KeyError:
            await self.bot.say(\
                    f"Comment not found for user: {user.display_name} with message id: {message_id}")
					
	@commands.command(name="jsdelpoll", aliases=["jsdl"], pass_context=True)
	async def joke_score_delete_poll(self, ctx, mention: str, message_id: int):
		""" Delete a Previous Poll from a Users History """
        if len(ctx.message.mentions) == 0:
            await self.bot.say("You forgot to mention anyone "
                                f"{ctx.message.author.mention}, you knob")
            return False

        if len(ctx.message.mentions) > 1:
            await self.bot.say("One at a time mate...")
            return False

        user = ctx.message.mentions[0]
        try:
			poll_votes = self.votes[user.id]["incidents"][str(message_id)]["comment"]["votes"]
            self.votes[user.id]["incidents"].pop(str(message_id))
			self.votes[user.id]["total"] -= poll_votes
            await self.save_votes()

            await self.bot.say("Poll successfully removed!")

        except KeyError:
            await self.bot.say(\
                    f"Poll not found for user: {user.display_name} with message id: {message_id}")

	@commands.command(name="jsdeluser", aliases=["jsdu"], pass_context=True)
	async def joke_score_delete_user(self, ctx, mention: str):
		""" Delete a Previous Poll from a Users History """
        if len(ctx.message.mentions) == 0:
            await self.bot.say("You forgot to mention anyone "
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
            await self.bot.say(\
                    f"User not on file: {user.display_name}")

    @commands.command(name="jokeleaderboard", aliases=["jstable","jslb"], pass_context=False)
    async def joke_score_leaderboard(self):
        """ Show the Joke Score Leaderboard """
        embed = discord.Embed(colour=discord.Colour(0xc27c0e),\
                url="https://github.com/STiGYFishh/Joke_Score_Discord/")

        embed.set_thumbnail(url=\
                "https://cdn.discordapp.com/emojis/296358609661591552.png?v=1")
        embed.set_footer(text="Joke Score Leaderboard")

        leaderboard_text = ""

        for user_id in self.votes.keys():
            user = await self.bot.get_user_info(user_id)
            leaderboard_text += f"{user.display_name}: {self.votes[user_id]['total']} \n"

        embed.add_field(name=random.choice(self.leaderboard_titles),\
                value=leaderboard_text, inline=False)

        await self.bot.say(embed=embed)

    @commands.command(name="jokescorereport", aliases=["jsr","incident_report"], pass_context=True)
    async def joke_score_report(self, ctx, mention: str, sort="new"):
        """ Show a User's Joke History, example: /jokescorereport @user top """
        if len(ctx.message.mentions) == 0:
            await self.bot.say("You forgot to mention anyone "
                                f"{ctx.message.author.mention}, you knob")
            return False

        if len(ctx.message.mentions) > 1:
            await self.bot.say("One at a time mate...")
            return False

        user = ctx.message.mentions[0]

        try:
            if sort.lower() in ["new","old","top"]:
                if sort == "new":
                    sorted_incidents = sorted(self.votes[user.id]["incidents"].keys(),\
                            key=lambda x: self.votes[user.id]["incidents"][x]['timestamp'], reverse=True)
                if sort == "old":
                    sorted_incidents = sorted(self.votes[user.id]["incidents"].keys(),\
                            key=lambda x: self.votes[user.id]["incidents"][x]['timestamp'])
                if sort == "top":
                    sorted_incidents = sorted(self.votes[user.id]["incidents"].keys(),\
                            key=lambda x: self.votes[user.id]["incidents"][x]['votes'], reverse=True)
        except (KeyError,TypeError):
            await self.bot.say("This user has no incidents to report")
            return False

        embed = discord.Embed(colour=discord.Colour(0xc27c0e),\
                url="https://github.com/STiGYFishh/Joke_Score_Discord/")

        embed.set_thumbnail(url=\
                "https://cdn.discordapp.com/emojis/296358609661591552.png?v=1")
        embed.set_footer(text=f"Joke Score Incident Report for {user.display_name}")

        fields = 0
        report_text = ""
        for incident_id in sorted_incidents:
            if fields >= 25:
                break

            date = datetime.fromtimestamp(\
                    int(self.votes[user.id]["incidents"][incident_id]["timestamp"])\
                 ).strftime("%d/%m/%y")

            votes = self.votes[user.id]["incidents"][incident_id]["votes"] 
            comment = self.votes[user.id]["incidents"][incident_id]["comment"] 

            report_text = f"Date: {date}\nVotes: {votes}\nComment: {comment}\n"

            embed.add_field(name=incident_id,value=report_text, inline=False)
            fields += 1

        await self.bot.say(embed=embed)

def setup(bot):
    bot.add_cog(JokeScore(bot))
