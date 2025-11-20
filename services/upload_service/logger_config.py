import logging
import json
import sys

SERVICE_NAME = "upload_service"


class JsonFormatter(logging.Formatter):
    """
    Format log records as JSON so they can be easily parsed by log aggregators.
    """

    def format(self, record: logging.LogRecord) -> str:
        log_data = {
            "level": record.levelname,
            "service": SERVICE_NAME,
            "message": record.getMessage(),
        }
        # Optional fields that we might pass via the `extra` argument
        if hasattr(record, "video_id"):
            log_data["video_id"] = record.video_id
        if hasattr(record, "trace_id"):
            log_data["trace_id"] = record.trace_id
        return json.dumps(log_data)


def get_logger() -> logging.Logger:
    """
    Configure and return a logger for this service.
    """
    logger = logging.getLogger(SERVICE_NAME)
    logger.setLevel(logging.INFO)

    # Avoid adding multiple handlers if this function is called more than once
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(JsonFormatter())
        logger.addHandler(handler)

    return logger


logger = get_logger()
