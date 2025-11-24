import os
from pathlib import Path
from typing import Optional

from minio import Minio
from minio.error import S3Error

from logger_config import logger

# Environment variables only — no hard-coded secrets
MINIO_ENDPOINT = os.getenv("MINIO_ENDPOINT", "minio:9000")
MINIO_ACCESS_KEY = os.getenv("MINIO_ACCESS_KEY")
MINIO_SECRET_KEY = os.getenv("MINIO_SECRET_KEY")
MINIO_BUCKET = os.getenv("MINIO_BUCKET", "therapy-videos")
MINIO_SECURE = os.getenv("MINIO_SECURE", "false").lower() == "true"

# Local directory where downloaded video/audio files will be saved
DOWNLOAD_DIR = Path("/tmp/audio_service/videos")
AUDIO_DIR = Path("/tmp/audio_service/audio")


def get_minio_client() -> Minio:
    """
    Create and return a MinIO client instance.
    """
    client = Minio(
        MINIO_ENDPOINT,
        access_key=MINIO_ACCESS_KEY,
        secret_key=MINIO_SECRET_KEY,
        secure=MINIO_SECURE,
    )
    return client


def download_video_file(bucket: str, object_name: str, video_id: str) -> Optional[Path]:
    """
    Download a video object from MinIO to a local file.
    Returns the local file path or None if download failed.
    """
    client = get_minio_client()

    DOWNLOAD_DIR.mkdir(parents=True, exist_ok=True)
    local_path = DOWNLOAD_DIR / f"{video_id}.mp4"

    try:
        logger.info(
            "Downloading video from MinIO",
            extra={"video_id": video_id, "bucket": bucket, "object_name": object_name},
        )

        client.fget_object(
            bucket_name=bucket,
            object_name=object_name,
            file_path=str(local_path),
        )

        logger.info(
            "Downloaded video from MinIO",
            extra={"video_id": video_id, "local_path": str(local_path)},
        )

        return local_path

    except S3Error as exc:
        logger.exception(
            f"Failed to download video from MinIO: {exc}",
            extra={"video_id": video_id, "bucket": bucket, "object_name": object_name},
        )
        return None
    except Exception as exc:
        logger.exception(
            f"Unexpected error while downloading video: {exc}",
            extra={"video_id": video_id},
        )
        return None


def upload_audio_file(bucket: str, local_path: Path, object_name: str) -> bool:
    """
    Upload an extracted MP3 audio file to MinIO.
    Returns True on success, False on failure.
    """
    client = get_minio_client()

    try:
        logger.info(
            "Uploading audio file to MinIO",
            extra={"bucket": bucket, "object_name": object_name},
        )

        client.fput_object(
            bucket_name=bucket,
            object_name=object_name,
            file_path=str(local_path),
        )

        logger.info(
            "Uploaded audio file to MinIO",
            extra={"bucket": bucket, "object_name": object_name},
        )
        return True

    except S3Error as exc:
        logger.exception(
            f"Failed to upload audio file to MinIO: {exc}",
            extra={"bucket": bucket, "object_name": object_name},
        )
        return False
    except Exception as exc:
        logger.exception(
            f"Unexpected error while uploading audio file: {exc}",
            extra={"bucket": bucket, "object_name": object_name},
        )
        return False
