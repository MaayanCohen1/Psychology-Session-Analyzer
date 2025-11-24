import os
import json
import psycopg2
from psycopg2.extras import Json
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

def init_db():
    """
    Creates the necessary tables if they do not exist.
    """
    create_table_query = """
    CREATE TABLE IF NOT EXISTS video_analysis (
        id SERIAL PRIMARY KEY,
        video_id VARCHAR(255) UNIQUE NOT NULL,
        analysis JSONB NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """
    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute(create_table_query)
        conn.commit()
        cur.close()
        logger.info("Database initialized and table ensured.")
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
    finally:
        if conn:
            conn.close()

def save_analysis_result(video_id: str, analysis_data: dict):
    """
    Saves the analysis result to the database.
    Uses UPSERT (Insert or Update) logic to handle re-analysis.
    """
    query = """
    INSERT INTO video_analysis (video_id, analysis)
    VALUES (%s, %s)
    ON CONFLICT (video_id) 
    DO UPDATE SET analysis = EXCLUDED.analysis, created_at = CURRENT_TIMESTAMP;
    """
    
    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        # Psycopg2 automatically adapts dict to JSONB if we dump it or use Json wrapper
        cur.execute(query, (video_id, json.dumps(analysis_data)))
        
        conn.commit()
        cur.close()
        logger.info(f"Analysis saved to DB for video: {video_id}")
        return True
    except Exception as e:
        logger.error(f"Failed to save analysis to DB: {e}")
        return False
    finally:
        if conn:
            conn.close()