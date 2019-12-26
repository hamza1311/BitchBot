from discord.ext import commands


class Starboard(commands.Cog):
    """A starboard.
    Allow users to star a message.
    Once a message reaches a certain number of stars, it is sent to the starboard channel and saved into the database
    TODOs:
    • TODO: Implement basic starboard functionality
    • TODO: Save stared messages to database
    • TODO: Allow users to see their star stats
    • TODO: Allow users to see top users who gets stared in a guild
    • TODO: Allow users to pull up a stared message by using the id

    SQL table:
        ```create table if not exists Starboard
        (
            message_id      bigint    not null,
            id              serial    not null primary key,
            started_at      timestamp not null default now(),
            message_content text,
            attachment      text,
            stars_count     int       not null
        );

        create unique index unique_message on Starboard (message_id);```
    """

    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_reaction_add(self, message):
        # Track stars here
        pass

    @commands.group(invoke_without_command=True)
    async def star(self, ctx, message):
        pass

    @star.group(invoke_without_command=True)
    async def stats(self, ctx):
        await ctx.send('Stub!')

    @stats.command(name='top')
    async def top_stared(self, ctx):
        await ctx.send('Stub!')


def setup(bot):
    bot.add_cog(Starboard(bot))