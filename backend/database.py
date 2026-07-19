from motor.motor_asyncio import AsyncIOMotorClient
from .config import settings

class Database:
    client: AsyncIOMotorClient = None

db = Database()

def get_database():
    return db.client[settings.DB_NAME]

async def connect_to_mongo():
    db.client = AsyncIOMotorClient(settings.MONGODB_URI)

async def close_mongo_connection():
    if db.client:
        db.client.close()
