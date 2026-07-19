import asyncio
from motor.motor_asyncio import AsyncIOMotorClient

async def test():
    client = AsyncIOMotorClient("mongodb://localhost:27017")
    db = client.test_db
    try:
        res = await db.test_col.find_one_and_update(
            {"phone": "123"},
            {"$set": {"phone": "123"}},
            upsert=True,
            return_document=True
        )
        print("Updated successfully", res)
    except Exception as e:
        print("Error updating:", repr(e))

asyncio.run(test())
