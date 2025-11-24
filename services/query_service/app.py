from fastapi import FastAPI, HTTPException
from db_handler import get_all_videos, get_video_analysis
from logger_config import logger

app = FastAPI(title="Query Service - Psychology Analyzer")

@app.get("/health")
async def health():
    return {"status": "ok"}

@app.get("/analyses")
async def list_analyses():
    """
    Returns a list of all videos that have been analyzed.
    """
    logger.info("Request received: List all analyses")
    videos = get_all_videos()
    return {"count": len(videos), "videos": videos}

@app.get("/analyses/{video_id}")
async def get_analysis(video_id: str):
    """
    Returns the full detailed analysis for a specific video ID.
    """
    logger.info(f"Request received: Get analysis for {video_id}")
    
    analysis = get_video_analysis(video_id)
    
    if not analysis:
        raise HTTPException(status_code=404, detail="Video analysis not found")
    
    return analysis