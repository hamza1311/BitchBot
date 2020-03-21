import asyncio
import logging
import aiohttp
import discord
from discord.ext import commands

import keys
from database import database
import util
import random
import hypercorn
import os
from services import ActivityService

bitch_bot_logger = logging.getLogger('BitchBot')
bitch_bot_logger.setLevel(logging.INFO)
file_handler = logging.FileHandler(filename='discord.log', encoding='utf-8', mode='w')
fmt = '%(name)s: %(levelname)s: %(asctime)s: %(message)s'
file_handler.setFormatter(logging.Formatter(fmt))
bitch_bot_logger.addHandler(file_handler)


# noinspection PyMethodMayBeStatic
class BitchBot(commands.Bot):
    def __init__(self, **kwargs):
        super().__init__(
            command_prefix=commands.when_mentioned_or('>'),
            help_command=util.BloodyHelpCommand(),
            owner_id=529535587728752644,
            case_insensitive=True,
        )

        self.quart_app = util.QuartWithBot(__name__, static_folder=None)
        self.quart_app.config['SECRET_KEY'] = keys.client_secret
        self.quart_app.debug = keys.debug
        # Probably should put it with config
        self.initial_cogs = kwargs.pop('cogs')

        # activity tracking related props
        self.activity_bucket = commands.CooldownMapping.from_cooldown(1.0, 120.0, commands.BucketType.member)

        # socket stats props
        self.socket_stats = {}

        self.lines_of_code_count = self._count_lines_of_code()

    # noinspection PyMethodMayBeStatic,SpellCheckingInspection
    async def setup_logger(self):
        discord_handler = util.DiscordLoggingHandler(self.loop, self.clientSession)

        dpy_logger = logging.getLogger('discord')
        dpy_logger.setLevel(logging.INFO)
        dpy_logger.addHandler(file_handler)
        dpy_logger.addHandler(discord_handler)

        bitch_bot_logger.addHandler(discord_handler)

    # noinspection PyAttributeOutsideInit
    async def start(self, *args, **kwargs):
        self.clientSession = aiohttp.ClientSession()

        await self.setup_logger()

        self.db = await database.init(self.loop)
        self.load_extension('util.timers')
        self.activity_service = ActivityService(self.db)
        for cog_name in self.initial_cogs:
            try:
                self.load_extension(f"cogs.{cog_name}")
                bitch_bot_logger.debug(f'Successfully loaded extension {cog_name}')
            except Exception as e:
                bitch_bot_logger.exception(f'Failed to load loaded extension {cog_name}', e)
        for i in ('spa_serve', 'routes', 'user_routes'):
            self.load_extension(f'web.backend.routes.{i}')
        await super().start(*args, **kwargs)

    def run(self, *args, **kwargs):
        async def start_quart():
            config = hypercorn.Config()
            config.bind = ["0.0.0.0:6969"]
            # noinspection PyUnresolvedReferences
            await hypercorn.asyncio.serve(self.quart_app, config)

        def done_callback(_):
            self.loop.create_task(self.close())

        future = asyncio.ensure_future(start_quart(), loop=self.loop)
        future.add_done_callback(done_callback)
        super().run(*args, **kwargs)

    async def close(self):
        await self.clientSession.close()
        await self.db.close()
        await super().close()

    async def send_ping_log_embed(self, message):
        embed = discord.Embed(title=f"{self.user.name} was mentioned in {message.guild}",
                              color=util.random_discord_color(),
                              description=f'**Message content:**\n{message.content}')
        embed.set_author(name=message.author, icon_url=message.author.avatar_url)
        embed.set_thumbnail(url=message.guild.icon_url)
        embed.add_field(name='Guild', value=f'{message.guild} ({message.guild.id})')
        embed.add_field(name='Channel', value=f'{message.channel.mention}')
        embed.add_field(name='Author', value=f'{message.author.display_name} ({message.author}; {message.author.id})')
        embed.add_field(name='Link', value=f'[Jump to message]({message.jump_url})')

        webhook = discord.Webhook.from_url(keys.logWebhook,
                                           adapter=discord.AsyncWebhookAdapter(self.clientSession))
        await webhook.send(embed=embed)

    async def on_message(self, message):
        if message.author.bot:  # don't do anything if the author is a bot
            return

        ctx = await self.get_context(message)

        if not ctx.valid:
            me = message.guild.me if message.guild is not None else self.user
            if me.mentioned_in(message):  # Bot was mentioned so
                await message.channel.send(random.choice(  # :pinng:
                    ["<a:ping:610784135627407370>", "<a:pinng:689843900889694314>"]))
                await self.send_ping_log_embed(message)  # and log the message

            if not self.activity_bucket.update_rate_limit(message):  # been two minutes since last update
                increment_by = 2
                await self.activity_service.increment(message.author.id, message.guild.id, increment_by)
                bitch_bot_logger.debug(f'Incremented activity of {message.author} ({message.author.id}) '
                                       f'in {message.guild} ({message.guild.id}) by {increment_by}')

        await self.invoke(ctx)

    async def on_ready(self):
        print(f"{self.user.name} is running")
        print("-" * len(self.user.name + " is running"))
        await self.change_presence(
            status=discord.Status.online,
            activity=discord.Game(f"use >help or @mention me")
        )

    async def on_socket_response(self, msg):
        event = msg['t']
        if event is None:
            return
        try:
            self.socket_stats[event] += 1
        except KeyError:
            self.socket_stats[event] = 1

    async def on_command_error(self, ctx: commands.Context, exception):
        exception = getattr(exception, 'original', exception)

        if isinstance(exception, commands.CheckFailure):
            await ctx.send(str(exception))
        elif isinstance(exception, commands.UserInputError):
            msg = f'See `{ctx.prefix}help {ctx.command.qualified_name}` for more info'
            await ctx.send('\n'.join([str(exception), msg]))
        elif isinstance(exception, commands.CommandNotFound):
            pass
        else:
            await ctx.send(f'{exception.__class__.__name__}: {str(exception)}')
            bitch_bot_logger.exception(f'{exception}\nMessage:{ctx.message.jump_url}')

    def get_mutual_guilds(self, member_id):
        for guild in self.guilds:
            if member_id in [x.id for x in guild.members]:
                yield guild

    def _get_all_files(self):
        for root, dirs, files in os.walk("."):
            if root.startswith(('./venv', './web/frontend/node_modules', '.git', '.idea')):
                continue
            for file in files:
                if file.endswith(('.py', '.ts')):
                    yield os.path.join(root, file)

    def _count_lines_of_code(self):
        all_files = list(self._get_all_files())
        lines_count = 0
        for file in all_files:
            with open(file) as f:
                read_file = f.read().split('\n')
                lines = [x for x in read_file if x != '']
                lines_count += len(lines)

        return lines_count

    def refresh_loc_count(self):
        self.lines_of_code_count = self._count_lines_of_code()
