import json
import os
import pika
from pika.credentials import PlainCredentials
from logger_config import logger

# Load environment variables
RABBITMQ_HOST = os.getenv("RABBITMQ_HOST")
RABBITMQ_PORT = int(os.getenv("RABBITMQ_PORT", 5672))
RABBITMQ_USER = os.getenv("RABBITMQ_DEFAULT_USER")
RABBITMQ_PASSWORD = os.getenv("RABBITMQ_DEFAULT_PASS")
QUEUE_NAME = os.getenv("QUEUE_VIDEO_PROCESSING", "video_processing_queue")

def publish_video_uploaded_event(video_id: str, bucket: str, object_name: str) -> None:
    """
    Publishes a message directly to the video processing queue.
    """
    if not all([RABBITMQ_HOST, RABBITMQ_USER, RABBITMQ_PASSWORD]):
        logger.error("Missing RabbitMQ environment variables.")
        return

    payload = {
        "video_id": video_id,
        "bucket": bucket,
        "object_name": object_name,
    }
    body = json.dumps(payload).encode("utf-8")

    connection = None
    try:
        credentials = PlainCredentials(RABBITMQ_USER, RABBITMQ_PASSWORD)
        params = pika.ConnectionParameters(
            host=RABBITMQ_HOST, 
            port=RABBITMQ_PORT, 
            credentials=credentials
        )
        connection = pika.BlockingConnection(params)
        channel = connection.channel()

        # Declare the queue to ensure it exists
        channel.queue_declare(queue=QUEUE_NAME, durable=True)

        # Publish directly to the queue (default exchange)
        channel.basic_publish(
            exchange="",
            routing_key=QUEUE_NAME,
            body=body,
            properties=pika.BasicProperties(
                delivery_mode=2,  # Make message persistent
            ),
        )
        logger.info(
            "Published message to queue", 
            extra={"queue": QUEUE_NAME, "video_id": video_id}
        )

    except Exception as exc:
        logger.exception(
            f"Failed to publish event: {exc}", 
            extra={"video_id": video_id}
        )
    finally:
        if connection:
            connection.close()