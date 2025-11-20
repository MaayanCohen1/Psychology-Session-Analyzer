import os
import io
from typing import Tuple

from minio import Minio
from minio.error import S3Error

from logger_config import logger

MINIO_ENDPOINT = os.getenv("MINIO_ENDPOINT", "minio:9000")
MINIO_ACCESS_KEY = os.getenv("MINIO_ACCESS_KEY", "minioadmin")
MINIO_SECRET_KEY = os.getenv("MINIO_SECRET_KEY", "minioadmin123")
MINIO_BUCKET = os.getenv("MINIO_BUCKET", "therapy-videos")
MINIO_SECURE = os.getenv("MINIO_SECURE", "false").lower() == "true"

minio_client = Minio(
    MINIO_ENDPOINT,
    access_key=MINIO_ACCESS_KEY,
    secret_key=MINIO_SECRET_KEY,
    secure=MINIO_SECURE,
)


def ensure_bucket_exists() -> None:
    """
    Ensure that the target bucket exists in MinIO.
    """
    try:
        if not minio_client.bucket_exists(MINIO_BUCKET):
            logger.info(f"Bucket '{MINIO_BUCKET}' does not exist. Creating it.")
            minio_client.make_bucket(MINIO_BUCKET)
    except S3Error as exc:
        logger.exception(f"Failed to ensure bucket exists: {exc}")
        raise


def upload_video_file(data: bytes, object_name: str, content_type: str) -> Tuple[str, str]:
    """
    Upload a video file to MinIO.

    Returns a tuple of (bucket_name, object_name).
    """
    ensure_bucket_exists()

    data_stream = io.BytesIO(data)
    size = len(data)

    try:
        minio_client.put_object(
            bucket_name=MINIO_BUCKET,
            object_name=object_name,
            data=data_stream,
            length=size,
            content_type=content_type,
        )
        logger.info(
            f"Uploaded video to MinIO",
            extra={"object_name": object_name},
        )
        return MINIO_BUCKET, object_name
    except S3Error as exc:
        logger.exception(f"Failed to upload video to MinIO: {exc}")
        raise
