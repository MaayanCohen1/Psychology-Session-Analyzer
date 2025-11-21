import uuid

from fastapi import FastAPI, UploadFile, File, HTTPException, status

from logger_config import logger
from storage import upload_video_file
from events import publish_video_uploaded_event

app = FastAPI(title="Upload Service")


@app.get("/health")
async def health():
    """
    Simple health check endpoint to verify the service is running.
    """
    logger.info("Health check called")
    return {"status": "ok"}


@app.post("/videos")
async def upload_video(file: UploadFile = File(...)):
    """
    Upload a video file, store it in MinIO, and publish an event.
    """
    video_id = str(uuid.uuid4())
    object_name = f"raw-videos/{video_id}_{file.filename}"
    bucket = "therapy-videos"

    logger.info(
        "Received video upload request",
        extra={"video_id": video_id},
    )

    try:
        file_bytes = await file.read()
        if not file_bytes:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Empty file upload is not allowed",
            )

        upload_video_file(
            data=file_bytes,
            object_name=object_name,
            content_type=file.content_type or "application/octet-stream",
        )

        publish_video_uploaded_event(
            video_id=video_id,
            bucket=bucket,
            object_name=object_name,
        )

        logger.info(
            "Video uploaded and event published",
            extra={"video_id": video_id, "object_name": object_name},
        )

        return {
            "video_id": video_id,
            "bucket": bucket,
            "object_name": object_name,
        }

    except HTTPException:
        raise
    except Exception as exc:
        logger.exception(
            f"Unexpected error while uploading video: {exc}",
            extra={"video_id": video_id},
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to upload video",
        )
