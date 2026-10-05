from datetime import datetime, timezone

from pymongo import ASCENDING


class TodoRepository:
    """All reads and writes for todos go through here, so views never touch mongo."""

    def __init__(self, collection):
        self._collection = collection

    def list_all(self):
        # _id breaks ties when two todos share the same millisecond
        cursor = self._collection.find().sort([('created_at', ASCENDING), ('_id', ASCENDING)])
        return [self._to_dict(doc) for doc in cursor]

    def create(self, description):
        now = datetime.now(timezone.utc)
        # Mongo keeps milliseconds only; truncate so POST and GET return the same value
        now = now.replace(microsecond=now.microsecond // 1000 * 1000)
        doc = {'description': description, 'created_at': now}
        result = self._collection.insert_one(doc)
        doc['_id'] = result.inserted_id
        return self._to_dict(doc)

    @staticmethod
    def _to_dict(doc):
        # ObjectId and datetime aren't JSON serializable
        return {
            'id': str(doc['_id']),
            'description': doc['description'],
            'created_at': doc['created_at'].isoformat(),
        }
