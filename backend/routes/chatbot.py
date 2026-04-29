from flask import Blueprint, request, jsonify
from services.gemini_service import analyze_dress_image, suggest_matching_items
from database import conn, cur
import os
import uuid
import json
import datetime
import hashlib
from werkzeug.utils import secure_filename

# Create blueprint for chatbot routes
chatbot_bp = Blueprint('chatbot', __name__)

# Configuration
UPLOAD_DIR = "uploaded_images"
os.makedirs(UPLOAD_DIR, exist_ok=True)

def allowed_file(filename):
    """Check if file extension is allowed"""
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@chatbot_bp.route('/chatbot/upload', methods=['POST'])
def chatbot_upload():
    """Upload image for chatbot indexing"""
    try:
        if 'image' not in request.files:
            return jsonify({'error': 'No image file provided'}), 400
        
        file = request.files['image']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        if not allowed_file(file.filename):
            return jsonify({'error': 'Invalid file type'}), 400
        
        # Get user_id from request (functions as username)
        user_id = request.form.get('user_id')
        if not user_id:
            return jsonify({'error': 'User ID required'}), 400
        
        # Generate unique filename
        filename = secure_filename(file.filename)
        unique_filename = f"{uuid.uuid4().hex}_{filename}"
        file_path = os.path.join(UPLOAD_DIR, unique_filename)

        image_bytes = file.read()
        image_hash = hashlib.md5(image_bytes).hexdigest()

        # Save file
        with open(file_path, 'wb') as f:
            f.write(image_bytes)

        # Process with Gemini
        metadata = analyze_dress_image(file_path)
        
        position = metadata.get("category", "upper")
        style = metadata.get("style", "casual")
        color = metadata.get("primary_color", "black")
        
        # Insert to database
        gemini_metadata_json = json.dumps(metadata)
        cur.execute(
            "INSERT INTO uploads (username, image_path, position, style, color, md5_hash, uploaded_at, gemini_metadata) VALUES (%s, %s, %s, %s, %s, %s, %s, %s) RETURNING id",
            (user_id, file_path, position, style, color, image_hash, datetime.datetime.now(), gemini_metadata_json)
        )
        nid = cur.fetchone()[0]
        conn.commit()
        
        return jsonify({
            'message': 'Image uploaded and indexed successfully',
            'image_id': nid,
            'filename': unique_filename
        }), 200
        
    except Exception as e:
        conn.rollback()
        print("UPLOAD ERROR >>>", repr(e))
        return jsonify({'error': f'Upload failed: {str(e)}'}), 500


@chatbot_bp.route('/chatbot/query', methods=['POST'])
def chatbot_query():
    """Query chatbot for similar images"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No JSON data provided'}), 400
        
        user_id = data.get('user_id')
        query_text = data.get('query', '').strip()
        
        if not user_id:
            return jsonify({'error': 'User ID required'}), 400
        
        if not query_text:
            return jsonify({'error': 'Query text required'}), 400
        
        # Fetch user's wardrobe from DB
        cur.execute("SELECT image_path, style, color, position, gemini_metadata FROM uploads WHERE username = %s", (user_id,))
        rows = cur.fetchall()
        
        wardrobe_items = []
        for r in rows:
            filename = os.path.basename(r[0])
            url = f'http://localhost:5000/image/{filename}'
            meta = r[4] if r[4] else {}
            wardrobe_items.append({
                'url': url,
                'style': r[1],
                'color': r[2],
                'position': r[3],
                'metadata': meta
            })

        # If no items, return empty
        if not wardrobe_items:
            return jsonify({
                'results': [],
                'query': query_text,
                'count': 0
            }), 200

        # Ask Gemini to rank items
        matched_urls = suggest_matching_items(query_text, wardrobe_items)
        
        formatted_results = []
        for url in matched_urls:
            # find style, color for this url
            item = next((x for x in wardrobe_items if x['url'] == url), None)
            if item:
                formatted_results.append({
                    'url': url,
                    'style': item['style'],
                    'color': item['color'],
                    'score': 1.0 # Placeholder since Gemini doesn't return exact distances
                })
        
        return jsonify({
            'results': formatted_results,
            'query': query_text,
            'count': len(formatted_results)
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Query failed: {str(e)}'}), 500

@chatbot_bp.route('/chatbot/status', methods=['GET'])
def chatbot_status():
    """Check chatbot service status"""
    return jsonify({
        'status': 'active',
        'message': 'Chatbot service is running'
    }), 200
