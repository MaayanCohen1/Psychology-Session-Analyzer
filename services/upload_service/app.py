from fastapi import FastAPI
from logger_config import logger

app = FastAPI(title="Upload Service")


@app.get("/health")
async def health():
    """
    Simple health check endpoint to verify the service is running.
    """
    logger.info("Health check called")
    return {"status": "ok"}
