import os
import json
import time
import pika
import pika.exceptions
from pathlib import Path

from storage import download_file
from assembly_client import AssemblyAIClient
from logger_config import logger

RABBITMQ_HOST = os.getenv("RABBITMQ_HOST")
RABBITMQ_PORT = int(os.getenv("RABBITMQ_PORT", 5672))
RABBITMQ_USER = os.getenv("RABBITMQ_DEFAULT_USER")
RABBITMQ_PASSWORD = os.getenv("RABBITMQ_DEFAULT_PASS")

MINIO_BUCKET = os.getenv("MINIO_BUCKET")
ASSEMBLYAI_API_KEY = os.getenv("ASSEMBLYAI_API_KEY")

INPUT_QUEUE = os.getenv("QUEUE_AUDIO_PROCESSING", "audio_processing_queue")
OUTPUT_QUEUE = "analysis_processing_queue"

DOWNLOAD_DIR = Path("/tmp/transcription")


def send_to_analysis(channel, video_id, transcript_text, utterances):
    payload = {
        "video_id": video_id,
        "transcript_text": transcript_text,
        "utterances": utterances
    }
    
    channel.queue_declare(queue=OUTPUT_QUEUE, durable=True)
    
    channel.basic_publish(
        exchange="",
        routing_key=OUTPUT_QUEUE,
        body=json.dumps(payload),
        properties=pika.BasicProperties(delivery_mode=2)
    )
    logger.info("Sent transcription result to analysis queue", extra={"video_id": video_id})


def process_message(ch, method, properties, body):
    local_file_path = None
    
    try:
        data = json.loads(body)
        video_id = data.get("video_id")
        bucket = data.get("bucket")
        audio_object_name = data.get("audio_object_name")

        logger.info(f"Processing transcription task for: {video_id}")

        DOWNLOAD_DIR.mkdir(parents=True, exist_ok=True)
        local_file_path = DOWNLOAD_DIR / f"{video_id}.mp3"
        
        success = download_file(bucket, audio_object_name, str(local_file_path))
        if not success:
            logger.error("Failed to download audio file. Acking message to avoid loop.")
            ch.basic_ack(delivery_tag=method.delivery_tag)
            return

        client = AssemblyAIClient(ASSEMBLYAI_API_KEY)
        
        upload_url = client.upload_file(str(local_file_path))
        
        transcript_id = client.transcribe(upload_url)
        
        text, utterances = client.get_result(transcript_id)

        send_to_analysis(ch, video_id, text, utterances)

        ch.basic_ack(delivery_tag=method.delivery_tag)
        logger.info(f"Task completed for {video_id}")

    except Exception as e:
        logger.exception(f"Error processing message: {e}")
        ch.basic_ack(delivery_tag=method.delivery_tag)
        
    finally:
        if local_file_path and local_file_path.exists():
            try:
                os.remove(local_file_path)
            except OSError:
                pass


def main():
    logger.info("Transcription Service Starting...")
    
    if not ASSEMBLYAI_API_KEY:
        logger.critical("ASSEMBLYAI_API_KEY is missing! Service cannot start.")
        return

    credentials = pika.PlainCredentials(RABBITMQ_USER, RABBITMQ_PASSWORD)
    params = pika.ConnectionParameters(host=RABBITMQ_HOST, port=RABBITMQ_PORT, credentials=credentials)

    connection = None
    
    # Retry logic for RabbitMQ connection
    while connection is None:
        try:
            connection = pika.BlockingConnection(params)
        except pika.exceptions.AMQPConnectionError:
            logger.warning("RabbitMQ is not ready yet. Retrying in 5 seconds...")
            time.sleep(5)

    channel = connection.channel()
    
    # Ensure the input queue exists
    channel.queue_declare(queue=INPUT_QUEUE, durable=True)
    
    # Process 1 message at a time (Fair dispatch)
    channel.basic_qos(prefetch_count=1)
    
    channel.basic_consume(queue=INPUT_QUEUE, on_message_callback=process_message)
    
    logger.info(f"Listening for messages on {INPUT_QUEUE}...")
    channel.start_consuming()


if __name__ == "__main__":
    main()