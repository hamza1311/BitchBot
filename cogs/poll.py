from discord.ext import commands
import discord

letter_emote = [
    "🇦",
    "🇧",
    "🇨",
    "🇩",
    "🇪",
    "🇫",
    "🇬",
    "🇭",
    "🇮",
    "🇯"
]


class Polls(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def poll(self, ctx, question, *answers):
        """
        Start a poll.

        If no answers are provided, it will default to yes/no
        Max of 10 answers
        If answers/questions contain spaces put it in quotes
        e.g. >poll "Do you like bacon" yes
        """
        
        if answers == ():
            msg = await ctx.send(f"**📊 {question}**")
            await msg.add_reaction("👍")
            await msg.add_reaction("👎")

        elif len(answers) < 10:

            inner = ""
            for i in range(len(answers)):
                inner += f"{letter_emote[i]} {answers[i]}\n"
            embed = discord.Embed(title= f"**📊 {question}**", description=inner, colour=0x02389e)
            msg = await ctx.send(embed=embed)
            for i in range(len(answers)):
                await msg.add_reaction(letter_emote[i])
        else:
            pass


def setup(bot):
    bot.add_cog(Polls(bot))
