import asyncio
import os
from passlib.context import CryptContext
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv
import pymongo

load_dotenv()

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

async def seed_database():
    mongo_uri = os.getenv("MONGODB_URI")
    db_name = os.getenv("DB_NAME", "rotiexpress")
    
    if not mongo_uri:
        print("MONGODB_URI not set.")
        return
        
    print(f"Connecting to MongoDB at {mongo_uri}...")
    client = AsyncIOMotorClient(mongo_uri)
    db = client[db_name]
    
    # 1. Create Indexes
    print("Creating indexes...")
    await db.customers.create_index([("phone", pymongo.ASCENDING)], unique=True)
    await db.orders.create_index([("order_code", pymongo.ASCENDING)], unique=True)
    await db.orders.create_index([("order_status", pymongo.ASCENDING), ("created_at", pymongo.DESCENDING)])
    await db.orders.create_index([("delivery_slot", pymongo.ASCENDING)])
    await db.orders.create_index([("customer.phone", pymongo.ASCENDING)])
    print("Indexes created.")
    
    # 2. Seed Admin User
    print("Seeding admin user...")
    admin = await db.admins.find_one({"username": "admin"})
    if not admin:
        await db.admins.insert_one({
            "username": "admin",
            "password_hash": pwd_context.hash("password123")
        })
        print("Admin user created: admin / password123")
    else:
        print("Admin user already exists.")
        
    # 3. Seed Default Settings
    print("Seeding default settings...")
    settings = await db.settings.find_one({"_id": "app_settings"})
    if not settings:
        await db.settings.insert_one({
            "_id": "app_settings",
            "price_per_roti": 10.0,
            "max_rotis_per_slot": 50,
            "min_advance_hours": 2
        })
        print("Default settings created.")
    else:
        print("Settings already exist.")
        
    print("Database seeded successfully.")
    client.close()

if __name__ == "__main__":
    asyncio.run(seed_database())
