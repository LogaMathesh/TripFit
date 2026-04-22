import os
import hashlib
import datetime
import psycopg2
from flask import Blueprint, request, jsonify
from werkzeug.utils import secure_filename
from celery.result import AsyncResult
from .celery_setup import celery_instance

# 1. Redefine these here to completely avoid importing from app.py
UPLOAD_FOLDER = 'uploaded_images'
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "webp"}

def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

def get_db_connection():
    return psycopg2.connect(
        dbname=os.environ.get("DB_NAME", "loga"),
        user=os.environ.get("DB_USER", "postgres"),
        password=os.environ.get("DB_PASSWORD", "loga"),
        host=os.environ.get("DB_HOST", "localhost"),
        port=os.environ.get("DB_PORT", "5432"),
    )

# Create a Blueprint
async_bp = Blueprint('async_bp', __name__)

@async_bp.route('/classify-async', methods=['POST'])
def classify_async_route():
    image_file = request.files.get('image')
    username = request.form.get('username')

    if not image_file or not username:
        return jsonify({'error': 'Image or username missing'}), 400

    if not allowed_file(image_file.filename):
        return jsonify({'error': 'Unsupported file type'}), 400

    image_bytes = image_file.read()
    image_hash = hashlib.md5(image_bytes).hexdigest()

    # 2. Get a fresh DB connection locally
    conn = get_db_connection()
    cur = conn.cursor()
    
    # Fast check for duplicates before sending to background
    cur.execute(
        "SELECT image_path, position, style, color FROM uploads WHERE username = %s AND md5_hash = %s",
        (username, image_hash)
    )
    existing = cur.fetchone()
    
    cur.close()
    conn.close()

    if existing:
        return jsonify({
            'status': 'completed',
            'position': existing[1],
            'style': existing[2],
            'color': existing[3],
            'image_url': f"http://localhost:5000/image/{os.path.basename(existing[0])}"
        })

    # Save file and dispatch task
    timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
    filename = secure_filename(f"{username}_{timestamp}_{image_file.filename}")
    file_path = os.path.join(UPLOAD_FOLDER, filename)
    
    with open(file_path, 'wb') as f:
        f.write(image_bytes)

    # Dispatch to Celery
    task = celery_instance.send_task('tasks.process_classification', args=[file_path, username, image_hash])
    
    return jsonify({
        'status': 'processing',
        'task_id': task.id
    }), 202

@async_bp.route('/task-status/<task_id>', methods=['GET'])
def get_task_status(task_id):
    task = AsyncResult(task_id, app=celery_instance)
    
    if task.state == 'PENDING':
        return jsonify({'status': 'processing'})
    elif task.state == 'SUCCESS':
        return jsonify(task.result) 
    elif task.state == 'FAILURE':
        return jsonify({'status': 'error', 'error': str(task.info)}), 500
    
    return jsonify({'status': task.state})