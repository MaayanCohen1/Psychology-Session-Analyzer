import uuid
import os
from fastapi import FastAPI, UploadFile, File, HTTPException, status
from logger_config import logger
from storage import upload_video_file, MINIO_BUCKET 
from events import publish_video_uploaded_event

app = FastAPI(title="Upload Service")

@app.get("/health")
async def health():
    """Health check endpoint."""
    logger.info("Health check called")
    return {"status": "ok"}

@app.post("/videos")
async def upload_video(file: UploadFile = File(...)):
    """
    Uploads a video, saves to MinIO, and triggers processing.
    """
    video_id = str(uuid.uuid4())
    object_name = f"raw-videos/{video_id}_{file.filename}"

    logger.info("Received upload request", extra={"video_id": video_id})

    try:
        # Note: Reading entire file into memory (not ideal for large files)
        file_bytes = await file.read()
        if not file_bytes:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Empty file upload is not allowed",
            )

        # Upload to MinIO
        upload_video_file(
            data=file_bytes,
            object_name=object_name,
            content_type=file.content_type or "application/octet-stream",
        )

        # Publish event to RabbitMQ
        publish_video_uploaded_event(
            video_id=video_id,
            bucket=MINIO_BUCKET,
            object_name=object_name,
        )

        return {
            "video_id": video_id,
            "bucket": MINIO_BUCKET,
            "object_name": object_name,
            "status": "processing_started"
        }

    except HTTPException:
        raise
    except Exception as exc:
        logger.exception(
            f"Unexpected error: {exc}", 
            extra={"video_id": video_id}
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        )