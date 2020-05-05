import discord
from discord.ext import commands
from datetime import datetime
from resources import Ban, Warn, Mute, Timer
from services import MuteService, WarningsService, BanService, ConfigService
from util import funs, checks, BloodyMenuPages, TextPagesData, converters


# noinspection PyIncorrectDocstring,PyUnresolvedReferences
class Moderation(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        pool = bot.db
        self.warnings_service = WarningsService(pool)
        self.mute_service = MuteService(pool)
        self.ban_service = BanService(pool)
        self.config_service = ConfigService(pool)

    def cog_check(self, ctx):
        if ctx.guild is None:
            raise commands.NoPrivateMessage("Mod commands can't be used in DMs")
        return True

    @commands.command()
    @commands.has_permissions(kick_members=True)
    async def kick(self, ctx: commands.Context, victim: discord.Member, *, reason: str = None):
        """
        Yeet a user

        Args:
            victim: Member you want to kick
            reason: Reason for kick
        """

        embed = discord.Embed(title=f"User was Kicked from {ctx.guild.name}",
                              color=funs.random_discord_color(),
                              timestamp=datetime.utcnow())
        embed.add_field(name='Kicked By', value=ctx.author.mention, inline=True)
        embed.add_field(name='Kicked user', value=victim.mention, inline=True)
        if reason:
            embed.add_field(name='Reason', value=reason, inline=False)
        embed.set_thumbnail(url=victim.avatar_url)

        await ctx.send(embed=embed)
        await victim.kick(reason=reason)

        try:
            embed.title = f"You have been Kicked from {ctx.guild.name}"
            await victim.send(embed=embed)
        except discord.Forbidden:
            await ctx.send("I can't dm that user. Kicked without notice")

    async def do_ban(self, ctx, victim, reason, time=None):
        if victim.id == ctx.author.id:
            await ctx.send("Why do want to ban yourself?\nI'm not gonna let you do it")
            return

        ban = Ban(
            reason=reason if reason else None,
            banned_by_id=ctx.author.id,
            banned_user_id=victim.id,
            guild_id=ctx.guild.id,
            unban_time=time
        )

        saved = await self.ban_service.insert(ban)

        embed = discord.Embed(title=f"User was banned from {ctx.guild.name}", color=funs.random_discord_color(),
                              timestamp=saved.banned_at)
        embed.add_field(name='Banned By', value=ctx.author.mention, inline=True)
        embed.add_field(name='Banned user', value=victim.mention, inline=True)
        if reason:
            embed.add_field(name='Reason', value=reason, inline=False)
        embed.set_thumbnail(url=victim.avatar_url)

        await ctx.send(f'ID: {saved.id}', embed=embed)

        try:
            embed.title = f"You have been banned from {ctx.guild.name}"
            await victim.send(embed=embed)
        except discord.Forbidden:
            await ctx.send("I can't DM that user. Banned without notice")

        await victim.ban(reason=f'{reason}\n(Operation performed by {ctx.author}; ID: {ctx.author.id})')

    @commands.command()
    @commands.has_permissions(ban_members=True)
    async def ban(self, ctx: commands.Context, victim: discord.Member, *, reason: str = None):
        """
        Ban a user

        Args:
            victim: Member you want to ban
            reason: Reason for ban - Optional
        """

        await self.do_ban(ctx, victim, reason)

    @commands.command()
    @commands.has_permissions(ban_members=True)
    async def tempban(self, ctx: commands.Context, victim: discord.Member, *,
                      time_and_reason: converters.HumanTime(other=True) = None):
        """
        Temporarily ban a user

        Args:
            victim: Member you want to ban
            time: Un-ban time - Optional
            reason: Reason for ban - Optional
        """
        if time_and_reason is None:
            time = None
            reason = ''
        else:
            time = time_and_reason.time
            reason = time_and_reason.other if time_and_reason.other is not None else ''
        await self.do_ban(ctx, victim, reason, time)

        if time:
            extras = {
                'ban_id': saved.id,
                'guild_id': saved.guild_id,
                'banned_user_id': saved.banned_user_id,
            }
            timer = Timer(
                event='tempban',
                created_at=ctx.message.created_at,
                expires_at=time,
                kwargs=extras
            )
            await self.bot.timers.create_timer(timer)

    async def do_unban(self, guild, user_id, reason):
        await self.ban_service.delete(guild.id, user_id)
        await guild.unban(discord.Object(id=user_id), reason=reason)

    @commands.Cog.listener()
    async def on_tempban_timer_complete(self, timer):
        kwargs = timer.kwargs
        guild = self.bot.get_guild(kwargs['guild_id'])
        reason = 'Unban from temp-ban timer expiring'
        await self.do_unban(guild, kwargs['banned_user_id'], reason=reason)

    async def do_mute(self, ctx, *, victim, reason=None, time=None):
        config = await self.config_service.get(ctx.guild.id)
        muted = ctx.guild.get_role(config.muted_role_id)

        if muted in victim.roles:
            await ctx.send('User is already muted')
            return

        mute = Mute(
            reason=reason,
            muted_by_id=ctx.author.id,
            muted_user_id=victim.id,
            guild_id=ctx.guild.id,
            unmute_time=time
        )
        inserted = await self.mute_service.insert(mute)

        await victim.add_roles(muted, reason=f'{reason}\n(Operation performed by {ctx.author})')
        await ctx.send(f"**User {victim.mention} has been muted by {ctx.author.mention}**\nID: {inserted.id}")

        try:
            msg = f"You have been muted in {ctx.guild.name} {f'for {time}' if time else ''}" \
                  f"\n{'Reason `{reason}`' if reason else ''}"

            await victim.send(msg)
        except discord.Forbidden:
            await ctx.send("I can't DM that user. Muted without notice")

    @commands.group(invoke_without_command=True)
    @commands.has_permissions(manage_roles=True)
    async def mute(self, ctx, victim: discord.Member, reason=None):
        """
        Permanently Mute a user

        Args:
            victim: Member you want to mute
            reason: Reason for mute - Optional
       """

        if victim.id == ctx.author.id:
            return await ctx.send("Why do want to mute yourself?\nI'm not gonna let you do it")

        async with ctx.typing():
            await self.do_mute(ctx, victim=victim, reason=reason)

    @mute.command(name='temp')
    @commands.has_permissions(manage_roles=True)
    async def temp_mute(self, ctx: commands.Context, victim: discord.Member, *,
                        time_and_reason: converters.HumanTime(other=True)):
        """
        Temporarily mute a user

        Args:
            victim: Member you want to mute
            time: Un-mute time - Optional
            reason: Reason for mute - Optional
        """

        time = time_and_reason.time
        reason = time_and_reason.other

        if victim.id == ctx.author.id:
            return await ctx.send("Why do want to mute yourself?\nI'm not gonna let you do it")

        async with ctx.typing():
            await self.do_mute(ctx, victim=victim, time=time, reason=reason)

            if time:
                extras = {
                    'mute_id': inserted.id,
                    'guild_id': inserted.guild_id,
                    'muted_user_id': inserted.muted_user_id,
                }
                timer = Timer(
                    event='tempmute',
                    created_at=ctx.message.created_at,
                    expires_at=time,
                    kwargs=extras
                )
                await self.bot.timers.create_timer(timer)

    async def do_unmute(self, guild, victim):
        config = await self.config_service.get(guild.id)
        muted = guild.get_role(config.muted_role_id)
        await victim.remove_roles(muted)
        await self.mute_service.delete(guild.id, victim.id)

    @commands.command()
    @commands.has_permissions(manage_roles=True, manage_channels=True)
    async def unmute(self, ctx: commands.Context, victim: discord.Member):
        """
        Unmute a user

        Args:
            victim: Member you want to unmute
        """

        await ctx.trigger_typing()
        await self.do_unmute(ctx.guild, victim)
        await ctx.send(f"**User {victim.mention} has been unmuted by {ctx.author.mention}**")

    @commands.Cog.listener()
    async def on_tempmute_timer_complete(self, timer):
        guild = self.bot.get_guild(timer.kwargs['guild_id'])
        await self.do_unmute(guild, guild.get_member(timer.kwargs['muted_user_id']))

    @commands.command()
    @commands.has_permissions(manage_messages=True)
    async def purge(self, ctx, limit, messages_of: discord.Member = None):
        """
        Purges given amount of messages from a given member if named

        Args:
            limit: The number of messages you want to delete
            messages_of: The user whose messages you want to kick
        """
        if messages_of is None:
            deleted = await ctx.channel.purge(limit=int(limit))
        else:
            def check(m):
                return m.author == messages_of

            deleted = await ctx.channel.purge(limit=int(limit), check=check)

        deleted_of = set()
        for message in deleted:
            deleted_of.add(message.author.name)

        await ctx.send(f'Deleted {len(deleted)} message(s) by {deleted_of}', delete_after=5)
        await ctx.message.delete(delay=2)

    @commands.command()
    @checks.is_mod()
    async def warn(self, ctx: commands.Context, victim: discord.Member, *, reason: str):
        """
        Warn a user

        Args:
            victim: Member you want to warn
            reason: Reason for warn
        """

        warning = Warn(
            reason=reason,
            warned_by_id=ctx.author.id,
            warned_user_id=victim.id,
            guild_id=ctx.guild.id
        )

        inserted = await self.warnings_service.insert(warning)

        embed = discord.Embed(title=f"User was warned from {ctx.guild.name}", color=funs.random_discord_color(),
                              timestamp=inserted.warned_at)
        embed.add_field(name='Warned By', value=ctx.author.mention, inline=True)
        embed.add_field(name='Warned user', value=victim.mention, inline=True)
        if reason:
            embed.add_field(name='Reason', value=inserted.reason, inline=False)
        embed.set_thumbnail(url=victim.avatar_url)

        await ctx.send(f'ID: {inserted.id}', embed=embed)

        try:
            embed.title = f"You have been warned in {ctx.guild.name}"
            await victim.send(embed=embed)
        except discord.Forbidden:
            await ctx.send("I can't DM that user. Warned without notice")

    @commands.command(aliases=['warnings'])
    @checks.is_mod()
    async def warns(self, ctx: commands.Context, warnings_for: discord.Member = None):
        """
        Get warnings for a user

        Args:
            warnings_for: Member whose warnings you want to get. All the warnings are returned if omitted.
        """
        if warnings_for is not None:
            warnings_for = warnings_for.id
        warnings = await self.warnings_service.get_all(ctx.guild.id, warnings_for)
        pages = commands.Paginator(prefix='```md', max_size=1980)
        index = 1
        sorted_warnings = sorted(warnings, key=lambda x: x.id)
        for warning in sorted_warnings:
            member = ctx.guild.get_member(warning.warned_user_id)
            if member is None:
                member = ctx.bot.get_user(warning.warned_user_id)

            line = f"{warning.id}.  {funs.format_human_readable_user(member)}\n" \
                   f"\tReason: {warning.reason}\n" \
                   f"\tWarned at: {warning.warned_at}\n" \
                   f"\tWarned by {self.bot.get_user(warning.warned_by_id)}\n"
            pages.add_line(line)
            index += 1

        react_paginator = BloodyMenuPages(TextPagesData(pages))
        await react_paginator.start(ctx)

    @mute.command(name='config')
    async def mute_config(self, ctx, role: discord.Role):
        """
        Configure mute role

        Args:
             role: the role you want to be used as the muted role
        """
        await self.config_service.set_mute_role(ctx.guild.id, role.id)
        await ctx.send(f'Inserted {role.mention} as mute role')

    @commands.group()
    async def mod(self, ctx):
        pass

    @mod.group(invoke_without_command=True, name='roles')
    async def mod_roles(self, ctx):
        pass

    @mod_roles.command(name='add')
    @checks.can_config()
    async def mod_role_add(self, ctx, role: discord.Role):
        """
        Add mod role

        Args:
            role: The role you want to add
        """
        inserted = await self.config_service.add_mod_role(role.id, ctx.guild.id)
        await ctx.send(
            f"Current mod roles are: {', '.join([ctx.guild.get_role(r).name for r in set(inserted.mod_roles)])}")

    @mod_roles.command(name='remove')
    @checks.can_config()
    async def mod_role_remove(self, ctx, role: discord.Role):
        """
        Remove a role from mod role

        Args:
            role: The role to remove
        """

        new_config = await self.config_service.remove_mute_role(ctx.guild.id, role.id)
        if new_config is None:
            return await ctx.send('This server was never confirmed')

        await ctx.send(
            f"Current mod roles are: {', '.join([ctx.guild.get_role(r).name for r in set(new_config.mod_roles)])}")


def setup(bot):
    bot.add_cog(Moderation(bot))
