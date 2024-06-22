#!/usr/bin/env python
import os
from pymongo import MongoClient, errors
import json
import aio_pika
import asyncio
import logging
from dateutil import parser
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Set up logging
logging.basicConfig(level=logging.DEBUG)

# MongoDB connection
mongo_uri = os.getenv('MONGO_URI')
if not mongo_uri:
    raise ValueError("MONGO_URI environment variable is not set")

try:
    mongo_client = MongoClient(mongo_uri)
    # Attempt to connect to the server
    mongo_client.admin.command('ping')
    logging.info("MongoDB connection successful!")
except errors.ConfigurationError as e:
    logging.error(f"MongoDB connection failed: {e}")
    raise

db = mongo_client.FakeData  # Assuming 'FakeData' is your database name
transactions = db.FakeDataCollection  # Assuming 'FakeDataCollection' is your collection name

# RabbitMQ connection string
connectionstring = os.getenv('RABBITMQCREDENTIAL')
if not connectionstring:
    raise ValueError("RABBITMQCREDENTIAL environment variable is not set")

async def main() -> None:
    try:
        connection = await aio_pika.connect_robust(connectionstring)
        async with connection:
            channel = await connection.channel()

            # Declaring queue
            queue = await channel.declare_queue("RabbitMQ_Q", durable=True, arguments={'x-queue-type': 'quorum'})

            end_time = datetime.utcnow() + timedelta(minutes=5)
            async with queue.iterator() as queue_iter:
                async for message in queue_iter:
                    async with message.process():
                        if datetime.utcnow() >= end_time:
                            logging.info("Stopping execution after 5 minutes.")
                            break

                        try:
                            # Decode byte string to JSON and load into Python dictionary
                            data = json.loads(message.body.decode())
                            logging.debug(f"Received message: {data}")

                            # Optional: Parse 'timestamp' if it's in your data
                            if 'timestamp' in data:
                                data['timestamp'] = parser.parse(data['timestamp'])

                            # Add ingestion timestamp
                            data['ingestion_timestamp'] = datetime.utcnow().isoformat()

                            # Insert into MongoDB
                            result = transactions.insert_one(data)
                            logging.info(f"Data inserted with _id: {result.inserted_id}")
                        except json.JSONDecodeError as e:
                            logging.error(f"Failed to decode JSON: {e}")
                        except errors.PyMongoError as e:
                            logging.error(f"MongoDB insertion error: {e}")
                        except Exception as e:
                            logging.error(f"An unexpected error occurred: {e}")

    except Exception as e:
        logging.error(f"An error occurred: {e}")

if __name__ == "__main__":
    asyncio.run(main())
