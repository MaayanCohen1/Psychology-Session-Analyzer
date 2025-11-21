import json
import os
import time

import pika
from pika.credentials import PlainCredentials

from logger_config import logger

RABBITMQ_HOST = os.getenv("RABBITMQ_HOST", "rabbitmq")
RABBITMQ_PORT = int(os.getenv("RABBITMQ_PORT", "5672"))
RABBITMQ_USER = os.getenv("RABBITMQ_USER", "user")
RABBITMQ_PASSWORD = os.getenv("RABBITMQ_PASSWORD", "pass")
RABBITMQ_EXCHANGE = os.getenv("RABBITMQ_EXCHANGE", "video.events")

QUEUE_NAME = "audio-service.video-uploaded"
ROUTING_KEY = "video.uploaded"


def create_channel():
    """
    Create and return a channel connected to RabbitMQ, with the
    exchange and queue declared and bound.
    """
    credentials = PlainCredentials(RABBITMQ_USER, RABBITMQ_PASSWORD)
    params = pika.ConnectionParameters(
        host=RABBITMQ_HOST,
        port=RABBITMQ_PORT,
        credentials=credentials,
    )
    connection = pika.BlockingConnection(params)
    channel = connection.channel()

    # Ensure the exchange exists (must match the publisher)
    channel.exchange_declare(
        exchange=RABBITMQ_EXCHANGE,
        exchange_type="topic",
        durable=True,
    )

    # Declare a durable queue for this service
    channel.queue_declare(queue=QUEUE_NAME, durable=True)

    # Bind queue to the exchange for the specific routing key
    channel.queue_bind(
        queue=QUEUE_NAME,
        exchange=RABBITMQ_EXCHANGE,
        routing_key=ROUTING_KEY,
    )

    return connection, channel


def handle_message(ch, method, properties, body: bytes):
    """
    Callback for incoming messages from RabbitMQ.
    """
    try:
        payload = json.loads(body.decode("utf-8"))
        video_id = payload.get("video_id")

        logger.info(
            "Received video.uploaded event",
            extra={"video_id": video_id},
        )

        # TODO: In the next step we will:
        #  - download the video from MinIO
        #  - extract audio using ffmpeg
        #  - upload audio file back to MinIO
    except Exception as exc:
        logger.exception(f"Failed to process message: {exc}")
    finally:
        # Always acknowledge the message so it will not be re-delivered
        ch.basic_ack(delivery_tag=method.delivery_tag)


def main():
    """
    Main loop: connect to RabbitMQ and start consuming messages.
    Will retry on connection errors.
    """
    while True:
        try:
            logger.info("Audio service connecting to RabbitMQ...")
            connection, channel = create_channel()
            logger.info("Audio service connected. Waiting for messages...")

            channel.basic_qos(prefetch_count=1)
            channel.basic_consume(
                queue=QUEUE_NAME,
                on_message_callback=handle_message,
            )

            channel.start_consuming()
        except Exception as exc:
            logger.exception(f"Connection to RabbitMQ lost: {exc}")
            logger.info("Retrying in 5 seconds...")
            time.sleep(5)


if __name__ == "__main__":
    main()
