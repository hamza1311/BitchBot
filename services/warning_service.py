from database.sql import SQL
from resources import Warn


class WarningsService:
    def __init__(self, pool):
        self.pool = pool

    async def insert(self, warn):
        async with self.pool.acquire() as connection:
            inserted = await connection.fetchrow('''
                insert into Warnings (reason, warned_by_id, warned_user_id, guild_id)
                values ($1, $2, $3, $4)
                returning *;
            ''', warn.reason, warn.warned_by_id, warn.warned_user_id, warn.guild_id)
            return Warn.convert(inserted)

    async def get_all(self, guild_id, user_id=None):
        query = f'''
        select * from Warnings
        where guild_id = $1 {'' if user_id is None else f'and warned_user_id = {user_id}'}
        order by warned_user_id;
        '''
        async with self.pool.acquire() as connection:
            fetched = await connection.fetch(query, guild_id)
        return Warn.convertMany(fetched)

    @classmethod
    def sql(cls):
        return SQL(
            createTable='''
                create table if not exists Warnings
                (
                    id             serial primary key,
                    reason         text      not null,
                    warned_at      timestamp not null default now(),
                    warned_by_id   bigint    not null,
                    warned_user_id bigint    not null,
                    guild_id       bigint    not null
                )
            '''
        )
