from resources import Resource
import json


class Timer(Resource):
    def __init__(self, **kwargs):
        self.id = kwargs.pop('id', 0)
        extra = kwargs.pop('extra', {'args': (), 'kwargs': {}})
        self.args = extra.get('args', [])
        self.kwargs = kwargs.pop('kwargs', {})
        self.event = kwargs.pop('event')
        self.created_at = kwargs.pop('created_at')
        self.expires_at = kwargs.pop('expires_at')

    @classmethod
    def convert(cls, record):
        extra = json.loads(record['extras'])
        return cls(
            id=record['id'],
            kwargs=record['extras'],
            event=record['event'],
            created_at=record['created_at'],
            expires_at=record['expires_at'],
        )
