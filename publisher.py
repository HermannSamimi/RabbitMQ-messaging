from faker import Faker
import json
import aio_pika
import asyncio
from dotenv import load_dotenv
import os
from datetime import datetime

# Load environment variables from .env file
load_dotenv()

# Get RabbitMQ credential from environment variable
rabbitmq_credential = os.getenv("RABBITMQCREDENTIAL")
if not rabbitmq_credential:
    raise ValueError("RabbitMQCredential environment variable is not set")

fake = Faker('en_US')

async def produce_data():
    try:
        connection = await aio_pika.connect_robust(os.getenv("RABBITMQCREDENTIAL"))
        async with connection:
            channel = await connection.channel()
            await channel.declare_queue('RabbitMQ_Q', durable=True, arguments={'x-queue-type': 'quorum'})
            while True:
                fake_user = {
                    "name": fake.name(),
                    "address": fake.address(),
                    "email": fake.email(),
                    "credential": {
                        "username": fake.user_name(),
                        "password": fake.password(),
                    },
                    "phone_number": fake.phone_number(),
                    "company": fake.company(),
                    "job": fake.job(),
                    "birthdate": fake.date_of_birth().isoformat(),
                    "ingestion_timestamp": datetime.utcnow().isoformat()
                }

                # Convert the dictionary to a JSON string
                fake_user_json = json.dumps(fake_user)
                print("Producing:", fake_user_json)
                await channel.default_exchange.publish(
                    aio_pika.Message(
                        body=fake_user_json.encode('utf-8'),
                        delivery_mode=aio_pika.DeliveryMode.PERSISTENT
                    ),
                    routing_key="RabbitMQ_Q"
                )

                await asyncio.sleep(10)
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == '__main__':
    asyncio.run(produce_data())
