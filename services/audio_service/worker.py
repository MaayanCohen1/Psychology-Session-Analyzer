import time

from logger_config import logger


def main():
    """
    Temporary worker loop that only logs that it is alive.
    In the next steps we will connect it to RabbitMQ.
    """
    logger.info("Audio service worker started, waiting for future messages...")
    while True:
        time.sleep(10)


if __name__ == "__main__":
    main()
