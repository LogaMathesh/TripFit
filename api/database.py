import os
import psycopg
from dotenv import load_dotenv
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

load_dotenv()

DB_URL = os.environ.get("SUPABASE_DB_URL")

def normalize_db_url(db_url):
    parts = urlsplit(db_url)
    query = parse_qsl(parts.query, keep_blank_values=True)
    filtered_query = [(key, value) for key, value in query if key != "pgbouncer"]
    return urlunsplit((parts.scheme, parts.netloc, parts.path, urlencode(filtered_query), parts.fragment))

def get_connection():
    if DB_URL:
        return psycopg.connect(normalize_db_url(DB_URL), autocommit=False, prepare_threshold=None)

    return psycopg.connect(
        dbname=os.environ.get("DB_NAME", "postgres"),
        user=os.environ.get("DB_USER", "postgres"),
        password=os.environ.get("DB_PASSWORD", "postgres"),
        host=os.environ.get("DB_HOST", "localhost"),
        port=os.environ.get("DB_PORT", "5432"),
    )
