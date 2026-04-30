import os
import psycopg

def init_db():
    print("Connecting to the database...")
    conn = psycopg.connect(
        dbname=os.environ.get("DB_NAME", "loga"),
        user=os.environ.get("DB_USER", "postgres"),
        password=os.environ.get("DB_PASSWORD", "postgres"),
        host=os.environ.get("DB_HOST", "localhost"),
        port=os.environ.get("DB_PORT", "5432"),
    )
    cur = conn.cursor()

    print("Creating tables...")
    cur.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY,
            username VARCHAR(255) UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
    ''')

    cur.execute('''
        CREATE TABLE IF NOT EXISTS uploads (
            id SERIAL PRIMARY KEY,
            username VARCHAR(255) NOT NULL REFERENCES users(username) ON DELETE CASCADE,
            image_path TEXT NOT NULL,
            position VARCHAR(255),
            style VARCHAR(255),
            color VARCHAR(255),
            md5_hash VARCHAR(255),
            uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            favorite BOOLEAN DEFAULT FALSE,
            gemini_metadata JSONB
        )
    ''')

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
    cur.close()
    conn.close()
    print("Database initialization complete! Tables 'users' and 'uploads' have been created.")

if __name__ == "__main__":
    init_db()
