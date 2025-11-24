import os
import json
import time
import pika
import pika.exceptions
import redis
from logger_config import logger
from db_handler import init_db, save_analysis_result
from gpt_handler import analyze_transcript

# --- Configuration ---
RABBITMQ_HOST = os.getenv("RABBITMQ_HOST")
RABBITMQ_PORT = int(os.getenv("RABBITMQ_PORT", 5672))
RABBITMQ_USER = os.getenv("RABBITMQ_DEFAULT_USER")
RABBITMQ_PASSWORD = os.getenv("RABBITMQ_DEFAULT_PASS")

# Redis Configuration
REDIS_HOST = os.getenv("REDIS_HOST", "redis")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))

# Queues
INPUT_QUEUE = "analysis_processing_queue"

# Initialize Redis Client
redis_client = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=0, decode_responses=True)

def process_message(ch, method, properties, body):
    """
    Callback function to handle incoming transcriptions.
    """
    try:
        data = json.loads(body)
        video_id = data.get("video_id")
        utterances = data.get("utterances") # List of {speaker, text}

        logger.info(f"Received analysis task for video: {video_id}")

        # --- Step 1: Check Cache (Redis) ---
        # If we already analyzed this video, skip the LLM call
        cached_result = redis_client.get(video_id)
        if cached_result:
            logger.info(f"Cache HIT for {video_id}. Skipping LLM analysis.")
            # Ideally, we verify it's in DB too, but for now we assume consistency.
            ch.basic_ack(delivery_tag=method.delivery_tag)
            return
        
        logger.info(f"Cache MISS for {video_id}. Proceeding to LLM.")

        # --- Step 2: Call OpenAI (LLM) ---
        analysis_result = analyze_transcript(utterances)

        # --- Step 3: Save to Database (PostgreSQL) ---
        save_success = save_analysis_result(video_id, analysis_result)
        
        if save_success:
            # --- Step 4: Update Cache (Redis) ---
            # We store the result in Redis with an expiration (e.g., 1 hour or 1 day)
            # This prevents re-analyzing the same video immediately
            redis_client.setex(video_id, 3600, json.dumps(analysis_result))
            logger.info(f"Result cached in Redis for {video_id}")
            
            # Ack the message only if saved successfully
            ch.basic_ack(delivery_tag=method.delivery_tag)
        else:
            logger.error("Failed to save to DB. Nacking message.")
            # Re-queue the message to try again later
            ch.basic_nack(delivery_tag=method.delivery_tag, requeue=True)

    except Exception as e:
        logger.exception(f"Critical error in process_message: {e}")
        ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False) # Dead letter

def main():
    logger.info("Analysis Service Starting...")

    # Initialize Database Table
    init_db()

    # RabbitMQ Connection Logic (Retry)
    credentials = pika.PlainCredentials(RABBITMQ_USER, RABBITMQ_PASSWORD)
    params = pika.ConnectionParameters(host=RABBITMQ_HOST, port=RABBITMQ_PORT, credentials=credentials)
    
    connection = None
    while connection is None:
        try:
            connection = pika.BlockingConnection(params)
        except pika.exceptions.AMQPConnectionError:
            logger.warning("RabbitMQ is not ready. Retrying in 5 seconds...")
            time.sleep(5)

    channel = connection.channel()
    channel.queue_declare(queue=INPUT_QUEUE, durable=True)
    channel.basic_qos(prefetch_count=1)

    channel.basic_consume(queue=INPUT_QUEUE, on_message_callback=process_message)
    
    logger.info(f"Listening on {INPUT_QUEUE}...")
    channel.start_consuming()

if __name__ == "__main__":
    main()