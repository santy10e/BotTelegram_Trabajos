import sqlite3

DB_NAME = "jobs.db"

def get_connection():
    return sqlite3.connect(DB_NAME)

def init_db():
    conn = get_connection()
    c = conn.cursor()

    c.execute("""
        CREATE TABLE IF NOT EXISTS jobs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT,
            company TEXT,
            location TEXT,
            link TEXT UNIQUE,
            source TEXT,
            created_at TEXT
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS subscribers (
            chat_id INTEGER PRIMARY KEY,
            created_at TEXT
        )
    """)

    conn.commit()
    conn.close()
    
def save_job_if_new(job):
    conn = get_connection()
    c = conn.cursor()
    try:
        c.execute("""
            INSERT INTO jobs (title, company, location, link, source, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            job["title"],
            job["company"],
            job["location"],
            job["link"],
            job["source"],
            datetime.utcnow().isoformat()
        ))
        conn.commit()
        conn.close()
        return True   # ES NUEVA
    except sqlite3.IntegrityError:
        conn.close()
        return False  # YA EXISTÍA