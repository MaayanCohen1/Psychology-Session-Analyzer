import os
import time

import pika
from pika.credentials import PlainCredentials

from logger_config import logger

RABBITMQ_HOST = os.getenv("RABBITMQ_HOST", "rabbitmq")
RABBITMQ_PORT = int(os.getenv("RABBITMQ_PORT", "5672"))
RABBITMQ_USER = os.getenv("RABBITMQ_USER", "user")
RABBITMQ_PASSWORD = os.getenv("RABBITMQ_PASSWORD", "pass")


def connect_to_rabbitmq():
    """
    Try to connect to RabbitMQ and return a blocking connection and channel.
    """
    credentials = PlainCredentials(RABBITMQ_USER, RABBITMQ_PASSWORD)
    params = pika.ConnectionParameters(
        host=RABBITMQ_HOST,
        port=RABBITMQ_PORT,
        credentials=credentials,
    )
    connection = pika.BlockingConnection(params)
    channel = connection.channel()
    return connection, channel


def main():
    """
    Main loop: keep trying to connect to RabbitMQ and log the status.
    """
    while True:
        try:
            logger.info("Audio service trying to connect to RabbitMQ...")
            connection, channel = connect_to_rabbitmq()
            logger.info("Audio service connected to RabbitMQ successfully.")

            # For now we do nothing else, just keep the connection open.
            # In the next steps we will start consuming messages here.
            while True:
                time.sleep(10)

        except Exception as exc:
            logger.exception(f"Audio service failed to connect or lost connection: {exc}")
            logger.info("Retrying in 5 seconds...")
            time.sleep(5)


if __name__ == "__main__":
    main()
