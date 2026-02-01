# db2_hj3415/mongo.py
from __future__ import annotations

from pymongo.asynchronous.mongo_client import AsyncMongoClient
from pymongo.asynchronous.database import AsyncDatabase
from datetime import timezone

from db2_hj3415.settings import Settings, get_settings


class Mongo:
    def __init__(self, settings: Settings | None = None):
        self.settings = settings or get_settings()
        self.client = AsyncMongoClient(
            self.settings.MONGO_URI,
            connectTimeoutMS=self.settings.MONGO_CONNECT_TIMEOUT_MS,
            serverSelectionTimeoutMS=self.settings.MONGO_SERVER_SELECTION_TIMEOUT_MS,
            tz_aware=True,
            tzinfo=timezone.utc,
        )

    def get_db(self) -> AsyncDatabase:
        return self.client[self.settings.DB_NAME]

    async def close(self) -> None:
        await self.client.close()


def mongo_from_env() -> Mongo:
    return Mongo(get_settings())