from faker import Faker
import json
import aio_pika
import asyncio
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

fake = Faker('en_US')

async def produce_data():
    connection = await aio_pika.connect_robust(os.getenv("RabbitMQCredential"))
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

            await asyncio.sleep(1)

if __name__ == '__main__':
    asyncio.run(produce_data())
