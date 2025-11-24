import os
import json
import logging
import time
import pika
import pika.exceptions

from storage import download_video_file, upload_audio_file
from extractor import extract_audio

# Configure Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("audio_service")

# Load configuration from environment variables
RABBITMQ_HOST = os.getenv("RABBITMQ_HOST")
RABBITMQ_PORT = int(os.getenv("RABBITMQ_PORT", 5672))
RABBITMQ_USER = os.getenv("RABBITMQ_DEFAULT_USER")
RABBITMQ_PASSWORD = os.getenv("RABBITMQ_DEFAULT_PASS")
MINIO_BUCKET = os.getenv("MINIO_BUCKET")

# Queue names
INPUT_QUEUE = os.getenv("QUEUE_VIDEO_PROCESSING", "video_processing_queue")
OUTPUT_QUEUE = os.getenv("QUEUE_AUDIO_PROCESSING", "audio_processing_queue")

def send_audio_ready_event(channel, video_id: str, audio_object_name: str):
    """
    Publishes a message to the next queue (audio_processing_queue).
    """
    payload = {
        "video_id": video_id,
        "bucket": MINIO_BUCKET,
        "audio_object_name": audio_object_name,
    }
    
    channel.queue_declare(queue=OUTPUT_QUEUE, durable=True)
    
    channel.basic_publish(
        exchange="",
        routing_key=OUTPUT_QUEUE,
        body=json.dumps(payload),
        properties=pika.BasicProperties(delivery_mode=2)
    )
    logger.info(
        "Sent task to transcription queue", 
        extra={"video_id": video_id}
    )

def process_message(ch, method, properties, body):
    """
    Callback function to process incoming messages.
    """
    try:
        data = json.loads(body)
        video_id = data.get("video_id")
        bucket = data.get("bucket")
        object_name = data.get("object_name")

        logger.info(f"Processing video: {video_id}")

        # 1. Download video
        local_video_path = download_video_file(bucket, object_name, video_id)
        if not local_video_path:
            logger.error("Failed to download video, skipping.")
            ch.basic_ack(delivery_tag=method.delivery_tag)
            return

        # 2. Extract audio
        local_audio_path = f"/tmp/audio_service/audio/{video_id}.mp3"
        extraction_success = extract_audio(local_video_path, local_audio_path)
        
        if not extraction_success:
            logger.error("Audio extraction failed, skipping.")
            ch.basic_ack(delivery_tag=method.delivery_tag)
            return

        # 3. Upload audio
        audio_object_name = f"processed-audio/{video_id}.mp3"
        upload_success = upload_audio_file(MINIO_BUCKET, local_audio_path, audio_object_name)

        if upload_success:
            # 4. Notify next service
            send_audio_ready_event(ch, video_id, audio_object_name)
        
        ch.basic_ack(delivery_tag=method.delivery_tag)
        
        # Cleanup
        if os.path.exists(local_video_path):
            os.remove(local_video_path)
        if os.path.exists(local_audio_path):
            os.remove(local_audio_path)

    except Exception as e:
        logger.exception(f"Error processing message: {e}")
        ch.basic_ack(delivery_tag=method.delivery_tag)

def main():
    logger.info("Audio Service Starting...")

    if not all([RABBITMQ_USER, RABBITMQ_PASSWORD, RABBITMQ_HOST]):
        logger.critical("Missing RabbitMQ environment variables. Exiting.")
        return

    credentials = pika.PlainCredentials(RABBITMQ_USER, RABBITMQ_PASSWORD)
    params = pika.ConnectionParameters(
        host=RABBITMQ_HOST, 
        port=RABBITMQ_PORT, 
        credentials=credentials
    )

    # --- מנגנון ה-RETRY החדש ---
    connection = None
    while connection is None:
        try:
            connection = pika.BlockingConnection(params)
        except pika.exceptions.AMQPConnectionError:
            logger.warning("RabbitMQ is not ready yet. Retrying in 5 seconds...")
            time.sleep(5)
    # ---------------------------

    try:
        channel = connection.channel()

        channel.queue_declare(queue=INPUT_QUEUE, durable=True)
        channel.basic_qos(prefetch_count=1)

        channel.basic_consume(
            queue=INPUT_QUEUE, 
            on_message_callback=process_message
        )

        logger.info(f"Listening on {INPUT_QUEUE}...")
        channel.start_consuming()

    except Exception as e:
        logger.error(f"Connection failed: {e}")

if __name__ == "__main__":
    main()