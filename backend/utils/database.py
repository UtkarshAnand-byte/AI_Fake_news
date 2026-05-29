import os
import json
import psycopg2
from psycopg2 import pool
from psycopg2.extras import RealDictCursor

# Primary database configuration
DEFAULT_DB_URI = "postgresql://neondb_owner:npg_mzaEZWONv0R5@ep-lucky-sunset-aqr2t66y-pooler.c-8.us-east-1.aws.neon.tech/neondb?sslmode=require&channel_binding=require"
DB_URI = os.getenv("DATABASE_URL", DEFAULT_DB_URI)

# Global pool instance
connection_pool = None
db_active = False

def init_db():
    """
    Initialize the PostgreSQL connection pool and create the analyses table.
    Gracefully degrades to in-memory persistence if connection fails.
    """
    global connection_pool, db_active
    print("[Database Engine] Connecting to Neon PostgreSQL database...")
    try:
        connection_pool = pool.ThreadedConnectionPool(
            minconn=1,
            maxconn=10,
            dsn=DB_URI
        )
        
        # Connect to run migrations
        conn = connection_pool.getconn()
        try:
            with conn.cursor() as cursor:
                # Schema creation statement
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS analyses (
                        id SERIAL PRIMARY KEY,
                        title TEXT NOT NULL,
                        text TEXT NOT NULL,
                        prediction VARCHAR(20) NOT NULL,
                        confidence DOUBLE PRECISION NOT NULL,
                        engine VARCHAR(100) NOT NULL,
                        metrics JSONB NOT NULL,
                        explanation JSONB NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    );
                """)
                # Schema evolution: add feedback column if not exists
                cursor.execute("""
                    ALTER TABLE analyses ADD COLUMN IF NOT EXISTS feedback VARCHAR(20) DEFAULT 'unverified';
                """)
                conn.commit()
            print("[Database Engine] PostgreSQL schema validated successfully. Persistent history active.")
            db_active = True
        finally:
            connection_pool.putconn(conn)
            
    except Exception as e:
        print(f"[Database Engine ERROR] Failed to connect to database: {e}.")
        print("[Database Engine WARNING] Graceful fallback active. Running in-memory log mode.")
        db_active = False
        connection_pool = None

# Fallback In-Memory Storage for history logs if Neon is down
in_memory_cache = []

def insert_analysis(title: str, text: str, prediction: str, confidence: float, engine: str, metrics: dict, explanation: list) -> bool:
    """
    Saves an analysis record to the database, falling back to in-memory list if offline.
    """
    global db_active
    
    # Prune extreme text details to avoid database bloat (e.g. cap at 5000 chars)
    shortened_text = text if len(text) <= 5000 else text[:5000] + "..."
    
    if db_active and connection_pool:
        try:
            conn = connection_pool.getconn()
            try:
                with conn.cursor() as cursor:
                    cursor.execute("""
                        INSERT INTO analyses (title, text, prediction, confidence, engine, metrics, explanation)
                        VALUES (%s, %s, %s, %s, %s, %s, %s)
                    """, (
                        title, 
                        shortened_text, 
                        prediction, 
                        confidence, 
                        engine, 
                        json.dumps(metrics), 
                        json.dumps(explanation)
                    ))
                    conn.commit()
                return True
            finally:
                connection_pool.putconn(conn)
        except Exception as e:
            print(f"[Database Engine ERROR] Failed to insert record: {e}. Falling back to in-memory record.")
            # Fall back to in memory logic below
    
    # In-memory storage logic
    record = {
        "id": len(in_memory_cache) + 1,
        "title": title,
        "text": shortened_text,
        "prediction": prediction,
        "confidence": confidence,
        "engine": engine,
        "metrics": metrics,
        "explanation": explanation,
        "feedback": "unverified",
        "created_at": "Present Time"
    }
    in_memory_cache.insert(0, record)
    if len(in_memory_cache) > 20:
        in_memory_cache.pop()
    return True

def get_recent_analyses(limit: int = 10) -> list:
    """
    Fetches the most recent analysis entries.
    """
    global db_active
    if db_active and connection_pool:
        try:
            conn = connection_pool.getconn()
            try:
                # Use RealDictCursor to map keys directly into JSON responses
                with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                    cursor.execute("""
                        SELECT id, title, text, prediction, confidence, engine, metrics, explanation, feedback, created_at
                        FROM analyses
                        ORDER BY id DESC
                        LIMIT %s
                    """, (limit,))
                    records = cursor.fetchall()
                    
                    # Convert psycopg2 RealDict Row instances and format datetime keys
                    result_list = []
                    for row in records:
                        formatted_row = dict(row)
                        formatted_row["created_at"] = row["created_at"].strftime("%H:%M") if row["created_at"] else ""
                        result_list.append(formatted_row)
                    return result_list
            finally:
                connection_pool.putconn(conn)
        except Exception as e:
            print(f"[Database Engine ERROR] Failed to fetch query: {e}. Falling back to in-memory storage.")
            # Degrade to in-memory
            
    return in_memory_cache[:limit]

def clear_all_analyses() -> bool:
    """
    Truncates the analyses table and wipes in-memory caches.
    """
    global db_active, in_memory_cache
    in_memory_cache.clear()
    
    if db_active and connection_pool:
        try:
            conn = connection_pool.getconn()
            try:
                with conn.cursor() as cursor:
                    cursor.execute("TRUNCATE TABLE analyses RESTART IDENTITY;")
                    conn.commit()
                print("[Database Engine] History tables truncated successfully.")
                return True
            finally:
                connection_pool.putconn(conn)
        except Exception as e:
            print(f"[Database Engine ERROR] Failed to clear tables: {e}.")
            return False
            
    return True

def update_analysis_feedback(analysis_id: int, feedback: str) -> bool:
    """
    Updates the feedback status (e.g. 'correct' or 'incorrect') for a specific analysis item.
    """
    global db_active
    if db_active and connection_pool:
        try:
            conn = connection_pool.getconn()
            try:
                with conn.cursor() as cursor:
                    cursor.execute("""
                        UPDATE analyses
                        SET feedback = %s
                        WHERE id = %s
                    """, (feedback, analysis_id))
                    rows_updated = cursor.rowcount
                    conn.commit()
                return rows_updated > 0
            finally:
                connection_pool.putconn(conn)
        except Exception as e:
            print(f"[Database Engine ERROR] Failed to update feedback for record {analysis_id}: {e}")
            return False
            
    # Fallback to in-memory cache update
    for record in in_memory_cache:
        if record["id"] == analysis_id:
            record["feedback"] = feedback
            return True
    return False

def get_feedback_training_data() -> list:
    """
    Fetches all analysis records that have user feedback to serve as training samples.
    If prediction is 'Fake' and feedback is 'correct', or prediction is 'Real' and feedback is 'incorrect', label is 1 (Fake).
    If prediction is 'Real' and feedback is 'correct', or prediction is 'Fake' and feedback is 'incorrect', label is 0 (Real).
    """
    global db_active
    samples = []
    
    if db_active and connection_pool:
        try:
            conn = connection_pool.getconn()
            try:
                with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                    cursor.execute("""
                        SELECT text, prediction, feedback
                        FROM analyses
                        WHERE feedback IN ('correct', 'incorrect')
                    """)
                    records = cursor.fetchall()
                    for row in records:
                        text = row["text"]
                        pred = row["prediction"]
                        fb = row["feedback"]
                        
                        # Determine actual label: 1 for Fake, 0 for Real
                        if (pred == "Fake" and fb == "correct") or (pred == "Real" and fb == "incorrect"):
                            label = 1
                        else:
                            label = 0
                        samples.append({"text": text, "label": label})
            finally:
                connection_pool.putconn(conn)
        except Exception as e:
            print(f"[Database Engine ERROR] Failed to fetch feedback training samples: {e}")
            
    # Fallback/merge with in-memory feedback samples
    for record in in_memory_cache:
        fb = record.get("feedback", "unverified")
        if fb in ('correct', 'incorrect'):
            text = record["text"]
            pred = record["prediction"]
            if (pred == "Fake" and fb == "correct") or (pred == "Real" and fb == "incorrect"):
                label = 1
            else:
                label = 0
            # Avoid duplicates in list
            if not any(s["text"] == text for s in samples):
                samples.append({"text": text, "label": label})
                
    return samples
