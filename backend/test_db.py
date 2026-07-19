import asyncio
from motor.motor_asyncio import AsyncIOMotorClient

async def test():
    client = AsyncIOMotorClient("mongodb+srv://sayednawaz2006_db_user:78xBA3bzR9xzKcfX@cluster0.chvkyar.mongodb.net/")
    db = client.test  # I need to check the DB name
    
    # Check config.py
