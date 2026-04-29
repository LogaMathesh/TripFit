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
    cur.execute("ALTER TABLE uploads ADD COLUMN IF NOT EXISTS gemini_metadata JSONB")
    
    # Phase 1: Profiles and Logs
    cur.execute('''
        CREATE TABLE IF NOT EXISTS user_profiles (
            id SERIAL PRIMARY KEY,
            username VARCHAR(255) UNIQUE NOT NULL REFERENCES users(username) ON DELETE CASCADE,
            gender VARCHAR(50),
            budget_level VARCHAR(100),
            sizes TEXT,
            style_preferences TEXT,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    cur.execute('''
        CREATE TABLE IF NOT EXISTS search_logs (
            id SERIAL PRIMARY KEY,
            username VARCHAR(255) REFERENCES users(username) ON DELETE CASCADE,
            raw_prompt TEXT NOT NULL,
            generated_query TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Phase 2: User Interactions
    cur.execute('''
        CREATE TABLE IF NOT EXISTS user_interactions (
            id SERIAL PRIMARY KEY,
            username VARCHAR(255) REFERENCES users(username) ON DELETE CASCADE,
            title TEXT,
            price VARCHAR(100),
            link TEXT,
            thumbnail TEXT,
            source VARCHAR(255),
            interaction_type VARCHAR(50),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
except Exception as e:
    print(f"Error executing schema migrations: {e}")
    conn.rollback()
