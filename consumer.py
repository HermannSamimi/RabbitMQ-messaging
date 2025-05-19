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
print("wow")
try:
    mongo_client = MongoClient(
        mongo_uri,
        tls=True,
        tlsAllowInvalidCertificates=True,
        serverSelectionTimeoutMS=30000
    )
    mongo_client.admin.command('ping')  # test connection
    logging.info("✅ MongoDB connection successful!")
except (errors.ServerSelectionTimeoutError, errors.ConfigurationError) as e:
    logging.error(f"❌ MongoDB connection failed: {e}")
    raise

# Use DB and Collection
db = mongo_client.FakeData
transactions = db.FakeDataCollection

# RabbitMQ connection string
connectionstring = os.getenv('RABBITMQCREDENTIAL')
if not connectionstring:
    raise ValueError("RABBITMQCREDENTIAL environment variable is not set")

async def main() -> None:
    try:
        # Set custom connection name for RabbitMQ UI
        connection = await aio_pika.connect_robust(
            connectionstring,
            client_properties={
                "connection_name": "Data Consumer"
            }
        )

        async with connection:
            channel = await connection.channel()

            # Declare queue (must match producer's routing)
            queue = await channel.declare_queue("RabbitMQ_Q", durable=True, arguments={'x-queue-type': 'quorum'})

            # Stop after 5 minutes
            end_time = datetime.utcnow() + timedelta(minutes=5)

            async with queue.iterator() as queue_iter:
                async for message in queue_iter:
                    async with message.process():
                        if datetime.utcnow() >= end_time:
                            logging.info("Stopping execution after 5 minutes.")
                            break

                        try:
                            data = json.loads(message.body.decode())
                            logging.debug(f"Received message: {data}")

                            if 'timestamp' in data:
                                data['timestamp'] = parser.parse(data['timestamp'])

                            data['ingestion_timestamp'] = datetime.utcnow().isoformat()

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