import os
import json
import datetime
import psycopg2
from PIL import Image
from .celery_setup import celery_instance
from services.gemini_service import analyze_dress_image

def get_db_connection():
    return psycopg2.connect(
        dbname=os.environ.get("DB_NAME", "loga"),
        user=os.environ.get("DB_USER", "postgres"),
        password=os.environ.get("DB_PASSWORD", "loga"),
        host=os.environ.get("DB_HOST", "localhost"),
        port=os.environ.get("DB_PORT", "5432"),
    )

@celery_instance.task(bind=True, name='tasks.process_classification')
def process_classification(self, file_path, username, image_hash):
    try:
        # Validate image safely
        with Image.open(file_path) as img:
            img.verify()
        
        # Run Classification via Gemini API
        metadata = analyze_dress_image(file_path)
        
        position = metadata.get("category", "upper")
        style = metadata.get("style", "casual")
        color = metadata.get("primary_color", "black")

        # Save to Database
        conn = get_db_connection()
        cur = conn.cursor()
        
        gemini_metadata_json = json.dumps(metadata)
        
        cur.execute(
            "INSERT INTO uploads (username, image_path, position, style, color, md5_hash, uploaded_at, gemini_metadata) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)",
            (username, file_path, position, style, color, image_hash, datetime.datetime.now(), gemini_metadata_json)
        )
        conn.commit()
        cur.close()
        conn.close()

        filename = os.path.basename(file_path)
        return {
            'status': 'completed',
            'position': position,
            'style': style,
            'color': color,
            'image_url': f"http://localhost:5000/image/{filename}"
        }
        
    except Exception as e:
        print(f"Task Failed: {e}")
        # Return a failure state instead of unknown so your frontend can show the error
        raise Exception(f"AI Classification failed: {str(e)}")