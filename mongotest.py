from pymongo import MongoClient
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

# MongoDB connection
mongo_uri = os.getenv('MONGO_URI')
mongo_client = MongoClient(mongo_uri)

try:
    # The ping command is cheap and does not require auth.
    mongo_client.admin.command('ping')
    print("MongoDB connection successful!")
    db = mongo_client.FakeData
    transactions = db.FakeDataCollection
    test_data = {"test": "data"}
    result = transactions.insert_one(test_data)
    print(f"Test data inserted with _id: {result.inserted_id}")
except Exception as e:
    print(f"MongoDB connection or insertion failed: {e}")
