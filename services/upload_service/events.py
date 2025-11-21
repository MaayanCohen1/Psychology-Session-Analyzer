import json
import os

import pika
from pika.adapters.blocking_connection import BlockingChannel
from pika.credentials import PlainCredentials

from logger_config import logger

RABBITMQ_HOST = os.getenv("RABBITMQ_HOST", "rabbitmq")
RABBITMQ_PORT = int(os.getenv("RABBITMQ_PORT", "5672"))
RABBITMQ_USER = os.getenv("RABBITMQ_USER", "user")
RABBITMQ_PASSWORD = os.getenv("RABBITMQ_PASSWORD", "pass")
RABBITMQ_EXCHANGE = os.getenv("RABBITMQ_EXCHANGE", "video.events")

ROUTING_KEY_VIDEO_UPLOADED = "video.uploaded"


def _create_channel() -> BlockingChannel:
    """
    Create a new blocking channel to RabbitMQ.
    """
    credentials = PlainCredentials(RABBITMQ_USER, RABBITMQ_PASSWORD)
    params = pika.ConnectionParameters(
        host=RABBITMQ_HOST,
        port=RABBITMQ_PORT,
        credentials=credentials,
    )
    connection = pika.BlockingConnection(params)
    channel = connection.channel()

    # Ensure the exchange exists
    channel.exchange_declare(
        exchange=RABBITMQ_EXCHANGE,
        exchange_type="topic",
        durable=True,
    )
    return channel


def publish_video_uploaded_event(video_id: str, bucket: str, object_name: str) -> None:
    """
    Publish a 'video.uploaded' event so other services can react to it.
    """
    payload = {
        "event_type": "video.uploaded",
        "video_id": video_id,
        "bucket": bucket,
        "object_name": object_name,
    }

    body = json.dumps(payload).encode("utf-8")

    try:
        channel = _create_channel()
        channel.basic_publish(
            exchange=RABBITMQ_EXCHANGE,
            routing_key=ROUTING_KEY_VIDEO_UPLOADED,
            body=body,
            properties=pika.BasicProperties(
                content_type="application/json",
                delivery_mode=2,  # persistent
            ),
        )
        logger.info(
            "Published video.uploaded event",
            extra={"video_id": video_id},
        )
        channel.close()
    except Exception as exc:
        logger.exception(
            f"Failed to publish video.uploaded event: {exc}",
            extra={"video_id": video_id},
        )
        # For now we do not fail the request if event publish fails.
