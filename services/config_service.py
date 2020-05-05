from database.sql import SQL
from resources import Prefix, GuildConfig, Blacklist


class GuildConfigService:
    def __init__(self, pool):
        self.pool = pool

    async def get(self, guild_id):
        async with self.pool.acquire() as con:
            fetched = await con.fetchrow('''
            select * from config_view
            where guild_id = $1
            ''', guild_id)
        if fetched is None:
            return None
        return GuildConfig.convert(fetched)

    async def setup_starboard(self, guild_id, starboard_channel_id, star_limit):
        query = '''
        insert into guildconfig (guild_id, starboard_channel, star_limit)
        values ($1, $2, $3)
        on conflict(guild_id) do update set starboard_channel = $2, star_limit = $3 
        returning *;
        '''

        async with self.pool.acquire() as conn:
            inserted = await conn.fetchrow(query, guild_id, starboard_channel_id, star_limit)
        return GuildConfig.convert(inserted)

    async def add_mod_role(self, role_id, guild_id):
        query = '''
        update guildconfig
        set mod_roles = guildconfig.mod_roles || $2
        where guild_id = $1
        returning *;
        '''
        async with self.pool.acquire() as connection:
            return GuildConfig.convert(await connection.fetchrow(query, guild_id, [role_id]))

    async def set_mute_role(self, guild_id, mute_role_id):
        async with self.pool.acquire() as connection:
            fetched = await connection.fetchrow(f'''
            insert into guildconfig (guild_id, mute_role_id)
            values ($1, $2)
            on conflict(guild_id) do update set mute_role_id = $2
            returning *;
            ''', guild_id, mute_role_id)

            return GuildConfig.convert(fetched)

    async def remove_mute_role(self, guild_id, role_id):
        async with self.pool.acquire() as connection:
            fetched = await connection.fetchrow(f'''
            update guildconfig
            set mod_roles = array_remove(mod_roles, $2)
            where guild_id = $1
            returning *;
            ''', guild_id, role_id)

            return GuildConfig.convert(fetched) if fetched is not None else None

    async def setup_logs(self, guild_id, webhook_url):
        async with self.pool.acquire() as connection:
            fetched = await connection.fetchrow(f'''
            insert into guildconfig (guild_id, event_log_webhook)
            values ($1, $2)
            on conflict(guild_id) do update set event_log_webhook = $2
            returning *;
            ''', guild_id, webhook_url)

            return GuildConfig.convert(fetched)

    async def delete_logs_webhook(self, guild_id):
        async with self.pool.acquire() as connection:
            fetched = await connection.fetchrow(f'''
            update GuildConfig
            set event_log_webhook = null
            where guild_id = $1
            returning *;
            ''', guild_id)

            return GuildConfig.convert(fetched) if fetched is not None else None

    async def delete_starboard(self, guild_id):
        async with self.pool.acquire() as connection:
            fetched = await connection.fetchrow(f'''
            update GuildConfig
            set starboard_channel = null, star_limit = null
            where guild_id = $1
            returning *;
            ''', guild_id)

            return GuildConfig.convert(fetched) if fetched is not None else None

    async def insert_prefix(self, prefix):
        async with self.pool.acquire() as con:
            fetched = await con.fetchrow('''
            insert into GuildConfig (guild_id, prefix)
            values ($1, $2)
            on conflict(guild_id) do update set prefix = $2
            returning *;
            ''', prefix.guild_id, prefix.prefix)

            return Prefix.convert(fetched)

    async def delete_prefix(self, guild_id):
        async with self.pool.acquire() as con:
            await con.execute('''
            update GuildConfig
            set prefix = null
            where guild_id = $1;
            ''', guild_id)

    async def get_all_prefixes(self):
        async with self.pool.acquire() as con:
            fetched = await con.fetch('''
            select guild_id, prefix from GuildConfig
            where prefix is not null;
            ''')

            return Prefix.convertMany(fetched) if fetched is not None else []

    async def get_blacklisted_users(self):
        async with self.pool.acquire() as con:
            fetched = await con.fetch('''
            select *
            from blacklist;
            ''')

        return Blacklist.convertMany(fetched) if fetched is not None else []

    async def blacklist_user(self, user_id, *, reason=None, until=None):
        async with self.pool.acquire() as con:
            inserted = await con.fetchrow('''
            insert into blacklist (user_id, reason, blacklisted_until)
            values ($1, $2, $3)
            returning *;
            ''', user_id, reason, until)

            return Blacklist.convert(inserted)

    async def remove_user_from_blacklist(self, user_id):
        async with self.pool.acquire() as con:
            return await con.execute('''
            delete from blacklist
            where user_id = $1;
            ''', user_id)

    @classmethod
    def sql(cls):
        return SQL(createTable='''
        create table if not exists GuildConfig
        (
            guild_id          bigint primary key,
            starboard_channel bigint,
            event_log_webhook text,
            mute_role_id bigint,
            mod_roles bigint[] not null default '{}'
        );
        
        create materialized view if not exists config_view as
        select *
        from guildconfig;
        
        create or replace function refresh_config_view()
            returns trigger
            language plpgsql
        as
        $$
        begin
            refresh materialized view config_view;
            return null;
        end
        $$;
        
        drop trigger if exists refresh_config_view_on_update
            on GuildConfig;
        
        create trigger refresh_config_view_on_update
            after update or insert
            on GuildConfig
        execute function refresh_config_view();
        
        create table if not exists blacklist
        (
            user_id           bigint primary key,
            blacklisted_at    timestamptz not null default now(),
            blacklisted_until timestamptz,
            reason text
        );
        ''')
