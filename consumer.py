#!/usr/bin/env python
import os
import json
import asyncio
import logging
from pymongo import MongoClient, errors
import aio_pika
from dateutil import parser
from datetime import datetime, timedelta
from dotenv import load_dotenv
import certifi

# Load environment variables
load_dotenv()

# Set up logging
logging.basicConfig(level=logging.DEBUG)

# MongoDB connection
mongo_uri = os.getenv('MONGO_URI')
if not mongo_uri:
    raise ValueError("MONGO_URI is not set")

try:
    # ✅ GitHub Actions-safe MongoDB connection (SCRAM + TLS)
    mongo_client = MongoClient(
        mongo_uri,
        tls=True,
        tlsCAFile=certifi.where(),      # ← use certifi’s up-to-date CA list
        serverSelectionTimeoutMS=30000
    )

    # Ping to test connection
    mongo_client.admin.command('ping')
    logging.info("✅ MongoDB connection successful")

except (errors.ServerSelectionTimeoutError, errors.ConfigurationError, errors.OperationFailure) as e:
    logging.error(f"❌ MongoDB connection failed: {e}")
    raise

# Set database and collection
db = mongo_client["FakeData"]
transactions = db["FakeDataCollection"]

# RabbitMQ connection
rabbitmq_uri = os.getenv('RABBITMQCREDENTIAL')
if not rabbitmq_uri:
    raise ValueError("RABBITMQCREDENTIAL is not set")

async def main() -> None:
    try:
        connection = await aio_pika.connect_robust(
            rabbitmq_uri,
            client_properties={"connection_name": "Data Consumer"}
        )

        async with connection:
            channel = await connection.channel()
            queue = await channel.declare_queue("RabbitMQ_Q", durable=True, arguments={'x-queue-type': 'quorum'})

            logging.info("🚀 Consumer started — listening to RabbitMQ_Q")
            end_time = datetime.utcnow() + timedelta(minutes=5)

            async with queue.iterator() as queue_iter:
                async for message in queue_iter:
                    async with message.process():
                        if datetime.utcnow() >= end_time:
                            logging.info("🕔 Time limit reached, shutting down consumer.")
                            break

                        try:
                            data = json.loads(message.body.decode())
                            logging.debug(f"📦 Message received: {data}")

                            if 'timestamp' in data:
                                data['timestamp'] = parser.parse(data['timestamp'])

                            data['ingestion_timestamp'] = datetime.utcnow().isoformat()

                            result = transactions.insert_one(data)
                            logging.info(f"✅ Inserted with _id: {result.inserted_id}")

                        except json.JSONDecodeError as e:
                            logging.error(f"❌ JSON decode error: {e}")
                        except errors.PyMongoError as e:
                            logging.error(f"❌ MongoDB insert error: {e}")
                        except Exception as e:
                            logging.error(f"❌ Unexpected error: {e}")

    except Exception as e:
        logging.error(f"❌ RabbitMQ connection error: {e}")

if __name__ == "__main__":
    asyncio.run(main())