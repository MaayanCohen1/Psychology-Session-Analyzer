import os
from minio import Minio
from minio.error import S3Error
from logger_config import logger

# MinIO Configuration from Environment Variables
MINIO_ENDPOINT = os.getenv("MINIO_ENDPOINT", "minio:9000")
MINIO_ACCESS_KEY = os.getenv("MINIO_ACCESS_KEY", "minioadmin")
MINIO_SECRET_KEY = os.getenv("MINIO_SECRET_KEY", "minioadmin123")
MINIO_SECURE = os.getenv("MINIO_SECURE", "false").lower() == "true"

def get_minio_client():
    """
    Initialize MinIO client.
    """
    return Minio(
        endpoint=MINIO_ENDPOINT,
        access_key=MINIO_ACCESS_KEY,
        secret_key=MINIO_SECRET_KEY,
        secure=MINIO_SECURE,
    )

def download_file(bucket_name: str, object_name: str, local_path: str) -> bool:
    """
    Downloads a file from MinIO to the local file system.
    Returns True if successful, False otherwise.
    """
    client = get_minio_client()

    try:
        logger.info(
            f"Downloading file from MinIO...",
            extra={"bucket": bucket_name, "object": object_name}
        )

        client.fget_object(
            bucket_name=bucket_name,
            object_name=object_name,
            file_path=str(local_path),
        )

        logger.info(f"Download successful: {local_path}")
        return True

    except S3Error as exc:
        logger.error(f"MinIO S3 Error: {exc}")
        return False
    except Exception as exc:
        logger.error(f"Unexpected error during download: {exc}")
        return False