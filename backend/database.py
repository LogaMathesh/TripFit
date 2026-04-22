import os
import psycopg2

def get_connection():
    conn = psycopg2.connect(
        dbname=os.environ.get("DB_NAME", "loga"),
        user=os.environ.get("DB_USER", "postgres"),
        password=os.environ.get("DB_PASSWORD", "loga"),
        host=os.environ.get("DB_HOST", "localhost"),
        port=os.environ.get("DB_PORT", "5432"),
    )
    return conn

# Export a single global connection and cursor to preserve existing app behavior
conn = get_connection()
cur = conn.cursor()

# Database migration / schema updates
try:
    cur.execute("ALTER TABLE uploads ADD COLUMN IF NOT EXISTS favorite BOOLEAN DEFAULT FALSE")
    conn.commit()
except Exception as e:
    print(f"Error adding favorite column: {e}")
    conn.rollback()
