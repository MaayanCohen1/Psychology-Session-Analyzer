import os
import psycopg2
from psycopg2.extras import RealDictCursor
from logger_config import logger

# Database Configuration
DB_HOST = os.getenv("POSTGRES_HOST", "postgres")
DB_NAME = os.getenv("POSTGRES_DB", "therapy_db")
DB_USER = os.getenv("POSTGRES_USER", "postgres")
DB_PASS = os.getenv("POSTGRES_PASSWORD", "postgres")
DB_PORT = int(os.getenv("POSTGRES_PORT", 5432))

def get_db_connection():
    """
    Establishes a connection to the PostgreSQL database.
    """
    try:
        conn = psycopg2.connect(
            host=DB_HOST,
            database=DB_NAME,
            user=DB_USER,
            password=DB_PASS,
            port=DB_PORT
        )
        return conn
    except Exception as e:
        logger.error(f"Failed to connect to database: {e}")
        raise

def get_all_videos():
    """
    Fetches a list of all analyzed videos (ID and Creation Date).
    Using RealDictCursor to get results as dictionaries (JSON-ready).
    """
    conn = get_db_connection()
    try:
        cur = conn.cursor(cursor_factory=RealDictCursor)
        # We only select the ID and Date, not the full heavy analysis
        cur.execute("SELECT id, video_id, created_at FROM video_analysis ORDER BY created_at DESC;")
        rows = cur.fetchall()
        return rows
    except Exception as e:
        logger.error(f"Error fetching all videos: {e}")
        return []
    finally:
        conn.close()

def get_video_analysis(video_id: str):
    """
    Fetches the full analysis JSON for a specific video ID.
    """
    conn = get_db_connection()
    try:
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute("SELECT * FROM video_analysis WHERE video_id = %s;", (video_id,))
        row = cur.fetchone()
        return row
    except Exception as e:
        logger.error(f"Error fetching analysis for {video_id}: {e}")
        return None
    finally:
        conn.close()