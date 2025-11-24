import logging
import sys

# Format: Time - Service Name - Level - Message
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

def get_logger(service_name: str):
    """
    Creates a standard logger that writes to stdout (for Docker/DataDog).
    """
    logger = logging.getLogger(service_name)
    logger.setLevel(logging.INFO)

    # Output logs to the console (stdout)
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(logging.Formatter(LOG_FORMAT))
    logger.addHandler(handler)

    return logger

# Create the logger instance
logger = get_logger("transcription_service")