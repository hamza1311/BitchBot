from resources import Resource


class Prefix(Resource):
    def __init__(self, guild_id, prefix):
        self.guild_id = guild_id
        self.prefix = prefix

    def __str__(self):
        return self.prefix
